"""Fetch Wikipedia summaries for post-validation brand candidates (independent evidence).

Reads  data/raw/task2/post_validation_candidates.csv  (category_id, brand, world_china, wiki_query, found_in_run)
Writes data/raw/task2/wiki_verification.jsonl         (one line per candidate: page title, url, extract, or error)

Pairs already fetched successfully with the same wiki_query are skipped, so re-running retries
failures and re-fetches pairs whose query was corrected (earlier lines stay as raw history; the
last line per pair wins). On a 404 the Wikipedia search API is used to find the page title.
Acceptance (does the extract show the brand clearly belongs to the category?) is a manual
judgment recorded in data/raw/task2/post_validation_decisions.csv.

    python scripts/verify_candidates.py
"""

import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "task2"
API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
SEARCH = "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=1&srsearch="
HEADERS = {"User-Agent": "ai-observatory-pilot/0.1 (research; contact via repo owner)"}


def fetch(title: str) -> dict:
    url = API + urllib.parse.quote(title.replace(" ", "_"), safe="")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
                d = json.loads(r.read())
            return {"title": d.get("title"), "url": d.get("content_urls", {}).get("desktop", {}).get("page"),
                    "type": d.get("type"), "extract": d.get("extract")}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"error": "404 not found"}
            err = f"HTTP {e.code}"
            if e.code == 429:
                time.sleep(20 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError) as e:
            err = repr(e)
        time.sleep(2 ** attempt)
    return {"error": err}


def search_title(query: str) -> str | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(SEARCH + urllib.parse.quote(query), headers=HEADERS), timeout=30) as r:
            hits = json.loads(r.read())["query"]["search"]
        return hits[0]["title"] if hits else None
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError):
        return None


def fetch_with_fallback(query: str) -> dict:
    rec = fetch(query)
    if rec.get("error") == "404 not found":
        title = search_title(query)
        if title:
            rec = {**fetch(title), "via_search": True}
    return rec


def main() -> None:
    out = RAW / "wiki_verification.jsonl"
    done = set()
    if out.exists():
        # skip pairs already fetched successfully with the same query (changing wiki_query forces a re-fetch)
        done = {(j["category_id"], j["brand"], j["wiki_query"]) for j in map(json.loads, open(out, encoding="utf-8")) if "error" not in j}
    with open(RAW / "post_validation_candidates.csv", newline="", encoding="utf-8") as f:
        cands = list(csv.DictReader(f))
    with open(out, "a", encoding="utf-8") as f:
        for c in cands:
            if (c["category_id"], c["brand"], c["wiki_query"]) in done:
                continue
            rec = {"category_id": c["category_id"], "brand": c["brand"], "wiki_query": c["wiki_query"], **fetch_with_fallback(c["wiki_query"])}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{c['category_id']}/{c['brand']}: {rec.get('title') or rec.get('error')}")
            time.sleep(1.0)


if __name__ == "__main__":
    main()
