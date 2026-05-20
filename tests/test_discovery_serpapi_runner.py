from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx

from news_scraping_pe.discovery.serpapi_runner import discover_and_store_jobs


def _job() -> dict[str, Any]:
    return {
        "job_id": "lula_2022__processo__ne10",
        "search_query": '"Lula" processo',
        "site_domain": "ne10.uol.com.br",
        "query_window_start": "2022-08-05",
        "query_window_end": "2022-10-30",
    }


def test_discover_and_store_jobs(tmp_path: Path) -> None:
    urls_file = tmp_path / "urls_pending.jsonl"

    def fake_discover(job: dict[str, Any], **kwargs: object) -> list[str]:
        return [f"https://ne10.uol.com.br/{job['job_id']}"]

    with (
        patch(
            "news_scraping_pe.discovery.serpapi_runner.discover_urls_for_job",
            side_effect=fake_discover,
        ),
        patch(
            "news_scraping_pe.discovery.serpapi_runner.read_api_key",
            return_value="test-key",
        ),
    ):
        stats = discover_and_store_jobs(
            [_job()],
            urls_path=urls_file,
            client=httpx.Client(),
        )

    assert stats.jobs_processed == 1
    assert stats.jobs_failed == 0
    assert stats.urls_discovered == 1
    assert stats.urls_stored == 1

    content = urls_file.read_text(encoding="utf-8")
    assert "serpapi" in content
    assert "lula_2022__processo__ne10" in content
