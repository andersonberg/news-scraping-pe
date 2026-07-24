"""Log local de jobs SerpAPI já tentados (rastreio de consumo de créditos)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from news_scraping_pe.config.paths import default_serpapi_usage_log_path
from news_scraping_pe.log import get_logger
from news_scraping_pe.storage.models import JobAttempt

logger = get_logger(__name__)

_REQUIRED_FIELDS = ("job_id", "attempted_at", "status", "urls_found")


def _resolve_path(path: Path | None) -> Path:
    """Retorna o caminho do log de uso (padrão ou explícito)."""
    return path if path is not None else default_serpapi_usage_log_path()


def append_job_attempt(record: JobAttempt, path: Path | None = None) -> None:
    """Acrescenta uma tentativa de job ao log local (sem deduplicação)."""
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.debug("Tentativa registrada: job_id=%s status=%s", record["job_id"], record["status"])


def iter_job_attempts(path: Path | None = None) -> Iterator[JobAttempt]:
    """
    Itera sobre as tentativas registradas no log local.

    Raises:
        ValueError: Se alguma linha não for JSON válido ou faltar campo obrigatório.
    """
    target = _resolve_path(path)

    if not target.exists():
        return

    with target.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError as exc:
                msg = f"Linha {line_number} em {target}: JSON inválido"
                raise ValueError(msg) from exc

            missing = [field for field in _REQUIRED_FIELDS if field not in raw]
            if missing:
                msg = f"Linha {line_number} em {target}: campos ausentes {missing}"
                raise ValueError(msg)

            yield JobAttempt(
                job_id=raw["job_id"],
                attempted_at=raw["attempted_at"],
                status=raw["status"],
                urls_found=raw["urls_found"],
            )


def load_attempted_job_ids(path: Path | None = None) -> set[str]:
    """Retorna o conjunto de ``job_id`` já registrados no log local (qualquer status)."""
    return {attempt["job_id"] for attempt in iter_job_attempts(path=path)}
