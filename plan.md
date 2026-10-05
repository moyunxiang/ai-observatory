# Plan

## Goal
Deliver to Jia Liu: sample results (~60 categories through Task 1→2→3, incl. rename cases) + a clear
description of how they were derived, as `outputs/master_table.csv` + `docs/methodology_report_{zh,en}.md`.

## Non-Goals
≥1000 categories; API automation (until key available); multiple AI models; B2B categories.

## Milestones
### Phase 1 — Code (DONE 2026-10-05)
Task-spec metric/prompt, manual sheet export/import, master table, per-category aliases. Tests pass.
### Phase 2 — Task 1 (DONE 2026-10-05)
189 seeds → 66 categories; unclassified = 0.
### Phase 3 — Task 2 (DONE 2026-10-05)
838 brand rows, ≥10 per category, evidence-linked.
### Phase 4 — Task 3 round 1 (WAITING ON USER)
User runs `runs/r1/manual_sheet.txt` in ChatGPT → import → score.
### Phase 5 — Rename loop
Per failed category: inspect `extra`/hits; (a) alias gap → add alias, re-score r1 (log it); (b) real brand missing from
table → add only with independent source, origin=added_post_validation, report both recalls; (c) AI misread the
category → rename in `categories.csv`, export r2 `--only <ids>`. Repeat ≤3 rounds; document unresolved ones.
### Phase 6 — Deliverables
`master`; methodology report (zh/en, first-order stats with column definitions); short note on scaling to 1000.

## Acceptance Criteria
- `check` passes; every brand row has source_url.
- Every Pass/Fail traceable: raw answer → parsed list → hits/extra → recall.
- Master table contains only Pass categories, no synonym duplicates.
- Report numbers come from `summary.json` / `category_attempts.csv`; anything not computed says `not computed`.

## Risks
- Manual copy-paste errors → `import` refuses empty answers, warns <5 parsed.
- Brand table tuned to GPT answers (overfitting) → post-validation additions flagged + dual recall reported.
- Region ambiguity (US vs China vs global) in categories like Health Insurance, ISPs, Real Estate Developers → expected failures; handled by renaming (e.g. add region) and documented.
- websearch-method evidence weaker → spot-check.

## Rollback
Git history per phase (1e004de skeleton, 303f31d code, 29daba6 Task 1, 1f4854e Task 2). `runs/` append-only; attempts are rows, never rewritten.

## Deliverables
`outputs/master_table.csv`, `outputs/category_status.csv`, `docs/methodology_report_zh.md`, `docs/methodology_report_en.md`.
