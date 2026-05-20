"""Orquestra descoberta SerpAPI e gravação em urls pendentes."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from news_scraping_pe.discovery.serpapi import SerpApiError, discover_urls_for_job, read_api_key
from news_scraping_pe.log import get_logger
from news_scraping_pe.storage.models import PendingUrl
from news_scraping_pe.storage.urls import append_pending_urls

logger = get_logger(__name__)

DISCOVERED_VIA_SERPAPI = "serpapi"


@dataclass(frozen=True)
class SerpApiDiscoveryStats:
    """Resumo de uma execução de descoberta SerpAPI."""

    jobs_processed: int
    jobs_failed: int
    urls_discovered: int
    urls_stored: int


def build_pending_records(urls: Iterable[str], job: Mapping[str, Any]) -> list[PendingUrl]:
    """Converte URLs descobertas em registros para ``urls_pending.jsonl``."""
    job_id = str(job["job_id"])
    return [
        PendingUrl(url=url, job_id=job_id, discovered_via=DISCOVERED_VIA_SERPAPI) for url in urls
    ]


def discover_and_store_jobs(
    jobs: Iterable[Mapping[str, Any]],
    *,
    urls_path: Path | None = None,
    client: httpx.Client | None = None,
) -> SerpApiDiscoveryStats:
    """
    Para cada job, consulta a SerpAPI e grava URLs novas em ``urls_pending.jsonl``.

    Jobs com erro na API são registrados em log e contados em ``jobs_failed``;
    o processamento continua nos demais.
    """
    api_key = read_api_key()
    jobs_processed = 0
    jobs_failed = 0
    urls_discovered = 0
    urls_stored = 0

    owns_client = client is None
    http_client = client if client is not None else httpx.Client(timeout=30.0)

    try:
        for job in jobs:
            job_id = job.get("job_id", "?")
            jobs_processed += 1
            logger.info("Processando job %d: job_id=%s", jobs_processed, job_id)

            try:
                urls = discover_urls_for_job(job, api_key=api_key, client=http_client)
            except SerpApiError:
                jobs_failed += 1
                logger.exception("Falha SerpAPI no job_id=%s", job_id)
                continue

            urls_discovered += len(urls)
            records = build_pending_records(urls, job)
            stored = append_pending_urls(records, path=urls_path)
            urls_stored += stored
            logger.info(
                "Job %s: %d URL(s) descoberta(s), %d gravada(s) como nova(s)",
                job_id,
                len(urls),
                stored,
            )
    finally:
        if owns_client:
            http_client.close()

    stats = SerpApiDiscoveryStats(
        jobs_processed=jobs_processed,
        jobs_failed=jobs_failed,
        urls_discovered=urls_discovered,
        urls_stored=urls_stored,
    )
    logger.info(
        "Descoberta SerpAPI concluída: jobs=%d falhas=%d urls_descobertas=%d urls_gravadas=%d",
        stats.jobs_processed,
        stats.jobs_failed,
        stats.urls_discovered,
        stats.urls_stored,
    )
    return stats
