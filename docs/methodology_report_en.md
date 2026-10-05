# Brand Category Discovery & AI Validation — Sample-Stage Methodology and Results (English)

> Generated 2026-10-06 (HKT). All numbers come from `outputs/report_stats.json` (`python3 scripts/report_stats.py r1_ds r2_ds r3_ds_holdout`) and `outputs/category_status.csv`. Same data and fact boundary as the Chinese version.

## 1. Task and scope

- Following `JIA_LIU_TASK.md`: Task 1 derive categories from well-known brands → Task 2 expand each category to ≥10 real brands → Task 3 validate category names with the fixed question `What are the best brands for {category}? List 10 brands.`; Brand Recall@10 ≥ 80% = Pass, otherwise rename and re-test.
- This is a **sample** stage: 60 B2C categories (the ≥1000 target is out of scope here).
- Brand Recall@10 = number of the AI's top-10 brands (after normalization, alias mapping and de-duplication) that appear in the category's brand table ÷ 10; fewer than 10 returned brands count as misses.
- Validation AI: OpenRouter `deepseek/deepseek-v4-pro`, one independent single-turn request per category, no system prompt.

## 2. Method (how the results were derived)

**Task 1 (seed pool → categories)**
1. Seeds: Kantar BrandZ 2025 Most Valuable Global Brands Top 100 + Most Valuable Chinese Brands Top 100 (original PDFs and `pdftotext` output in `data/raw/sources/`, with SHA256).
2. After de-duplication (11 overlaps): 189 brands. Each brand was manually given a fine-grained raw_label and one primary category; synonymous labels were merged (30 merge records, `data/category_merges.csv`).
3. B2B brands (e.g. Microsoft, SAP, NVIDIA, Aramco) are classified too, but their 6 categories are marked `out_of_scope` and excluded from Task 2/3 (the project targets consumer categories).

**Task 2 (brand tables)**
1. For each B2C category, public list pages were consulted (Wikipedia lists, Brand Finance, FashionUnited, industry statistics pages). Every page and the brand names on it are logged in `data/raw/task2/evidence.jsonl` (method=webfetch: page read directly; websearch: based on a search-result summary, weaker evidence).
2. Brands that are real and clearly belong to the category were selected manually (SELECTION in `scripts/build_category_brands.py`); the script attaches an evidence URL to every brand and fails if none exists; seed brands must appear in their primary category's table.
3. Matching: normalization (case, accents, punctuation, &/and, trailing Inc/Ltd/Group/.com, …) + a global alias table + per-category aliases (category entries take precedence, e.g. Sony→PlayStation only in game_consoles).

**Task 3 (AI validation, renaming, table completion)**
1. r1_ds: 60 categories, temperature 0. The AI's `extra` brands (not in the table) were inspected per category and attributed to: parser error / alias gap / brand-table gap / category name misunderstood.
2. After fixing the parser and aliases, the **same raw answers** were re-scored (no new AI calls).
3. Table gaps: plausible real brands from `extra` became candidates (135). Wikipedia REST summaries were fetched (`scripts/verify_candidates.py`, raw responses archived). Strict rule: the summary must directly state that the brand belongs to the category; 7 brands without a usable Wikipedia page were confirmed via web search. Accepted brands are marked `origin=added_post_validation`, and a "pre-additions" recall is computed separately.
4. The 5 categories whose names were misunderstood were renamed and re-tested (r2_ds).
5. Hold-out r3_ds_holdout: with the brand table frozen, all 60 final names were re-sampled at temperature 1.0. These results are **evaluation only**: they did not change the tables and are not part of the master table.

## 3. First-order results

### 3.1 Task 1 / Task 2 size

| Metric | Value |
|---|---|
| Seed brands (after de-duplication) | 189 (World 88 / China 101) |
| Categories | 66 (B2C 60 / out_of_scope 6) |
| Label merge records | 30 |
| Unclassified seed brands | 0 |
| Brand-table rows (60 B2C categories) | 957 |
| Origin: seed / expanded / added_post_validation | 163 / 675 / 119 |
| Evidence: webfetch / websearch / wikipedia_summary / kantar_seed / cross_category | 360 / 448 / 112 / 31 / 6 |
| World / China rows | 720 / 237 |
| Brands per category min / median / max | 10 / 16 / 29 |
| Post-validation candidates / accepted | 135 / 119 |

