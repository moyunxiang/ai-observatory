"""First-order statistics for the methodology report (all numbers in docs/ come from here).

    python scripts/report_stats.py > outputs/report_stats.json

Per run it re-scores the saved raw answers with the *current* brand table and aliases, so
"with additions" and "pre additions" (excluding origin=added_post_validation) are comparable.
"""

import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from observatory.data import DATA_DIR, alias_maps, load_categories, load_category_brands, load_seed_brands, read_csv  # noqa: E402
from observatory.metrics import passes, recall_at_k  # noqa: E402
from observatory.parse import parse_brand_list  # noqa: E402

RUNS = ROOT / "runs"


def run_stats(run_id: str, table: dict, amaps: dict) -> dict:
    recs = [json.loads(line) for line in open(RUNS / run_id / "responses.jsonl", encoding="utf-8")]
    meta = json.loads((RUNS / run_id / "meta.json").read_text())
    per_cat, full, pre = {}, [], []
    for r in recs:
        if "error" in r:
            continue
        cid = r["category_id"]
        pred = parse_brand_list(r["response"])
        rf = recall_at_k([b["brand"] for b in table[cid]], pred, alias_map=amaps[cid])["recall"]
        rp = recall_at_k([b["brand"] for b in table[cid] if b["origin"] != "added_post_validation"], pred, alias_map=amaps[cid])["recall"]
        per_cat[cid] = {"category_name": r["category_name"], "recall": rf, "recall_pre_additions": rp,
                        "n_parsed": len(pred)}
        full.append(rf)
        pre.append(rp)

    def summ(xs):
        return {"n": len(xs), "n_pass": sum(passes(x) for x in xs), "pass_rate": round(sum(passes(x) for x in xs) / len(xs), 4),
                "mean": round(statistics.mean(xs), 4), "median": statistics.median(xs),
                "std": round(statistics.pstdev(xs), 4), "min": min(xs), "max": max(xs)}

    cost = sum((r.get("response_meta") or {}).get("usage", {}).get("cost", 0) for r in recs)
    return {"run_id": run_id, "model": meta.get("model"), "temperature": meta.get("temperature"),
            "n_requests": len(recs), "n_errors": sum("error" in r for r in recs), "cost_usd": round(cost, 4),
            "with_additions": summ(full), "pre_additions": summ(pre), "per_category": per_cat}


def main() -> None:
    cats = load_categories()
    b2c = [c["category_id"] for c in cats if c["scope"] == "B2C"]
    seeds = load_seed_brands()
    table = load_category_brands()
    amaps = alias_maps(b2c)
    rows = [b for cid in b2c for b in table[cid]]
    sizes = [len(table[cid]) for cid in b2c]
    decisions = read_csv(DATA_DIR / "raw" / "task2" / "post_validation_decisions.csv")
    out = {
        "task1": {"n_seed_brands": len(seeds), "seed_world_china": dict(Counter(s["world_china"] for s in seeds)),
                  "n_categories": len(cats), "n_b2c": len(b2c), "n_out_of_scope": len(cats) - len(b2c),
                  "n_merges": len(read_csv(DATA_DIR / "category_merges.csv")),
                  "n_unclassified": sum(s["primary_category_id"] not in {c["category_id"] for c in cats} for s in seeds)},
        "task2": {"n_rows": len(rows), "origin": dict(Counter(b["origin"] for b in rows)),
                  "source_method": dict(Counter(b["source_method"].split(":")[0] for b in rows)),
                  "world_china": dict(Counter(b["world_china"] for b in rows)),
                  "brands_per_category": {"min": min(sizes), "median": statistics.median(sizes), "max": max(sizes)},
                  "post_validation_candidates": len(decisions),
                  "post_validation_accepted": sum(d["decision"] == "accept" for d in decisions)},
        "aliases": {"global_canonical": len(json.load(open(DATA_DIR / "brand_aliases.json"))),
                    "category_specific": sum(len(v) for v in json.load(open(DATA_DIR / "category_aliases.json")).values())},
        "attempts": read_csv(DATA_DIR / "category_attempts.csv"),
        "runs": {rid: run_stats(rid, table, amaps) for rid in sys.argv[1:] or ["r1_ds", "r2_ds"]},
    }
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
