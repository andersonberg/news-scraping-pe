from pathlib import Path

from news_scraping_pe.env import load_project_dotenv, project_dotenv_path


def test_project_dotenv_path_is_under_repo() -> None:
    path = project_dotenv_path()
    assert path.name == ".env"
    assert "news-scraping-pe" in path.parts


def test_load_project_dotenv_with_explicit_file(tmp_path: Path) -> None:
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("SERPAPI_API_KEY=from-test-file\n", encoding="utf-8")

    loaded = load_project_dotenv(path=dotenv_file)

    assert loaded is True
