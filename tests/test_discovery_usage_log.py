from pathlib import Path

import pytest

from news_scraping_pe.discovery.usage_log import (
    append_job_attempt,
    iter_job_attempts,
    load_attempted_job_ids,
)
from news_scraping_pe.storage.models import JobAttempt


def _attempt(job_id: str, status: str = "ok", urls_found: int = 2) -> JobAttempt:
    return JobAttempt(
        job_id=job_id,
        attempted_at="2026-07-18T12:00:00+00:00",
        status=status,
        urls_found=urls_found,
    )


def test_append_and_iter_job_attempts(tmp_path: Path) -> None:
    target = tmp_path / "usage_log.jsonl"

    append_job_attempt(_attempt("j1"), path=target)
    append_job_attempt(_attempt("j2", status="error", urls_found=0), path=target)

    attempts = list(iter_job_attempts(path=target))

    assert len(attempts) == 2
    assert attempts[0]["job_id"] == "j1"
    assert attempts[1]["status"] == "error"


def test_iter_job_attempts_empty_when_file_missing(tmp_path: Path) -> None:
    target = tmp_path / "missing.jsonl"

    assert list(iter_job_attempts(path=target)) == []


def test_load_attempted_job_ids_deduplicates(tmp_path: Path) -> None:
    target = tmp_path / "usage_log.jsonl"

    append_job_attempt(_attempt("j1"), path=target)
    append_job_attempt(_attempt("j1", status="error"), path=target)
    append_job_attempt(_attempt("j2"), path=target)

    assert load_attempted_job_ids(path=target) == {"j1", "j2"}


def test_iter_job_attempts_invalid_json(tmp_path: Path) -> None:
    target = tmp_path / "bad.jsonl"
    target.write_text("{invalid}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON inválido"):
        list(iter_job_attempts(path=target))


def test_iter_job_attempts_missing_field(tmp_path: Path) -> None:
    target = tmp_path / "usage_log.jsonl"
    target.write_text('{"job_id": "j1"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="campos ausentes"):
        list(iter_job_attempts(path=target))
