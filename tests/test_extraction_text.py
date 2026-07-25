from pathlib import Path

import httpx
import pytest

from news_scraping_pe.extraction.text import (
    create_http_client,
    extract_raw_text_from_html,
    fetch_html,
    fetch_raw_text,
)

_FIXTURE_HTML = Path(__file__).parent / "fixtures" / "sample_article.html"


@pytest.fixture
def sample_html() -> str:
    return _FIXTURE_HTML.read_text(encoding="utf-8")


def test_extract_raw_text_from_html(sample_html: str) -> None:
    text = extract_raw_text_from_html(sample_html, "https://example.com/artigo")

    assert text is not None
    assert "processo judicial" in text
    assert "justiça eleitoral" in text


def test_extract_returns_none_for_empty_html() -> None:
    assert extract_raw_text_from_html("<html></html>", "https://example.com") is None


def test_create_http_client_sends_browser_identity() -> None:
    client = create_http_client()
    try:
        assert "Mozilla/5.0" in client.headers["User-Agent"]
        assert "text/html" in client.headers["Accept"]
        assert client.headers["Accept-Language"].startswith("pt-BR")
        assert client.follow_redirects is True
    finally:
        client.close()


def test_fetch_html_success() -> None:
    html = "<html><body><p>Conteudo minimo para teste de download.</p></body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = fetch_html("https://example.com/noticia", client)

    assert result == html


def test_fetch_html_returns_none_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert fetch_html("https://example.com/missing", client, max_retries=0) is None


def test_fetch_html_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("news_scraping_pe.extraction.text.time.sleep", lambda _s: None)
    html = "<html><body><p>ok</p></body></html>"
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(403)
        return httpx.Response(200, text=html)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = fetch_html("https://example.com/x", client, max_retries=3)

    assert result == html
    assert calls["n"] == 2


def test_fetch_html_gives_up_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("news_scraping_pe.extraction.text.time.sleep", lambda _s: None)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(403)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = fetch_html("https://example.com/x", client, max_retries=2)

    assert result is None
    assert calls["n"] == 3


def test_fetch_raw_text_end_to_end(sample_html: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=sample_html)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    text = fetch_raw_text("https://ne10.uol.com.br/artigo-teste", client=client)

    assert text is not None
    assert "Candidato responde" in text
