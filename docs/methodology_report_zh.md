# 品牌 Category 发现与 AI 验证 —— Sample 阶段方法与结果报告（中文）

> 生成时间：2026-10-06（HKT）。数据快照：git commit 见文末。所有数字来自 `outputs/report_stats.json`（`python3 scripts/report_stats.py r1_ds r2_ds r3_ds_holdout r4_qwen_crossmodel`）与 `outputs/category_status.csv`。

## 1. 任务与范围

- 依据 `JIA_LIU_TASK.md`：Task 1 从知名品牌反推 Category → Task 2 每类扩充到 ≥10 个真实品牌 → Task 3 用固定问题 `What are the best brands for {category}? List 10 brands.` 验证 Category 名称，Brand Recall@10 ≥ 80% 记为 Pass，不通过则改名重测。
- 本阶段为 **sample**：60 个 B2C Category（最终目标 ≥1000，本次不做）。
- Brand Recall@10 = AI 返回的前 10 个品牌（规范化 + 别名映射 + 去重后）中出现在该类品牌表里的个数 ÷ 10；AI 少于 10 个时缺位计为未命中。
- 验证用 AI：OpenRouter `deepseek/deepseek-v4-pro`，每个 Category 一次独立单轮请求，无 system prompt。

## 2. 方法（how the results were derived）

**Task 1（种子池 → Category）**
1. 种子来源：Kantar BrandZ 2025 Most Valuable Global Brands Top 100 + Most Valuable Chinese Brands Top 100（PDF 原件与 `pdftotext` 结果存于 `data/raw/sources/`，含 SHA256）。
2. 去重（两榜重叠 11 个）后 189 个品牌；每个品牌人工指定一个细粒度标签（raw_label）和主 Category；同义/近义标签合并（30 条合并记录，`data/category_merges.csv`）。
3. B2B 品牌（如 Microsoft、SAP、NVIDIA、Aramco）也已归类，但其 6 个 Category 标为 `out_of_scope`，不进入 Task 2/3（项目面向消费品类）。

**Task 2（扩充品牌表）**
1. 每个 B2C Category 查阅公开榜单页面（Wikipedia 列表、Brand Finance、FashionUnited、行业统计页等），每个页面及其上的品牌名记录在 `data/raw/task2/evidence.jsonl`（method=webfetch 表示直接读取页面；websearch 表示依据搜索结果摘要，证据较弱）。
2. 人工挑选“真实、明确属于该品类”的品牌（`scripts/build_category_brands.py` 中的 SELECTION），脚本自动为每个品牌匹配证据 URL，找不到证据则构建失败；种子品牌必须出现在其主 Category 的表中。
3. 品牌名匹配：规范化（大小写、重音、标点、&/and、结尾 Inc/Ltd/Group/.com 等）+ 全局别名表 + 类别内别名表（类别内优先，例如 game_consoles 中 Sony→PlayStation）。

**Task 3（AI 验证、改名与补表）**
1. r1_ds：60 类，temperature 0。逐类检查 AI 的 `extra`（不在表里的品牌）并归因：解析器错误 / 别名缺口 / 品牌表缺口 / 类别名被误解。
2. 解析器与别名修复后，对**同一批原始回答**重新打分（不重新调用 AI）。
3. 品牌表缺口：把 extra 中疑似真实同品类品牌列为候选（135 个），用 Wikipedia REST API 抓取摘要（`scripts/verify_candidates.py`，原始返回存档），严格规则：摘要必须直接说明该品牌属于该品类；Wikipedia 无页面的 7 个用网页搜索确认。采纳的品牌标记 `origin=added_post_validation`，并单独计算“补表前 recall”。
4. 类别名被误解的 5 类改名后重测（r2_ds）。
5. 留出集 r3_ds_holdout：品牌表冻结后，用 temperature 1.0 对 60 个最终名称重新采样；结果**只用于评估，不回改品牌表，不计入主表**。

## 3. 一级结论（First-order results）

### 3.1 Task 1 / Task 2 规模

