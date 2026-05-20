.PHONY: sync sync-all lint format test validate-config expand-queries discover-serpapi clean

# Instala dependências (inclui grupo dev) e o pacote em modo editável
sync:
	uv sync

# Inclui extras opcionais (ex.: playwright)
sync-all:
	uv sync --all-extras

lint:
	uv run ruff check src tests scripts
	uv run ruff format --check src tests scripts
	uv run mypy src

format:
	uv run ruff check --fix src tests scripts
	uv run ruff format src tests scripts

test:
	uv run pytest

validate-config:
	uv run news-scraping-pe validate-config

expand-queries:
	uv run news-scraping-pe expand-queries -o data/queries.expanded.jsonl

discover-serpapi:
	uv run news-scraping-pe discover-serpapi --limit 1

clean:
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
