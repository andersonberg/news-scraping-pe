"""Persistência local de dados coletados (URLs pendentes, artigos)."""

from news_scraping_pe.storage.articles import (
    append_article,
    append_articles,
    build_article_id,
    iter_articles,
    read_articles,
    validate_article,
)
from news_scraping_pe.storage.dedup import normalize_url, url_dedup_key, url_host
from news_scraping_pe.storage.models import PendingUrl
from news_scraping_pe.storage.urls import (
    append_pending_url,
    append_pending_urls,
    iter_pending_urls,
    read_pending_urls,
)

__all__ = [
    "PendingUrl",
    "append_article",
    "append_articles",
    "append_pending_url",
    "append_pending_urls",
    "build_article_id",
    "iter_articles",
    "iter_pending_urls",
    "read_articles",
    "read_pending_urls",
    "validate_article",
    "normalize_url",
    "url_dedup_key",
    "url_host",
]
