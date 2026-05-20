from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx

from news_scraping_pe.extraction.fetch_runner import fetch_and_store_pending_urls
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
