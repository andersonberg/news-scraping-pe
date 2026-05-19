from news_scraping_pe.cli import build_parser


def test_parser_has_validate_and_expand() -> None:
    parser = build_parser()
    args = parser.parse_args(["validate-config", "--config", "config/searches.example.yaml"])
    assert args.command == "validate-config"
