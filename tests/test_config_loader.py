from pathlib import Path

import pytest

from news_scraping_pe.config.loader import expand_query_jobs, validate_search_config
from news_scraping_pe.config.paths import repo_root


@pytest.fixture
def example_config_path() -> Path:
    return repo_root() / "config" / "searches.example.yaml"


def test_validate_example_config(example_config_path: Path) -> None:
    validate_search_config(example_config_path)


def test_expand_queries_non_empty(example_config_path: Path) -> None:
    from news_scraping_pe.config.loader import load_search_config

    config = load_search_config(example_config_path)
    jobs = expand_query_jobs(config)
    # candidatos × variantes de nome × 6 termos × 3 portais tier-1 (com variantes no YAML)
    assert len(jobs) >= 144
    assert len(jobs) == 270
    assert jobs[0]["job_id"]
    assert "search_query" in jobs[0]
