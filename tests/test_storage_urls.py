import json
from pathlib import Path

import pytest

from news_scraping_pe.storage.urls import (
    PendingUrl,
    append_pending_url,
    append_pending_urls,
    iter_pending_urls,
    read_pending_urls,
)


def _sample_record() -> PendingUrl:
    return PendingUrl(
        url="https://ne10.uol.com.br/politica/exemplo",
        job_id="bolsonaro_2022__processo__ne10",
        discovered_via="serpapi",
    )


def test_append_and_read_single_record(tmp_path: Path) -> None:
    target = tmp_path / "urls_pending.jsonl"

    append_pending_url(_sample_record(), path=target)
    records = read_pending_urls(path=target)

    assert records == [_sample_record()]


def test_append_multiple_records(tmp_path: Path) -> None:
    target = tmp_path / "urls_pending.jsonl"
    second = PendingUrl(
        url="https://jconline.com.br/noticia",
        job_id="lula_2022__acao__jc",
        discovered_via="jc_spider",
    )

    written = append_pending_urls([_sample_record(), second], path=target)

    assert written == 2
    assert len(read_pending_urls(path=target)) == 2


def test_iter_skips_blank_lines(tmp_path: Path) -> None:
    target = tmp_path / "urls_pending.jsonl"
    target.write_text(
        json.dumps(_sample_record(), ensure_ascii=False) + "\n\n",
        encoding="utf-8",
    )

    assert list(iter_pending_urls(path=target)) == [_sample_record()]


def test_iter_empty_when_file_missing(tmp_path: Path) -> None:
    target = tmp_path / "missing.jsonl"

    assert read_pending_urls(path=target) == []


def test_validate_rejects_missing_field(tmp_path: Path) -> None:
    invalid = {"url": "https://example.com", "discovered_via": "serpapi"}
    with pytest.raises(ValueError, match="job_id"):
        append_pending_url(invalid, path=tmp_path / "x.jsonl")


def test_validate_rejects_invalid_json_line(tmp_path: Path) -> None:
    target = tmp_path / "urls_pending.jsonl"
    target.write_text("not json\n", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON inválido"):
        list(iter_pending_urls(path=target))
