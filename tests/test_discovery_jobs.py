import json
from pathlib import Path

import pytest

from news_scraping_pe.discovery.jobs import iter_jobs_from_jsonl, select_jobs


def _write_jobs(path: Path, jobs: list[dict[str, object]]) -> None:
    lines = [json.dumps(job, ensure_ascii=False) for job in jobs]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_iter_jobs_from_jsonl(tmp_path: Path) -> None:
    target = tmp_path / "jobs.jsonl"
    _write_jobs(
        target,
        [
            {"job_id": "a", "candidate_id": "c1", "portal_id": "ne10"},
            {"job_id": "b", "candidate_id": "c2", "portal_id": "jc"},
        ],
    )

    jobs = list(iter_jobs_from_jsonl(target))

    assert len(jobs) == 2
    assert jobs[0]["job_id"] == "a"


def test_select_jobs_with_filters(tmp_path: Path) -> None:
    jobs = [
        {"job_id": "j1", "candidate_id": "lula_2022", "portal_id": "ne10"},
        {"job_id": "j2", "candidate_id": "lula_2022", "portal_id": "jc"},
        {"job_id": "j3", "candidate_id": "bolsonaro_2022", "portal_id": "ne10"},
    ]

    selected = select_jobs(jobs, candidate_id="lula_2022", portal_id="ne10", limit=10)

    assert len(selected) == 1
    assert selected[0]["job_id"] == "j1"


def test_iter_jobs_invalid_json(tmp_path: Path) -> None:
    target = tmp_path / "bad.jsonl"
    target.write_text("{invalid}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON inválido"):
        list(iter_jobs_from_jsonl(target))
