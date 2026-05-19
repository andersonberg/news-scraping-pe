from typing import Any

import httpx
import pytest

from news_scraping_pe.discovery.serpapi import (
    SerpApiError,
    build_serpapi_params,
    discover_urls_for_job,
    extract_urls_from_response,
    fetch_search_results,
    read_api_key,
)


def _sample_job() -> dict[str, Any]:
    return {
        "job_id": "lula_2022__processo__ne10",
        "search_query": '"Luiz Inácio Lula da Silva" processo',
        "site_domain": "ne10.uol.com.br",
        "query_window_start": "2022-08-05",
        "query_window_end": "2022-10-30",
    }


def test_build_serpapi_params_from_job_fields() -> None:
    params = build_serpapi_params(_sample_job())

    assert params["engine"] == "google_news"
    assert "site:ne10.uol.com.br" in params["q"]
    assert params["tbs"] == "cdr:1,cd_min:8/5/2022,cd_max:10/30/2022"
    assert params["gl"] == "br"
    assert params["hl"] == "pt"


def test_build_serpapi_params_uses_existing_block() -> None:
    job = {
        **_sample_job(),
        "serpapi_params": {"engine": "google_news", "q": "consulta pronta", "tbs": "cdr:1"},
    }

    assert build_serpapi_params(job) == {
        "engine": "google_news",
        "q": "consulta pronta",
        "tbs": "cdr:1",
    }


def test_extract_urls_from_news_results() -> None:
    payload = {
        "news_results": [
            {"link": "https://ne10.uol.com.br/a"},
            {"link": "https://ne10.uol.com.br/b"},
        ]
    }

    assert extract_urls_from_response(payload) == [
        "https://ne10.uol.com.br/a",
        "https://ne10.uol.com.br/b",
    ]


def test_extract_urls_falls_back_to_organic_results() -> None:
    payload = {"organic_results": [{"link": "https://jconline.com.br/x"}]}

    assert extract_urls_from_response(payload) == ["https://jconline.com.br/x"]


def test_read_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    with pytest.raises(SerpApiError, match="SERPAPI_API_KEY"):
        read_api_key()


def test_fetch_search_results_raises_on_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "Invalid API key"})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(SerpApiError, match="Invalid API key"):
        fetch_search_results({"engine": "google_news", "q": "test"}, "secret", client)


def test_discover_urls_for_job_with_mock_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["api_key"] == "test-key"
        assert request.url.params["engine"] == "google_news"
        return httpx.Response(
            200,
            json={"news_results": [{"link": "https://ne10.uol.com.br/artigo"}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    urls = discover_urls_for_job(_sample_job(), api_key="test-key", client=client)

    assert urls == ["https://ne10.uol.com.br/artigo"]