#### Column Definitions
- **Metric**: Definition — name of the statistic.
- **Value**: Definition — the statistic; Computation — `task1` / `task2` fields of `scripts/report_stats.py`; Unit — count of brands/rows/categories; Source — `data/seed_brands.csv`, `data/categories.csv`, `data/category_merges.csv`, `data/category_brands.csv`, `data/raw/task2/post_validation_decisions.csv`. World/China is a manual label (rule: HQ in mainland China / Hong Kong / Macau = China, otherwise World), not a direct observation. websearch evidence comes from search summaries and is weaker than webfetch. Uncertainty: not computed.

### 3.2 Task 3 results per run

| Run | Model / temperature | Categories | Basis | Pass | Pass rate | Mean | Median | Std | Min | Max | Cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| r1_ds first scoring (initial parser & aliases) | deepseek-v4-pro / 0 | 60 | initial table | 23 | 0.383 | 0.6283 | not computed | not computed | not computed | not computed | 0.0617 |
| r1_ds (after parser/alias fixes) | deepseek-v4-pro / 0 | 60 | pre-additions | 25 | 0.4167 | 0.6883 | 0.7 | 0.2222 | 0.0 | 1.0 | same |
| r1_ds (after fixes) | deepseek-v4-pro / 0 | 60 | with additions | 56 | 0.9333 | 0.8733 | 0.9 | 0.1991 | 0.0 | 1.0 | same |
| r2_ds (5 renamed categories) | deepseek-v4-pro / 0 | 5 | pre-additions | 4 | 0.8 | 0.78 | 0.8 | 0.098 | 0.6 | 0.9 | 0.0085 |
| r2_ds (5 renamed categories) | deepseek-v4-pro / 0 | 5 | with additions | 5 | 1.0 | 0.96 | 1.0 | 0.049 | 0.9 | 1.0 | same |
| Final (latest attempt per category) | — | 60 | with additions | 60 | 1.0 | — | — | — | — | — | — |
| r3_ds_holdout (hold-out) | deepseek-v4-pro / 1.0 | 60 | pre-additions | 28 | 0.4667 | 0.69 | 0.7 | 0.2461 | 0.0 | 1.0 | 0.043 |
| r3_ds_holdout (hold-out) | deepseek-v4-pro / 1.0 | 60 | with additions (frozen table) | 44 | 0.7333 | 0.7983 | 0.9 | 0.2149 | 0.0 | 1.0 | same |

#### Column Definitions
- **Run**: run_id, i.e. `runs/<run_id>/`.
- **Model / temperature**: OpenRouter model id and sampling temperature (`runs/<id>/meta.json`).
- **Categories**: number of categories scored in the run.
- **Basis**: "pre-additions" = brand table restricted to origin ∈ {seed, expanded}; "with additions" = including added_post_validation.
- **Pass**: number of categories with Recall@10 ≥ 0.8. **Pass rate** = Pass / Categories.
- **Mean / Median / Std / Min / Max**: statistics of per-category Recall@10 (population std); range 0–1.
- **Cost USD**: sum of usage.cost returned by OpenRouter.
- **Source**: `outputs/report_stats.json`, recomputed from raw answers `runs/*/responses.jsonl` with the current code. Exception: the "first scoring" row is taken from `log.md` at the time (initial parser and aliases); current code no longer produces it. Re-computing with the old parser from commit ed733c9 plus current aliases gives 26/60, mean 0.6533.
- Uncertainty: one sample per category; CI / seed variance not computed. The r1 vs r3 difference mixes temperature and sampling randomness.

### 3.3 Renames (category_id unchanged; counted as attempt 2 of the same category)

