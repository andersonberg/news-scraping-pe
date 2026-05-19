"""Carregamento de variáveis de ambiente do projeto."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from news_scraping_pe.config.paths import repo_root
from news_scraping_pe.log import get_logger

logger = get_logger(__name__)


def project_dotenv_path() -> Path:
    """Caminho do arquivo ``.env`` na raiz do repositório."""
    return repo_root() / ".env"


def load_project_dotenv(path: Path | None = None) -> bool:
    """
    Carrega variáveis do ``.env`` do projeto.

    Usa caminho explícito (não depende do call stack), o que funciona em
    heredocs, notebooks e ``python -c``.

    Returns:
        ``True`` se o arquivo existir e foi lido; ``False`` caso contrário.
    """
    dotenv_file = path if path is not None else project_dotenv_path()
    loaded = load_dotenv(dotenv_path=dotenv_file, override=False)

    if loaded:
        logger.debug("Variáveis carregadas de %s", dotenv_file)
    else:
        logger.debug("Arquivo .env não encontrado em %s", dotenv_file)

    return loaded
