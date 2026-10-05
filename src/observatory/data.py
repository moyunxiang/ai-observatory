"""Load and sanity-check the pilot input files in data/."""

import csv
import json
from pathlib import Path

from .normalize import normalize_brand

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REFERENCE_SIZE = 10


def load_categories(path: Path = DATA_DIR / "categories.csv") -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_reference_brands(path: Path = DATA_DIR / "reference_brands.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_aliases(path: Path = DATA_DIR / "brand_aliases.json") -> dict[str, list[str]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_reference(categories: list[dict], reference: dict, alias_map: dict) -> list[str]:
    """Return a list of human-readable problems; empty list means ready to run."""
    problems = []
    for cat in categories:
        cid = cat["category_id"]
        entry = reference.get(cid)
        if entry is None:
            problems.append(f"{cid}: missing from reference_brands.json")
            continue
        brands = entry.get("brands", [])
        keys = {normalize_brand(b, alias_map) for b in brands}
        if len(brands) != REFERENCE_SIZE:
            problems.append(f"{cid}: has {len(brands)} brands, expected {REFERENCE_SIZE}")
        elif len(keys) != len(brands):
            problems.append(f"{cid}: duplicate brands after normalization")
        if not entry.get("source"):
            problems.append(f"{cid}: 'source' is empty")
    return problems
