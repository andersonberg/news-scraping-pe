"""One-off: reescreve job_id no serpapi_usage_log para o novo formato de 4 segmentos.

Mapeia cada tentativa antiga (job_id de 3 segmentos) para o job_id novo (4 segmentos)
da variante correspondente, casando tentativas ordenadas por attempted_at com as
variantes na ordem do arquivo expandido regenerado. Falha ruidosamente em qualquer
divergência de contagem. Faz backup .bak antes de gravar.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from news_scraping_pe.config.paths import (
    default_queries_expanded_path,
    default_serpapi_usage_log_path,
)


def ordered_new_ids_by_prefix(expanded_path: Path) -> dict[str, list[str]]:
    """Agrupa job_ids novos por prefixo de 3 segmentos, preservando a ordem do arquivo."""
    groups: dict[str, list[str]] = defaultdict(list)
    with expanded_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            job_id = json.loads(line)["job_id"]
            prefix = job_id.rsplit("__", 1)[0]
            groups[prefix].append(job_id)
    return dict(groups)


def migrate(expanded_path: Path, usage_log_path: Path, *, dry_run: bool) -> int:
    new_ids_by_prefix = ordered_new_ids_by_prefix(expanded_path)

    attempts: list[dict] = []
    with usage_log_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                attempts.append(json.loads(line))

    groups: dict[str, list[int]] = defaultdict(list)
    for i, a in enumerate(attempts):
        groups[a["job_id"]].append(i)

    mapping: dict[int, str] = {}
    mismatches: list[str] = []
    for old_id, idxs in groups.items():
        new_ids = new_ids_by_prefix.get(old_id)
        if not new_ids:
            mismatches.append(f"{old_id}: nenhuma variante correspondente no expandido")
            continue
        if len(idxs) > len(new_ids):
            mismatches.append(f"{old_id}: {len(idxs)} tentativas > {len(new_ids)} variantes")
            continue
        for pos, i in enumerate(sorted(idxs, key=lambda i: attempts[i]["attempted_at"])):
            mapping[i] = new_ids[pos]

    if mismatches:
        print("Migração abortada — divergências:", file=sys.stderr)
        for m in mismatches:
            print(f"  - {m}", file=sys.stderr)
        return 1

    for i, new_id in mapping.items():
        attempts[i]["job_id"] = new_id

    print(f"{len(mapping)} tentativa(s) remapeada(s) de {len(groups)} grupo(s).")
    if dry_run:
        print("dry-run: nada gravado.")
        return 0

    backup = usage_log_path.with_suffix(usage_log_path.suffix + ".bak")
    backup.write_text(usage_log_path.read_text(encoding="utf-8"), encoding="utf-8")
    with usage_log_path.open("w", encoding="utf-8") as fh:
        for a in attempts:
            fh.write(json.dumps(a, ensure_ascii=False) + "\n")
    print(f"Gravado. Backup em {backup}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expanded", type=Path, default=default_queries_expanded_path())
    parser.add_argument("--usage-log", type=Path, default=default_serpapi_usage_log_path())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return migrate(args.expanded, args.usage_log, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