| 指标 | 数值 |
|---|---|
| 种子品牌数（去重后） | 189（World 88 / China 101） |
| Category 总数 | 66（B2C 60 / out_of_scope 6） |
| 标签合并记录 | 30 |
| 未归类种子品牌 | 0 |
| 品牌表总行数（60 个 B2C 类） | 957 |
| 来源：seed / expanded / added_post_validation | 163 / 675 / 119 |
| 证据类型：webfetch / websearch / wikipedia_summary / kantar_seed / cross_category | 360 / 448 / 112 / 31 / 6 |
| World / China 行数 | 720 / 237 |
| 每类品牌数 min / median / max | 10 / 16 / 29 |
| 补表候选 / 采纳 | 135 / 119 |

#### Column Definitions
- **指标**：Definition 统计项名称；Source 见各值。
- **数值**：Definition 对应统计值；Computation `scripts/report_stats.py` 的 `task1` / `task2` 字段；Unit 个/行；Source `data/seed_brands.csv`、`data/categories.csv`、`data/category_merges.csv`、`data/category_brands.csv`、`data/raw/task2/post_validation_decisions.csv`。World/China 为人工标注（规则：总部在中国大陆/香港/澳门 = China，其余 = World），非直接观测。websearch 证据来自搜索摘要，强度低于 webfetch。不确定性：not computed。

### 3.2 Task 3 各轮结果

| 轮次 | 模型 / temperature | 类别数 | 口径 | Pass | Pass rate | Mean | Median | Std | Min | Max | 成本 USD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| r1_ds 首次打分（初版解析器与别名） | deepseek-v4-pro / 0 | 60 | 初始品牌表 | 23 | 0.383 | 0.6283 | not computed | not computed | not computed | not computed | 0.0617 |
| r1_ds（修复解析器/别名后） | deepseek-v4-pro / 0 | 60 | 补表前 | 26 | 0.4333 | 0.69 | 0.7 | 0.2226 | 0.0 | 1.0 | 同上 |
| r1_ds（修复后） | deepseek-v4-pro / 0 | 60 | 补表后 | 56 | 0.9333 | 0.875 | 0.9 | 0.1997 | 0.0 | 1.0 | 同上 |
| r2_ds（5 个改名类） | deepseek-v4-pro / 0 | 5 | 补表前 | 4 | 0.8 | 0.78 | 0.8 | 0.098 | 0.6 | 0.9 | 0.0085 |
| r2_ds（5 个改名类） | deepseek-v4-pro / 0 | 5 | 补表后 | 5 | 1.0 | 0.96 | 1.0 | 0.049 | 0.9 | 1.0 | 同上 |
| 最终（每类最近一次尝试） | — | 60 | 补表后 | 60 | 1.0 | — | — | — | — | — | — |
| r3_ds_holdout（留出集） | deepseek-v4-pro / 1.0 | 60 | 补表前 | 29 | 0.4833 | 0.6917 | 0.7 | 0.2465 | 0.0 | 1.0 | 0.043 |
| r3_ds_holdout（留出集） | deepseek-v4-pro / 1.0 | 60 | 补表后（冻结表） | 44 | 0.7333 | 0.8 | 0.9 | 0.2153 | 0.0 | 1.0 | 同上 |
| r4_qwen_crossmodel（跨模型） | qwen3.7-plus / 0 | 60 | 补表前 | 20 | 0.3333 | 0.6233 | 0.6 | 0.2298 | 0.0 | 1.0 | 0.2214 |
| r4_qwen_crossmodel（跨模型） | qwen3.7-plus / 0 | 60 | 补表后（冻结表） | 32 | 0.5333 | 0.7217 | 0.8 | 0.205 | 0.0 | 1.0 | 同上 |

#### Column Definitions
- **轮次**：run_id，对应 `runs/<run_id>/`。
- **模型 / temperature**：OpenRouter 模型 id 与采样温度（`runs/<id>/meta.json`）。
- **类别数**：该轮被打分的 Category 数。
- **口径**：“补表前”= 只用 origin ∈ {seed, expanded} 的品牌表；“补表后”= 含 added_post_validation。
- **Pass**：Recall@10 ≥ 0.8 的类别数。**Pass rate** = Pass / 类别数。
- **Mean / Median / Std / Min / Max**：各类 Recall@10 的统计（Std 为总体标准差）；单位 0–1。
- **成本 USD**：OpenRouter 返回的 usage.cost 之和。
- **Source**：`outputs/report_stats.json`（由原始回答 `runs/*/responses.jsonl` 用当前代码重算）。例外：第一行“首次打分”取自当时的 `log.md` 记录（初版解析器与初版别名），当前代码不再产生该数字；用 commit ed733c9 的旧解析器 + 当前别名复算为 26/60、mean 0.6533。
- 不确定性：每类只采样 1 次，未计算 CI / seed variance（not computed）；r1 与 r3 的差异同时混合了采样温度与随机性。

