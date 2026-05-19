"""Persistência local de dados coletados (URLs pendentes, artigos)."""

from news_scraping_pe.storage.urls import (
    PendingUrl,
    append_pending_url,
    append_pending_urls,
    iter_pending_urls,
)

__all__ = [
    "PendingUrl",
    "append_pending_url",
    "append_pending_urls",
    "iter_pending_urls",
]
