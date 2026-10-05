---
title: "Brand Category Discovery and AI Validation"
subtitle: "Sample results and method"
author: "Yunxiang Mo"
date: "October 2026"
---

## Summary

I built a Category → Brand table for **60 consumer categories (957 brand rows)**, starting from the Kantar BrandZ 2025 Global and China Top 100 brands, and validated every category name with the fixed question *"What are the best brands for {category}? List 10 brands."*

- **All 60 categories pass** (Brand Recall@10 ≥ 0.8) with DeepSeek V4 Pro, after expanding the brand tables and renaming 5 categories.
- Because some brands were added after seeing DeepSeek's answers, I froze the table and ran two **independent checks**:
  - DeepSeek re-sampled at temperature 1.0: **44/60** pass.
  - A second model, Qwen 3.7 Plus: **32/60** pass (12 more categories score 0.7, one brand short).
  - **28 categories pass both checks.**
- Total API cost for all reported runs: **about US$0.34**.

## Method

**Task 1: brands → categories.** Seed pool = Kantar BrandZ 2025 Most Valuable Global Brands (Top 100) + Most Valuable Chinese Brands (Top 100), 189 unique brands (88 World, 101 China). Each brand was assigned one primary category; synonymous labels were merged (30 merges), giving 66 categories. Six B2B categories (e.g. semiconductors, enterprise software) are kept but not validated, since the target is consumer-facing queries. **Unclassified seed brands: 0.**

**Task 2: expand each category.** For each of the 60 consumer categories I collected other major brands from public ranking pages (Wikipedia lists, Brand Finance, industry statistics). Every brand row carries a source URL. **Every category has ≥ 10 brands** (min 10, median 16, max 29). World/China = headquarters location (mainland China, Hong Kong, Macau = China).

**Task 3: AI validation.** Each category is asked once, in a fresh single-turn request, through OpenRouter. The answer is parsed into a brand list, and

> **Brand Recall@10 = (number of the AI's first 10 brands found in the category's table) / 10**, Pass if ≥ 0.8.

Brand names are matched after normalization (case, accents, punctuation, "Inc./Group/.com" suffixes) and an alias list for spelling variants (e.g. *Shoo Loong Kan* = *Xiaolongkan*). If the AI returns fewer than 10 brands, the missing slots count as misses.

**When a category failed**, I looked at the brands the AI returned that were not in the table and classified each failure:

1. **Missing brand.** The AI named a real brand of that category that my table lacked. It was added only if an independent source (mostly the Wikipedia summary) explicitly describes it as that kind of brand: 119 of 135 candidates accepted. These rows are flagged, and recall is always also reported *without* them ("pre-additions").
2. **Misunderstood name.** The AI answered a different category. The category was renamed and re-tested (5 cases, below).

## Results

| Run | Model / temperature | Brand table | Pass | Mean Recall@10 |
|---|---|---|---|---|
| Round 1, first scoring | DeepSeek V4 Pro / 0 | initial | 23 / 60 | 0.63 |
| Round 1 | DeepSeek V4 Pro / 0 | initial (pre-additions) | 26 / 60 | 0.69 |
| Round 1 | DeepSeek V4 Pro / 0 | with additions | 56 / 60 | 0.88 |
| Round 2 (5 renamed) | DeepSeek V4 Pro / 0 | with additions | 5 / 5 | 0.96 |
| **Final (latest attempt per category)** | DeepSeek V4 Pro / 0 | with additions | **60 / 60** | — |
| Hold-out (table frozen) | DeepSeek V4 Pro / 1.0 | with additions | 44 / 60 | 0.80 |
| Cross-model (table frozen) | Qwen 3.7 Plus / 0 | with additions | 32 / 60 | 0.72 |
| Cross-model (table frozen) | Qwen 3.7 Plus / 0 | pre-additions | 20 / 60 | 0.62 |

*Column definitions.* **Run**: one pass over the categories. The first row used my first parser and alias list (later fixed: e.g. it read Markdown bullet notes as brands). It is kept for transparency, and all other rows re-score the same saved answers with the final code. **Brand table**: "pre-additions" excludes the 119 brands added after validation. **Pass**: number of categories with Recall@10 ≥ 0.8. **Mean Recall@10**: average over categories, range 0–1. Each category was sampled once per run; no confidence intervals were computed.

**Renamed categories** (round 1 → round 2, DeepSeek):

