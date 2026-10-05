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

#### 2026-10-05 19:35 HKT — Export Task 3 round-1 sheet; docs refresh

**Context**: Task 1/2 checks pass. Validation AI = user's ChatGPT, manual.

**Actions**: `python3 scripts/validate.py export --run-id r1` (60 prompts). Rewrote README for the task-spec procedure; updated state.md and plan.md.

**Results**: `runs/r1/manual_sheet.txt` with 60 sections. No answers yet; no results.

**Next**: User fills sheet → `import runs/r1` → `score runs/r1`.

#### 2026-10-05 20:05 HKT — Switch Task 3 to API: OpenRouter + DeepSeek

**Context**: User: use OpenRouter (key in `.env`, gitignored), DeepSeek is enough. Manual sheet `runs/r1/` kept but not used.

**Actions**:
- `curl https://openrouter.ai/api/v1/models` -> chose `deepseek/deepseek-v4-pro` (latest non-dated general DeepSeek; $0.21/M in, $0.42/M out).
- Implemented `openrouter` provider in `src/observatory/llm.py` (stdlib urllib; key from env or .env; retries on 408/429/5xx with backoff; single user message, no system prompt; records served_model/provider/usage in `response_meta`).
- Smoke: `query --provider openrouter --model deepseek/deepseek-v4-pro --temperature 0 --run-id ds_smoke --only hot_pot health_insurance`; `score runs/ds_smoke --no-record`.
- Full run started: `python3 -u scripts/validate.py query --provider openrouter --model deepseek/deepseek-v4-pro --temperature 0 --run-id r1_ds` (background).

**Results (smoke, real DeepSeek output)**: health_insurance 0.8 Pass; hot_pot 0.4 Fail. Parser handled "Little Sheep (Xiabu Xiabu's sister brand)", "Aetna (a CVS Health company)" correctly. ~$0.0003/call.
- hot_pot misses: "CouCou Hot Pot" vs table alias "Coucou Hotpot" (alias gap); Happy Lamb, Dong Lai Shun, Dolar Shop, Boiling Point, Tanyoto not in table (table gap).

**Decisions / Assumptions**: temperature 0, 1 sample/category. Alias fixes found after seeing answers will be logged and applied by re-scoring the same raw responses.

**Next**: Score r1_ds; failure analysis.

> 2026-10-05 起按更新后的全局规则：`log.md` / `plan.md` 说明性内容使用中文；`state.md` 合并进 `plan.md`。以上旧条目保持原样（不改写历史）。

#### 2026-10-05 21:40 HKT — 第一轮 DeepSeek 全量结果 r1_ds 及失败分析

