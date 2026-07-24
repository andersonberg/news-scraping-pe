"""Tipos compartilhados do módulo de persistência."""

from typing import TypedDict


class PendingUrl(TypedDict):
    """Registro mínimo de uma URL descoberta e ainda não extraída."""

    url: str
    job_id: str
    discovered_via: str


class JobAttempt(TypedDict):
    """Registro de uma tentativa de consulta SerpAPI para um job."""

    job_id: str
    attempted_at: str
    status: str
    urls_found: int