### 3.3 改名记录（category_id 不变，算同一个 Category 的第 2 次尝试）

| category_id | 原名称（r1） | r1 现象 | 新名称（r2） | r2 Recall（补表前 / 补表后） |
|---|---|---|---|---|
| property_developers | Real Estate Developers | 返回高端建材/家电品牌（Sub-Zero、Miele…），r1=0.0 | Chinese Real Estate Developers | 0.8 / 0.9 |
| payment_networks | Credit Card Networks | 混入发卡行与联名卡（Chase、Capital One、Delta SkyMiles），0.4 | Payment Card Networks | 0.9 / 0.9 |
| home_improvement | Home Improvement Stores | 后 5 个为工具/油漆品牌（DeWalt、Benjamin Moore），0.5 | Home Improvement Retail Chains | 0.8 / 1.0 |
| ai_chatbots | AI Chatbots | 返回公司名（OpenAI、Anthropic、xAI） | AI Chatbot Apps | 仍返回公司名；加类别别名后 0.8 / 1.0（加别名后 r1 原名也已达 0.9，改名本身非必要） |
| cigarettes | Cigarettes | 拒答，0.0 | Cigarette Brands | 0.6 / 1.0（但留出集 temperature 1.0 再次拒答） |

#### Column Definitions
- **category_id**：类别主键（`data/categories.csv`）。**原名称 / 新名称**：被测的 `{category}` 文本。
- **r1 现象**：对 `runs/r1_ds/results.csv` 中 parsed/extra 的人工归纳（非自动指标）；数字为修复解析器后的 r1 Recall（补表前）。
- **r2 Recall**：`runs/r2_ds` 的 Recall@10，补表前 / 补表后。Source：`outputs/report_stats.json`。
- ai_chatbots 的公司→产品别名（OpenAI→ChatGPT 等）属于人工判断，非直接观测。

### 3.4 逐类结果（60 类）

