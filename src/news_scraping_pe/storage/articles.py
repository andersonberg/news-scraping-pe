"""Leitura e escrita de artigos coletados (JSONL)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

import jsonschema

from news_scraping_pe.config.paths import default_articles_output_path, schema_path
from news_scraping_pe.log import get_logger
from news_scraping_pe.storage.dedup import normalize_url

logger = get_logger(__name__)

_article_schema_cache: dict[str, Any] | None = None


def _article_schema() -> dict[str, Any]:
    """Carrega e cacheia o JSON Schema de artigos."""
    global _article_schema_cache
    if _article_schema_cache is None:
        schema_file = schema_path("article_schema.json")
        with schema_file.open(encoding="utf-8") as handle:
            _article_schema_cache = json.load(handle)
    return _article_schema_cache


def _resolve_path(path: Path | None) -> Path:
    """Retorna o caminho do arquivo JSONL de artigos."""
    return path if path is not None else default_articles_output_path()


def build_article_id(url: str) -> str:
    """Gera identificador estável a partir da URL normalizada (SHA-256)."""
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _clean_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Remove chaves com valor ``None`` (schema não permite propriedades extras)."""
    return {key: value for key, value in record.items() if value is not None}


def validate_article(record: Mapping[str, Any]) -> dict[str, Any]:
    """
    Valida um artigo contra ``docs/article_schema.json``.

    Raises:
        ValueError: Se o registro for inválido.
    """
    cleaned = _clean_record(record)
    try:
        jsonschema.validate(instance=cleaned, schema=_article_schema())
    except jsonschema.ValidationError as exc:
        msg = f"Artigo inválido: {exc.message}"
        raise ValueError(msg) from exc
    return cleaned


def _encode_article(record: Mapping[str, Any]) -> str:
    """Serializa um artigo validado como linha JSON."""
    return json.dumps(record, ensure_ascii=False)


def _decode_line(line: str, line_number: int) -> dict[str, Any]:
    """Interpreta uma linha do JSONL de artigos."""
    try:
        raw = json.loads(line)
    except json.JSONDecodeError as exc:
        msg = f"Linha {line_number}: JSON inválido"
        raise ValueError(msg) from exc
    if not isinstance(raw, dict):
        msg = f"Linha {line_number}: esperado objeto JSON"
        raise ValueError(msg)
    return validate_article(raw)


def load_existing_article_ids(path: Path | None = None) -> set[str]:
    """Retorna ``article_id`` já presentes no arquivo."""
    target = _resolve_path(path)
    if not target.exists():
        return set()

    ids: set[str] = set()
    for article in iter_articles(path=target):
        ids.add(str(article["article_id"]))
    return ids


def append_article(record: Mapping[str, Any], path: Path | None = None) -> bool:
    """
    Valida e acrescenta um artigo ao JSONL.

    Returns:
        ``True`` se gravou; ``False`` se ``article_id`` já existir.
    """
    written = append_articles([record], path=path)
    return written == 1


def append_articles(
    records: Iterable[Mapping[str, Any]],
    path: Path | None = None,
) -> int:
    """
    Valida e acrescenta artigos novos ao JSONL.

    Artigos com ``article_id`` duplicado são ignorados.

    Returns:
        Quantidade de artigos gravados.
    """
    target = _resolve_path(path)
    existing_ids = load_existing_article_ids(target)

    to_write: list[dict[str, Any]] = []
    skipped = 0

    for record in records:
        validated = validate_article(record)
        article_id = str(validated["article_id"])
        if article_id in existing_ids:
            skipped += 1
            logger.debug("Artigo duplicado ignorado: article_id=%s", article_id)
            continue
        existing_ids.add(article_id)
        to_write.append(validated)

    if skipped:
        logger.info("Ignorados %d artigo(s) duplicado(s)", skipped)

    if not to_write:
        logger.info("Nenhum artigo novo para gravar em %s", target)
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        for article in to_write:
            handle.write(_encode_article(article) + "\n")

    logger.info("Gravados %d artigo(s) em %s", len(to_write), target)
    return len(to_write)


def iter_articles(path: Path | None = None) -> Iterator[dict[str, Any]]:
    """
    Itera sobre artigos do JSONL.

    Raises:
        ValueError: Se alguma linha for inválida.
    """
    target = _resolve_path(path)

    if not target.exists():
        logger.info("Arquivo de artigos não existe: %s", target)
        return

    logger.info("Lendo artigos de %s", target)
    count = 0

    with target.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            yield _decode_line(stripped, line_number)
            count += 1

    logger.info("Lidos %d artigo(s) de %s", count, target)


def read_articles(path: Path | None = None) -> list[dict[str, Any]]:
    """Carrega todos os artigos em uma lista."""
    return list(iter_articles(path=path))
