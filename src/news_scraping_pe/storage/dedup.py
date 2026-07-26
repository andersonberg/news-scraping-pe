"""Normalização e deduplicação de URLs."""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from news_scraping_pe.log import get_logger
from news_scraping_pe.storage.models import PendingUrl

logger = get_logger(__name__)

_TRACKING_QUERY_PARAMS = frozenset(
    {
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "ref",
        "referrer",
        "utm_campaign",
        "utm_content",
        "utm_id",
        "utm_medium",
        "utm_source",
        "utm_term",
    }
)


def normalize_url(url: str) -> str:
    """
      Produz uma forma canônica da URL para comparação e armazenamento.

      Remove fragmento, parâmetros de rastreamento comuns, normaliza host/esquema
    em minúsculas e remove barra final do caminho (exceto raiz ``/``).
    """
    stripped = url.strip()
    parsed = urlparse(stripped)

    if not parsed.scheme or not parsed.netloc:
        logger.warning("URL sem esquema/host reconhecível, mantendo original: %s", stripped)
        return stripped

    query_pairs = parse_qs(parsed.query, keep_blank_values=False)
    filtered_query = {
        key: values
        for key, values in query_pairs.items()
        if key.lower() not in _TRACKING_QUERY_PARAMS
    }
    sorted_query = urlencode(sorted(filtered_query.items()), doseq=True)

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            sorted_query,
            "",
        )
    )


def url_dedup_key(url: str) -> str:
    """Chave estável para detectar duplicatas (URL normalizada)."""
    return normalize_url(url)


def url_host(url: str) -> str:
    """Extrai o host (netloc) em minúsculas; string vazia se não parseável."""
    return urlparse(url.strip()).netloc.lower()


def load_existing_url_keys(keys_source: Iterable[str]) -> set[str]:
    """Monta um conjunto de chaves já conhecidas a partir de URLs brutas ou normalizadas."""
    return {url_dedup_key(url) for url in keys_source}


def filter_unique_pending_urls(
    records: Iterable[PendingUrl],
    existing_keys: set[str],
) -> tuple[list[PendingUrl], int]:
    """
    Remove duplicatas dentro do lote e em relação a ``existing_keys``.

    Returns:
        Tupla ``(registros únicos com URL normalizada, quantidade ignorada)``.
    """
    unique: list[PendingUrl] = []
    seen = set(existing_keys)
    skipped = 0

    for record in records:
        key = url_dedup_key(record["url"])
        if key in seen:
            skipped += 1
            logger.debug(
                "URL duplicada ignorada (job_id=%s): %s",
                record["job_id"],
                record["url"],
            )
            continue

        seen.add(key)
        unique.append(
            PendingUrl(
                url=key,
                job_id=record["job_id"],
                discovered_via=record["discovered_via"],
            )
        )

    if skipped:
        logger.info("Ignoradas %d URL(s) duplicada(s) no lote", skipped)

    return unique, skipped
