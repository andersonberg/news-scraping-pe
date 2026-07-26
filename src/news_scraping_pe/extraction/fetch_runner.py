"""Orquestra extração de artigos a partir de URLs pendentes."""

from __future__ import annotations

import os
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any

import httpx

from news_scraping_pe.extraction.metadata import extract_title_and_published_at
from news_scraping_pe.extraction.text import (
    create_http_client,
    extract_raw_text_from_html,
    fetch_html,
)
from news_scraping_pe.log import get_logger
from news_scraping_pe.storage.articles import append_articles, build_article_id
from news_scraping_pe.storage.dedup import url_host
from news_scraping_pe.storage.models import PendingUrl

logger = get_logger(__name__)

_DEFAULT_DOMAIN_DELAY_SECONDS = 2.0


def _resolve_domain_delay(delay: float | None) -> float:
    """Resolve atraso explícito ou variável ``FETCH_DOMAIN_DELAY_SECONDS``."""
    if delay is not None:
        return delay
    env_value = os.getenv("FETCH_DOMAIN_DELAY_SECONDS", "").strip()
    if env_value:
        return float(env_value)
    return _DEFAULT_DOMAIN_DELAY_SECONDS


@dataclass(frozen=True)
class FetchArticlesStats:
    """Resumo da execução de ``fetch-articles``."""

    urls_processed: int
    urls_failed: int
    articles_stored: int
    urls_missing_job: int


def build_article_record(
    pending: PendingUrl,
    job: Mapping[str, Any],
    *,
    raw_text: str,
    title: str,
    published_at: str,
) -> dict[str, Any]:
    """Monta um registro de artigo alinhado ao schema, a partir do job e da URL pendente."""
    collected_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    record: dict[str, Any] = {
        "article_id": build_article_id(pending["url"]),
        "url": pending["url"],
        "portal_id": job["portal_id"],
        "title": title,
        "published_at": published_at,
        "raw_text": raw_text,
        "candidate_id": job["candidate_id"],
        "election_year": job["election_year"],
        "office": job["office"],
        "search_term_id": job["search_term_id"],
        "query_window_start": job["query_window_start"],
        "query_window_end": job["query_window_end"],
        "discovered_via": pending["discovered_via"],
        "collected_at": collected_at,
        "language": "pt-BR",
        "extraction_method": "trafilatura",
    }

    if job.get("candidate_name"):
        record["candidate_name"] = job["candidate_name"]
    if job.get("search_query"):
        record["search_query"] = job["search_query"]

    return record


def fetch_article_from_pending(
    pending: PendingUrl,
    job: Mapping[str, Any],
    client: httpx.Client,
) -> dict[str, Any] | None:
    """
    Baixa e extrai um artigo a partir de uma URL pendente.

    Returns:
        Registro de artigo pronto para validação/gravação, ou ``None`` em falha.
    """
    url = pending["url"]
    html = fetch_html(url, client)
    if html is None:
        return None

    raw_text = extract_raw_text_from_html(html, url)
    if raw_text is None:
        return None

    fallback_date = str(job["query_window_end"])
    title, published_at = extract_title_and_published_at(
        html,
        url,
        fallback_date=fallback_date,
        raw_text=raw_text,
    )

    return build_article_record(
        pending,
        job,
        raw_text=raw_text,
        title=title,
        published_at=published_at,
    )


def interleave_by_host(pending: list[PendingUrl]) -> list[PendingUrl]:
    """Reordena para alternar hosts (round-robin), preservando conjunto e ordem por host."""
    groups: dict[str, list[PendingUrl]] = {}
    for record in pending:
        groups.setdefault(url_host(record["url"]), []).append(record)

    result: list[PendingUrl] = []
    queues = list(groups.values())
    while queues:
        queues = [q for q in queues if q]
        for q in queues:
            result.append(q.pop(0))
    return result


def fetch_and_store_pending_urls(
    pending_urls: Iterable[PendingUrl],
    jobs_index: Mapping[str, Mapping[str, Any]],
    *,
    articles_path: Path | None = None,
    client: httpx.Client | None = None,
    domain_delay: float | None = None,
) -> FetchArticlesStats:
    """
    Processa URLs pendentes, extrai texto e grava artigos novos.

    URLs cujo ``job_id`` não existir no índice são ignoradas (contadas em
    ``urls_missing_job``). Acessos consecutivos ao mesmo host são espaçados
    por ``domain_delay`` segundos.
    """
    urls_processed = 0
    urls_failed = 0
    urls_missing_job = 0
    articles_stored = 0

    owns_client = client is None
    http_client = client if client is not None else create_http_client()
    delay = _resolve_domain_delay(domain_delay)
    last_hit: dict[str, float] = {}
    pending_list = interleave_by_host(list(pending_urls))

    try:
        for pending in pending_list:
            urls_processed += 1
            job_id = pending["job_id"]
            job = jobs_index.get(job_id)

            if job is None:
                urls_missing_job += 1
                logger.error("Job não encontrado no índice: %s (url=%s)", job_id, pending["url"])
                continue

            host = url_host(pending["url"])
            previous = last_hit.get(host)
            if previous is not None:
                elapsed = monotonic() - previous
                remaining = delay - elapsed
                if remaining > 0:
                    logger.debug("Aguardando %.1fs antes de novo acesso a %s", remaining, host)
                    time.sleep(remaining)
            last_hit[host] = monotonic()

            logger.info("Extraindo artigo %d: %s", urls_processed, pending["url"])
            article = fetch_article_from_pending(pending, job, http_client)

            if article is None:
                urls_failed += 1
                logger.warning("Falha na extração: %s", pending["url"])
                continue

            stored = append_articles([article], path=articles_path)
            articles_stored += stored
    finally:
        if owns_client:
            http_client.close()

    stats = FetchArticlesStats(
        urls_processed=urls_processed,
        urls_failed=urls_failed,
        articles_stored=articles_stored,
        urls_missing_job=urls_missing_job,
    )
    logger.info(
        "Fetch-articles concluído: processadas=%d falhas=%d gravadas=%d sem_job=%d",
        stats.urls_processed,
        stats.urls_failed,
        stats.articles_stored,
        stats.urls_missing_job,
    )
    return stats