| category_id | Original name (r1) | r1 observation | New name (r2) | r2 Recall (pre / with additions) |
|---|---|---|---|---|
| property_developers | Real Estate Developers | returned luxury fixtures/appliance brands (Sub-Zero, Miele…), r1 = 0.0 | Chinese Real Estate Developers | 0.8 / 0.9 |
| payment_networks | Credit Card Networks | mixed in issuers and co-branded cards (Chase, Capital One, Delta SkyMiles), 0.4 | Payment Card Networks | 0.9 / 0.9 |
| home_improvement | Home Improvement Stores | last 5 were tool/paint brands (DeWalt, Benjamin Moore), 0.5 | Home Improvement Retail Chains | 0.8 / 1.0 |
| ai_chatbots | AI Chatbots | returned company names (OpenAI, Anthropic, xAI) | AI Chatbot Apps | still company names; with category aliases 0.8 / 1.0 (with those aliases the original r1 name also reaches 0.9, so the rename itself was not necessary) |
| cigarettes | Cigarettes | refused to answer, 0.0 | Cigarette Brands | 0.6 / 1.0 (but refused again in the hold-out at temperature 1.0) |

#### Column Definitions
- **category_id**: category key (`data/categories.csv`). **Original / New name**: the `{category}` text tested.
- **r1 observation**: manual summary of parsed/extra in `runs/r1_ds/results.csv` (not an automatic metric); the number is r1 Recall after parser fixes (pre-additions).
- **r2 Recall**: Recall@10 in `runs/r2_ds`, pre / with additions. Source: `outputs/report_stats.json`.
- The company→product aliases for ai_chatbots (OpenAI→ChatGPT, etc.) are a manual judgment, not a direct observation.

### 3.4 Per-category results (60 categories)

