"""Leitura e seleção de jobs a partir de JSONL expandido."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

from news_scraping_pe.log import get_logger

logger = get_logger(__name__)


def iter_jobs_from_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """
    Itera sobre jobs em um arquivo JSONL (uma linha = um job).

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se alguma linha não for JSON válido.
    """
    if not path.exists():
        msg = f"Arquivo de jobs não encontrado: {path}"
        raise FileNotFoundError(msg)

    logger.info("Lendo jobs de %s", path)

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError as exc:
                msg = f"Linha {line_number} em {path}: JSON inválido"
                raise ValueError(msg) from exc
            if not isinstance(raw, dict):
                msg = f"Linha {line_number} em {path}: esperado objeto JSON"
                raise ValueError(msg)
            yield raw


def job_matches_filters(
    job: Mapping[str, Any],
    *,
    job_id: str | None,
    candidate_id: str | None,
    portal_id: str | None,
) -> bool:
    """Verifica se o job passa nos filtros informados (None = sem filtro)."""
    if job_id is not None and job.get("job_id") != job_id:
        return False
    if candidate_id is not None and job.get("candidate_id") != candidate_id:
        return False
    return not (portal_id is not None and job.get("portal_id") != portal_id)


def select_jobs(
    jobs: Iterable[Mapping[str, Any]],
    *,
    job_id: str | None = None,
    candidate_id: str | None = None,
    portal_id: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Filtra e limita a lista de jobs.

    Args:
        jobs: Jobs de origem.
        job_id: Mantém só este ``job_id`` (exato).
        candidate_id: Filtra por candidato.
        portal_id: Filtra por portal.
        limit: Máximo de jobs após filtros (``None`` = todos).
    """
    selected: list[dict[str, Any]] = []

    for job in jobs:
        if not job_matches_filters(
            job,
            job_id=job_id,
            candidate_id=candidate_id,
            portal_id=portal_id,
        ):
            continue
        selected.append(dict(job))
        if limit is not None and len(selected) >= limit:
            break

    logger.info("Selecionados %d job(s) para processamento", len(selected))
    return selected
