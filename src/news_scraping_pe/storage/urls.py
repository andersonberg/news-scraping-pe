"""Leitura e escrita de URLs pendentes de extração (JSONL)."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import TypedDict

from news_scraping_pe.config.paths import default_urls_pending_path
from news_scraping_pe.log import get_logger

logger = get_logger(__name__)

_REQUIRED_FIELDS = ("url", "job_id", "discovered_via")


class PendingUrl(TypedDict):
    """Registro mínimo de uma URL descoberta e ainda não extraída."""

    url: str
    job_id: str
    discovered_via: str


def _resolve_path(path: Path | None) -> Path:
    """Retorna o caminho do arquivo JSONL (padrão ou explícito)."""
    return path if path is not None else default_urls_pending_path()


def _validate_record(record: Mapping[str, object]) -> PendingUrl:
    """
    Garante que o registro contém os campos obrigatórios com valores não vazios.

    Raises:
        ValueError: Se algum campo obrigatório faltar ou for inválido.
    """
    missing = [field for field in _REQUIRED_FIELDS if field not in record]
    if missing:
        msg = f"Campos obrigatórios ausentes: {', '.join(missing)}"
        raise ValueError(msg)

    url = record["url"]
    job_id = record["job_id"]
    discovered_via = record["discovered_via"]

    if not isinstance(url, str) or not url.strip():
        raise ValueError("Campo 'url' deve ser uma string não vazia")
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("Campo 'job_id' deve ser uma string não vazia")
    if not isinstance(discovered_via, str) or not discovered_via.strip():
        raise ValueError("Campo 'discovered_via' deve ser uma string não vazia")

    return PendingUrl(
        url=url.strip(),
        job_id=job_id.strip(),
        discovered_via=discovered_via.strip(),
    )


def _encode_record(record: PendingUrl) -> str:
    """Serializa um registro como linha JSON."""
    return json.dumps(record, ensure_ascii=False)


def _decode_line(line: str, line_number: int) -> PendingUrl:
    """
    Interpreta uma linha do JSONL.

    Raises:
        ValueError: Se a linha não for JSON válido ou o registro for inválido.
    """
    try:
        raw = json.loads(line)
    except json.JSONDecodeError as exc:
        msg = f"Linha {line_number}: JSON inválido"
        raise ValueError(msg) from exc

    if not isinstance(raw, dict):
        msg = f"Linha {line_number}: esperado objeto JSON"
        raise ValueError(msg)

    return _validate_record(raw)


def append_pending_url(record: PendingUrl | Mapping[str, object], path: Path | None = None) -> None:
    """
    Acrescenta uma URL pendente ao final do arquivo JSONL.

    Cria o diretório pai do arquivo se ainda não existir.
    """
    append_pending_urls([record], path=path)


def append_pending_urls(
    records: Iterable[PendingUrl | Mapping[str, object]],
    path: Path | None = None,
) -> int:
    """
    Acrescenta várias URLs pendentes ao arquivo JSONL.

    Returns:
        Quantidade de registros gravados.
    """
    target = _resolve_path(path)
    validated = [_validate_record(record) for record in records]

    if not validated:
        logger.debug("Nenhuma URL pendente para gravar em %s", target)
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("a", encoding="utf-8") as handle:
        for record in validated:
            handle.write(_encode_record(record) + "\n")

    logger.info("Gravadas %d URL(s) pendente(s) em %s", len(validated), target)
    return len(validated)


def iter_pending_urls(path: Path | None = None) -> Iterator[PendingUrl]:
    """
    Itera sobre todas as URLs pendentes do arquivo JSONL.

    Yields:
        Registros validados na ordem em que aparecem no arquivo.

    Raises:
        ValueError: Se alguma linha não for JSON válido ou estiver incompleta.
    """
    target = _resolve_path(path)

    if not target.exists():
        logger.info("Arquivo de URLs pendentes não existe: %s", target)
        return

    logger.info("Lendo URLs pendentes de %s", target)
    count = 0

    with target.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            yield _decode_line(stripped, line_number)
            count += 1

    logger.info("Lidas %d URL(s) pendente(s) de %s", count, target)


def read_pending_urls(path: Path | None = None) -> list[PendingUrl]:
    """Carrega todas as URLs pendentes em uma lista (conveniência sobre ``iter_pending_urls``)."""
    return list(iter_pending_urls(path=path))
