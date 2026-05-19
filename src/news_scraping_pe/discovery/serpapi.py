"""Cliente SerpAPI para descoberta de URLs via Google News."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

import httpx

from news_scraping_pe.log import get_logger

logger = get_logger(__name__)

SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
_DEFAULT_TIMEOUT_SECONDS = 30.0


class SerpApiError(Exception):
    """Erro ao consultar ou interpretar resposta da SerpAPI."""


def read_api_key() -> str:
    """
    Lê a chave da API a partir da variável ``SERPAPI_API_KEY``.

    Raises:
        SerpApiError: Se a variável não estiver definida ou estiver vazia.
    """
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not api_key:
        msg = "Variável de ambiente SERPAPI_API_KEY não configurada"
        raise SerpApiError(msg)
    return api_key


def _format_date_for_tbs(iso_date: str) -> str:
    """Converte ``YYYY-MM-DD`` para o formato ``M/D/YYYY`` usado pelo parâmetro ``tbs``."""
    year, month, day = iso_date.split("-")
    return f"{int(month)}/{int(day)}/{year}"


def build_serpapi_params(job: Mapping[str, Any]) -> dict[str, str]:
    """
    Monta parâmetros da SerpAPI a partir de um job expandido.

    Usa ``job['serpapi_params']`` quando presente; caso contrário deriva de
    ``search_query``, ``site_domain`` e janela de datas do job.
    """
    existing = job.get("serpapi_params")
    if isinstance(existing, dict):
        return {str(key): str(value) for key, value in existing.items()}

    query = str(job["search_query"])
    site_domain = job.get("site_domain")
    if site_domain:
        query = f"{query} site:{site_domain}"

    window_start = str(job["query_window_start"])
    window_end = str(job["query_window_end"])
    tbs = (
        f"cdr:1,cd_min:{_format_date_for_tbs(window_start)},"
        f"cd_max:{_format_date_for_tbs(window_end)}"
    )

    return {
        "engine": "google_news",
        "q": query,
        "tbs": tbs,
        "gl": "br",
        "hl": "pt",
    }


def extract_urls_from_response(payload: Mapping[str, Any]) -> list[str]:
    """
    Extrai links de artigos do JSON retornado pela SerpAPI.

    Consulta ``news_results`` e, se vazio, ``organic_results``.
    """
    urls: list[str] = []

    for section in ("news_results", "organic_results"):
        results = payload.get(section)
        if not isinstance(results, list):
            continue
        for item in results:
            if not isinstance(item, dict):
                continue
            link = item.get("link")
            if isinstance(link, str) and link.strip():
                urls.append(link.strip())

    logger.info("Extraídas %d URL(s) da resposta SerpAPI", len(urls))
    return urls


def fetch_search_results(
    params: Mapping[str, str],
    api_key: str,
    client: httpx.Client,
) -> dict[str, Any]:
    """
    Executa uma busca na SerpAPI e retorna o JSON da resposta.

    Raises:
        SerpApiError: Em falha HTTP ou corpo JSON inválido.
    """
    request_params = dict(params)
    request_params["api_key"] = api_key

    logger.info("Consultando SerpAPI (engine=%s)", request_params.get("engine", "?"))
    safe_params = {key: value for key, value in request_params.items() if key != "api_key"}
    logger.debug("Parâmetros SerpAPI (sem api_key): %s", safe_params)

    try:
        response = client.get(SERPAPI_SEARCH_URL, params=request_params)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        msg = f"Falha HTTP na SerpAPI: {exc}"
        logger.error(msg)
        raise SerpApiError(msg) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        msg = "Resposta SerpAPI não é JSON válido"
        logger.error(msg)
        raise SerpApiError(msg) from exc

    if not isinstance(payload, dict):
        msg = "Resposta SerpAPI deve ser um objeto JSON"
        raise SerpApiError(msg)

    error_field = payload.get("error")
    if isinstance(error_field, str) and error_field:
        msg = f"SerpAPI retornou erro: {error_field}"
        logger.error(msg)
        raise SerpApiError(msg)

    logger.info("Resposta SerpAPI recebida com sucesso")
    return payload


def discover_urls_for_job(
    job: Mapping[str, Any],
    *,
    api_key: str | None = None,
    client: httpx.Client | None = None,
) -> list[str]:
    """
    Executa uma busca SerpAPI para um único job e devolve URLs encontradas.

    Args:
        job: Registro expandido (ex.: linha de ``queries.expanded.jsonl``).
        api_key: Chave da API; se omitida, lê ``SERPAPI_API_KEY``.
        client: Cliente HTTP reutilizável; criado se não informado.

    Returns:
        Lista de URLs (possivelmente vazia).
    """
    resolved_key = api_key if api_key is not None else read_api_key()
    params = build_serpapi_params(job)
    job_id = job.get("job_id", "?")

    logger.info("Descoberta SerpAPI para job_id=%s", job_id)

    owns_client = client is None
    http_client = client if client is not None else httpx.Client(timeout=_DEFAULT_TIMEOUT_SECONDS)

    try:
        payload = fetch_search_results(params, resolved_key, http_client)
    finally:
        if owns_client:
            http_client.close()

    urls = extract_urls_from_response(payload)
    logger.info("Job %s: %d URL(s) descoberta(s)", job_id, len(urls))
    return urls