| # | category_id | r1 name | final name | brands (added) | r1 pre | r1 with | r2 pre | r2 with | final | holdout pre | holdout with | qwen pre | qwen with |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | smartphones | Smartphones | Smartphones | 14 (3) | 0.7 | 1.0 | – | – | Pass | 0.6 | 0.8 | 0.7 | 0.9 |
| 2 | search_engines | Search Engines | Search Engines | 12 (0) | 1.0 | 1.0 | – | – | Pass | 0.9 | 0.9 | 0.9 | 0.9 |
| 3 | social_media | Social Media Platforms | Social Media Platforms | 17 (0) | 0.9 | 0.9 | – | – | Pass | 1.0 | 1.0 | 0.8 | 0.8 |
| 4 | short_video | Short Video Apps | Short Video Apps | 15 (2) | 0.7 | 0.9 | – | – | Pass | 0.8 | 0.9 | 0.9 | 1.0 |
| 5 | video_streaming | Video Streaming Services | Video Streaming Services | 16 (0) | 1.0 | 1.0 | – | – | Pass | 1.0 | 1.0 | 0.9 | 0.9 |
| 6 | music_streaming | Music Streaming Services | Music Streaming Services | 14 (4) | 0.6 | 1.0 | – | – | Pass | 0.6 | 1.0 | 0.6 | 0.9 |
| 7 | ecommerce | Online Shopping Platforms | Online Shopping Platforms | 16 (5) | 0.4 | 0.9 | – | – | Pass | 0.7 | 0.8 | 0.0 | 0.0 |
| 8 | fast_food | Fast Food Chains | Fast Food Chains | 18 (3) | 0.7 | 1.0 | – | – | Pass | 0.9 | 1.0 | 0.8 | 0.9 |
| 9 | coffee_chains | Coffee Chains | Coffee Chains | 17 (3) | 0.7 | 1.0 | – | – | Pass | 0.6 | 0.9 | 0.6 | 0.7 |
| 10 | bubble_tea | Bubble Tea Chains | Bubble Tea Chains | 18 (2) | 0.7 | 0.9 | – | – | Pass | 0.8 | 0.9 | 0.7 | 0.7 |
| 11 | hot_pot | Hot Pot Restaurant Chains | Hot Pot Restaurant Chains | 13 (3) | 0.7 | 1.0 | – | – | Pass | 0.6 | 0.7 | 0.4 | 0.5 |
| 12 | soft_drinks | Soft Drinks | Soft Drinks | 14 (3) | 0.7 | 1.0 | – | – | Pass | 0.7 | 0.9 | 0.6 | 0.9 |
| 13 | bottled_water | Bottled Water | Bottled Water | 20 (3) | 0.5 | 0.8 | – | – | Pass | 0.7 | 0.9 | 0.5 | 0.7 |
| 14 | dairy | Dairy Products | Dairy Products | 15 (2) | 0.7 | 0.9 | – | – | Pass | 0.0 | 0.2 | 0.1 | 0.3 |
| 15 | baijiu | Baijiu | Baijiu | 17 (0) | 0.9 | 0.9 | – | – | Pass | 0.9 | 0.9 | 0.9 | 0.9 |
| 16 | beer | Beer | Beer | 23 (9) | 0.1 | 1.0 | – | – | Pass | 0.2 | 0.6 | 0.1 | 0.6 |
| 17 | energy_drinks | Energy Drinks | Energy Drinks | 18 (3) | 0.5 | 0.8 | – | – | Pass | 0.4 | 0.7 | 0.3 | 0.5 |
| 18 | soy_sauce | Soy Sauce | Soy Sauce | 17 (4) | 0.6 | 1.0 | – | – | Pass | 0.1 | 0.2 | 0.5 | 0.9 |
| 19 | processed_meat | Processed Meat Products | Processed Meat Products | 16 (4) | 0.6 | 1.0 | – | – | Pass | 0.2 | 0.3 | 0.4 | 0.6 |
| 20 | banks | Banks | Banks | 29 (0) | 1.0 | 1.0 | – | – | Pass | 1.0 | 1.0 | 0.4 | 0.4 |
| 21 | payment_networks | Credit Card Networks | Payment Card Networks | 11 (0) | 0.4 | 0.4 | 0.9 | 0.9 | Pass | 0.9 | 0.9 | 0.9 | 0.9 |
| 22 | digital_payments | Digital Payment Services | Digital Payment Services | 12 (0) | 0.9 | 0.9 | – | – | Pass | 0.9 | 0.9 | 0.6 | 0.6 |
| 23 | insurance | Insurance Companies | Insurance Companies | 21 (0) | 0.8 | 0.8 | – | – | Pass | 0.7 | 0.7 | 0.4 | 0.4 |
| 24 | health_insurance | Health Insurance | Health Insurance | 11 (0) | 0.8 | 0.8 | – | – | Pass | 0.8 | 0.8 | 0.8 | 0.8 |
| 25 | mobile_carriers | Mobile Carriers | Mobile Carriers | 21 (0) | 1.0 | 1.0 | – | – | Pass | 0.9 | 0.9 | 0.3 | 0.3 |
| 26 | isps | Internet Service Providers | Internet Service Providers | 12 (0) | 0.8 | 0.8 | – | – | Pass | 0.9 | 0.9 | 1.0 | 1.0 |
| 27 | airlines | Airlines | Airlines | 24 (0) | 0.9 | 0.9 | – | – | Pass | 1.0 | 1.0 | 0.9 | 0.9 |
| 28 | express_delivery | Express Delivery Services | Express Delivery Services | 17 (2) | 0.8 | 1.0 | – | – | Pass | 0.6 | 0.7 | 0.7 | 0.9 |
| 29 | food_delivery | Food Delivery Platforms | Food Delivery Platforms | 14 (0) | 0.8 | 0.8 | – | – | Pass | 0.9 | 0.9 | 0.8 | 0.8 |
| 30 | ride_hailing | Ride-Hailing Apps | Ride-Hailing Apps | 10 (0) | 0.9 | 0.9 | – | – | Pass | 0.9 | 0.9 | 0.8 | 0.8 |
| 31 | online_travel | Online Travel Agencies | Online Travel Agencies | 17 (3) | 0.7 | 1.0 | – | – | Pass | 0.8 | 0.9 | 0.7 | 0.7 |
| 32 | hotel_chains | Hotel Chains | Hotel Chains | 22 (3) | 0.7 | 1.0 | – | – | Pass | 0.5 | 0.5 | 0.4 | 0.4 |
| 33 | restaurant_reviews | Restaurant Review Platforms | Restaurant Review Platforms | 12 (0) | 0.9 | 0.9 | – | – | Pass | 1.0 | 1.0 | 0.8 | 0.8 |
| 34 | real_estate_agencies | Real Estate Agencies | Real Estate Agencies | 15 (2) | 0.8 | 1.0 | – | – | Pass | 0.8 | 0.9 | 0.7 | 0.8 |
| 35 | property_developers | Real Estate Developers | Chinese Real Estate Developers | 12 (1) | 0.0 | 0.0 | 0.8 | 0.9 | Pass | 0.7 | 0.8 | 0.6 | 0.7 |
| 36 | electric_vehicles | Electric Vehicles | Electric Vehicles | 19 (0) | 1.0 | 1.0 | – | – | Pass | 0.9 | 0.9 | 0.9 | 0.9 |
| 37 | cars | Cars | Cars | 16 (0) | 0.9 | 0.9 | – | – | Pass | 0.8 | 0.8 | 0.7 | 0.7 |
| 38 | luxury_fashion | Luxury Fashion | Luxury Fashion | 17 (3) | 0.7 | 1.0 | – | – | Pass | 0.7 | 1.0 | 0.6 | 0.7 |
| 39 | sportswear | Sportswear | Sportswear | 14 (4) | 0.6 | 1.0 | – | – | Pass | 0.7 | 0.8 | 0.6 | 0.8 |
| 40 | fast_fashion | Fast Fashion | Fast Fashion | 13 (0) | 0.9 | 0.9 | – | – | Pass | 1.0 | 1.0 | 0.8 | 0.8 |
| 41 | cosmetics | Cosmetics | Cosmetics | 18 (0) | 0.9 | 0.9 | – | – | Pass | 0.5 | 0.5 | 0.6 | 0.6 |
| 42 | jewelry | Jewelry | Jewelry | 19 (6) | 0.4 | 1.0 | – | – | Pass | 0.4 | 1.0 | 0.4 | 0.8 |
| 43 | home_appliances | Home Appliances | Home Appliances | 19 (4) | 0.6 | 1.0 | – | – | Pass | 0.5 | 0.8 | 0.6 | 0.7 |
| 44 | air_conditioners | Air Conditioners | Air Conditioners | 13 (2) | 0.7 | 0.9 | – | – | Pass | 0.6 | 0.7 | 0.7 | 0.8 |
| 45 | televisions | TVs | TVs | 10 (0) | 0.8 | 0.8 | – | – | Pass | 0.9 | 0.9 | 0.8 | 0.8 |
| 46 | laptops | Laptops | Laptops | 11 (0) | 0.8 | 0.8 | – | – | Pass | 0.9 | 0.9 | 0.9 | 0.9 |
| 47 | drones | Drones | Drones | 12 (0) | 0.8 | 0.8 | – | – | Pass | 0.5 | 0.5 | 0.7 | 0.7 |
| 48 | game_consoles | Video Game Consoles | Video Game Consoles | 16 (4) | 0.6 | 1.0 | – | – | Pass | 0.6 | 1.0 | 0.6 | 0.8 |
| 49 | consumer_electronics | Consumer Electronics | Consumer Electronics | 15 (4) | 0.6 | 1.0 | – | – | Pass | 0.7 | 0.8 | 0.5 | 0.7 |
| 50 | ai_chatbots | AI Chatbots | AI Chatbot Apps | 15 (2) | 0.8 | 0.9 | 0.8 | 1.0 | Pass | 0.8 | 0.9 | 0.3 | 0.5 |
| 51 | supermarkets | Supermarket Chains | Supermarket Chains | 16 (2) | 0.7 | 0.9 | – | – | Pass | 0.7 | 0.7 | 0.6 | 0.7 |
| 52 | home_improvement | Home Improvement Stores | Home Improvement Retail Chains | 15 (2) | 0.5 | 0.5 | 0.8 | 1.0 | Pass | 0.9 | 1.0 | 0.7 | 0.7 |
| 53 | furniture | Furniture Stores | Furniture Stores | 13 (3) | 0.5 | 0.8 | – | – | Pass | 0.7 | 1.0 | 0.6 | 0.8 |
| 54 | tcm | Traditional Chinese Medicine | Traditional Chinese Medicine | 12 (2) | 0.6 | 0.8 | – | – | Pass | 0.5 | 0.6 | 0.2 | 0.2 |
| 55 | online_healthcare | Online Healthcare Platforms | Online Healthcare Platforms | 18 (5) | 0.3 | 0.8 | – | – | Pass | 0.5 | 0.6 | 0.4 | 0.6 |
| 56 | job_platforms | Job Search Platforms | Job Search Platforms | 15 (0) | 0.8 | 0.8 | – | – | Pass | 0.8 | 0.8 | 0.9 | 0.9 |
| 57 | news_apps | News Apps | News Apps | 17 (3) | 0.7 | 1.0 | – | – | Pass | 0.8 | 0.9 | 0.4 | 0.6 |
| 58 | video_games | Video Game Companies | Video Game Companies | 24 (5) | 0.5 | 1.0 | – | – | Pass | 0.3 | 0.8 | 0.9 | 1.0 |
| 59 | movie_studios | Movie Studios | Movie Studios | 16 (0) | 0.8 | 0.8 | – | – | Pass | 0.8 | 0.8 | 0.9 | 0.9 |
| 60 | cigarettes | Cigarettes | Cigarette Brands | 14 (4) | 0.0 | 0.0 | 0.6 | 1.0 | Pass | 0.0 | 0.0 | 0.6 | 0.9 |

