"""Descoberta de URLs em fontes externas."""

from news_scraping_pe.discovery.jobs import iter_jobs_from_jsonl, select_jobs
from news_scraping_pe.discovery.serpapi import (
    SerpApiError,
    build_serpapi_params,
    discover_urls_for_job,
    extract_urls_from_response,
    read_api_key,
)
from news_scraping_pe.discovery.serpapi_runner import (
    SerpApiDiscoveryStats,
    discover_and_store_jobs,
)

__all__ = [
    "SerpApiDiscoveryStats",
    "SerpApiError",
    "build_serpapi_params",
    "discover_and_store_jobs",
    "discover_urls_for_job",
    "extract_urls_from_response",
    "iter_jobs_from_jsonl",
    "read_api_key",
    "select_jobs",
]
