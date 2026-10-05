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

#### 2026-10-05 19:20 HKT — Task 2: category brand tables (60 B2C categories, 838 rows)

**Context**: Task 1 done (189 seeds, 60 B2C + 6 out_of_scope categories). Need >=10 real brands per category, merged with seeds, each traceable.

**Actions**:
- Web research per category (WebFetch of list pages, mainly Wikipedia / Brand Finance / FashionUnited; WebSearch where pages were blocked). Every consulted page logged in `data/raw/task2/evidence.jsonl` (113 entries; method = webfetch | websearch).
- Added per-category aliases (`data/category_aliases.json`) on top of global `data/brand_aliases.json`; merge = union per canonical (bug found: first version overrode global variants, PlayStation lost "Sony PlayStation"; fixed in `data.alias_maps`).
- Normalization: trailing "com" token stripped (Booking.com == Booking). Test added.
- `scripts/build_category_brands.py`: curated SELECTION -> `data/category_brands.csv` with auto-attached source_url/source_method/origin; fails if any brand lacks evidence.
- `score --no-record`, `OBSERVATORY_RUNS_DIR` env override for smoke tests.
- Smoke test in scratchpad (SYNTHETIC answers, not GPT output, not saved in repo): export -> import -> score on hot_pot + game_consoles -> both 0.8 as constructed (8/10 hits). Confirms parser + aliases + metric end-to-end.

**Results**: 838 rows; per-category 10–29 brands; source_method: websearch 441, webfetch 360, kantar_seed 31, cross_category 6. World 609 / China 229. `check`: "All Task 1/2 checks OK". Tests 14/14 OK.

**Decisions / Assumptions**:
- World/China rule: China = HQ in mainland China / Hong Kong / Macau; otherwise World (e.g. Taiwan-origin tea chains = World). Assumption — confirm with Jia Liu.
- Websearch-method rows rely on a search summary of the cited page (weaker than webfetch). Verification: spot-check sample by user; upgrade to webfetch if challenged.
- Several verification searches named candidate brands in the query (confirmation search). Documented as a limitation.
- Parent/brand aliasing kept minimal (exceptions: Aetna<->CVS Health, Claro/Telcel<->América Móvil, Movistar<->Telefónica).

**Next**: Export full manual sheet (run r1) for user to run in ChatGPT; then import/score; rename failed categories.