| # | category_id | r1 name | final name | brands (added) | r1 pre | r1 with | r2 pre | r2 with | final | holdout pre | holdout with |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | smartphones | Smartphones | Smartphones | 14 (3) | 0.7 | 1.0 | – | – | Pass | 0.6 | 0.8 |
| 2 | search_engines | Search Engines | Search Engines | 12 (0) | 1.0 | 1.0 | – | – | Pass | 0.9 | 0.9 |
| 3 | social_media | Social Media Platforms | Social Media Platforms | 17 (0) | 0.9 | 0.9 | – | – | Pass | 1.0 | 1.0 |
| 4 | short_video | Short Video Apps | Short Video Apps | 15 (2) | 0.7 | 0.9 | – | – | Pass | 0.8 | 0.9 |
| 5 | video_streaming | Video Streaming Services | Video Streaming Services | 16 (0) | 1.0 | 1.0 | – | – | Pass | 1.0 | 1.0 |
| 6 | music_streaming | Music Streaming Services | Music Streaming Services | 14 (4) | 0.6 | 1.0 | – | – | Pass | 0.6 | 1.0 |
| 7 | ecommerce | Online Shopping Platforms | Online Shopping Platforms | 16 (5) | 0.4 | 0.9 | – | – | Pass | 0.7 | 0.8 |
| 8 | fast_food | Fast Food Chains | Fast Food Chains | 18 (3) | 0.7 | 1.0 | – | – | Pass | 0.9 | 1.0 |
| 9 | coffee_chains | Coffee Chains | Coffee Chains | 17 (3) | 0.7 | 1.0 | – | – | Pass | 0.6 | 0.9 |
| 10 | bubble_tea | Bubble Tea Chains | Bubble Tea Chains | 18 (2) | 0.7 | 0.9 | – | – | Pass | 0.8 | 0.9 |
| 11 | hot_pot | Hot Pot Restaurant Chains | Hot Pot Restaurant Chains | 13 (3) | 0.7 | 1.0 | – | – | Pass | 0.6 | 0.7 |
| 12 | soft_drinks | Soft Drinks | Soft Drinks | 14 (3) | 0.7 | 1.0 | – | – | Pass | 0.7 | 0.9 |
| 13 | bottled_water | Bottled Water | Bottled Water | 20 (3) | 0.5 | 0.8 | – | – | Pass | 0.7 | 0.9 |
| 14 | dairy | Dairy Products | Dairy Products | 15 (2) | 0.7 | 0.9 | – | – | Pass | 0.0 | 0.2 |
| 15 | baijiu | Baijiu | Baijiu | 17 (0) | 0.9 | 0.9 | – | – | Pass | 0.9 | 0.9 |
| 16 | beer | Beer | Beer | 23 (9) | 0.1 | 1.0 | – | – | Pass | 0.2 | 0.6 |
| 17 | energy_drinks | Energy Drinks | Energy Drinks | 18 (3) | 0.5 | 0.8 | – | – | Pass | 0.4 | 0.7 |
| 18 | soy_sauce | Soy Sauce | Soy Sauce | 17 (4) | 0.6 | 1.0 | – | – | Pass | 0.1 | 0.2 |
| 19 | processed_meat | Processed Meat Products | Processed Meat Products | 16 (4) | 0.6 | 1.0 | – | – | Pass | 0.2 | 0.3 |
| 20 | banks | Banks | Banks | 29 (0) | 1.0 | 1.0 | – | – | Pass | 1.0 | 1.0 |
| 21 | payment_networks | Credit Card Networks | Payment Card Networks | 11 (0) | 0.4 | 0.4 | 0.9 | 0.9 | Pass | 0.9 | 0.9 |
| 22 | digital_payments | Digital Payment Services | Digital Payment Services | 12 (0) | 0.9 | 0.9 | – | – | Pass | 0.9 | 0.9 |
| 23 | insurance | Insurance Companies | Insurance Companies | 21 (0) | 0.8 | 0.8 | – | – | Pass | 0.7 | 0.7 |
| 24 | health_insurance | Health Insurance | Health Insurance | 11 (0) | 0.8 | 0.8 | – | – | Pass | 0.8 | 0.8 |
| 25 | mobile_carriers | Mobile Carriers | Mobile Carriers | 21 (0) | 1.0 | 1.0 | – | – | Pass | 0.9 | 0.9 |
| 26 | isps | Internet Service Providers | Internet Service Providers | 12 (0) | 0.8 | 0.8 | – | – | Pass | 0.9 | 0.9 |
| 27 | airlines | Airlines | Airlines | 24 (0) | 0.9 | 0.9 | – | – | Pass | 1.0 | 1.0 |
| 28 | express_delivery | Express Delivery Services | Express Delivery Services | 17 (2) | 0.8 | 1.0 | – | – | Pass | 0.6 | 0.7 |
| 29 | food_delivery | Food Delivery Platforms | Food Delivery Platforms | 14 (0) | 0.8 | 0.8 | – | – | Pass | 0.9 | 0.9 |
| 30 | ride_hailing | Ride-Hailing Apps | Ride-Hailing Apps | 10 (0) | 0.9 | 0.9 | – | – | Pass | 0.9 | 0.9 |
| 31 | online_travel | Online Travel Agencies | Online Travel Agencies | 17 (3) | 0.7 | 1.0 | – | – | Pass | 0.8 | 0.9 |
| 32 | hotel_chains | Hotel Chains | Hotel Chains | 22 (3) | 0.7 | 1.0 | – | – | Pass | 0.5 | 0.5 |
| 33 | restaurant_reviews | Restaurant Review Platforms | Restaurant Review Platforms | 12 (0) | 0.9 | 0.9 | – | – | Pass | 1.0 | 1.0 |
| 34 | real_estate_agencies | Real Estate Agencies | Real Estate Agencies | 15 (2) | 0.7 | 0.9 | – | – | Pass | 0.7 | 0.8 |
| 35 | property_developers | Real Estate Developers | Chinese Real Estate Developers | 12 (1) | 0.0 | 0.0 | 0.8 | 0.9 | Pass | 0.7 | 0.8 |
| 36 | electric_vehicles | Electric Vehicles | Electric Vehicles | 19 (0) | 1.0 | 1.0 | – | – | Pass | 0.9 | 0.9 |
| 37 | cars | Cars | Cars | 16 (0) | 0.9 | 0.9 | – | – | Pass | 0.8 | 0.8 |
| 38 | luxury_fashion | Luxury Fashion | Luxury Fashion | 17 (3) | 0.7 | 1.0 | – | – | Pass | 0.7 | 1.0 |
| 39 | sportswear | Sportswear | Sportswear | 14 (4) | 0.6 | 1.0 | – | – | Pass | 0.7 | 0.8 |
| 40 | fast_fashion | Fast Fashion | Fast Fashion | 13 (0) | 0.9 | 0.9 | – | – | Pass | 1.0 | 1.0 |
| 41 | cosmetics | Cosmetics | Cosmetics | 18 (0) | 0.9 | 0.9 | – | – | Pass | 0.5 | 0.5 |
| 42 | jewelry | Jewelry | Jewelry | 19 (6) | 0.4 | 1.0 | – | – | Pass | 0.4 | 1.0 |
| 43 | home_appliances | Home Appliances | Home Appliances | 19 (4) | 0.6 | 1.0 | – | – | Pass | 0.5 | 0.8 |
| 44 | air_conditioners | Air Conditioners | Air Conditioners | 13 (2) | 0.7 | 0.9 | – | – | Pass | 0.6 | 0.7 |
| 45 | televisions | TVs | TVs | 10 (0) | 0.8 | 0.8 | – | – | Pass | 0.9 | 0.9 |
| 46 | laptops | Laptops | Laptops | 11 (0) | 0.8 | 0.8 | – | – | Pass | 0.9 | 0.9 |
| 47 | drones | Drones | Drones | 12 (0) | 0.8 | 0.8 | – | – | Pass | 0.5 | 0.5 |
| 48 | game_consoles | Video Game Consoles | Video Game Consoles | 16 (4) | 0.6 | 1.0 | – | – | Pass | 0.6 | 1.0 |
| 49 | consumer_electronics | Consumer Electronics | Consumer Electronics | 15 (4) | 0.6 | 1.0 | – | – | Pass | 0.7 | 0.8 |
| 50 | ai_chatbots | AI Chatbots | AI Chatbot Apps | 15 (2) | 0.8 | 0.9 | 0.8 | 1.0 | Pass | 0.8 | 0.9 |
| 51 | supermarkets | Supermarket Chains | Supermarket Chains | 16 (2) | 0.7 | 0.9 | – | – | Pass | 0.7 | 0.7 |
| 52 | home_improvement | Home Improvement Stores | Home Improvement Retail Chains | 15 (2) | 0.5 | 0.5 | 0.8 | 1.0 | Pass | 0.9 | 1.0 |
| 53 | furniture | Furniture Stores | Furniture Stores | 13 (3) | 0.5 | 0.8 | – | – | Pass | 0.7 | 1.0 |
| 54 | tcm | Traditional Chinese Medicine | Traditional Chinese Medicine | 12 (2) | 0.6 | 0.8 | – | – | Pass | 0.5 | 0.6 |
| 55 | online_healthcare | Online Healthcare Platforms | Online Healthcare Platforms | 18 (5) | 0.3 | 0.8 | – | – | Pass | 0.5 | 0.6 |
| 56 | job_platforms | Job Search Platforms | Job Search Platforms | 15 (0) | 0.8 | 0.8 | – | – | Pass | 0.8 | 0.8 |
| 57 | news_apps | News Apps | News Apps | 17 (3) | 0.7 | 1.0 | – | – | Pass | 0.8 | 0.9 |
| 58 | video_games | Video Game Companies | Video Game Companies | 24 (5) | 0.5 | 1.0 | – | – | Pass | 0.3 | 0.8 |
| 59 | movie_studios | Movie Studios | Movie Studios | 16 (0) | 0.8 | 0.8 | – | – | Pass | 0.8 | 0.8 |
| 60 | cigarettes | Cigarettes | Cigarette Brands | 14 (4) | 0.0 | 0.0 | 0.6 | 1.0 | Pass | 0.0 | 0.0 |

