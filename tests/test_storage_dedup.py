from news_scraping_pe.storage.dedup import (
    filter_unique_pending_urls,
    normalize_url,
    url_dedup_key,
    url_host,
)
from news_scraping_pe.storage.urls import PendingUrl


def test_normalize_url_strips_fragment_and_tracking() -> None:
    raw = "HTTPS://NE10.uol.com.br/Noticia?utm_source=google&fbclid=abc#comentarios"
    assert normalize_url(raw) == "https://ne10.uol.com.br/Noticia"


def test_normalize_url_removes_trailing_slash() -> None:
    assert normalize_url("https://jconline.com.br/politica/") == "https://jconline.com.br/politica"


def test_normalize_url_keeps_non_tracking_query() -> None:
    url = "https://example.com/artigo?id=42&secao=politica"
    assert normalize_url(url) == "https://example.com/artigo?id=42&secao=politica"


def test_url_dedup_key_treats_tracking_variants_as_equal() -> None:
    a = "https://ne10.uol.com.br/x?utm_medium=email"
    b = "https://ne10.uol.com.br/x/"
    assert url_dedup_key(a) == url_dedup_key(b)


def test_filter_unique_pending_urls_within_batch() -> None:
    records = [
        PendingUrl(url="https://a.com/1", job_id="j1", discovered_via="serpapi"),
        PendingUrl(url="https://a.com/1?utm_source=email", job_id="j2", discovered_via="serpapi"),
    ]
    unique, skipped = filter_unique_pending_urls(records, set())

    assert len(unique) == 1
    assert skipped == 1
    assert unique[0]["url"] == "https://a.com/1"


def test_filter_unique_pending_urls_against_existing_keys() -> None:
    record = PendingUrl(url="https://a.com/1", job_id="j1", discovered_via="serpapi")
    unique, skipped = filter_unique_pending_urls([record], {"https://a.com/1"})

    assert unique == []
    assert skipped == 1


def test_url_host_extracts_lowercased_netloc() -> None:
    assert url_host("https://WWW.Example.COM/a/b?x=1") == "www.example.com"
    assert url_host("http://ne10.uol.com.br/artigo") == "ne10.uol.com.br"


def test_url_host_empty_for_unparseable() -> None:
    assert url_host("not-a-url") == ""