**背景**：Task 1/2 已完成，第一轮 Task 3 用 `deepseek/deepseek-v4-pro`（OpenRouter，temperature 0，每类 1 次独立单轮请求）。
**操作**：
- `python3 -u scripts/validate.py query --provider openrouter --model deepseek/deepseek-v4-pro --temperature 0 --run-id r1_ds`（后台，约 45 分钟，60/60 无报错，总成本 $0.0617）
- `python3 scripts/validate.py score runs/r1_ds`
- 逐类检查 `results.csv` 的 parsed / extra。
**结果（首次打分，旧解析器）**：23/60 Pass，mean recall 0.6283。
**发现的问题（按原因分类）**：
1. 解析器 bug：`**1. Amazon**`（编号包在加粗里）未剥离编号 → ecommerce/payment_networks/home_improvement/furniture 都是 0.0；嵌套子弹点 `- **Best for:**` 被当成品牌（sportswear、home_appliances）；结尾 `Disclaimer` 被收入（tcm）。
2. 别名优先级 bug：全局别名的 canonical 自映射覆盖了类别别名（例：game_consoles 中 `Valve` 没映射到 Steam Deck）。
3. 别名缺口（同一品牌不同写法）：Shoo Loong Kan=小龙坎、Costco Wholesale、Coldwell Banker Real Estate、Guangzhou Baiyunshan Pharmaceutical 等。
4. 品牌表缺口：DeepSeek 返回的多为真实品牌但不在表中（美国市场偏向明显，如 Mountain Dew、Tidal、Van Cleef & Arpels、Capcom）。
5. 类别名被误解：Real Estate Developers → 返回高端建材/家电品牌；Credit Card Networks → 混入发卡行（Chase、Capital One）；Home Improvement Stores → 后 5 个是工具/油漆品牌；AI Chatbots → 返回公司名（OpenAI、Anthropic）；Cigarettes → 拒答。
**修复**：
- `parse.py`：先剥离行首 `#`/`**`/`>`；有顶层编号时只取顶层编号行（缩进 >3 视为子项）；`A/B` 取前者；支持中文括号。新增 4 个测试（来自真实回答格式），旧测试 `test_numbered_markdown` 期望改为“编号优先”（有意的行为变化）。18/18 通过。
- `data.alias_maps`：先全局再用类别别名覆盖；`normalize_brand` 跟随最多 3 步别名链。
- `category_attempts.csv` 改为同一 run 重新打分时替换该 run 的行（`upsert_attempts`），避免旧解析器的结果残留。
- 补充别名（看到回答后添加的纯写法变体，逐条见 git diff `data/brand_aliases.json`）。
**决策 / 假设**：
- 对同一批原始回答修解析器/别名后重新打分是合法的（不改变 AI 输出）；但所有“看到答案后”新增的别名都记录在案。
- 品牌表缺口：只采纳有独立证据（Wikipedia 摘要）且明确属于该品类的品牌，标记 `added_post_validation`，并同时报告 `recall_pre_additions`。假设：这样可以区分“表不全”和“类别名有问题”；验证方式：报告中对比两种 recall。
- 类别误解的 5 类改名后用新 run 重测：`r2_ds --only property_developers payment_networks home_improvement ai_chatbots cigarettes`（已后台启动）。
**下一步**：Wikipedia 核实 124 个候选品牌（`scripts/verify_candidates.py`，遇 429 限流已加退避）→ 人工判定 → 加入品牌表 → 重打分 r1_ds；打分 r2_ds。

#### 2026-10-05 23:30 HKT — 改名重测 r2_ds、补表（post-validation）、打分与主表 bug 修复

**背景**：r1_ds 解析器修复后 23/60；需要区分“表不全”“别名缺口”“类别名问题”。
**操作**：
1. 改名（`data/categories.csv`，category_id 不变）：Credit Card Networks→Payment Card Networks；Real Estate Developers→Chinese Real Estate Developers；Home Improvement Stores→Home Improvement Retail Chains；AI Chatbots→AI Chatbot Apps；Cigarettes→Cigarette Brands。
   `python3 -u scripts/validate.py query --provider openrouter --model deepseek/deepseek-v4-pro --temperature 0 --run-id r2_ds --only property_developers payment_networks home_improvement ai_chatbots cigarettes`
2. 补表候选：从 r1_ds/r2_ds 的 extra 中挑出“看起来是真实同品类品牌”的 135 个 → `data/raw/task2/post_validation_candidates.csv`；`python3 scripts/verify_candidates.py` 拉取 Wikipedia REST 摘要（遇 429 限流，加退避；404 时用 search API 兜底，兜底命中常错，全部人工审）→ `data/raw/task2/wiki_verification.jsonl`（原始，追加）。
3. 人工判定 → `data/raw/task2/post_validation_decisions.csv`：严格规则=摘要必须直接说明该品牌属于该品类。最终采纳 119（其中 7 个 Wikipedia 无页面、经 WebSearch 结果确认：Happy Lamb、Dolar Shop、Dong Lai Shun、Higeta、Sempio、Ohsawa、Kishibori），拒绝 16（如 Josh 已转型、Target 非超市、C4/Alani Nu/Joybird/Essentia 等页面未提及品牌）。
4. `build_category_brands.py` 读取采纳项，origin=`added_post_validation`，source 为 Wikipedia/搜索页面 → 957 行。
5. AI Chatbot Apps 改名后仍返回公司名（0.2）→ 加类别别名 OpenAI→ChatGPT、Anthropic→Claude、Google→Gemini、Microsoft→Microsoft Copilot、Meta→Meta AI、xAI→Grok（判断：该品类公司品牌与产品一一对应；报告中标注）。
6. 规范化：去掉 suffix 后残留的结尾 "and"（"Poly Developments and Holdings"）。测试 19/19。
7. Bug 修复：(a) 同一 run 重新打分会把行移到文件末尾，`master` 按文件顺序取“最新”导致 r1_ds 覆盖 r2_ds；改为按 `meta.json` 的 started_at 排序。(b) attempt 编号改为只数“更早启动”的 run。
**结果**：r1_ds 56/60（含补表）；r2_ds 5/5；`master`：60/60 Pass，957 行 → `outputs/master_table.csv`。
   commit 84efd4f 冻结此时的品牌表。