#### Column Definitions
- **#**：序号。**category_id**：类别主键。
- **r1 name / final name**：r1 时的名称 / 最终通过验证的名称（`outputs/category_status.csv`）。
- **brands (added)**：该类品牌表总数（括号内为 added_post_validation 数）。Source `data/category_brands.csv`。
- **r1 pre / r1 with**：r1_ds 的 Recall@10，补表前 / 补表后（0–1）。
- **r2 pre / r2 with**：r2_ds（仅改名类），“–”表示该类未参加 r2。
- **final**：每类最近一次尝试（按 run 启动时间）的结果，进入主表的依据。
- **holdout pre / holdout with**：r3_ds_holdout（temperature 1.0，品牌表冻结）的 Recall@10。
- **qwen pre / qwen with**：r4_qwen_crossmodel（`qwen/qwen3.7-plus`，temperature 0，品牌表冻结）的 Recall@10。
- Computation：`scripts/report_stats.py` → `scripts/report_tables.py`。单次采样，无 CI（not computed）。

### 3.5 留出集失败类别（16 个，补表后 Recall < 0.8）

hot_pot 0.7、dairy 0.2、beer 0.6、energy_drinks 0.7、soy_sauce 0.2、processed_meat 0.3、insurance 0.7、express_delivery 0.7、hotel_chains 0.5、cosmetics 0.5、air_conditioners 0.7、drones 0.5、supermarkets 0.7、tcm 0.6、online_healthcare 0.6、cigarettes 0.0（拒答）。
观察到的 extra 类型（来自 `runs/r3_ds_holdout/results.csv`）：
- 已有品牌的新写法：如 `Fenty Beauty by Rihanna`、`Dior Beauty`、`Sempio 501`、`Higeta Honzen`、`USPS Priority Mail Express`、`Liuyishou Hotpot`。
- 新的长尾品牌：如 dairy 中 Chobani、Cabot、Straus；processed_meat 中 Nueske's、Spam、Herta；soy_sauce 中 Yamaroku、Bragg Liquid Aminos；hotel_chains 中 Aman、Rosewood、Six Senses。
- 拒答：cigarettes。

