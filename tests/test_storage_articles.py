from datetime import UTC, datetime
from pathlib import Path

import pytest

from news_scraping_pe.storage.articles import (
    append_article,
    append_articles,
    build_article_id,
    read_articles,
    validate_article,
)


def _sample_article(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "article_id": build_article_id("https://ne10.uol.com.br/politica/artigo-teste"),
        "url": "https://ne10.uol.com.br/politica/artigo-teste",
        "portal_id": "ne10",
        "title": "Candidato responde a processo",
        "published_at": "2022-09-15",
        "raw_text": "Texto completo da matéria para validação do schema.",
        "candidate_id": "lula_2022",
        "election_year": 2022,
        "office": "presidente",
        "search_term_id": "processo",
        "query_window_start": "2022-08-05",
        "query_window_end": "2022-10-30",
        "discovered_via": "serpapi",
        "collected_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "language": "pt-BR",
        "extraction_method": "trafilatura",
    }
    base.update(overrides)
    return base


def test_build_article_id_is_stable() -> None:
    url = "https://NE10.uol.com.br/Artigo/?utm_source=x"
    assert build_article_id(url) == build_article_id("https://ne10.uol.com.br/Artigo")


def test_validate_article_accepts_cnn_portal() -> None:
    article = _sample_article(portal_id="cnn")
    validated = validate_article(article)
    assert validated["portal_id"] == "cnn"


def test_validate_article_accepts_optional_view_count() -> None:
    article = _sample_article(view_count=1200, view_count_source="portal_display")
    validated = validate_article(article)
    assert validated["view_count"] == 1200


def test_validate_article_rejects_unknown_field() -> None:
    article = _sample_article(extra_field="x")
    with pytest.raises(ValueError, match="Artigo inválido"):
        validate_article(article)


def test_append_and_read_article(tmp_path: Path) -> None:
    target = tmp_path / "articles.jsonl"
    article = _sample_article()

    assert append_article(article, path=target) is True
    stored = read_articles(path=target)

    assert len(stored) == 1
    assert stored[0]["article_id"] == article["article_id"]


def test_append_skips_duplicate_article_id(tmp_path: Path) -> None:
    target = tmp_path / "articles.jsonl"
    article = _sample_article()
    variant = _sample_article(
        title="Outro título",
        url="https://ne10.uol.com.br/politica/artigo-teste?utm=1",
    )

    assert append_articles([article, variant], path=target) == 1
    assert len(read_articles(path=target)) == 1