| Original name | What the AI did | New name | Recall@10 after |
|---|---|---|---|
| Real Estate Developers | listed appliance/fixture brands (Sub-Zero, Miele) | Chinese Real Estate Developers | 0.9 |
| Credit Card Networks | mixed in card issuers (Chase, Capital One) | Payment Card Networks | 0.9 |
| Home Improvement Stores | listed tool/paint brands (DeWalt, Benjamin Moore) | Home Improvement Retail Chains | 1.0 |
| Cigarettes | refused to answer | Cigarette Brands | 1.0 |
| AI Chatbots | listed companies (OpenAI, Anthropic) | AI Chatbot Apps | 1.0 |

*Column definitions.* **What the AI did**: my reading of the round-1 answer. **Recall@10 after**: round-2 score with additions. For AI Chatbots the rename alone did not help: the answer still listed companies, and it passed only after mapping company → product (OpenAI → ChatGPT). That mapping is my judgment.

**Sample of the master table** (full table: 957 rows, attached):

| Category | Brand | World/China | Result |
|---|---|---|---|
| Smartphones | Apple / Samsung / Google Pixel | World | Pass |
| Smartphones | Xiaomi / Huawei / OPPO / vivo | China | Pass |
| Baijiu | Moutai / Wuliangye / Luzhou Laojiao | China | Pass |
| Electric Vehicles | Tesla / BMW | World | Pass |
| Electric Vehicles | BYD / Li Auto / NIO | China | Pass |
| Bubble Tea Chains | Mixue Bingcheng / Heytea / Chagee | China | Pass |

*Column definitions.* One row per brand in the real table; several brands are shown per line here only to save space. **Result**: validation result of the category's latest attempt.

## What the checks show

- *Observed:* the brand additions also help on new answers. In the DeepSeek hold-out, passes rise from 29 to 44 with the additions; with Qwen, from 20 to 32. So they are not fitted to one single answer, but the 60/60 is optimistic.
- *Observed:* the two models agree on 40 of 60 categories: 28 pass both, 12 fail both. The categories failing both are broad food and drink (Dairy Products, Beer, Energy Drinks, Processed Meat Products, Hot Pot Restaurant Chains), services (Insurance Companies, Hotel Chains, Supermarket Chains, Online Healthcare Platforms), Cosmetics, Drones and Traditional Chinese Medicine.
- *Observed, Qwen:* "Online Shopping Platforms" was read as e-commerce *software* (Shopify, WooCommerce; recall 0.0), and "AI Chatbot Apps" partly as business chatbot builders (Intercom, ManyChat). These are naming problems a single model did not reveal.
- *Interpretation:* most other misses are real brands outside my table: US regional or niche names (Mint Mobile, USAA, GEICO), premium or craft picks (Aman, Westmalle), and DTC beauty (Rare Beauty). Broad category names seem to invite a different "long tail" each time. Narrower names, e.g. by sub-type or market, are the likely fix. This is not yet tested.

## Limitations

- One sample per category per run; no variance or confidence interval was computed.
- Brand additions and some aliases were made after seeing round-1 answers. This is mitigated by reporting pre-additions recall and by the frozen-table hold-out and cross-model runs.
- About half of the Task 2 rows are supported by search-result snippets, not by full pages. World/China labels and "clearly belongs to the category" are manual judgments.
- Both validators answered with a US-centric bias, which affects the World/China balance of what counts as "best".

## Next steps toward 1,000 categories

1. **Larger seed pool**: Kantar and Brand Finance sector rankings plus e-commerce category trees.
2. **Semi-automated Task 2**: candidate brands from several sources, with human spot checks.
3. **Multi-model validation by default**: a category passes only if it passes on at least two models. The categories that fail on both models get narrower names.

The code, raw AI answers, evidence logs and per-category results are in the repository: <https://github.com/moyunxiang/ai-observatory>. Every number here can be recomputed from the saved answers.

## Appendix: per-category results

<!-- APPENDIX -->

*Column definitions.* **Brands (W/C)**: rows in the brand table (World / China). **DeepSeek r1 pre → with**: round-1 Recall@10 before and after brand additions; *renamed* shows round 2 for the five renamed categories. **Final**: result of the latest attempt, which decides inclusion in the master table. **Hold-out**: DeepSeek at temperature 1.0 with the frozen table. **Qwen**: Qwen 3.7 Plus with the frozen table. All recall values are in the range 0–1, from a single sample.
