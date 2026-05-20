from news_scraping_pe.cli import build_parser


def test_parser_has_validate_and_expand() -> None:
    parser = build_parser()
    args = parser.parse_args(["validate-config", "--config", "config/searches.example.yaml"])
    assert args.command == "validate-config"


def test_parser_has_discover_serpapi() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "discover-serpapi",
            "--job-id",
            "lula_2022__processo__ne10",
            "--limit",
            "1",
        ]
    )
    assert args.command == "discover-serpapi"
    assert args.job_id == "lula_2022__processo__ne10"
    assert args.limit == 1


def test_parser_has_fetch_articles() -> None:
    parser = build_parser()
    args = parser.parse_args(["fetch-articles", "--limit", "2"])
    assert args.command == "fetch-articles"
    assert args.limit == 2
