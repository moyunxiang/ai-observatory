# Project State

> Last updated: 2026-10-05 19:35 HKT
> Source of truth for new Claude sessions.

## 1. Current Goal
Sample stage of Jia Liu's task (`JIA_LIU_TASK.md`): run Task 1 → 2 → 3 on ~60 categories, produce sample
results + a methodology write-up (how results were derived). Full target (≥1000 validated categories) is NOT in scope now.

## 2. Current Status
- Task 1 DONE: 189 seed brands (Kantar BrandZ 2025 Global + China Top 100), 66 categories (60 B2C + 6 out_of_scope), unclassified = 0.
- Task 2 DONE: `data/category_brands.csv` 838 rows, 10–29 brands per B2C category, all with source URL. `check` passes.
- Task 3 PENDING: `runs/r1/manual_sheet.txt` exported (60 prompts). Waiting for user to run it in ChatGPT and paste answers.
- **No Task 3 results exist yet.** Nothing in `runs/` is scored.

## 3. Active Tasks
### P0
- [ ] User fills `runs/r1/manual_sheet.txt` (new Temporary Chat per category) → `import` → `score`
### P1
- [ ] Analyse failures: alias gap (fix alias, re-score same run) vs naming problem (rename, new run with `--only`)
- [ ] Rename round(s) r2, r3 … until pass or documented give-up
- [ ] `master` → `outputs/master_table.csv`; methodology report zh/en in `docs/`
### P2
- [ ] User spot-check of brand table (esp. websearch-method rows)
- [ ] API mode once prof provides a key (implement `query_llm`)

## 4. Valid Findings / Confirmed Facts
- F0: Metric = |AI top10 ∩ brand table| / 10 (denominator fixed 10), pass ≥ 0.8. Old "denominator = reference set" definition is deprecated.
- F1: Fixed prompt = `What are the best brands for {category}? List 10 brands.`
- F2: Pipeline verified end-to-end with SYNTHETIC answers in scratchpad (not real results).

## 5. Open Questions
- Q1: Is B2C-only scope OK for Jia Liu (B2B seeds like Microsoft/SAP classified but not validated)?
- Q2: World/China rule (HK/Macau = China, Taiwan = World) acceptable?
- Q3: Which ChatGPT model/settings the user used (recorded in sheet header).

## 6. Key Files
- `data/seed_brands.csv`, `data/categories.csv`, `data/category_merges.csv` (Task 1)
- `scripts/build_category_brands.py` (curated SELECTION) → `data/category_brands.csv` (Task 2)
- `data/brand_aliases.json`, `data/category_aliases.json` (matching)
- `scripts/validate.py` (check/export/import/score/master), `src/observatory/*`

## 7. How to Run / Verify
```bash
python3 -m unittest discover -s tests
python3 scripts/build_category_brands.py && python3 scripts/validate.py check
python3 scripts/validate.py import runs/r1 && python3 scripts/validate.py score runs/r1
```

## 8. Data / Artifact Locations
- `data/raw/sources/`: Kantar PDFs + txt + SHA256SUMS (raw; never edit)
- `data/raw/task2/evidence.jsonl`: Task 2 web evidence (append-only)
- `runs/<id>/manual_sheet.txt`, `responses.jsonl`: raw AI answers (never overwrite; `import` refuses)

## 9. Deprecated Paths / Do Not Revert
- 20 hand-picked pilot categories + exactly-10 reference set + recall denominator = reference size: replaced by task-spec procedure.
- `data/reference_brands.json`: removed (was an empty template).
- Old prompt "best-known and most representative brands … exactly 10": replaced by task's fixed prompt.

## 10. Current Assumptions
- A1: B2C-only Task 2/3 scope. Validation: confirm with Jia Liu.
- A2: Ambiguous primaries (Tencent→Video Game Companies, TCL→TVs, Sony→Consumer Electronics, LinkedIn→Social Media). Validation: review.
- A3: websearch-method evidence is acceptable for sample stage. Validation: user spot-check.

## 11. Handoff Notes
Do not fabricate GPT answers or results. Re-scoring after alias edits is allowed (same raw answers); log every alias added after seeing answers, and report `recall_pre_additions` if brands are added to tables post-validation (origin=added_post_validation).
