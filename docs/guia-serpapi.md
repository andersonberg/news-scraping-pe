# Guia SerpAPI — passo a passo

Este documento descreve como rodar o pipeline **implementado até aqui** usando SerpAPI para descobrir URLs e, em seguida, extrair o texto das matérias.

**Fora do escopo deste guia:** spiders Scrapy dos portais (NE10, JC, Diário de PE, nacionais) — ver [ROADMAP.md](ROADMAP.md) passos 10+.

---

## 1. O que você precisa antes de começar

| Item | Detalhe |
|------|---------|
| Python + uv | `uv sync` na raiz do repositório |
| SerpAPI | Chave em [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key) |
| Config local | `config/searches.yaml` (copiar de `searches.example.yaml`) |
| Ambiente | `.env` com `SERPAPI_API_KEY` (copiar de `.env.example`) |

**Custo:** cada job em `discover-serpapi` = **1 requisição** à SerpAPI. Com **720** jobs em `searches.example.yaml` (8 portais), rodar tudo de uma vez consome 720 créditos; configs locais com mais portais (ex.: 10 → **900** jobs) custam proporcionalmente mais. Use `--limit` e `--job-id` para testes.

---

## 2. Como a configuração se organiza

### `config/searches.yaml` — fonte da pesquisa

Define o **desenho do estudo** (revisado com o cientista político):

- `search_terms` — famílias de palavras (ação, processo, denúncia + justiça eleitoral, …)
- `candidates` — quem, cargo (`presidente` ou `governador_pe`), ano, **janela de datas**, variantes do nome
- `portals` — sites de notícia (`id`, `domain`, `tier`, `spider`, …)

**Expansão:** cada candidato habilitado é combinado com **todos** os portais habilitados (× termos × variantes de nome). O campo `office` no candidato (`presidente` ou `governador_pe`) identifica o cargo na eleição; não restringe quais portais entram no job.

Portais no exemplo versionado (`searches.example.yaml`): NE10, JC, Diário de PE, G1, Folha, UOL, Estadão, R7.

A CLI **não lê** `searches.yaml` na descoberta diretamente. Primeiro você gera o JSONL expandido.

### `data/queries.expanded.jsonl` — fila de trabalho

Gerado por `expand-queries`. Cada linha é um **job**, por exemplo:

```json
{
  "job_id": "lula_2022__processo__g1",
  "candidate_id": "lula_2022",
  "search_query": "\"Luiz Inácio Lula da Silva\" processo",
  "portal_id": "g1",
  "site_domain": "g1.globo.com",
  "query_window_start": "2022-08-05",
  "query_window_end": "2022-10-30",
  "office": "presidente",
  "election_year": 2022
}
```

`discover-serpapi` e `fetch-articles` usam este arquivo. O SerpAPI monta a query Google assim:

- Texto: `search_query`
- Restrição de site: `site:site_domain`
- Intervalo de datas: parâmetro `tbs` derivado de `query_window_start` / `query_window_end`

---

## 3. Variáveis de ambiente (`.env`)

```bash
SERPAPI_API_KEY=sua_chave_aqui
LOG_LEVEL=INFO
EXTRACTION_TIMEOUT_SECONDS=30

SEARCH_CONFIG_PATH=config/searches.yaml
URLS_PENDING_PATH=data/urls_pending.jsonl
ARTICLES_OUTPUT_PATH=data/articles.jsonl
```

A CLI chama `load_project_dotenv()` e carrega `.env` pela **raiz do projeto** (funciona mesmo em scripts `python <<'PY'` se usar o módulo `news_scraping_pe.env`).

---

## 4. Passo a passo completo

### Passo 0 — Instalar dependências

```bash
cd /caminho/para/news-scraping-pe
uv sync
```

### Passo 1 — Preparar config e ambiente

```bash
cp config/searches.example.yaml config/searches.yaml
cp .env.example .env
# Edite .env e coloque SERPAPI_API_KEY
# Revise searches.yaml (candidatos, termos, portais, janelas)
```

### Passo 2 — Validar a config

```bash
uv run news-scraping-pe validate-config
```

Saída esperada (stderr):

```text
INFO ... Validando configuração: .../config/searches.yaml
INFO ... Configuração válida: .../config/searches.yaml
```

Com log detalhado:

```bash
uv run news-scraping-pe -v validate-config
```

### Passo 3 — Expandir jobs

```bash
uv run news-scraping-pe expand-queries -o data/queries.expanded.jsonl
```

Com `searches.example.yaml` (8 portais): **720 jobs** — (7 variantes de nome para presidente + 8 para governador PE) × 6 termos × 8 portais.

Conferir:

```bash
wc -l data/queries.expanded.jsonl
head -n 1 data/queries.expanded.jsonl | uv run python -m json.tool
```

Listar alguns `job_id`:

```bash
uv run python -c "
import json
from pathlib import Path
for line in Path('data/queries.expanded.jsonl').read_text().splitlines()[:8]:
    print(json.loads(line)['job_id'])
"
```

**Quando regerar:** sempre que alterar `search_terms`, `candidates` ou `portals` no YAML.

