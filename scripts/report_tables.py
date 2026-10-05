"""Print the per-category markdown table used in docs/methodology_report_*.md.

    python scripts/report_stats.py r1_ds r2_ds r3_ds_holdout > outputs/report_stats.json
    python scripts/report_tables.py > outputs/report_table.md
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    stats = json.load(open(ROOT / "outputs" / "report_stats.json", encoding="utf-8"))
    runs = stats["runs"]
    sizes, posts = {}, {}
    for r in csv.DictReader(open(ROOT / "data" / "category_brands.csv", encoding="utf-8")):
        sizes[r["category_id"]] = sizes.get(r["category_id"], 0) + 1
        posts[r["category_id"]] = posts.get(r["category_id"], 0) + (r["origin"] == "added_post_validation")
    status = {r["category_id"]: r for r in csv.DictReader(open(ROOT / "outputs" / "category_status.csv", encoding="utf-8-sig"))}
    r1, r2, r3 = runs["r1_ds"]["per_category"], runs["r2_ds"]["per_category"], runs["r3_ds_holdout"]["per_category"]

    def f(x):
        return f"{x:.1f}"

    print("| # | category_id | r1 name | final name | brands (added) | r1 pre | r1 with | r2 pre | r2 with | final | holdout pre | holdout with |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, cid in enumerate(r1, 1):
        a, b, h = r1[cid], r2.get(cid), r3[cid]
        print(f"| {i} | {cid} | {a['category_name']} | {status[cid]['final_name']} | {sizes[cid]} ({posts[cid]}) | "
              f"{f(a['recall_pre_additions'])} | {f(a['recall'])} | "
              f"{f(b['recall_pre_additions']) if b else '–'} | {f(b['recall']) if b else '–'} | "
              f"{status[cid]['result']} | {f(h['recall_pre_additions'])} | {f(h['recall'])} |")


if __name__ == "__main__":
    main()
