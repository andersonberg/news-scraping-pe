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
from news_scraping_pe.config.paths import (
    default_articles_output_path,
    default_config_path,
    default_queries_expanded_path,
    default_serpapi_usage_log_path,
    default_urls_pending_path,
    repo_root,
)
from news_scraping_pe.discovery.jobs import iter_jobs_from_jsonl, load_jobs_index, select_jobs
from news_scraping_pe.discovery.quota import compute_quota_status
from news_scraping_pe.discovery.serpapi_runner import discover_and_store_jobs
from news_scraping_pe.env import load_project_dotenv
from news_scraping_pe.extraction.fetch_runner import fetch_and_store_pending_urls
from news_scraping_pe.log import configure_logging, get_logger
from news_scraping_pe.storage.urls import iter_pending_urls, select_pending_urls

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


def _read_job_ids_file(path: str) -> set[str]:
    """Lê um arquivo com um ``job_id`` por linha (linhas em branco ignoradas)."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return {stripped for line in lines if (stripped := line.strip())}


def _cmd_discover_serpapi(args: argparse.Namespace) -> int:
    jobs_path = Path(args.jobs)
    urls_path = Path(args.urls_output)
    usage_log_path = Path(args.usage_log)

    try:
        all_jobs = iter_jobs_from_jsonl(jobs_path)
        job_ids = _read_job_ids_file(args.job_ids_file) if args.job_ids_file else None
        jobs = select_jobs(
            all_jobs,
            job_id=args.job_id,
            candidate_id=args.candidate_id,
            portal_id=args.portal_id,
            job_ids=job_ids,
            limit=args.limit,
        )
    except (FileNotFoundError, ValueError):
        logger.exception("Não foi possível carregar jobs de %s", jobs_path)
        return 1

    if not jobs:
        logger.warning("Nenhum job selecionado com os filtros informados")
        return 1

    stats = discover_and_store_jobs(
        jobs,
        urls_path=urls_path,
        usage_log_path=usage_log_path,
        skip_attempted=not args.force,
    )
    logger.info(
        "Resumo: %d job(s), %d falha(s), %d pulado(s) (já tentados), %d URL(s) gravada(s) em %s",
        stats.jobs_processed,
        stats.jobs_failed,
        stats.jobs_skipped_already_attempted,
        stats.urls_stored,
        urls_path,
    )
    return 1 if stats.jobs_failed and stats.urls_stored == 0 else 0


def _cmd_quota_status(args: argparse.Namespace) -> int:
    jobs_path = Path(args.jobs)
    usage_log_path = Path(args.usage_log)

    try:
        all_jobs = iter_jobs_from_jsonl(jobs_path)
        status = compute_quota_status(
            all_jobs,
            usage_log_path=usage_log_path,
            monthly_quota=args.monthly_quota,
            candidate_id=args.candidate_id,
            portal_id=args.portal_id,
        )
    except (FileNotFoundError, ValueError):
        logger.exception("Não foi possível calcular status de cota a partir de %s", jobs_path)
        return 1

    logger.info(
        "Jobs: %d total, %d já feitos (%d neste mês), %d restantes",
        status.total_jobs,
        status.done_all_time,
        status.done_this_month,
        status.remaining_total,
    )
    logger.info(
        "Cota mensal: %d | usada neste mês: %d | disponível: %d",
        args.monthly_quota,
        status.done_this_month,
        status.remaining_quota_this_month,
    )
    logger.info("Próximo lote sugerido: %d job(s)", len(status.next_batch_job_ids))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "\n".join(status.next_batch_job_ids) + ("\n" if status.next_batch_job_ids else ""),
        encoding="utf-8",
    )
    logger.info("Lote sugerido gravado em %s", out)

    return 0


def _cmd_fetch_articles(args: argparse.Namespace) -> int:
    pending_path = Path(args.urls_input)
    jobs_path = Path(args.jobs)
    articles_path = Path(args.articles_output)

    try:
        jobs_index = load_jobs_index(jobs_path)
        pending = select_pending_urls(
            iter_pending_urls(pending_path),
            job_id=args.job_id,
            candidate_id=args.candidate_id,
            portal_id=args.portal_id,
            limit=args.limit,
        )
    except (FileNotFoundError, ValueError):
        logger.exception("Falha ao preparar fetch-articles")
        return 1

    if not pending:
        logger.warning("Nenhuma URL pendente selecionada")
        return 1

    stats = fetch_and_store_pending_urls(
        pending,
        jobs_index,
        articles_path=articles_path,
    )
    logger.info(
        "Resumo: %d URL(s) processada(s), %d falha(s), %d artigo(s) gravado(s) em %s",
        stats.urls_processed,
        stats.urls_failed,
        stats.articles_stored,
        articles_path,
    )

    if stats.urls_missing_job:
        logger.warning("%d URL(s) sem job correspondente no índice", stats.urls_missing_job)

    if stats.articles_stored == 0:
        return 1
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

    p_discover = sub.add_parser(
        "discover-serpapi",
        help="Descobre URLs via SerpAPI e grava em urls_pending.jsonl",
    )
    p_discover.add_argument(
        "--jobs",
        type=str,
        default=str(default_queries_expanded_path()),
        help="JSONL de jobs expandidos",
    )
    p_discover.add_argument(
        "--urls-output",
        type=str,
        default=str(default_urls_pending_path()),
        help="Saída de URLs pendentes",
    )
    p_discover.add_argument("--job-id", type=str, help="Processar apenas este job_id")
    p_discover.add_argument("--candidate-id", type=str, help="Filtrar por candidato")
    p_discover.add_argument("--portal-id", type=str, help="Filtrar por portal (ex.: ne10)")
    p_discover.add_argument(
        "--job-ids-file",
        type=str,
        help="Arquivo com um job_id por linha (ex.: saída de quota-status)",
    )
    p_discover.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Máximo de jobs a processar após filtros",
    )
    p_discover.add_argument(
        "--usage-log",
        type=str,
        default=str(default_serpapi_usage_log_path()),
        help="Log local de jobs já tentados (usado para pular repetições)",
    )
    p_discover.add_argument(
        "--force",
        action="store_true",
        help="Reprocessa jobs mesmo se já tiverem sido tentados antes (gasta créditos de novo)",
    )
    p_discover.set_defaults(func=_cmd_discover_serpapi)

    p_quota = sub.add_parser(
        "quota-status",
        help="Mostra progresso de jobs SerpAPI e sugere o próximo lote a rodar",
    )
    p_quota.add_argument(
        "--jobs",
        type=str,
        default=str(default_queries_expanded_path()),
        help="JSONL de jobs expandidos",
    )
    p_quota.add_argument(
        "--usage-log",
        type=str,
        default=str(default_serpapi_usage_log_path()),
        help="Log local de jobs já tentados",
    )
    p_quota.add_argument(
        "--monthly-quota",
        type=int,
        default=230,
        help="Créditos disponíveis por mês (margem de segurança abaixo do limite da conta)",
    )
    p_quota.add_argument("--candidate-id", type=str, help="Restringir status a um candidato")
    p_quota.add_argument("--portal-id", type=str, help="Restringir status a um portal")
    p_quota.add_argument(
        "-o",
        "--output",
        type=str,
        default=str(repo_root() / "data" / "serpapi_next_batch.txt"),
        help="Arquivo de saída com o próximo lote de job_ids (um por linha)",
    )
    p_quota.set_defaults(func=_cmd_quota_status)

    p_fetch = sub.add_parser(
        "fetch-articles",
        help="Extrai texto de URLs pendentes e grava em articles.jsonl",
    )
    p_fetch.add_argument(
        "--urls-input",
        type=str,
        default=str(default_urls_pending_path()),
        help="JSONL de URLs pendentes",
    )
    p_fetch.add_argument(
        "--jobs",
        type=str,
        default=str(default_queries_expanded_path()),
        help="JSONL de jobs expandidos (metadados por job_id)",
    )
    p_fetch.add_argument(
        "--articles-output",
        type=str,
        default=str(default_articles_output_path()),
        help="Saída de artigos coletados",
    )
    p_fetch.add_argument("--job-id", type=str, help="Processar só URLs deste job_id")
    p_fetch.add_argument("--candidate-id", type=str, help="Filtrar por candidato")
    p_fetch.add_argument("--portal-id", type=str, help="Filtrar por portal")
    p_fetch.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Máximo de URLs a processar após filtros",
    )
    p_fetch.set_defaults(func=_cmd_fetch_articles)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da CLI; configura logging antes de executar o subcomando."""
    parser = build_parser()
    args = parser.parse_args(argv)

    load_project_dotenv()
    level = logging.DEBUG if args.verbose else None
    configure_logging(level=level)

    logger.debug("Executando comando: %s", args.command)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
