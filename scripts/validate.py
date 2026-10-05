"""Pilot validation CLI.

    python scripts/validate.py check                      # inputs + prompts, no API call
    python scripts/validate.py query --provider X --model Y   # raw answers -> runs/<run_id>/responses.jsonl
    python scripts/validate.py score runs/<run_id>        # Recall@10 -> results.csv, summary.json

query and score are separate so raw LLM output is always saved first and can be
re-scored (e.g. after alias fixes) without new API calls.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from observatory.data import check_reference, load_aliases, load_categories, load_reference_brands  # noqa: E402
from observatory.llm import PROMPT_TEMPLATE, SUPPORTED_PROVIDERS, build_prompt, query_llm  # noqa: E402
from observatory.metrics import PASS_THRESHOLD, passes, recall_at_k  # noqa: E402
from observatory.normalize import build_alias_map  # noqa: E402
from observatory.parse import parse_brand_list  # noqa: E402

RUNS_DIR = ROOT / "runs"


def cmd_check(args) -> int:
    categories = load_categories()
    reference = load_reference_brands()
    alias_map = build_alias_map(load_aliases())
    print(f"{len(categories)} categories loaded.\n")
    for cat in categories:
        print(f"[{cat['category_id']}] {build_prompt(cat['category_name'])}")
    problems = check_reference(categories, reference, alias_map)
    print()
    if problems:
        print(f"Reference set NOT ready ({len(problems)} problems):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("Reference set OK.")
    return 0


def cmd_query(args) -> int:
    if args.provider not in SUPPORTED_PROVIDERS:
        print(f"Provider '{args.provider}' is not implemented yet (supported: {sorted(SUPPORTED_PROVIDERS) or 'none'}).")
        return 1
    categories = load_categories()
    if args.only:
        categories = [c for c in categories if c["category_id"] in set(args.only)]
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)  # never overwrite an existing run

    meta = {
        "run_id": run_id,
        "provider": args.provider,
        "model": args.model,
        "temperature": args.temperature,
        "prompt_template": PROMPT_TEMPLATE,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

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
    reference = load_reference_brands()
    alias_map = build_alias_map(load_aliases())
    problems = check_reference(load_categories(), reference, alias_map)
    if problems:
        print("Reference set not ready; run `check` first.")
        return 1

    rows = []
    with open(run_dir / "responses.jsonl", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            cid = rec["category_id"]
            row = {"category_id": cid, "category_name": rec["category_name"]}
            if "error" in rec:
                row.update(status="error", recall="", n_predicted="", hits="", missed="", extra="", parsed="")
            else:
                predicted = parse_brand_list(rec["response"])
                r = recall_at_k(reference[cid]["brands"], predicted, k=10, alias_map=alias_map)
                row.update(
                    status="pass" if passes(r["recall"]) else "fail",
                    recall=f"{r['recall']:.2f}",
                    n_predicted=r["n_predicted"],
                    hits="; ".join(r["hits"]),
                    missed="; ".join(r["missed"]),
                    extra="; ".join(r["extra"]),
                    parsed="; ".join(predicted),
                )
            rows.append(row)

    with open(run_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    scored = [r for r in rows if r["status"] != "error"]
    summary = {
        "n_categories": len(rows),
        "n_scored": len(scored),
        "n_errors": len(rows) - len(scored),
        "n_pass": sum(r["status"] == "pass" for r in rows),
        "pass_threshold": PASS_THRESHOLD,
        "mean_recall": (sum(float(r["recall"]) for r in scored) / len(scored)) if scored else None,
        "failed_categories": [r["category_id"] for r in rows if r["status"] == "fail"],
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for r in rows:
        print(f"{r['status']:5}  {r['recall']:>4}  {r['category_name']}")
    print(f"\n{summary['n_pass']}/{summary['n_scored']} passed (threshold {PASS_THRESHOLD}).")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="validate inputs and print prompts (no API call)")

    q = sub.add_parser("query", help="query the LLM once per category and save raw answers")
    q.add_argument("--provider", required=True)
    q.add_argument("--model", required=True)
    q.add_argument("--temperature", type=float, default=0.0)
    q.add_argument("--run-id", help="defaults to a timestamp")
    q.add_argument("--only", nargs="*", help="subset of category_ids (for smoke tests)")

    s = sub.add_parser("score", help="compute Recall@10 for a saved run")
    s.add_argument("run_dir")

    args = p.parse_args()
    return {"check": cmd_check, "query": cmd_query, "score": cmd_score}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
