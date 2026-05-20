"""Extração de conteúdo de páginas de notícias."""

from news_scraping_pe.extraction.fetch_runner import (
    FetchArticlesStats,
    fetch_and_store_pending_urls,
)
from news_scraping_pe.extraction.text import (
    extract_raw_text_from_html,
    fetch_html,
    fetch_raw_text,
)

__all__ = [
    "FetchArticlesStats",
    "extract_raw_text_from_html",
    "fetch_and_store_pending_urls",
    "fetch_html",
    "fetch_raw_text",
]