### 3.6 交付主表

`outputs/master_table.csv`：60 个 Category、957 行（Category | Brand | World/China | Category验证结果），仅包含最终 Pass 的类别。示例：

| Category | Brand | World/China | Category验证结果 |
|---|---|---|---|
| Smartphones | Apple | World | Pass |
| Smartphones | Xiaomi | China | Pass |
| Smartphones | Huawei | China | Pass |
| Baijiu | Moutai | China | Pass |
| Baijiu | Wuliangye | China | Pass |
| Chinese Real Estate Developers | Vanke | China | Pass |

#### Column Definitions
- **Category**：最终通过验证的类别名称。**Brand**：品牌名（表中规范写法）。**World/China**：人工标注（规则见 3.1）。**Category验证结果**：该类最终尝试的结果（全部为 Pass）。Source `outputs/master_table.csv`。

## 4. Key Findings（二级结论，已标注性质）

- **Candidate finding**：第一轮失败的主要原因不是类别名，而是品牌表覆盖不足与匹配问题（修复解析器/别名后补表前仅 26/60，补表后 56/60；真正需要改名的只有 5 类）。
- **Candidate finding**：补表在留出集上同样有效（留出集补表前 29/60 → 补表后 44/60），说明补进的品牌不只是迎合 r1 的单次回答；但留出集通过率（44/60）明显低于 r1（56/60），说明 r1 上的通过率偏乐观。
- **Candidate finding**：跨模型（Qwen 3.7 Plus，冻结表）补表后 32/60、补表前 20/60；另有 12 类为 0.7。与 DeepSeek 留出集对照：两者都通过 28 类、都不通过 12 类、仅 DeepSeek 通过 16 类、仅 Qwen 通过 4 类（soy_sauce、express_delivery、air_conditioners、cigarettes）。
- **Observation**：Qwen 把 "Online Shopping Platforms" 理解为电商建站软件（Shopify、WooCommerce，Recall 0.0），把 "AI Chatbot Apps" 部分理解为企业客服机器人工具（Intercom、ManyChat，0.5）——单模型未暴露的命名歧义。
- **Interpretation**：泛化型食品类（Dairy Products、Soy Sauce、Processed Meat Products）在留出集上 Recall 只有 0.2–0.3，可能是类别名过宽，AI 每次采样会给出不同的长尾/手工品牌；这类类别可能需要更窄的命名（例如按子品类或地区）。需进一步验证。
- **Interpretation**：DeepSeek 的回答明显偏美国市场（Health Insurance、Supermarkets、Furniture 等），对“World/China”平衡有影响。
- **Observation**：Cigarettes 类在 temperature 0 改名后可回答，但 temperature 1.0 下再次拒答，结果不稳定。

