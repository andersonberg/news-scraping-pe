"""CLI principal do projeto."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from news_scraping_pe.config.loader import (
    expand_query_jobs,
    load_search_config,
    validate_search_config,
)
from news_scraping_pe.config.paths import default_config_path, repo_root


def _cmd_validate_config(args: argparse.Namespace) -> int:
    path = Path(args.config) if args.config else default_config_path()
    if not path.exists():
        print(f"Arquivo não encontrado: {path}", file=sys.stderr)
        print("Copie config/searches.example.yaml → config/searches.yaml", file=sys.stderr)
        return 1
    validate_search_config(path)
    print(f"OK: {path}")
    return 0


def _cmd_expand_queries(args: argparse.Namespace) -> int:
    path = Path(args.config) if args.config else default_config_path()
    if not path.exists():
        print(f"Arquivo não encontrado: {path}", file=sys.stderr)
        return 1
    config = load_search_config(path)
    jobs = expand_query_jobs(config)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for job in jobs:
            fh.write(json.dumps(job, ensure_ascii=False) + "\n")
    print(f"{len(jobs)} jobs → {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="news-scraping-pe",
        description="Pipeline de coleta de notícias eleitorais (PE / BR)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate-config", help="Valida YAML contra JSON Schema")
    p_validate.add_argument("--config", type=str, help="Caminho do searches.yaml")
    p_validate.set_defaults(func=_cmd_validate_config)

    p_expand = sub.add_parser("expand-queries", help="Expande candidatos × termos × portais")
    p_expand.add_argument("--config", type=str, help="Caminho do searches.yaml")
    p_expand.add_argument(
        "-o",
        "--output",
        type=str,
        default=str(repo_root() / "data" / "queries.expanded.jsonl"),
    )
    p_expand.set_defaults(func=_cmd_expand_queries)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
