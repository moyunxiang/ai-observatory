"""Category validation CLI (Task 3 of JIA_LIU_TASK.md).

    python scripts/validate.py check                        # Task 1/2 acceptance checks, no API call
    python scripts/validate.py export --run-id R [--only ID ...]   # manual sheet -> runs/R/manual_sheet.txt
    python scripts/validate.py import runs/R                # filled sheet -> runs/R/responses.jsonl
    python scripts/validate.py query --provider P --model M # (API mode, not configured yet)
    python scripts/validate.py score runs/R                 # Recall@10 -> results.csv, summary.json, attempts
    python scripts/validate.py master                       # outputs/master_table.csv (Pass categories only)

Raw answers are always saved before scoring and never overwritten; `score`
can be re-run on saved answers (e.g. after alias fixes) without re-querying.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from observatory.data import (  # noqa: E402
    append_attempts, check_category_brands, check_seeds, load_aliases, load_attempts,
    load_categories, load_category_brands, load_seed_brands,
)
from observatory.llm import PROMPT_TEMPLATE, SUPPORTED_PROVIDERS, build_prompt, query_llm  # noqa: E402
from observatory.manual import parse_sheet, render_sheet  # noqa: E402
from observatory.metrics import PASS_THRESHOLD, passes, recall_at_k  # noqa: E402
from observatory.normalize import build_alias_map  # noqa: E402
from observatory.parse import parse_brand_list  # noqa: E402

RUNS_DIR = ROOT / "runs"
OUTPUTS_DIR = ROOT / "outputs"
MIN_PARSED_WARN = 5


def _select(categories: list[dict], only: list[str] | None) -> list[dict]:
    if not only:
        return categories
    known = {c["category_id"] for c in categories}
    unknown = set(only) - known
    if unknown:
        raise SystemExit(f"Unknown category_id(s): {sorted(unknown)}")
    return [c for c in categories if c["category_id"] in set(only)]


def _new_run_dir(run_id: str | None) -> Path:
    run_dir = RUNS_DIR / (run_id or datetime.now().strftime("%Y%m%d_%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=False)  # never overwrite an existing run
    return run_dir


def cmd_check(args) -> int:
    categories = load_categories()
    seeds = load_seed_brands()
    alias_map = build_alias_map(load_aliases())
    problems = check_seeds(seeds, categories)
    problems += check_category_brands([c["category_id"] for c in categories], load_category_brands(), seeds, alias_map)
    print(f"{len(seeds)} seed brands, {len(categories)} categories.")
    if problems:
        print(f"NOT ready ({len(problems)} problems):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("All Task 1/2 checks OK.")
    return 0


def cmd_export(args) -> int:
    categories = _select(load_categories(), args.only)
    run_dir = _new_run_dir(args.run_id)
    items = [
        {"category_id": c["category_id"], "category_name": c["category_name"], "prompt": build_prompt(c["category_name"])}
        for c in categories
    ]
    (run_dir / "manual_sheet.txt").write_text(render_sheet(items), encoding="utf-8")
    print(f"Wrote {len(items)} prompts to {run_dir / 'manual_sheet.txt'}")
    return 0


def cmd_import(args) -> int:
    run_dir = Path(args.run_dir)
    out = run_dir / "responses.jsonl"
    if out.exists():
        print(f"{out} already exists; refusing to overwrite.")
        return 1
    meta, records = parse_sheet((run_dir / "manual_sheet.txt").read_text(encoding="utf-8"))
    missing_meta = [k for k in ("model", "date", "web_search", "temporary_chat") if not meta.get(k)]
    empty = [r["category_id"] for r in records if not r["response"]]
    if missing_meta or empty:
        print(f"Sheet incomplete. Missing header fields: {missing_meta}; empty answers: {empty}")
        return 1
    for r in records:
        n = len(parse_brand_list(r["response"]))
        if n < MIN_PARSED_WARN:
            print(f"WARNING {r['category_id']}: only {n} brands parsed; check the pasted answer.")

    (run_dir / "meta.json").write_text(json.dumps({
        "run_id": run_dir.name, "mode": "manual", "prompt_template": PROMPT_TEMPLATE,
        **meta, "imported_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Imported {len(records)} answers -> {out}")
    return 0


def cmd_query(args) -> int:
    if args.provider not in SUPPORTED_PROVIDERS:
        print(f"Provider '{args.provider}' is not implemented yet (supported: {sorted(SUPPORTED_PROVIDERS) or 'none'}).")
        return 1
    categories = _select(load_categories(), args.only)
    run_dir = _new_run_dir(args.run_id)
    (run_dir / "meta.json").write_text(json.dumps({
        "run_id": run_dir.name, "mode": "api", "provider": args.provider, "model": args.model,
        "temperature": args.temperature, "prompt_template": PROMPT_TEMPLATE,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    with open(run_dir / "responses.jsonl", "a", encoding="utf-8") as f:
        for cat in categories:
            prompt = build_prompt(cat["category_name"])
            record = {"category_id": cat["category_id"], "category_name": cat["category_name"], "prompt": prompt}
            try:
                record["response"] = query_llm(prompt, args.provider, args.model, args.temperature)
            except Exception as e:  # keep going; failed categories are recorded, not dropped
                record["error"] = repr(e)
            record["timestamp"] = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{cat['category_id']}: {'ERROR' if 'error' in record else 'ok'}")
    print(f"\nRaw responses saved to {run_dir / 'responses.jsonl'}")
    return 0


def cmd_score(args) -> int:
    run_dir = Path(args.run_dir)
    records = [json.loads(line) for line in open(run_dir / "responses.jsonl", encoding="utf-8")]
    alias_map = build_alias_map(load_aliases())
    brand_table = load_category_brands()
    problems = check_category_brands([r["category_id"] for r in records], brand_table, load_seed_brands(), alias_map)
    if problems:
        print("Brand table not ready for this run; run `check` first.")
        return 1

    rows = []
    for rec in records:
        cid = rec["category_id"]
        row = {"category_id": cid, "category_name": rec["category_name"]}
        if "error" in rec:
            row.update(result="error", recall="", recall_pre_additions="", n_predicted="", hits="", extra="", parsed="")
        else:
            predicted = parse_brand_list(rec["response"])
            table = [b["brand"] for b in brand_table[cid]]
            pre = [b["brand"] for b in brand_table[cid] if b["origin"] != "added_post_validation"]
            r = recall_at_k(table, predicted, k=10, alias_map=alias_map)
            r_pre = recall_at_k(pre, predicted, k=10, alias_map=alias_map)
            row.update(
                result="Pass" if passes(r["recall"]) else "Fail",
                recall=f"{r['recall']:.1f}",
                recall_pre_additions=f"{r_pre['recall']:.1f}",
                n_predicted=r["n_predicted"],
                hits="; ".join(r["hits"]),
                extra="; ".join(r["extra"]),
                parsed="; ".join(predicted),
            )
        rows.append(row)

    with open(run_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    scored = [r for r in rows if r["result"] != "error"]
    summary = {
        "run_id": run_dir.name,
        "n_categories": len(rows),
        "n_scored": len(scored),
        "n_errors": len(rows) - len(scored),
        "n_pass": sum(r["result"] == "Pass" for r in rows),
        "pass_threshold": PASS_THRESHOLD,
        "mean_recall": round(sum(float(r["recall"]) for r in scored) / len(scored), 4) if scored else None,
        "failed_categories": [r["category_id"] for r in rows if r["result"] == "Fail"],
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    # Record attempts (idempotent per category + run_id, so re-scoring does not duplicate).
    attempts = load_attempts()
    done = {(a["category_id"], a["run_id"]) for a in attempts}
    new = []
    for r in scored:
        if (r["category_id"], run_dir.name) in done:
            continue
        n_prev = sum(a["category_id"] == r["category_id"] for a in attempts)
        new.append({
            "category_id": r["category_id"], "attempt": n_prev + 1, "category_name": r["category_name"],
            "run_id": run_dir.name, "recall": r["recall"], "recall_pre_additions": r["recall_pre_additions"],
            "result": r["result"],
        })
    if new:
        append_attempts(new)

    for r in rows:
        print(f"{r['result']:5}  {r['recall']:>4}  {r['category_name']}")
    print(f"\n{summary['n_pass']}/{summary['n_scored']} passed (threshold {PASS_THRESHOLD}). "
          f"{len(new)} new attempt rows recorded.")
    return 0


def cmd_master(args) -> int:
    latest: dict[str, dict] = {}
    for a in load_attempts():  # file order = chronological
        latest[a["category_id"]] = a
    brand_table = load_category_brands()
    OUTPUTS_DIR.mkdir(exist_ok=True)

    rows = []
    for cid, a in latest.items():
        if a["result"] != "Pass":
            continue
        for b in brand_table[cid]:
            rows.append({"Category": a["category_name"], "Brand": b["brand"],
                         "World/China": b["world_china"], "Category验证结果": "Pass"})
    with open(OUTPUTS_DIR / "master_table.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["Category", "Brand", "World/China", "Category验证结果"])
        w.writeheader()
        w.writerows(rows)

    status = [{"category_id": cid, "final_name": a["category_name"], "attempts": a["attempt"],
               "final_recall": a["recall"], "result": a["result"]} for cid, a in latest.items()]
    with open(OUTPUTS_DIR / "category_status.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(status[0].keys()) if status else ["category_id"])
        w.writeheader()
        w.writerows(status)

    n_pass = sum(a["result"] == "Pass" for a in latest.values())
    print(f"{n_pass}/{len(latest)} validated categories pass; {len(rows)} brand rows -> {OUTPUTS_DIR / 'master_table.csv'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="Task 1/2 acceptance checks (no API call)")

    e = sub.add_parser("export", help="write a manual ChatGPT sheet for a new run")
    e.add_argument("--run-id", help="defaults to a timestamp")
    e.add_argument("--only", nargs="*", help="subset of category_ids")

    i = sub.add_parser("import", help="parse a filled manual sheet into responses.jsonl")
    i.add_argument("run_dir")

    q = sub.add_parser("query", help="(API mode) query the LLM once per category")
    q.add_argument("--provider", required=True)
    q.add_argument("--model", required=True)
    q.add_argument("--temperature", type=float, default=0.0)
    q.add_argument("--run-id", help="defaults to a timestamp")
    q.add_argument("--only", nargs="*", help="subset of category_ids")

    s = sub.add_parser("score", help="compute Recall@10 for a saved run")
    s.add_argument("run_dir")

    sub.add_parser("master", help="build outputs/master_table.csv from latest attempts")

    args = p.parse_args()
    handlers = {"check": cmd_check, "export": cmd_export, "import": cmd_import,
                "query": cmd_query, "score": cmd_score, "master": cmd_master}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
