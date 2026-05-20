from pathlib import Path

import pytest

from news_scraping_pe.config.loader import expand_query_jobs, validate_search_config
from news_scraping_pe.config.paths import repo_root


@pytest.fixture
def example_config_path() -> Path:
    return repo_root() / "config" / "searches.example.yaml"


def test_validate_example_config(example_config_path: Path) -> None:
    validate_search_config(example_config_path)


def test_expand_queries_office_portal_pairing(example_config_path: Path) -> None:
    from news_scraping_pe.config.loader import load_search_config

    config = load_search_config(example_config_path)
    jobs = expand_query_jobs(config)

    # 7 variantes presidente × 6 termos × 5 nacionais = 210
    # 8 variantes governador × 6 termos × 3 regionais = 144
    assert len(jobs) == 354

    for job in jobs:
        office = job["office"]
        portal_id = job["portal_id"]
        regional = {"ne10", "jc", "diario_pe"}
        national = {"g1", "folha", "uol", "estadao", "r7"}

        if office == "presidente":
            assert portal_id in national, job
            assert portal_id not in regional, job
        if office == "governador_pe":
            assert portal_id in regional, job
            assert portal_id not in national, job

    assert jobs[0]["job_id"]
    assert "search_query" in jobs[0]
