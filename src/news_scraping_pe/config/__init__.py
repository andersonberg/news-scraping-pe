"""Configuração de buscas (YAML + JSON Schema)."""

from news_scraping_pe.config.loader import (
    expand_query_jobs,
    load_search_config,
    validate_search_config,
)

__all__ = ["expand_query_jobs", "load_search_config", "validate_search_config"]
