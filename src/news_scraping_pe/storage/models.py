"""Tipos compartilhados do módulo de persistência."""

from typing import TypedDict


class PendingUrl(TypedDict):
    """Registro mínimo de uma URL descoberta e ainda não extraída."""

    url: str
    job_id: str
    discovered_via: str
