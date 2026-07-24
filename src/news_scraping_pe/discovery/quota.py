"""Cálculo de status de cota SerpAPI e sugestão de próximo lote de jobs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from news_scraping_pe.discovery.jobs import job_matches_filters
from news_scraping_pe.discovery.usage_log import iter_job_attempts
from news_scraping_pe.log import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class QuotaStatus:
    """Resumo do progresso de jobs SerpAPI e sugestão de próximo lote."""

    total_jobs: int
    done_all_time: int
    done_this_month: int
    remaining_total: int
    remaining_quota_this_month: int
    next_batch_job_ids: list[str]


def compute_quota_status(
    jobs: Iterable[Mapping[str, Any]],
    *,
    usage_log_path: Path | None = None,
    monthly_quota: int,
    candidate_id: str | None = None,
    portal_id: str | None = None,
    month: str | None = None,
) -> QuotaStatus:
    """
    Calcula o progresso de jobs SerpAPI e sugere o próximo lote a rodar.

    Jobs são considerados na ordem em que aparecem em ``jobs`` (ordem
    sequencial de ``queries.expanded.jsonl``), preenchendo o lote sugerido
    até ``monthly_quota`` menos os créditos já usados neste mês. ``month``
    é o mês corrente em formato ``YYYY-MM`` (padrão: mês atual em UTC).
    """
    current_month = month if month is not None else datetime.now(UTC).strftime("%Y-%m")

    scoped_jobs = [
        dict(job)
        for job in jobs
        if job_matches_filters(job, job_id=None, candidate_id=candidate_id, portal_id=portal_id)
    ]
    scoped_job_ids = {str(job["job_id"]) for job in scoped_jobs}

    attempted_job_ids: set[str] = set()
    done_this_month_ids: set[str] = set()
    for attempt in iter_job_attempts(path=usage_log_path):
        job_id = attempt["job_id"]
        if job_id not in scoped_job_ids:
            continue
        attempted_job_ids.add(job_id)
        if attempt["attempted_at"].startswith(current_month):
            done_this_month_ids.add(job_id)

    remaining_quota_this_month = max(monthly_quota - len(done_this_month_ids), 0)

    next_batch: list[str] = []
    for job in scoped_jobs:
        job_id = str(job["job_id"])
        if job_id in attempted_job_ids:
            continue
        if len(next_batch) >= remaining_quota_this_month:
            break
        next_batch.append(job_id)

    status = QuotaStatus(
        total_jobs=len(scoped_jobs),
        done_all_time=len(attempted_job_ids),
        done_this_month=len(done_this_month_ids),
        remaining_total=len(scoped_jobs) - len(attempted_job_ids),
        remaining_quota_this_month=remaining_quota_this_month,
        next_batch_job_ids=next_batch,
    )
    logger.info(
        "Status de cota: total=%d feitos=%d feitos_no_mes=%d restantes=%d proximo_lote=%d",
        status.total_jobs,
        status.done_all_time,
        status.done_this_month,
        status.remaining_total,
        len(status.next_batch_job_ids),
    )
    return status
