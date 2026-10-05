# Plan

## Goal
Run a reproducible 20-category Recall@10 validation pilot with saved raw LLM output.

## Non-Goals
Scaling to 1,000 categories; multiple models; fancy fuzzy matching; dashboards.

## Milestones
### Phase 0 — Skeleton (done 2026-10-05)
Structure, inputs, normalization, Recall@10, parser, CLI, tests, README.
### Phase 1 — Inputs + provider (blocked on user)
Fill reference brands + source; implement `query_llm` for chosen provider; `check` exits 0.
### Phase 2 — First real run
Smoke test on 1–2 categories, inspect parsing; then full run; `score` → results.csv / summary.json.
### Phase 3 — Failure analysis
For failed categories: check misses (alias? ambiguity? naming?), refine names/aliases, rerun as a new run_id.

## Acceptance Criteria
- Unit tests pass; `check` exits 0 before any query.
- Each run dir has meta.json + responses.jsonl (raw) + results.csv + summary.json.
- Every pass/fail traceable to raw response + parsed list + hits/misses.

## Risks
- Parser mis-reads unusual LLM formats → inspect `parsed` column on smoke test.
- Alias gaps produce false misses → review `missed`/`extra` before concluding category is ambiguous.
- Reference set built with the same LLM → circular validation.
- Nondeterminism → record temperature; consider repeated samples.

## Rollback
All changes are new files; runs are append-only in `runs/`. Revert code via git once initialized.

## Deliverables
Code + `runs/<run_id>/` artifacts + short report (zh/en) after Phase 2.