### Passo 4 — Descobrir URLs com SerpAPI

Recomendado começar com **um job** para validar créditos e resultados:

```bash
# Exemplo: Lula 2022, termo processo, portal G1
uv run news-scraping-pe -v discover-serpapi \
  --job-id lula_2022__processo__g1
```

Outros filtros úteis:

```bash
# Primeiro job que bater no filtro (ainda 1 crédito se --limit 1)
uv run news-scraping-pe discover-serpapi \
  --candidate-id marilia_arraes_2022 \
  --portal-id jc \
  --limit 1

# Vários jobs (cuidado com créditos)
uv run news-scraping-pe discover-serpapi --limit 10

# Todos os jobs do JSONL (produção — planeje créditos SerpAPI; 720 no example, 900 com 10 portais)
uv run news-scraping-pe discover-serpapi
```

**O que acontece internamente:**

1. Lê jobs de `data/queries.expanded.jsonl` (com filtros).
2. Descarta jobs cujo `job_id` já apareça no log local `data/serpapi_usage_log.jsonl` (ver seção 6) — a menos que `--force` seja usado.
3. Para cada job restante, chama Google News via SerpAPI (`discovery/serpapi.py`).
4. Extrai links de `news_results` / `organic_results`.
5. Grava em `data/urls_pending.jsonl` com deduplicação (`storage/urls.py` + `storage/dedup.py`).
6. Cada URL recebe `discovered_via: serpapi` e o `job_id` do job.
7. Registra a tentativa (sucesso ou erro) em `data/serpapi_usage_log.jsonl`, com timestamp.

Conferir URLs gravadas:

```bash
wc -l data/urls_pending.jsonl
head -n 3 data/urls_pending.jsonl | uv run python -m json.tool
```

Rodar o mesmo job de novo **não gasta crédito de novo**: o `job_id` já está no log local, então o job é pulado (log: “Job já tentado anteriormente, pulando”). Para forçar uma nova consulta ao mesmo job (ex.: para pegar resultados mais recentes), use `--force`.

### Passo 5 — Extrair texto das matérias

```bash
uv run news-scraping-pe -v fetch-articles \
  --job-id lula_2022__processo__g1 \
  --limit 10
```

Filtros (mesma lógica de `discover-serpapi`):

- `--job-id`, `--candidate-id`, `--portal-id`, `--limit`
- `--urls-input` (padrão: `data/urls_pending.jsonl`)
- `--jobs` (padrão: `data/queries.expanded.jsonl` — metadados por `job_id`)
- `--articles-output` (padrão: `data/articles.jsonl`)

**O que acontece internamente:**

1. Seleciona linhas de `urls_pending.jsonl`.
2. Busca metadados do job no índice de `queries.expanded.jsonl`.
3. Baixa HTML (`extraction/text.py`).
4. Extrai texto com trafilatura; título/data via `extraction/metadata.py`.
5. Valida e grava em `articles.jsonl` (`storage/articles.py`).

Conferir artigos:

```bash
wc -l data/articles.jsonl
head -n 1 data/articles.jsonl | uv run python -m json.tool
```

### Passo 6 — Qualidade e nova rodada

Antes de uma coleta grande:

```bash
make lint test
```

Se mudou `searches.yaml`:

```bash
uv run news-scraping-pe validate-config
uv run news-scraping-pe expand-queries -o data/queries.expanded.jsonl
```

Se quiser recoletar do zero (cuidado: apaga dados locais):

```bash
rm -f data/urls_pending.jsonl data/articles.jsonl
```

---

## 5. Fluxo recomendado por escopo

### Teste inicial (baixo custo)

```bash
uv run news-scraping-pe validate-config
uv run news-scraping-pe expand-queries

uv run news-scraping-pe discover-serpapi \
  --job-id lula_2022__processo__g1

uv run news-scraping-pe fetch-articles \
  --job-id lula_2022__processo__g1 \
  --limit 5
```

### Governador PE (regional)

```bash
uv run news-scraping-pe discover-serpapi \
  --candidate-id marilia_arraes_2022 \
  --portal-id jc \
  --limit 6

uv run news-scraping-pe fetch-articles \
  --candidate-id marilia_arraes_2022 \
  --portal-id jc \
  --limit 20
```

### Presidente (nacional) — por portal

```bash
for portal in g1 folha uol estadao r7; do
  uv run news-scraping-pe discover-serpapi \
    --candidate-id lula_2022 \
    --portal-id "$portal" \
    --limit 6
done
```

Ajuste `--limit` conforme orçamento SerpAPI.

---

## 6. Cota mensal e trabalho com múltiplas contas

Se sua conta SerpAPI tem um limite mensal (ex.: 250 requisições no plano gratuito) e o backlog de jobs é maior que isso, use o comando `quota-status` para saber quantos créditos já foram usados neste mês e qual o próximo lote de jobs a rodar.

### Como funciona o rastreio

