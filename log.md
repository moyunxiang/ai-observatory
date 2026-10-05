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

#### 2026-10-05 17:45 HKT — Re-scope to JIA_LIU_TASK.md; Phase 1 code + Task 1 seed pool

**Context**: User provided full spec `JIA_LIU_TASK.md`. Plan approved (~50 categories sample; validation AI = user's ChatGPT, manual copy-paste until API available). Differences vs. pilot: start from brands (Task 1); brand table >=10 (Task 2); Recall@10 denominator = AI's 10; fixed prompt "What are the best brands for {category}? List 10 brands."

**Actions**:
- `git init`; commit 1e004de (old skeleton). Identity checked: moyunxiang <2556377578@qq.com>.
- Code (commit 303f31d): new Recall@10 definition in `metrics.py`; new `PROMPT_TEMPLATE`; `data.py` for CSV tables; `manual.py` (sheet export/parse); `validate.py` subcommands export/import/score/master; tests 13/13 OK. Removed empty `data/reference_brands.json` (0 brands, template only).
- Downloaded seed sources (raw, kept under `data/raw/sources/` + SHA256SUMS):
  - `curl -sSL -o ... https://indd.adobe.com/view/publication/453609a6-.../Kantar_BrandZ_2025_Most_Valuable_Chinese_Brands_EN.pdf`
  - `curl -sSL -A "Mozilla/5.0" -o ... https://www.mediar.cz/wp-content/uploads/2025/05/kantar-brandz-2025.pdf` (Global Top 100 ranking table, 2 pages)
  - `pdftotext -layout` for both. mediaguru.cz URL returned HTML, discarded (not a source).
- Wrote `data/seed_brands.csv` (Global 100 + China 100, 11 overlaps -> 189 unique; World 88 / China 101), each with raw_label + primary_category_id + Kantar's own category. Wrote `data/categories.csv` (66: 60 B2C + 6 out_of_scope) and `data/category_merges.csv` (30 raw_label -> category merges).
- Added `scope` column; check/export/query only use B2C categories.

**Results**: `check`: 0 seed problems (unclassified = 0); 223 Task 2 problems (brand tables not built yet). Tests OK.

**Decisions / Assumptions**:
- Used Kantar 2025 editions (not 2026) because full tables were downloadable for both lists. 
- B2C-only scope for Task 2/3; B2B brands (Microsoft, SAP, NVIDIA, Aramco, ...) still classified (into out_of_scope categories) so unclassified=0 holds. Assumption: project targets consumer categories — confirm with Jia Liu.
- Ambiguous primary categories (Assumption, verify by review): Tencent -> Video Game Companies; TCL -> TVs; Sony -> Consumer Electronics; LinkedIn merged into Social Media; Microsoft out_of_scope.

**Next**: Task 2 — build `data/category_brands.csv` (>=10 brands/category with source URL) via web search.
