# AI Observatory — Category Validation Pilot

Pilot (20 categories) for a longer-term goal: 1,000+ consumer product/service
categories, each with representative brands, validated for whether an LLM
understands each category consistently.

## Experiment

1. Input: 20 categories in `data/categories.csv`.
2. Each category has a **reference set of 10 brands** in `data/reference_brands.json`.
3. For each category, the LLM is queried **independently** (one single-turn request, no shared history):
   > What are the best-known and most representative brands for {category}? List exactly 10 brands.
4. Brand names from both sides are normalized, then **Recall@10** is computed:
   `Recall@10 = |reference ∩ top-10(LLM, normalized + deduplicated)| / |reference|`
5. A category **passes** if Recall@10 ≥ 0.8 (i.e. ≥ 8 of 10 reference brands recovered).
6. Failed categories are inspected later (ambiguous / poorly named?), renamed or refined, and re-validated.

## Layout

```
data/
  categories.csv          # category_id, category_name (20 rows)
  reference_brands.json   # {category_id: {category_name, brands[10], source, notes}}  <- to be filled
  brand_aliases.json      # {canonical: [variants]} explicit alias table, e.g. {"Hewlett-Packard": ["HP"]}
src/observatory/
  normalize.py            # brand-name normalization (rules + alias table)
  metrics.py              # Recall@K and pass threshold
  parse.py                # extract brand list from free-text LLM answer
  data.py                 # load + sanity-check input files
  llm.py                  # prompt template + LLM client (NOT configured yet)
scripts/validate.py       # CLI: check / query / score
tests/test_core.py        # unit tests (stdlib unittest)
runs/<run_id>/            # one dir per real run: meta.json, responses.jsonl (raw), results.csv, summary.json
```

## Normalization rules

Lowercase; strip accents; `&` → `and`; drop apostrophes and ®/™; other punctuation → space;
drop leading "the"; drop trailing corporate suffixes (Inc, Corp, Co, Ltd, LLC, Group, …).
Anything that needs judgment (abbreviations, parent vs. sub-brand, local names) goes in
`brand_aliases.json` so it is explicit and reviewable.

## Usage

```bash
python3 -m unittest discover -s tests -v          # unit tests
python3 scripts/validate.py check                 # validate inputs, print the 20 prompts (no API call)
python3 scripts/validate.py query --provider P --model M [--temperature 0] [--only running_shoes]
python3 scripts/validate.py score runs/<run_id>   # Recall@10 per category -> results.csv, summary.json
```

`query` saves raw answers first and never overwrites an existing run; `score` can be
re-run on saved answers (e.g. after editing aliases) without new API calls.

## Status

- Reference brands: **not filled yet** (`check` lists what is missing).
- LLM provider: **not configured yet** (`query` refuses to run).
- No validation results exist yet.