**决策 / 假设**：
- 假设：补表来自同一模型的答案，会使通过率偏乐观。验证方式：留出集 r3_ds_holdout（temperature 1.0，全部 60 个最终名称，品牌表冻结，结果 `--no-record` 不进入主表），同时报告 `recall_pre_additions`。
**下一步**：打分 r3_ds_holdout；写中英文方法报告。

#### 2026-10-06 00:40 HKT — 留出集 r3_ds_holdout 与中英文方法报告

**背景**：主表 60/60 Pass，但补表来自同一模型答案，需要独立评估。
**操作**：
- `python3 -u scripts/validate.py query --provider openrouter --model deepseek/deepseek-v4-pro --temperature 1.0 --run-id r3_ds_holdout`（品牌表冻结于 84efd4f；60/60 无报错，$0.043）
- `python3 scripts/validate.py score runs/r3_ds_holdout --no-record`
- 新增 `scripts/report_stats.py`（用当前代码从原始回答重算所有一级统计）与 `scripts/report_tables.py`（逐类表）；输出 `outputs/report_stats.json`、`outputs/report_table.md`。
- 复算“初版解析器”口径：用 `git show ed733c9:src/observatory/parse.py` + 当前别名，r1_ds 补表前 26/60、mean 0.6533（log 中当时记录的 23/60 使用的是初版别名，现代码不再产生该数）。
- 写 `docs/methodology_report_zh.md`、`docs/methodology_report_en.md`；写作中发现两处手填数字与统计不符（property_developers r2 补表前应为 0.8、payment_networks r2 应为 0.9/0.9），已按 `report_stats.json` 改正。
- 删除 `state.md`（内容已合并进中文 `plan.md`，遵循新全局规则）；更新 README。
**结果**：留出集补表后 44/60（mean 0.7983，median 0.9，std 0.2149），补表前 28/60（mean 0.69）。失败 16 类：hot_pot、dairy、beer、energy_drinks、soy_sauce、processed_meat、insurance、express_delivery、hotel_chains、cosmetics、air_conditioners、drones、supermarkets、tcm、online_healthcare、cigarettes（temperature 1.0 再次拒答）。
**决策 / 假设**：留出集结果不回改品牌表、不进主表（保持其作为评估集的意义）。
**下一步**：用户审阅报告 → 发给 Jia Liu。

#### 2026-10-06 00:06 HKT — Qwen 跨模型验证、解析器 RE/MAX 修复、精简报告 PDF