#### Column Definitions
- **#**: row number. **category_id**: category key.
- **r1 name / final name**: name in r1 / final validated name (`outputs/category_status.csv`).
- **brands (added)**: number of brands in the category table (in brackets: added_post_validation). Source `data/category_brands.csv`.
- **r1 pre / r1 with**: r1_ds Recall@10 pre / with additions (0–1).
- **r2 pre / r2 with**: r2_ds (renamed categories only); "–" = not in r2.
- **final**: result of the latest attempt per category (ordered by run start time); basis for the master table.
- **holdout pre / holdout with**: r3_ds_holdout Recall@10 (temperature 1.0, frozen table).
- Computation: `scripts/report_stats.py` → `scripts/report_tables.py`. Single sample; no CI (not computed).

### 3.5 Hold-out failures (16 categories, Recall < 0.8 with additions)

hot_pot 0.7, dairy 0.2, beer 0.6, energy_drinks 0.7, soy_sauce 0.2, processed_meat 0.3, insurance 0.7, express_delivery 0.7, hotel_chains 0.5, cosmetics 0.5, air_conditioners 0.7, drones 0.5, supermarkets 0.7, tcm 0.6, online_healthcare 0.6, cigarettes 0.0 (refusal).
Observed types of `extra` (from `runs/r3_ds_holdout/results.csv`):
- New spellings of brands already in the table: e.g. `Fenty Beauty by Rihanna`, `Dior Beauty`, `Sempio 501`, `Higeta Honzen`, `USPS Priority Mail Express`, `Liuyishou Hotpot`.
- New long-tail brands: e.g. Chobani, Cabot, Straus (dairy); Nueske's, Spam, Herta (processed_meat); Yamaroku, Bragg Liquid Aminos (soy_sauce); Aman, Rosewood, Six Senses (hotel_chains).
- Refusal: cigarettes.

