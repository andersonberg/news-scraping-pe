"""Carrega e valida config/searches.yaml; expande jobs de busca."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from news_scraping_pe.config.paths import schema_path


def load_search_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    if not isinstance(data, dict):
        msg = f"Config inválida (esperado mapping): {path}"
        raise ValueError(msg)
    return data


def validate_search_config(path: Path) -> dict[str, Any]:
    import json

    config = load_search_config(path)
    schema_file = schema_path("search_config_schema.json")
    with schema_file.open(encoding="utf-8") as fh:
        schema = json.load(fh)
    jsonschema.validate(instance=config, schema=schema)
    return config


def _build_query_string(
    candidate_name: str,
    keywords: list[str],
    extra_keywords: list[str] | None,
) -> str:
    parts = [f'"{candidate_name}"', *keywords]
    if extra_keywords:
        parts.extend(f'"{k}"' if " " in k else k for k in extra_keywords)
    return " ".join(parts)


def _slugify_variant(name: str) -> str:
    """Slug ASCII, seguro para uso como 4º segmento do job_id (nunca contém '__')."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
    return slug or "sem-variante"


def expand_query_jobs(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Gera um job por candidato × termo × variante de nome × portal habilitado."""
    jobs: list[dict[str, Any]] = []
    terms = config["search_terms"]
    candidates = [c for c in config["candidates"] if c.get("enabled", True)]
    portals = [p for p in config["portals"] if p.get("enabled", True)]

    for candidate in candidates:
        names: list[str] = candidate.get("search_name_variants") or [candidate["name"]]
        window = candidate["query_window"]
        for term in terms:
            keywords: list[str] = term["keywords"]
            extra: list[str] | None = term.get("extra_keywords")
            for display_name in names:
                query = _build_query_string(display_name, keywords, extra)
                variant_slug = _slugify_variant(display_name)
                for portal in portals:
                    job_id = f"{candidate['id']}__{term['id']}__{portal['id']}__{variant_slug}"
                    jobs.append(
                        {
                            "job_id": job_id,
                            "candidate_id": candidate["id"],
                            "candidate_name": candidate["name"],
                            "search_name_variant": display_name,
                            "office": candidate["office"],
                            "election_year": candidate["election_year"],
                            "search_term_id": term["id"],
                            "search_query": query,
                            "portal_id": portal["id"],
                            "site_domain": portal["domain"],
                            "query_window_start": window["start"],
                            "query_window_end": window["end"],
                            "discovered_via": f"{portal.get('spider', portal['id'])}_spider",
                        }
                    )
    return jobs
