# Contribuindo

## Fluxo de trabalho Git

1. Crie uma branch a partir de `main`: `feat/nome-curto` ou `fix/nome-curto`.
2. Commits em **português ou inglês**, no imperativo e com escopo claro:
   - `feat(spiders): adiciona spider NE10`
   - `fix(config): corrige janela de Paulo Câmara 2018`
3. Abra um Pull Request contra `main` com descrição do que mudou e como testar.
4. CI deve passar (lint + testes).

## Ambiente local

- Use **[uv](https://docs.astral.sh/uv/)** (`uv sync` na raiz do repo).
- Após alterar dependências em `pyproject.toml`, rode `uv lock` e commitar `uv.lock`.
- Prefira `uv run <comando>` ou `make` em vez de ativar o venv manualmente.

## Ritmo de entrega

Siga o [docs/ROADMAP.md](docs/ROADMAP.md): **um passo por vez**, pausa para revisão, `make lint test`, teste manual e **commit curto** antes do próximo passo.

## Padrões de código

- **PEP 20:** simples é melhor que complexo; uma função = uma responsabilidade.
- **Docstrings** em funções e métodos públicos.
- **Logging** (`logging` stdlib): `INFO` no fluxo normal, `WARNING`/`ERROR` em falhas; evitar `print`.
- **Ruff** + **mypy** (`make lint`).
- **pytest** só para comportamento não trivial.
- Não commitar `.env`, `config/searches.yaml` (dados locais) nem `data/articles.jsonl`.

## Scrapy

- Um spider por portal em `src/news_scraping_pe/scrapy/spiders/`.
- Itens alinhados ao schema em `docs/article_schema.json`.
- Respeitar `robots.txt` e throttle; projeto acadêmico de varredura única — evitar carga desnecessária nos portais.

## Configuração de buscas

- Alterações em candidatos/termos/janelas: editar `config/searches.example.yaml` e documentar no PR.
- Copiar para `config/searches.yaml` localmente (não versionado).
