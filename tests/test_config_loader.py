from pathlib import Path

import pytest

from news_scraping_pe.config.loader import (
    expand_query_jobs,
    load_search_config,
    validate_search_config,
)
from news_scraping_pe.config.paths import repo_root


@pytest.fixture
def example_config_path() -> Path:
    return repo_root() / "config" / "searches.example.yaml"


def test_validate_example_config(example_config_path: Path) -> None:
    validate_search_config(example_config_path)


def test_expand_queries_all_enabled_portals(example_config_path: Path) -> None:
    config = load_search_config(example_config_path)
    jobs = expand_query_jobs(config)

    enabled_portal_ids = {p["id"] for p in config["portals"] if p.get("enabled", True)}
    enabled_candidate_ids = {c["id"] for c in config["candidates"] if c.get("enabled", True)}
    num_terms = len(config["search_terms"])

    expected = 0
    for candidate in config["candidates"]:
        if not candidate.get("enabled", True):
            continue
        names = candidate.get("search_name_variants") or [candidate["name"]]
        expected += len(names) * num_terms * len(enabled_portal_ids)

    assert len(jobs) == expected == 720

    for job in jobs:
        assert job["portal_id"] in enabled_portal_ids, job
        assert job["candidate_id"] in enabled_candidate_ids, job

    pairs = {(j["candidate_id"], j["portal_id"]) for j in jobs}
    for candidate_id in enabled_candidate_ids:
        for portal_id in enabled_portal_ids:
            assert (candidate_id, portal_id) in pairs

    job_ids = {j["job_id"] for j in jobs}
    assert "bolsonaro_2022__processo__ne10" in job_ids
    assert "marilia_arraes_2022__processo__g1" in job_ids

    assert jobs[0]["job_id"]
    assert "search_query" in jobs[0]
