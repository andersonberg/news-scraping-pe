"""CLI principal do projeto."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from news_scraping_pe.config.loader import (
    expand_query_jobs,
    load_search_config,
    validate_search_config,
)
from news_scraping_pe.config.paths import default_config_path, repo_root
from news_scraping_pe.log import configure_logging, get_logger

logger = get_logger(__name__)


def _resolve_config_path(config_arg: str | None) -> Path:
    """Retorna o caminho do arquivo de configuração a partir do argumento CLI."""
    return Path(config_arg) if config_arg else default_config_path()


def _cmd_validate_config(args: argparse.Namespace) -> int:
    path = _resolve_config_path(args.config)
    if not path.exists():
        logger.error("Arquivo não encontrado: %s", path)
        logger.info("Copie config/searches.example.yaml → config/searches.yaml")
        return 1

    logger.info("Validando configuração: %s", path)
    validate_search_config(path)
    logger.info("Configuração válida: %s", path)
    return 0


def _cmd_expand_queries(args: argparse.Namespace) -> int:
    path = _resolve_config_path(args.config)
    if not path.exists():
        logger.error("Arquivo não encontrado: %s", path)
        return 1

    logger.info("Carregando configuração: %s", path)
    config = load_search_config(path)
    jobs = expand_query_jobs(config)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Gravando %d jobs em %s", len(jobs), out)

    with out.open("w", encoding="utf-8") as fh:
        for job in jobs:
            fh.write(json.dumps(job, ensure_ascii=False) + "\n")

    logger.info("Expansão concluída: %d jobs → %s", len(jobs), out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        prog="news-scraping-pe",
        description="Pipeline de coleta de notícias eleitorais (PE / BR)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log em nível DEBUG",
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
    """Ponto de entrada da CLI; configura logging antes de executar o subcomando."""
    parser = build_parser()
    args = parser.parse_args(argv)

    level = logging.DEBUG if args.verbose else None
    configure_logging(level=level)

    logger.debug("Executando comando: %s", args.command)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