- Toda execução de `discover-serpapi` grava cada tentativa (sucesso ou erro) em `data/serpapi_usage_log.jsonl` — um arquivo **local, não versionado** (coberto pela regra `*.jsonl` do `.gitignore`), com `job_id`, `attempted_at`, `status` e `urls_found`.
- Por padrão, `discover-serpapi` **pula automaticamente** qualquer `job_id` já presente nesse log, então rodar o mesmo comando várias vezes é seguro e não desperdiça créditos.
- Como o log é local, ele só sabe o que **esta conta/máquina** já rodou. Ele não sabe o que outra pessoa da equipe já rodou com a própria conta.

### `quota-status`: ver progresso e próximo lote

```bash
uv run news-scraping-pe quota-status --monthly-quota 230
```

Isso imprime:

- total de jobs, quantos já foram feitos (no total e neste mês) e quantos restam;
- créditos disponíveis neste mês (`--monthly-quota` menos os já usados no mês corrente);
- o próximo lote sugerido de `job_id`s, respeitando a **ordem sequencial** em que aparecem em `queries.expanded.jsonl` (ou seja, termina os jobs de um candidato/portal antes de passar para o próximo).

O lote sugerido também é gravado em `data/serpapi_next_batch.txt` (um `job_id` por linha; use `-o` para outro caminho). Para rodá-lo:

```bash
uv run news-scraping-pe discover-serpapi --job-ids-file data/serpapi_next_batch.txt
```

`--monthly-quota` deve ficar **um pouco abaixo** do limite real da conta (ex.: 230 em vez de 250) como margem de segurança. `--candidate-id`/`--portal-id` restringem o status a um subconjunto (útil quando cada pessoa está cobrindo um recorte diferente).

### Coordenando entre contas da equipe

Como o log de uso é local a cada máquina/conta, a divisão do trabalho entre pessoas é **manual**: combinem por chat/planilha quem roda qual fatia, para não gastar créditos de contas diferentes no mesmo `job_id`. Duas abordagens simples:

1. **Por candidato/portal:** cada pessoa roda `quota-status --candidate-id X` (ou `--portal-id X`) para um recorte que ninguém mais está cobrindo naquele mês.
2. **Por sequência:** como a ordem dos jobs em `queries.expanded.jsonl` é estável, quem terminar um lote avisa qual foi o último `job_id` processado; a próxima pessoa roda `quota-status` e pega a continuação (jobs após aquele ponto já aparecem como pendentes, já que o log local de quem rodou antes é o que decide isso — cada pessoa soma o que já viu no grupo).

Em ambos os casos, `discover-serpapi --force` só deve ser usado deliberadamente (ex.: recoletar um job específico), já que ele ignora o skip automático.

---

## 7. Formato dos arquivos de saída

### `urls_pending.jsonl`

```json
{
  "url": "https://g1.globo.com/...",
  "job_id": "lula_2022__processo__g1",
  "discovered_via": "serpapi"
}
```

### `articles.jsonl`

Campos obrigatórios definidos em [`article_schema.json`](article_schema.json). Exemplo em [`data/articles.example.jsonl`](../data/articles.example.jsonl).

`view_count` é opcional (ainda não extraído automaticamente nesta fase).

### `serpapi_usage_log.jsonl` (local, não versionado)

```json
{
  "job_id": "lula_2022__processo__g1",
  "attempted_at": "2026-07-18T14:32:05.123456+00:00",
  "status": "ok",
  "urls_found": 4
}
```

Ver seção 6 para como esse arquivo é usado (skip automático + `quota-status`).

---

## 8. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| `SERPAPI_API_KEY não configurada` | `.env` vazio ou não carregado | Preencher `.env`; CLI carrega sozinha; em scripts use `load_project_dotenv()` |
| `AssertionError` ao usar `load_dotenv()` sem caminho | Heredoc / `-c` sem arquivo | Use `from news_scraping_pe.env import load_project_dotenv` |
| `Nenhum job selecionado` | Filtro `--job-id` errado | Liste ids com o comando do passo 3 |
| Muitas falhas em `fetch-articles` | URL é PDF, paywall ou página sem texto | Normal; veja logs `WARNING`; aumente `--limit` |
| `urls_failed` alto | Sites bloqueiam bot ou HTML vazio | Esperado em parte; filtrar URLs manualmente depois |
| `Job não encontrado no índice` | `job_id` em pending não existe no JSONL expandido | Regerar `expand-queries` ou limpar pending antigo |
| Créditos SerpAPI acabam rápido | 1 crédito por job | Use `--limit`; processe por candidato/portal; use `quota-status` para planejar por mês (seção 6) |

---

## 9. Referência rápida da CLI

```bash
uv run news-scraping-pe --help
uv run news-scraping-pe discover-serpapi --help
uv run news-scraping-pe fetch-articles --help
uv run news-scraping-pe quota-status --help
```

| Flag global | Efeito |
|-------------|--------|
| `-v` / `--verbose` | Log nível DEBUG |

---

## 10. Próximos passos no projeto

- Spiders regionais (NE10, JC, Diário de PE) alimentarão o mesmo `urls_pending.jsonl` com `discovered_via: ne10_spider`, etc.
- Spiders nacionais só se necessário além do SerpAPI.
- `view_count` por portal (passo 13 do roadmap).

Atualizações de implementação: [ROADMAP.md](ROADMAP.md).
