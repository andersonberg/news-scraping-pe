from pathlib import Path

from news_scraping_pe.discovery.quota import compute_quota_status
from news_scraping_pe.discovery.usage_log import append_job_attempt
from news_scraping_pe.storage.models import JobAttempt


def _jobs() -> list[dict[str, object]]:
    return [
        {"job_id": "j1", "candidate_id": "lula_2022", "portal_id": "ne10"},
        {"job_id": "j2", "candidate_id": "lula_2022", "portal_id": "jc"},
        {"job_id": "j3", "candidate_id": "lula_2022", "portal_id": "g1"},
        {"job_id": "j4", "candidate_id": "bolsonaro_2022", "portal_id": "ne10"},
    ]


def test_compute_quota_status_no_attempts(tmp_path: Path) -> None:
    usage_log = tmp_path / "usage_log.jsonl"

    status = compute_quota_status(
        _jobs(),
        usage_log_path=usage_log,
        monthly_quota=2,
        month="2026-07",
    )

    assert status.total_jobs == 4
    assert status.done_all_time == 0
    assert status.done_this_month == 0
    assert status.remaining_total == 4
    assert status.remaining_quota_this_month == 2
    assert status.next_batch_job_ids == ["j1", "j2"]


def test_compute_quota_status_skips_attempted_and_respects_month(tmp_path: Path) -> None:
    usage_log = tmp_path / "usage_log.jsonl"
    append_job_attempt(
        JobAttempt(
            job_id="j1", attempted_at="2026-06-01T00:00:00+00:00", status="ok", urls_found=1
        ),
        path=usage_log,
    )
    append_job_attempt(
        JobAttempt(
            job_id="j2", attempted_at="2026-07-05T00:00:00+00:00", status="ok", urls_found=3
        ),
        path=usage_log,
    )

    status = compute_quota_status(
        _jobs(),
        usage_log_path=usage_log,
        monthly_quota=5,
        month="2026-07",
    )

    assert status.done_all_time == 2
    assert status.done_this_month == 1
    assert status.remaining_total == 2
    assert status.remaining_quota_this_month == 4
    assert status.next_batch_job_ids == ["j3", "j4"]


def test_compute_quota_status_scoped_by_candidate(tmp_path: Path) -> None:
    usage_log = tmp_path / "usage_log.jsonl"

    status = compute_quota_status(
        _jobs(),
        usage_log_path=usage_log,
        monthly_quota=100,
        candidate_id="lula_2022",
        month="2026-07",
    )

    assert status.total_jobs == 3
    assert status.next_batch_job_ids == ["j1", "j2", "j3"]


def test_compute_quota_status_quota_exhausted(tmp_path: Path) -> None:
    usage_log = tmp_path / "usage_log.jsonl"
    for job_id in ("j1", "j2"):
        append_job_attempt(
            JobAttempt(
                job_id=job_id, attempted_at="2026-07-01T00:00:00+00:00", status="ok", urls_found=1
            ),
            path=usage_log,
        )

    status = compute_quota_status(
        _jobs(),
        usage_log_path=usage_log,
        monthly_quota=2,
        month="2026-07",
    )

    assert status.remaining_quota_this_month == 0
    assert status.next_batch_job_ids == []
