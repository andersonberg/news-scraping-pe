from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx

from news_scraping_pe.extraction.fetch_runner import (
    fetch_and_store_pending_urls,
    interleave_by_host,
)
from news_scraping_pe.storage.models import PendingUrl

_SAMPLE_HTML = """
<html><head><title>Titulo da noticia</title></head>
<body><article><p>Texto da materia com conteudo eleitoral suficiente.</p></article></body>
</html>
"""


def _pending() -> PendingUrl:
    return PendingUrl(
        url="https://ne10.uol.com.br/politica/artigo",
        job_id="lula_2022__processo__ne10",
        discovered_via="serpapi",
    )


def _job() -> dict[str, Any]:
    return {
        "job_id": "lula_2022__processo__ne10",
        "candidate_id": "lula_2022",
        "candidate_name": "Luiz Inácio Lula da Silva",
        "office": "presidente",
        "election_year": 2022,
        "search_term_id": "processo",
        "search_query": '"Lula" processo',
        "portal_id": "ne10",
        "query_window_start": "2022-08-05",
        "query_window_end": "2022-10-30",
    }


def test_fetch_and_store_pending_urls(tmp_path: Path) -> None:
    articles_file = tmp_path / "articles.jsonl"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_SAMPLE_HTML)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with patch(
        "news_scraping_pe.extraction.fetch_runner.append_articles",
        side_effect=lambda records, path=None: len(list(records)),
    ) as mock_append:
        stats = fetch_and_store_pending_urls(
            [_pending()],
            {"lula_2022__processo__ne10": _job()},
            articles_path=articles_file,
            client=client,
        )

    assert stats.urls_processed == 1
    assert stats.urls_failed == 0
    assert stats.articles_stored == 1
    assert stats.urls_missing_job == 0
    mock_append.assert_called_once()


def test_same_host_requests_are_spaced(tmp_path: Path, monkeypatch: Any) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(
        "news_scraping_pe.extraction.fetch_runner.time.sleep",
        lambda s: sleeps.append(s),
    )
    monkeypatch.setattr("news_scraping_pe.extraction.fetch_runner.monotonic", lambda: 0.0)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_SAMPLE_HTML)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    p1 = _pending()
    p2 = _pending()
    p2["url"] = p1["url"] + "-2"

    with patch(
        "news_scraping_pe.extraction.fetch_runner.append_articles",
        side_effect=lambda records, path=None: len(list(records)),
    ):
        fetch_and_store_pending_urls(
            [p1, p2],
            {"lula_2022__processo__ne10": _job()},
            articles_path=tmp_path / "articles.jsonl",
            client=client,
            domain_delay=2.0,
        )

    assert sleeps == [2.0]


def test_distinct_host_requests_are_not_spaced(tmp_path: Path, monkeypatch: Any) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(
        "news_scraping_pe.extraction.fetch_runner.time.sleep",
        lambda s: sleeps.append(s),
    )
    monkeypatch.setattr("news_scraping_pe.extraction.fetch_runner.monotonic", lambda: 0.0)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_SAMPLE_HTML)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    p1 = _pending()
    p2 = _pending()
    p2["url"] = "https://jconline.com.br/politica/artigo"

    with patch(
        "news_scraping_pe.extraction.fetch_runner.append_articles",
        side_effect=lambda records, path=None: len(list(records)),
    ):
        fetch_and_store_pending_urls(
            [p1, p2],
            {"lula_2022__processo__ne10": _job()},
            articles_path=tmp_path / "articles.jsonl",
            client=client,
            domain_delay=2.0,
        )

    assert sleeps == []


def test_interleave_by_host_alternates_and_preserves_set() -> None:
    a1 = PendingUrl(url="https://a.com/1", job_id="j", discovered_via="d")
    a2 = PendingUrl(url="https://a.com/2", job_id="j", discovered_via="d")
    b1 = PendingUrl(url="https://b.com/1", job_id="j", discovered_via="d")
    out = interleave_by_host([a1, a2, b1])

    assert out == [a1, b1, a2]
    assert sorted(r["url"] for r in out) == [
        "https://a.com/1",
        "https://a.com/2",
        "https://b.com/1",
    ]
