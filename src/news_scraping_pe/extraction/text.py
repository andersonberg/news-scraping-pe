"""Extração de texto bruto de páginas de notícias."""

from __future__ import annotations

import os

import httpx
import trafilatura

from news_scraping_pe.log import get_logger

logger = get_logger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)
_DEFAULT_HEADERS = {
    "User-Agent": _DEFAULT_USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}


def _resolve_timeout(timeout: float | None) -> float:
    """Resolve timeout explícito ou variável ``EXTRACTION_TIMEOUT_SECONDS``."""
    if timeout is not None:
        return timeout
    env_value = os.getenv("EXTRACTION_TIMEOUT_SECONDS", "").strip()
    if env_value:
        return float(env_value)
    return _DEFAULT_TIMEOUT_SECONDS


def fetch_html(
    url: str,
    client: httpx.Client,
    *,
    timeout: float | None = None,
) -> str | None:
    """
    Baixa o HTML de uma URL.

    Returns:
        Conteúdo HTML ou ``None`` em falha HTTP/recuperável.
    """
    resolved_timeout = _resolve_timeout(timeout)
    logger.info("Baixando HTML: %s", url)

    try:
        response = client.get(url, timeout=resolved_timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Falha ao baixar %s: %s", url, exc)
        return None

    if not response.text or not response.text.strip():
        logger.warning("Resposta vazia para %s", url)
        return None

    logger.info("HTML recebido de %s (%d bytes)", url, len(response.text))
    return response.text


def extract_raw_text_from_html(html: str, url: str) -> str | None:
    """
    Extrai texto principal do HTML com trafilatura.

    Returns:
        Texto bruto ou ``None`` se a extração não produzir conteúdo útil.
    """
    logger.debug("Extraindo texto com trafilatura: %s", url)

    text = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=False,
    )

    if text is None or not text.strip():
        logger.warning("Trafilatura não extraiu texto de %s", url)
        return None

    cleaned = text.strip()
    logger.info("Texto extraído de %s (%d caracteres)", url, len(cleaned))
    return cleaned


def create_http_client() -> httpx.Client:
    """Cria cliente HTTP padrão para extração de artigos."""
    return httpx.Client(headers=_DEFAULT_HEADERS, follow_redirects=True)


def fetch_raw_text(
    url: str,
    *,
    client: httpx.Client | None = None,
    timeout: float | None = None,
) -> str | None:
    """
    Baixa uma URL e devolve o texto bruto da matéria.

    Args:
        url: URL do artigo.
        client: Cliente HTTP reutilizável; criado se omitido.
        timeout: Timeout em segundos (ou ``EXTRACTION_TIMEOUT_SECONDS``).

    Returns:
        Texto da notícia ou ``None`` se download/extração falhar.
    """
    owns_client = client is None
    http_client = client if client is not None else create_http_client()

    try:
        html = fetch_html(url, http_client, timeout=timeout)
        if html is None:
            return None
        return extract_raw_text_from_html(html, url)
    finally:
        if owns_client:
            http_client.close()