### 3.6 Deliverable master table

`outputs/master_table.csv`: 60 categories, 957 rows (Category | Brand | World/China | Category验证结果), only finally passed categories. Example:

| Category | Brand | World/China | Category验证结果 |
|---|---|---|---|
| Smartphones | Apple | World | Pass |
| Smartphones | Xiaomi | China | Pass |
| Smartphones | Huawei | China | Pass |
| Baijiu | Moutai | China | Pass |
| Baijiu | Wuliangye | China | Pass |
| Chinese Real Estate Developers | Vanke | China | Pass |

#### Column Definitions
- **Category**: final validated category name. **Brand**: brand name (table spelling). **World/China**: manual label (rule in 3.1). **Category验证结果**: result of the category's final attempt (all Pass). Source `outputs/master_table.csv`.

## 4. Key Findings (second-order, labelled)

- **Candidate finding**: first-round failures were mainly caused by brand-table coverage and matching, not category names (after parser/alias fixes: 25/60 pre-additions vs 56/60 with additions; only 5 categories needed renaming).
- **Candidate finding**: the additions also help on the hold-out (28/60 pre-additions → 44/60 with additions), so they are not merely fitted to one r1 answer; but the hold-out pass count (44/60) is clearly below r1 (56/60), i.e. the r1 pass rate is optimistic.
- **Interpretation**: broad food categories (Dairy Products, Soy Sauce, Processed Meat Products) reach only 0.2–0.3 on the hold-out; a possible explanation is that these names are too broad and each sample surfaces different long-tail/artisanal brands, so narrower names (sub-category or region) may be needed. Needs verification.
- **Interpretation**: DeepSeek's answers lean towards the US market (Health Insurance, Supermarkets, Furniture, …), which affects the World/China balance.
- **Observation**: Cigarettes became answerable after renaming at temperature 0 but was refused again at temperature 1.0; the result is unstable.

## 5. Limitations

- Single model (DeepSeek), one sample per category; temperature and randomness are not separated between r1 and r3.
- Addition candidates come from the same model's answers (with an independent-evidence gate), which may bias the tables towards that model; mitigated by the pre-additions basis and the hold-out.
- 448 rows rely on search-result summaries (websearch), weaker than direct page reads; some confirmation searches included candidate brand names in the query.
- Aliases were added after seeing answers (spelling variants of the same brand, plus judgment-based company→product aliases for ai_chatbots), which may raise recall.
- World/China labels and "clearly belongs to the category" are manual judgments.

## 6. Follow-up Analysis Needed

- Cross-model validation (e.g. GPT, Qwen, Claude) and multiple samples per category to report variance/CI.
- For the 16 hold-out failures: separate spelling variants from truly missing brands, or test narrower names in a new run (without editing the frozen table).
- Scaling to 1000 categories: larger seed pool (Kantar category rankings, Brand Finance sector rankings, e-commerce category trees), automated Task 2 candidate generation with manual spot checks.

## 7. Reproduce

```bash
python3 -m unittest discover -s tests
python3 scripts/build_category_brands.py && python3 scripts/validate.py check
python3 scripts/validate.py score runs/r1_ds && python3 scripts/validate.py score runs/r2_ds
python3 scripts/validate.py score runs/r3_ds_holdout --no-record
python3 scripts/validate.py master
python3 scripts/report_stats.py r1_ds r2_ds r3_ds_holdout > outputs/report_stats.json
python3 scripts/report_tables.py > outputs/report_table.md
```
