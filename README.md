# news-scraping-pe

Coleta histórica **única** de notícias em mídia aberta sobre ações judiciais contra candidatos a **Presidente da República** e **Governador de Pernambuco** (eleições **2018** e **2022**). Projeto de pesquisa acadêmica — não é um produto de monitoramento contínuo.

## Objetivo

1. **Fase 1 (este repositório):** descobrir URLs e extrair **texto bruto** + metadados (incl. visualizações quando disponíveis).
2. **Fase 2 (fora deste repo):** data science — correlação com pesquisas de intenção de voto.

## Fontes (prioridade)

| Tier | Fontes | Estratégia |
|------|--------|------------|
| 1 | NE10, Jornal do Commercio, Diário de PE | Spiders Scrapy diretos |
| 2 | Ampla | SerpAPI, GDELT (complemento) |
| 3 | G1, Folha, UOL, Estadão, R7 | Fallback se cobertura baixa |

## Estrutura do repositório

```
news-scraping-pe/
├── config/              # Buscas (YAML) — ver searches.example.yaml
├── docs/                # JSON Schemas (artigo, config)
├── data/                # Saídas locais (gitignored exceto exemplos)
├── src/news_scraping_pe/
│   ├── config/          # Carregamento e validação do YAML
│   ├── discovery/       # SerpAPI, GDELT (a implementar)
│   ├── extraction/      # Parsers de artigo / view_count (a implementar)
│   └── scrapy/          # Projeto Scrapy (spiders, items, settings)
├── scripts/             # Utilitários CLI
└── tests/
```

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes e ambientes)
- Python **3.11+** (o uv pode instalar automaticamente via `.python-version`)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Configuração rápida

```bash
git clone git@github.com:SEU_USUARIO/news-scraping-pe.git
cd news-scraping-pe

uv sync          # cria .venv, instala deps + pacote (grupo dev incluso)
# opcional: source .venv/bin/activate

cp .env.example .env
# Edite .env com SERPAPI_API_KEY

cp config/searches.example.yaml config/searches.yaml
```

O lockfile [`uv.lock`](uv.lock) garante builds reproduzíveis — commitar junto com `pyproject.toml`.

## Uso (stubs — implementação em andamento)

```bash
# Validar config de buscas
uv run news-scraping-pe validate-config

# Expandir candidatos × termos → jobs (JSONL)
uv run news-scraping-pe expand-queries -o data/queries.expanded.jsonl

# Scrapy (na raiz do repo, quando spiders existirem)
uv run scrapy list

# Extra opcional (portais com JS pesado)
uv sync --extra playwright
```

## Dados de saída

Artigos em JSONL conforme [`docs/article_schema.json`](docs/article_schema.json). Exemplo: [`data/articles.example.jsonl`](data/articles.example.jsonl).

Campos obrigatórios: URL, texto bruto, candidato, janela de busca, etc. `view_count` é **opcional** — o artigo é salvo mesmo sem contador de visualizações.

## Desenvolvimento

```bash
uv sync
uv run pre-commit install
make lint test
```

Comandos úteis:

| Comando | Descrição |
|---------|-----------|
| `uv sync` | Instala/atualiza dependências conforme `uv.lock` |
| `uv lock` | Atualiza o lockfile após mudar `pyproject.toml` |
| `uv add httpx` | Adiciona dependência de runtime |
| `uv add --group dev pytest-mock` | Adiciona dependência de desenvolvimento |
| `uv run pytest` | Executa no ambiente do projeto sem ativar `.venv` |

Ver [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

MIT — ver [LICENSE](LICENSE).
