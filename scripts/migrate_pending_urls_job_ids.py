"""One-off: reescreve job_id em urls_pending.jsonl para o novo formato de 4 segmentos.

Usa o serpapi_usage_log já migrado (job_id novo) como fonte de verdade: agrupa blocos
contíguos de urls_pending.jsonl por job_id antigo e casa 1:1, em ordem, com as tentativas
bem-sucedidas (status="ok", urls_found>0) daquele job_id antigo. Só migra grupos onde a
contagem de blocos bate exatamente com a contagem de tentativas; os demais (contagem
divergente — histórico irreconciliável, ex.: buscas de variantes com resultados
sobrepostos) permanecem com o job_id antigo e são listados no relatório. Faz backup .bak
antes de gravar.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from news_scraping_pe.config.paths import (
    default_serpapi_usage_log_path,
    default_urls_pending_path,
)


def ok_new_ids_by_old_id(usage_log_path: Path) -> dict[str, list[str]]:
    """Agrupa job_ids novos (tentativas ok com urls_found>0) por prefixo antigo, em ordem."""
    groups: dict[str, list[str]] = defaultdict(list)
    with usage_log_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            attempt = json.loads(line)
            if attempt["status"] != "ok" or attempt["urls_found"] <= 0:
                continue
            new_id = attempt["job_id"]
            old_id = new_id.rsplit("__", 1)[0]
            groups[old_id].append(new_id)
    return dict(groups)


def contiguous_blocks(records: list[dict]) -> dict[str, list[tuple[int, int]]]:
    """Agrupa índices de linhas contíguas com o mesmo job_id, em ordem de ocorrência."""
    blocks: dict[str, list[tuple[int, int]]] = defaultdict(list)
    cur_id: str | None = None
    start = 0
    for i, rec in enumerate(records):
        if rec["job_id"] != cur_id:
            if cur_id is not None:
                blocks[cur_id].append((start, i))
            cur_id = rec["job_id"]
            start = i
    if cur_id is not None:
        blocks[cur_id].append((start, len(records)))
    return dict(blocks)


def migrate(usage_log_path: Path, pending_path: Path, *, dry_run: bool) -> int:
    new_ids_by_old = ok_new_ids_by_old_id(usage_log_path)

    records: list[dict] = []
    with pending_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    blocks_by_old = contiguous_blocks(records)

    migrated_lines = 0
    skipped: list[str] = []
    for old_id, blocks in blocks_by_old.items():
        new_ids = new_ids_by_old.get(old_id, [])
        if len(blocks) != len(new_ids):
            skipped.append(f"{old_id}: {len(blocks)} bloco(s) x {len(new_ids)} tentativa(s)")
            continue
        for (start, end), new_id in zip(blocks, new_ids, strict=True):
            for i in range(start, end):
                records[i]["job_id"] = new_id
            migrated_lines += end - start

    print(f"{migrated_lines} linha(s) migrada(s) em {len(blocks_by_old) - len(skipped)} grupo(s).")
    if skipped:
        print(f"{len(skipped)} grupo(s) ambíguo(s) deixados sem alteração:")
        for s in skipped:
            print(f"  - {s}")

    if dry_run:
        print("dry-run: nada gravado.")
        return 0

    backup = pending_path.with_suffix(pending_path.suffix + ".bak")
    backup.write_text(pending_path.read_text(encoding="utf-8"), encoding="utf-8")
    with pending_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Gravado. Backup em {backup}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usage-log", type=Path, default=default_serpapi_usage_log_path())
    parser.add_argument("--pending", type=Path, default=default_urls_pending_path())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return migrate(args.usage_log, args.pending, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
