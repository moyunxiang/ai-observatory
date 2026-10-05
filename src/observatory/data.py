"""Load and sanity-check the input tables in data/.

    seed_brands.csv       Task 1: brand, world_china, primary_category_id, source_list, notes
    categories.csv        Task 1: category_id, category_name (current name under test), scope (B2C/out_of_scope)
    category_merges.csv   Task 1: raw_label, merged_into_category_id, reason
    category_brands.csv   Task 2: category_id, brand, world_china, origin, source_url
    category_attempts.csv Task 3: one row per (category, run) validation attempt
    brand_aliases.json    {canonical: [variants]}           (applies to every category)
    category_aliases.json {category_id: {canonical: [variants]}}  (only within that category)
"""

import csv
import json
from pathlib import Path

from .normalize import build_alias_map, normalize_brand

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MIN_BRANDS = 10
WORLD_CHINA = {"World", "China"}
ORIGINS = {"seed", "expanded", "added_post_validation"}
ATTEMPT_FIELDS = ["category_id", "attempt", "category_name", "run_id", "recall", "recall_pre_additions", "result"]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_categories(b2c_only: bool = False) -> list[dict]:
    """b2c_only=True returns only categories that go through Task 2/3."""
    cats = read_csv(DATA_DIR / "categories.csv")
    return [c for c in cats if c["scope"] == "B2C"] if b2c_only else cats


def load_seed_brands() -> list[dict]:
    return read_csv(DATA_DIR / "seed_brands.csv")


def load_category_brands() -> dict[str, list[dict]]:
    table: dict[str, list[dict]] = {}
    for row in read_csv(DATA_DIR / "category_brands.csv"):
        table.setdefault(row["category_id"], []).append(row)
    return table


def load_attempts() -> list[dict]:
    return read_csv(DATA_DIR / "category_attempts.csv")


def upsert_attempts(run_id: str, rows: list[dict]) -> None:
    """Replace this run's rows (re-scoring the same raw answers), keep all other runs."""
    path = DATA_DIR / "category_attempts.csv"
    kept = [a for a in load_attempts() if a["run_id"] != run_id]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ATTEMPT_FIELDS)
        w.writeheader()
        w.writerows(kept + rows)


def load_aliases() -> dict[str, list[str]]:
    with open(DATA_DIR / "brand_aliases.json", encoding="utf-8") as f:
        return json.load(f)


def load_category_aliases() -> dict[str, dict[str, list[str]]]:
    path = DATA_DIR / "category_aliases.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def alias_maps(category_ids: list[str]) -> dict[str, dict[str, str]]:
    """Per-category alias map = global aliases + that category's own aliases."""
    global_aliases = load_aliases()
    per_cat = load_category_aliases()
    global_map = build_alias_map(global_aliases)
    maps = {}
    for cid in category_ids:
        m = dict(global_map)
        m.update(build_alias_map(per_cat.get(cid, {})))  # category entries win on conflict
        maps[cid] = m
    return maps


def check_seeds(seeds: list[dict], categories: list[dict]) -> list[str]:
    """Task 1 acceptance: every seed brand maps to an existing category."""
    cat_ids = {c["category_id"] for c in categories}
    problems = []
    for s in seeds:
        if s["world_china"] not in WORLD_CHINA:
            problems.append(f"seed {s['brand']}: world_china={s['world_china']!r}")
        if s["primary_category_id"] not in cat_ids:
            problems.append(f"seed {s['brand']}: unclassified / unknown category {s['primary_category_id']!r}")
    return problems


def check_category_brands(
    category_ids: list[str],
    brand_table: dict[str, list[dict]],
    seeds: list[dict],
    alias_by_cat: dict[str, dict[str, str]],
) -> list[str]:
    """Task 2 acceptance: >= 10 unique brands per category, each with a source."""
    problems = []
    for cid in category_ids:
        alias_map = alias_by_cat.get(cid, {})
        rows = brand_table.get(cid, [])
        keys = {normalize_brand(r["brand"], alias_map) for r in rows}
        if len(keys) < MIN_BRANDS:
            problems.append(f"{cid}: {len(keys)} unique brands, need >= {MIN_BRANDS}")
        if len(keys) != len(rows):
            problems.append(f"{cid}: duplicate brands after normalization")
        for r in rows:
            if not r.get("source_url"):
                problems.append(f"{cid}/{r['brand']}: empty source_url")
            if r["world_china"] not in WORLD_CHINA:
                problems.append(f"{cid}/{r['brand']}: world_china={r['world_china']!r}")
            if r["origin"] not in ORIGINS:
                problems.append(f"{cid}/{r['brand']}: origin={r['origin']!r}")
    # Task 2 step 3: seed brands must be merged into their primary category's table.
    wanted = set(category_ids)
    for s in seeds:
        cid = s["primary_category_id"]
        if cid in wanted:
            alias_map = alias_by_cat.get(cid, {})
            keys = {normalize_brand(r["brand"], alias_map) for r in brand_table.get(cid, [])}
            if normalize_brand(s["brand"], alias_map) not in keys:
                problems.append(f"{cid}: seed brand {s['brand']} missing from category_brands.csv")
    return problems
