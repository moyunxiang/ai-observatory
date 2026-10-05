# Project State

> Last updated: 2026-10-05 17:05 HKT
> Source of truth for new Claude sessions.

## 1. Current Goal
Pilot (20 categories): query an LLM per category for 10 representative brands, compute Recall@10
against a reference set, pass if ≥ 0.8. Long-term: scale to 1,000+ categories (NOT now).

## 2. Current Status
- Project skeleton done; unit tests pass (10/10).
- `data/reference_brands.json` has all 20 categories but **empty brand lists**.
- LLM provider **not implemented** (`SUPPORTED_PROVIDERS` empty in `src/observatory/llm.py`).
- **No validation run has been executed. No results exist.**

## 3. Active Tasks
### P0
- [ ] Get reference brands (10/category) + their source from user
- [ ] Get provider / model / temperature / API key setup from user; implement `query_llm`
### P1
- [ ] Smoke test: `query --only <1-2 categories>` then `score`
- [ ] Full 20-category run
### P2
- [ ] Inspect failed categories, rename/refine, rerun

## 4. Valid Findings / Confirmed Facts
- F0: `check` / `query` guard / unit tests verified locally (Python 3.14.6).

## 5. Open Questions
- Q1: Who provides reference brands, and what is the source (manual curation / market data / other)?
- Q2: Provider + model + temperature? Single sample or N samples per category?
- Q3: Keep prompt verbatim (free text, parsed) or append an output-format instruction (e.g. one per line)?
- Q4: Region scope (global vs. US vs. China) — strongly affects Coffee Chains, Food Delivery, Ride-Hailing.

## 6. Key Files
- `data/categories.csv`, `data/reference_brands.json`, `data/brand_aliases.json`: inputs
- `src/observatory/{normalize,metrics,parse,data,llm}.py`: core logic
- `scripts/validate.py`: CLI (check / query / score)

## 7. How to Run / Verify
```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py check
```

## 8. Data / Artifact Locations
- `runs/<run_id>/responses.jsonl`: raw LLM output (raw data — never delete/overwrite)

## 9. Deprecated Paths / Do Not Revert
- (none yet)

## 10. Current Assumptions
- A1: Recall@10 denominator = number of unique normalized reference brands (=10).
- A2: LLM list is normalized + deduped before truncation to top 10.
- Validation: confirm with user.

## 11. Handoff Notes
Do not fabricate reference brands or results. Do not call paid APIs without user confirmation.
