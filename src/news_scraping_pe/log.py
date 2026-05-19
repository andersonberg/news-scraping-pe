"""Configuração centralizada de logging do projeto."""

from __future__ import annotations

import logging
import os
import sys
from typing import Final

PACKAGE_LOGGER: Final[str] = "news_scraping_pe"

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _resolve_level(level: int | str | None) -> int:
    """Converte nível explícito, variável de ambiente ou padrão em constante logging."""
    if level is not None:
        if isinstance(level, int):
            return level
        return logging.getLevelNamesMapping()[level.upper()]

    env_level = os.getenv("LOG_LEVEL", "INFO")
    return logging.getLevelNamesMapping()[env_level.upper()]


def configure_logging(level: int | str | None = None) -> None:
    """
    Configura o logger raiz do pacote ``news_scraping_pe``.

    Envía saída para stderr. Chamadas repetidas não adicionam handlers duplicados.
    ``LOG_LEVEL`` no ambiente (ex.: DEBUG, INFO) é usado quando ``level`` é omitido.
    """
    logger = logging.getLogger(PACKAGE_LOGGER)
    if logger.handlers:
        logger.setLevel(_resolve_level(level))
        return

    resolved = _resolve_level(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt=_DEFAULT_FORMAT, datefmt=_DEFAULT_DATE_FORMAT))

    logger.setLevel(resolved)
    logger.addHandler(handler)
    logger.propagate = False

    setup_logger = logging.getLogger(__name__)
    setup_logger.debug("Logging configurado (nível=%s)", logging.getLevelName(resolved))


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger filho de ``news_scraping_pe``.

    Args:
        name: Nome do módulo (ex.: ``news_scraping_pe.cli`` ou ``cli``).
    """
    if name.startswith(f"{PACKAGE_LOGGER}."):
        return logging.getLogger(name)
    if name == PACKAGE_LOGGER:
        return logging.getLogger(name)
    return logging.getLogger(f"{PACKAGE_LOGGER}.{name}")
