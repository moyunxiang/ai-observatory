"""Print the per-category markdown table used in docs/methodology_report_*.md,
and write the same numbers to outputs/category_results.csv.

    python scripts/report_stats.py r1_ds r2_ds r3_ds_holdout r4_qwen_crossmodel > outputs/report_stats.json
    python scripts/report_tables.py > outputs/report_table.md
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROSS = "r4_qwen_crossmodel"


def main() -> None:
    stats = json.load(open(ROOT / "outputs" / "report_stats.json", encoding="utf-8"))
    runs = stats["runs"]
    sizes, posts, china = {}, {}, {}
    for r in csv.DictReader(open(ROOT / "data" / "category_brands.csv", encoding="utf-8")):
        sizes[r["category_id"]] = sizes.get(r["category_id"], 0) + 1
        china[r["category_id"]] = china.get(r["category_id"], 0) + (r["world_china"] == "China")
        posts[r["category_id"]] = posts.get(r["category_id"], 0) + (r["origin"] == "added_post_validation")
    status = {r["category_id"]: r for r in csv.DictReader(open(ROOT / "outputs" / "category_status.csv", encoding="utf-8-sig"))}
    r1, r2, r3 = runs["r1_ds"]["per_category"], runs["r2_ds"]["per_category"], runs["r3_ds_holdout"]["per_category"]
    r4 = runs.get(CROSS, {}).get("per_category", {})

    def f(x):
        return f"{x:.1f}" if x is not None else "–"

    def get(run, cid, key):
        return run[cid][key] if cid in run else None

    rows = []
    for cid in r1:
        rows.append({
            "category_id": cid, "r1_name": r1[cid]["category_name"], "final_name": status[cid]["final_name"],
            "n_brands": sizes[cid], "n_world": sizes[cid] - china[cid], "n_china": china[cid],
            "n_added_post_validation": posts[cid],
            "r1_pre": get(r1, cid, "recall_pre_additions"), "r1_with": get(r1, cid, "recall"),
            "r2_pre": get(r2, cid, "recall_pre_additions"), "r2_with": get(r2, cid, "recall"),
            "final_result": status[cid]["result"],
            "holdout_pre": get(r3, cid, "recall_pre_additions"), "holdout_with": get(r3, cid, "recall"),
            "qwen_pre": get(r4, cid, "recall_pre_additions"), "qwen_with": get(r4, cid, "recall"),
        })

    with open(ROOT / "outputs" / "category_results.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows({k: ("" if v is None else v) for k, v in row.items()} for row in rows)

    # Compact appendix table for the short report (docs/report_*.md).
    with open(ROOT / "outputs" / "report_appendix.md", "w", encoding="utf-8") as fh:
        fh.write("| # | Category | Brands (W/C) | DeepSeek r1 pre → with | Final | Hold-out | Qwen |\n")
        fh.write("|-|------------|-----|----------|---|---|---|\n")  # dash counts set relative column widths
        for i, r in enumerate(rows, 1):
            r1s = f"{f(r['r1_pre'])} → {f(r['r1_with'])}"
            if r["r2_with"] is not None:
                r1s += f" (renamed: {f(r['r2_pre'])} → {f(r['r2_with'])})"
            fh.write(f"| {i} | {r['final_name']} | {r['n_brands']} ({r['n_world']}/{r['n_china']}) | {r1s} | "
                     f"{r['final_result']} | {f(r['holdout_with'])} | {f(r['qwen_with'])} |\n")

    print("| # | category_id | r1 name | final name | brands (added) | r1 pre | r1 with | r2 pre | r2 with | final | holdout pre | holdout with | qwen pre | qwen with |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        print(f"| {i} | {r['category_id']} | {r['r1_name']} | {r['final_name']} | {r['n_brands']} ({r['n_added_post_validation']}) | "
              f"{f(r['r1_pre'])} | {f(r['r1_with'])} | {f(r['r2_pre'])} | {f(r['r2_with'])} | {r['final_result']} | "
              f"{f(r['holdout_pre'])} | {f(r['holdout_with'])} | {f(r['qwen_pre'])} | {f(r['qwen_with'])} |")


if __name__ == "__main__":
    main()