## 5. 局限

- 主验证只用 DeepSeek，Qwen 仅作为一次冻结表的交叉检验；每类单次采样；r1/r3 差异未分离温度与随机性。
- 补表候选来自同一模型的回答（虽有独立证据门槛），存在偏向该模型的风险；已用“补表前”口径与留出集对照。
- 448 行证据来自搜索结果摘要（websearch），强度低于直接读页；部分核实搜索在查询中包含候选品牌名。
- “看到答案后”添加了别名（均为同一品牌的写法变体，另有 ai_chatbots 公司→产品的判断性别名），可能使 recall 偏高。
- World/China 标签与“明确属于该品类”的判断为人工判断。

## 6. Follow-up Analysis Needed

- 已完成 Qwen 交叉验证；后续可加 GPT/Claude，并每类多次采样以给出方差/CI。
- 对留出集失败的 16 类：区分“写法变体”与“真正缺失品牌”，或改为更窄的类别名后再测（新 run，不回改冻结表）。
- 扩展到 1000 类：扩大种子池（Kantar 各行业榜、Brand Finance 行业榜、电商类目树），Task 2 自动化候选生成 + 人工抽检。

## 7. 复现

```bash
python3 -m unittest discover -s tests
python3 scripts/build_category_brands.py && python3 scripts/validate.py check
python3 scripts/validate.py score runs/r1_ds && python3 scripts/validate.py score runs/r2_ds
python3 scripts/validate.py score runs/r3_ds_holdout --no-record
python3 scripts/validate.py master
python3 scripts/validate.py score runs/r4_qwen_crossmodel --no-record
python3 scripts/report_stats.py r1_ds r2_ds r3_ds_holdout r4_qwen_crossmodel > outputs/report_stats.json
python3 scripts/report_tables.py > outputs/report_table.md
```
