"""Descoberta de URLs em fontes externas."""

from news_scraping_pe.discovery.serpapi import (
    SerpApiError,
    build_serpapi_params,
    discover_urls_for_job,
    extract_urls_from_response,
    read_api_key,
)

__all__ = [
    "SerpApiError",
    "build_serpapi_params",
    "discover_urls_for_job",
    "extract_urls_from_response",
    "read_api_key",
]
