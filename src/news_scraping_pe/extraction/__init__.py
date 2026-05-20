"""Extração de conteúdo de páginas de notícias."""

from news_scraping_pe.extraction.text import (
    extract_raw_text_from_html,
    fetch_html,
    fetch_raw_text,
)

__all__ = [
    "extract_raw_text_from_html",
    "fetch_html",
    "fetch_raw_text",
]
