"""Caminhos padrão relativos à raiz do repositório."""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """Sobe de src/news_scraping_pe/config até a raiz do repo."""
    return Path(__file__).resolve().parents[3]


def default_config_path() -> Path:
    env = os.getenv("SEARCH_CONFIG_PATH")
    if env:
        p = Path(env)
        return p if p.is_absolute() else repo_root() / p
    return repo_root() / "config" / "searches.yaml"


def schema_path(name: str) -> Path:
    return repo_root() / "docs" / name
