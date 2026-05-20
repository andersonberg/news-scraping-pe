from news_scraping_pe.extraction.metadata import extract_title_and_published_at

_HTML = """
<html><head><title>Titulo via meta</title></head>
<body><article><p>Corpo.</p></article></body>
</html>
"""


def test_extract_title_and_published_at() -> None:
    title, published = extract_title_and_published_at(
        _HTML,
        "https://example.com/artigo",
        fallback_date="2022-10-30",
        raw_text="Linha inicial do texto",
    )

    assert title
    assert published == "2022-10-30" or len(published) == 10
