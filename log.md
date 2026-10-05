# Log

#### 2026-10-05 17:05 HKT — Create pilot project skeleton

**Context**: Empty directory. Task: minimal Python project for a 20-category LLM brand Recall@10 pilot. No paid API calls, no fabricated results.

**Actions**:
- Created `data/categories.csv` (20 rows), `data/reference_brands.json` (20 entries, empty brands), `data/brand_aliases.json` (`{}`).
- Implemented `src/observatory/` normalize / metrics / parse / data / llm (stub), `scripts/validate.py` (check/query/score), `tests/test_core.py`.
- Commands: `python3 -m unittest discover -s tests -v`; `python3 scripts/validate.py check`; `python3 scripts/validate.py query --provider openai --model x`.

**Results**: 10/10 tests pass. `check` lists 40 problems (0 brands + empty source × 20). `query` refuses: "Provider 'openai' is not implemented yet". No run directory created.

**Decisions / Assumptions**:
- Stdlib only, no deps. Tests use synthetic names, not real reference data.
- Assumption A1/A2 (Recall denominator; dedupe before truncation) — validate with user.
- Reference brands intentionally left empty to avoid model-generated ground truth (circularity).
- Not a git repo yet; not initialized (not requested).

**Next**: Get reference brands + provider config from user; implement `query_llm`; smoke test.
