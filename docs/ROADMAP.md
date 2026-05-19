# Roadmap — passos pequenos com pausa para revisão

Cada passo termina com: **revisão → `make lint test` → teste manual → commit curto → pausa**.

Não avançar ao passo seguinte sem sua confirmação.

**Escopo fechado:** eleições **2018 e 2022** apenas. **2014 não entra** neste projeto.

---

## Convenções (PEP 20 + simplicidade)

- Uma função/método = **uma responsabilidade**.
- Preferir código explícito a abstrações prematuras.
- **Docstrings** em funções e métodos públicos (o quê + entradas/saída quando não for óbvio).
- **Logging** (`logging` stdlib): `INFO` no caminho feliz, `WARNING` para recuperável, `ERROR` para falha; sem `print` em produção.
- Testes só onde validam comportamento real (não testar o óbvio).

---

## Concluído

| # | Entrega |
|---|---------|
| 0 | Schemas, `searches.example.yaml`, CLI `validate-config` / `expand-queries`, repo + uv |

---

## Próximos passos

### Passo 1 — Setup local versionado (sem código novo)

**Entrega:** `config/searches.yaml` local, `.env` com chaves, primeiro `uv run news-scraping-pe expand-queries`.

**Commit sugerido:** `chore: config local e lockfile` (só se versionar algo novo; `.env` e `searches.yaml` ficam fora do git).

**Checklist manual:** `validate-config` OK; `queries.expanded.jsonl` gerado com 270 jobs.

---

### Passo 2 — Logging centralizado ✅

**Entrega:** módulo `news_scraping_pe/log.py`; CLI usa `logging` e flag `-v` / `LOG_LEVEL`.

**Commit sugerido:** `feat(logging): configura logging padrão do projeto`

**Teste manual:**
```bash
uv run news-scraping-pe validate-config
uv run news-scraping-pe -v validate-config
LOG_LEVEL=DEBUG uv run news-scraping-pe validate-config
```

---

### Passo 3 — Persistência de URLs pendentes ✅

**Entrega:** `news_scraping_pe/storage/urls.py` — `append_pending_url`, `append_pending_urls`, `iter_pending_urls`, `read_pending_urls`.

**Commit sugerido:** `feat(storage): leitura e escrita de urls pendentes`

**Teste manual (Python):**
```python
from news_scraping_pe.storage.urls import append_pending_url, read_pending_urls
append_pending_url({"url": "https://example.com/a", "job_id": "test__processo__ne10", "discovered_via": "manual"})
print(read_pending_urls())
```

---

### Passo 4 — Deduplicação de URLs ✅

**Entrega:** `storage/dedup.py` (`normalize_url`, `filter_unique_pending_urls`); `append_pending_urls` ignora duplicatas.

**Commit sugerido:** `feat(storage): deduplicação de URLs`

**Teste manual:** gravar a mesma URL duas vezes (com `utm_*` diferente) e conferir uma linha em `data/urls_pending.jsonl`.

---

### Passo 5 — Cliente SerpAPI (uma query por vez)

**Entrega:** `discovery/serpapi.py` — dado um job do JSONL expandido, retorna lista de URLs; lê `SERPAPI_API_KEY` do ambiente; logs de request/erro.

**Arquivos:** 1 módulo + testes com `httpx` mockado (sem chamada real na CI).

**Commit sugerido:** `feat(discovery): cliente SerpAPI para descoberta de URLs`

**Teste manual:** 1 query real contra SerpAPI; conferir URLs no log ou arquivo temporário.

---

### Passo 6 — Orquestrador SerpAPI → urls pendentes

**Entrega:** comando CLI `discover-serpapi` que lê N jobs (ou todos), chama passo 5, grava no pool (passos 3–4).

**Commit sugerido:** `feat(cli): comando discover-serpapi`

**Teste manual:** rodar para 1 candidato × 1 termo × 1 portal regional.

---

### Passo 7 — Extração de texto (trafilatura)

**Entrega:** `extraction/text.py` — função `fetch_raw_text(url) -> str | None` com timeout e logging.

**Commit sugerido:** `feat(extraction): extração de texto com trafilatura`

**Teste manual:** 2–3 URLs reais de matérias dos portais regionais.

---

### Passo 8 — Persistência de artigos JSONL

**Entrega:** `storage/articles.py` — validar campos obrigatórios do schema e append em `data/articles.jsonl`.

**Commit sugerido:** `feat(storage): grava artigos em JSONL`

---

### Passo 9 — Pipeline “URL pendente → artigo”

**Entrega:** CLI `fetch-articles` que lê `urls_pending`, chama passo 7, grava passo 8; metadados do job propagados.

**Commit sugerido:** `feat(cli): comando fetch-articles`

---

### Passo 10 — Spider NE10 (somente descoberta)

**Entrega:** spider Scrapy que, para um job, preenche `urls_pending` (busca interna do site).

**Commit sugerido:** `feat(spiders): spider NE10 para descoberta de URLs`

**Teste manual:** `uv run scrapy crawl ne10 -a job_id=...` (ou equivalente mínimo).

---

### Passo 11 — Spider JC (descoberta)

Mesmo padrão do passo 10.

**Commit sugerido:** `feat(spiders): spider JC para descoberta de URLs`

---

### Passo 12 — Spider Diário de PE (descoberta)

Mesmo padrão do passo 10.

**Commit sugerido:** `feat(spiders): spider Diário de PE para descoberta de URLs`

---

### Passo 13 — view_count (opcional, um portal por vez)

**Entrega:** parser de visualizações só onde o HTML expuser; campo omitido se não houver.

Subpassos sugeridos: 13a NE10 → 13b JC → 13c Diário de PE (cada um = 1 commit).

---

### Passo 14 — GDELT (avaliação + integração mínima)

**Entrega:** script/query que lista URLs candidatas; só integrar ao pool se cobertura &lt; limiar.

**Commit sugerido:** `feat(discovery): integração GDELT complementar`

---

### Passo 15 — Métricas de cobertura

**Entrega:** CLI `report-coverage` — contagem por candidato/portal/termo; sugere se Tier 3 é necessário.

**Decisão a tomar neste passo:** limiar (ex.: &lt; 10 artigos/candidato).

---

### Passo 16 — Tier 3 nacionais (condicional)

Só após passo 15 indicar necessidade. **Um portal por commit** (G1, Folha, …).

---

### Passo 17 — Wayback (complemento)

**Entrega:** fallback para URLs que retornam 404 na extração.

**Commit sugerido:** `feat(extraction): fallback Wayback Machine`

---

## Fase 2 (fora deste repo)

Data science: frequência de menções, correlação com intenção de voto.

---

## Decisões fechadas

| Tema | Decisão |
|------|---------|
| Anos | 2018 e 2022 |
| 2014 | **Não incluir** |
| Portais prioritários | NE10, JC, Diário de PE |
| Saída scraping | Texto bruto + metadados; `view_count` opcional |
| Ritmo | Pausa + commit após **cada** passo acima |

## Decisão em aberto

- Limiar de “cobertura baixa” para Tier 3 (definir no **passo 15**).
