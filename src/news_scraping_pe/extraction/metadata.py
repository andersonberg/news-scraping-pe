"""Metadados de artigo extraídos do HTML."""

from __future__ import annotations

from trafilatura.metadata import extract_metadata

from news_scraping_pe.log import get_logger

logger = get_logger(__name__)


def _normalize_date(raw_date: str) -> str | None:
    """Converte data para ``YYYY-MM-DD`` quando possível."""
    cleaned = raw_date.strip()
    if len(cleaned) >= 10 and cleaned[4] == "-":
        return cleaned[:10]
    return None


def extract_title_and_published_at(
    html: str,
    url: str,
    *,
    fallback_date: str,
    raw_text: str | None = None,
) -> tuple[str, str]:
    """
    Obtém título e data de publicação a partir do HTML.

    Args:
        html: HTML da página.
        url: URL do artigo.
        fallback_date: Data ISO ``YYYY-MM-DD`` usada se não houver metadado.
        raw_text: Texto extraído, usado como fallback de título.

    Returns:
        Tupla ``(title, published_at)`` com ``published_at`` em ``YYYY-MM-DD``.
    """
    metadata = extract_metadata(html, default_url=url)

    title = ""
    if metadata and metadata.title:
        title = metadata.title.strip()

    if not title and raw_text:
        first_line = raw_text.strip().splitlines()[0].strip()
        title = first_line[:200] if first_line else ""

    if not title:
        title = "Sem título"
        logger.warning("Título não encontrado para %s; usando fallback", url)

    published_at = fallback_date
    if metadata and metadata.date:
        normalized = _normalize_date(str(metadata.date))
        if normalized:
            published_at = normalized
        else:
            logger.warning(
                "Data não normalizada para %s (%s); usando fallback %s",
                url,
                metadata.date,
                fallback_date,
            )

    return title, published_at
