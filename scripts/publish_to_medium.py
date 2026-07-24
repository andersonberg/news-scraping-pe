"""Publica um arquivo Markdown como rascunho no Medium via API.

Uso:
    uv run python scripts/publish_to_medium.py articles/article-search-then-extract.md

A primeira linha do arquivo deve ser o título no formato:
    # Título do Artigo

O script remove esse cabeçalho do corpo e usa o texto como título da publicação.

Variáveis de ambiente necessárias (em .env):
    MEDIUM_INTEGRATION_TOKEN  — token gerado em medium.com/me/settings/security

O artigo é publicado como rascunho (publishStatus=draft).
Revise e publique manualmente no editor do Medium.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

from news_scraping_pe.env import load_project_dotenv
from news_scraping_pe.log import configure_logging, get_logger

MEDIUM_API_BASE = "https://api.medium.com/v1"

TAGS = ["web-scraping", "python", "data-science", "scrapy", "research"]

logger = get_logger(__name__)


def read_token() -> str:
    import os

    token = os.getenv("MEDIUM_INTEGRATION_TOKEN", "").strip()
    if not token:
        logger.error(
            "Variável MEDIUM_INTEGRATION_TOKEN não configurada. "
            "Gere um token em: https://medium.com/me/settings/security"
        )
        sys.exit(1)
    return token


def get_user_id(client: httpx.Client) -> str:
    response = client.get(f"{MEDIUM_API_BASE}/me")
    response.raise_for_status()
    data = response.json()
    user_id: str = data["data"]["id"]
    username: str = data["data"]["username"]
    logger.info("Autenticado como @%s (id=%s)", username, user_id)
    return user_id


def parse_article(path: Path) -> tuple[str, str]:
    """Extrai (título, corpo) do arquivo Markdown.

    Espera que a primeira linha seja '# Título'. Remove o H1 do corpo
    para evitar duplicação no Medium.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title = ""
    body_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            body_start = i + 1
            break

    if not title:
        logger.error("Não encontrei um título '# ...' no arquivo %s", path)
        sys.exit(1)

    # Remove linhas em branco iniciais após o título
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1

    body = "\n".join(lines[body_start:]).strip()
    return title, body


def publish_draft(
    client: httpx.Client,
    user_id: str,
    title: str,
    content: str,
    tags: list[str],
) -> dict[str, object]:
    payload = {
        "title": title,
        "contentFormat": "markdown",
        "content": content,
        "tags": tags[:5],  # Medium aceita no máximo 5 tags
        "publishStatus": "draft",
    }

    logger.info("Publicando rascunho: %r", title)
    response = client.post(
        f"{MEDIUM_API_BASE}/users/{user_id}/posts",
        json=payload,
    )

    if response.status_code not in (200, 201):
        logger.error(
            "Erro da API Medium (HTTP %d): %s",
            response.status_code,
            response.text,
        )
        sys.exit(1)

    return response.json()  # type: ignore[no-any-return]


def build_client(token: str) -> httpx.Client:
    return httpx.Client(
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30.0,
    )


def main(argv: list[str] | None = None) -> int:
    load_project_dotenv()
    configure_logging()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "article",
        type=Path,
        help="Caminho para o arquivo .md (ex.: articles/article-search-then-extract.md)",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=TAGS,
        help="Tags do artigo (máx. 5). Padrão: %(default)s",
    )
    args = parser.parse_args(argv)

    article_path: Path = args.article
    if not article_path.exists():
        logger.error("Arquivo não encontrado: %s", article_path)
        return 1

    title, body = parse_article(article_path)
    logger.info("Artigo lido: %r (%d caracteres no corpo)", title, len(body))

    token = read_token()

    with build_client(token) as client:
        user_id = get_user_id(client)
        result = publish_draft(client, user_id, title, body, args.tags)

    post_data = result.get("data", {})
    post_url = post_data.get("url", "—")
    post_id = post_data.get("id", "—")

    print()
    print("✓ Rascunho criado com sucesso!")
    print(f"  URL: {post_url}")
    print(f"  ID:  {post_id}")
    print()
    print("Abra a URL acima no Medium para revisar e publicar.")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