**背景**：用户要求用 Qwen（“别太贵也别太弱”）做跨模型检验，并要一份精简、像正式 report、带本人署名、不含本地化引用（如 `JIA_LIU_TASK.md`）的 PDF，外加结果 CSV 和 repo 链接。服务于最大目标：用第二个模型在冻结品牌表上检验 Category 名称是否真的被 AI 正确理解。
**操作**：
- 选模型：OpenRouter 上 `qwen/qwen3.7-plus`（$0.32/$1.28 每百万 token，Plus 档；Max 档贵 4–5 倍，Flash 档偏弱）。
- 冒烟测试（scratchpad，`OBSERVATORY_RUNS_DIR`）：2 类正常；发现 `score --no-record` 仍会读其他 run 的 meta.json 而报错 → 改为 `--no-record` 时完全跳过 attempts 计算（`scripts/validate.py`）。
- `python3 -u scripts/validate.py query --provider openrouter --model qwen/qwen3.7-plus --temperature 0 --run-id r4_qwen_crossmodel`（60/60 无报错，约 50 秒/类，$0.2214）
- `python3 scripts/validate.py score runs/r4_qwen_crossmodel --no-record` → 首次 31/60。逐条检查失败类的 parsed/extra：发现 real_estate_agencies 中 `RE/MAX` 被“A/B 取前者”规则切成 `RE`（解析器 bug，品牌表本有 RE/MAX）。
- 修复 `src/observatory/parse.py`：全大写 `X/Y`（`[A-Z0-9]+/[A-Z0-9]+`）不拆分；新增测试 `test_slash_takes_first_brand_but_keeps_caps_names`；21 个测试全过。
- 重算全部：`score runs/r1_ds`、`score runs/r2_ds`、`score runs/r3_ds_holdout --no-record`、`score runs/r4_qwen_crossmodel --no-record`、`master`、`report_stats.py r1_ds r2_ds r3_ds_holdout r4_qwen_crossmodel`、`report_tables.py`。
- `scripts/report_tables.py` 新增输出 `outputs/category_results.csv`（逐类各轮分数，含 World/China 计数）与 `outputs/report_appendix.md`（精简报告附录表）。
- 新写精简报告 `docs/report_en.md`、`docs/report_zh.md`（署名 Yunxiang Mo），`scripts/report_pdf.sh`（pandoc → HTML → headless Chrome）生成 `outputs/report_{en,zh}.pdf`（各 5 页）；详细方法报告同步新数字并加 Qwen 行。
**结果**：
- 修复只影响 real_estate_agencies：r1 补表前 25→26/60（mean 0.6883→0.69），补表后仍 56/60（mean 0.875）；留出集补表前 28→29/60，补表后仍 44/60（mean 0.80）；主表仍 60/60、957 行。
- Qwen：补表后 32/60（mean 0.7217，median 0.8），补表前 20/60（mean 0.6233）；12 类得 0.7。与 DeepSeek 留出集：都通过 28、都不通过 12、仅 DeepSeek 16、仅 Qwen 4。
- Qwen 把 Online Shopping Platforms 理解为电商建站软件（0.0），AI Chatbot Apps 部分理解为企业客服工具（0.5）。
**决策 / 假设**：Qwen 结果只作检验，不回改品牌表、不进 attempts；未为 Qwen 的写法变体（如 Chongqing Xiaolongkan）补别名，避免拟合检验集。署名用 “Yunxiang Mo”（由 git 用户名 moyunxiang 推断，假设；待用户确认）。
**下一步**：提交并推送到 https://github.com/moyunxiang/ai-observatory；用户审阅 PDF 后发给 Jia Liu。
**更正**：上一条标为 “2026-10-06 00:40 HKT” 的日志时间戳有误（Qwen 运行开始于 2026-10-05 23:05 HKT，该条实际写于此之前）；原条目保留不改。

#### 2026-10-06 00:07 HKT — 推送到 GitHub

**背景**：用户给出 repo 地址 https://github.com/moyunxiang/ai-observatory（public，原为空仓库）。
**操作**：`git remote add origin https://github.com/moyunxiang/ai-observatory.git`；HTTPS 推送经环境代理报 `Proxy CONNECT aborted`，SSH 无 key（`Permission denied (publickey)`）；最终 `gh auth setup-git` 后去掉代理环境变量推送：`env -u HTTPS_PROXY -u HTTP_PROXY -u ALL_PROXY ... git push -u origin master`。
**结果**：远端 master = a969607，作者均为 moyunxiang <2556377578@qq.com>；推送前核对历史中无 `sk-or-v1`/key，`.env` 未被跟踪。
**下一步**：用户审阅 `outputs/report_en.pdf` / `report_zh.pdf` 后发给 Jia Liu。
