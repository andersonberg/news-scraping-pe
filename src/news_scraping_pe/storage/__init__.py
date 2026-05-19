"""Persistência local de dados coletados (URLs pendentes, artigos)."""

from news_scraping_pe.storage.dedup import normalize_url, url_dedup_key
from news_scraping_pe.storage.models import PendingUrl
from news_scraping_pe.storage.urls import (
    append_pending_url,
    append_pending_urls,
    iter_pending_urls,
    read_pending_urls,
)

__all__ = [
    "PendingUrl",
    "append_pending_url",
    "append_pending_urls",
    "iter_pending_urls",
    "read_pending_urls",
    "normalize_url",
    "url_dedup_key",
]
