import json
from pathlib import Path

import pytest

from news_scraping_pe.discovery.jobs import load_jobs_index, parse_job_id


def test_parse_job_id() -> None:
    assert parse_job_id("lula_2022__processo__ne10") == (
        "lula_2022",
        "processo",
        "ne10",
    )


def test_parse_job_id_invalid() -> None:
    with pytest.raises(ValueError, match="job_id inválido"):
        parse_job_id("apenas_um_campo")


def test_parse_job_id_with_variant() -> None:
    assert parse_job_id("lula_2022__processo__ne10__lula") == (
        "lula_2022",
        "processo",
        "ne10",
    )


def test_load_jobs_index(tmp_path: Path) -> None:
    path = tmp_path / "jobs.jsonl"
    path.write_text(
        json.dumps({"job_id": "a", "portal_id": "ne10"}, ensure_ascii=False)
        + "\n"
        + json.dumps({"job_id": "b", "portal_id": "jc"}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    index = load_jobs_index(path)

    assert set(index) == {"a", "b"}
    assert index["a"]["portal_id"] == "ne10"
