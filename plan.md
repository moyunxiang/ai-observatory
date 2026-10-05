# 项目计划

> 最后更新：2026-10-06 00:06 HKT
> 本文件是新 Claude session 的首要上下文（原 `state.md` 已合并进来）。说明性内容使用中文。

## 1. 最大目标

为 AI Observatory 构建一张 **Category → 品牌** 主表：**≥1000 个**通过 AI 验证、互不重复的消费品/服务 Category，每个至少 10 个真实、明确属于该品类的品牌（标注 World/China），且 Category 名称符合真实用户/AI 搜索语义——用固定问题 `What are the best brands for {category}? List 10 brands.` 提问时，AI 返回的 Top 10 中至少 8 个在品牌表里（Brand Recall@10 ≥ 0.8）。

### 成功标准
- 最终表 ≥1000 个独立 Category，全部 Pass，无同义重复。
- 每一行可追溯：品牌来源 URL、AI 原始回答、解析结果、命中列表。

### 当前阶段的定位
- Jia Liu 要求本阶段**不交完整结果**，只交 **sample results + 方法说明（how you derive these results）**，用于评估是否参与后续项目（预期约一周）。本仓库当前就是这个 sample 阶段（60 个 Category）。

## 2. 当前状态

- Task 1 完成：189 个种子品牌（Kantar BrandZ 2025 Global/China Top 100）→ 66 个 Category（60 B2C + 6 out_of_scope），未归类 = 0。
- Task 2 完成：`data/category_brands.csv` 957 行（838 初始 + 119 验证后补充），每类 ≥10，均有来源。
- Task 3：OpenRouter `deepseek/deepseek-v4-pro`，temperature 0。
  - r1_ds（60 类）→ 修解析器/别名/补表后 56/60；r2_ds（5 个改名类）5/5；主表 60/60 Pass（`outputs/master_table.csv`）。
  - 留出集 r3_ds_holdout（temperature 1.0，品牌表冻结于 commit 84efd4f）：补表后 44/60（mean 0.80），补表前 29/60（mean 0.6917）。
  - 跨模型 r4_qwen_crossmodel（`qwen/qwen3.7-plus`，temperature 0，冻结表，$0.2214）：补表后 32/60（mean 0.7217），补表前 20/60；另 12 类为 0.7。与留出集都通过 28 类、都不通过 12 类。
- 解析器修复（2026-10-06）：`RE/MAX` 这类全大写斜杠名不再被切成 `RE`；只影响 real_estate_agencies（r1 补表前 25→26/60，留出集补表前 28→29/60，补表后通过数不变）。
- 交付材料：精简报告 `outputs/report_{en,zh}.pdf`（源 `docs/report_{en,zh}.md`，署名 Yunxiang Mo，`sh scripts/report_pdf.sh` 生成）；详细方法报告 `docs/methodology_report_{zh,en}.md`；逐类结果 `outputs/category_results.csv`；主表 `outputs/master_table.csv`。
- 仓库已推送至 https://github.com/moyunxiang/ai-observatory（public）。

## 3. 当前阶段目标

把 sample 结果整理成可交付材料，并诚实呈现“补表前 / 补表后 / 留出集”三种口径，让 Jia Liu 能判断方法是否可扩展到 1000 类。这是通往最大目标的必要一步：先证明流程可复现、可追溯，再谈规模化。

## 4. 当前任务

### P0
- [x] 打分留出集（完成：44/60）
- [x] 中英文方法报告（完成）
- [x] Qwen 跨模型验证（完成：32/60）
- [ ] 用户审阅精简报告 PDF → 发给 Jia Liu（附 `outputs/master_table.csv`、`outputs/category_results.csv`、repo 链接）
  - 服务于最大目标：本阶段交付物就是方法说明 + 样例结果，决定是否进入 1000 类阶段。
### P1
- [ ] 留出集失败的 16 类：区分写法变体 vs 真缺失，或换更窄名称新 run 重测（不得改冻结表后再拿 r3 当留出集）
- [ ] 用户抽查品牌表（尤其 source_method=websearch 的行）
### P2
- [ ] 扩展到 1000 类的方案：更大的种子池（Kantar 类目榜、Brand Finance 各行业榜、电商类目树）、自动化 Task 2、多模型交叉验证

## 5. 里程碑

- Phase 1 代码改造（完成）→ Phase 2 Task 1（完成）→ Phase 3 Task 2（完成）→ Phase 4 Task 3 第一轮（完成）→ Phase 5 改名/补表（完成）→ **Phase 6 留出验证 + 报告（进行中）**

## 6. 已确认结论

- F0：指标 = |AI top10 ∩ 品牌表| / 10（分母固定 10），≥0.8 Pass。旧口径（分母=参考集大小）已废弃。
- F1：r1_ds 首次打分（旧解析器）23/60，mean 0.6283；失败主因依次为解析器 bug、品牌表不全、别名缺口，真正的类别名问题只有 5 个。
- F2：改名对 4/5 个“误解型”失败有效（payment_networks、property_developers、home_improvement、cigarettes）；ai_chatbots 改名无效，靠公司→产品别名解决。
- F3：Cigarettes 原名被 DeepSeek 拒答，改为 Cigarette Brands 后正常回答。
- F4：DeepSeek 回答明显偏美国市场（如 Health Insurance、Supermarkets、Furniture）。
- F5：留出集补表前 29/60 → 补表后 44/60：补表在新采样上仍有效，但 r1 的 56/60 偏乐观。
- F6：Dairy / Soy Sauce / Processed Meat 留出集仅 0.2–0.3；Cigarette Brands 在 temperature 1.0 再次拒答。
- F7：Qwen 把 "Online Shopping Platforms" 理解为电商建站软件（Shopify 等，0.0），"AI Chatbot Apps" 部分理解为企业客服机器人工具（0.5）——单模型未暴露的命名歧义。
- F8：两模型都不通过的 12 类：hot_pot、dairy、beer、energy_drinks、processed_meat、insurance、hotel_chains、cosmetics、drones、supermarkets、tcm、online_healthcare（多为宽泛品类，AI 给出表外长尾品牌）。

## 7. 未解决问题 / 阻塞项

- Q1：B2C-only 范围是否被接受（B2B 种子已归类但不验证）？
- Q2：World/China 规则（大陆/港澳=China，台湾=World）是否可接受？
- Q3：补表是否算“迎合 AI”？由留出集结果回答。
- Q4：已做 Qwen 交叉检验；是否把“≥2 个模型通过”作为正式通过标准？（会显著降低通过数）

## 8. 关键文件

- `JIA_LIU_TASK.md`：原始任务要求
- `data/seed_brands.csv`、`data/categories.csv`、`data/category_merges.csv`：Task 1
- `scripts/build_category_brands.py`（人工 SELECTION + 自动挂来源）→ `data/category_brands.csv`：Task 2
- `data/brand_aliases.json`（全局）、`data/category_aliases.json`（类别内，优先）
- `scripts/verify_candidates.py`：补表候选的 Wikipedia 核实
- `scripts/validate.py`：check / export / import / query / score / master
- `src/observatory/`：normalize / metrics / parse / manual / data / llm（openrouter）
- `scripts/report_stats.py` → `scripts/report_tables.py` → `scripts/report_pdf.sh`：报告数字、逐类表/CSV、PDF

## 9. 运行与验证

```bash
python3 -m unittest discover -s tests
python3 scripts/build_category_brands.py && python3 scripts/validate.py check
python3 -u scripts/validate.py query --provider openrouter --model deepseek/deepseek-v4-pro --temperature 0 --run-id <id> [--only ...]
python3 scripts/validate.py score runs/<id> [--no-record]
python3 scripts/validate.py master
```
API key：`.env` 中 `OPENROUTER_API_KEY`（已 gitignore，勿打印/提交）。

## 10. 数据与产物位置

- `data/raw/sources/`：Kantar PDF + txt + SHA256SUMS（原始，不改）
- `data/raw/task2/evidence.jsonl`：Task 2 网页证据；`wiki_verification.jsonl`：补表核实原始返回；`post_validation_candidates.csv` / `post_validation_decisions.csv`：候选与人工判定
- `runs/<id>/responses.jsonl`：AI 原始回答（不可覆盖）；`results.csv` / `summary.json`：派生
- `data/category_attempts.csv`：每类每次尝试（同 run 重打分会替换该 run 的行）
- `outputs/master_table.csv`、`outputs/category_status.csv`

## 11. 非目标 / 边界

- 本阶段不扩到 1000 类；不做 B2B 类别；Qwen 只作为冻结表检验，不回改品牌表。

## 12. 废弃路线 / 不要回退

- 20 个预设类别 + 恰好 10 个参考品牌 + 分母=参考集：已按任务要求替换。
- 旧 prompt（"best-known and most representative ... exactly 10"）：已换成任务固定问题。
- `state.md`：已合并进本文件（全局规则改为 plan.md + log.md）。
- 手动 ChatGPT 流程（`runs/r1/manual_sheet.txt`）：保留代码与文件，但已改用 API。

## 13. 当前假设

- A1：对同一批原始回答修解析器/别名后重打分是合法的。验证：报告中列出所有事后别名。
- A2：补表只采纳有独立证据且“摘要直接说明属于该品类”的品牌。验证：`post_validation_decisions.csv` 可逐条复核。
- A3：temperature 1.0 的同模型重采样可作为留出集。局限：不是跨模型验证。

## 14. 验收标准

- `check` 通过；每行有 source_url；测试全过。
- 报告的每个数字可从 `summary.json` / `category_attempts.csv` / `results.csv` 复算；未计算的写 `not computed`。

## 15. 风险

- 补表过拟合 → 报告补表前 recall + 留出集。
- 单模型偏差（美国中心）→ 在报告中如实说明；后续可多模型。
- websearch 证据较弱 → 用户抽查。

## 16. 回滚策略

- git 历史：1e004de 骨架 → 303f31d 代码 → 29daba6 Task 1 → 1f4854e Task 2 → ed733c9 手动表 → 84efd4f Task 3 → d67688a 留出集与报告 → （本次）Qwen 跨模型与精简报告。`runs/` 只追加。

## 17. 输出物

- `outputs/master_table.csv`（Category | Brand | World/China | Category验证结果）
- `outputs/category_status.csv`
- `outputs/report_en.pdf`、`outputs/report_zh.pdf`（精简报告，对外）
- `outputs/category_results.csv`（逐类各轮分数）
- `docs/methodology_report_zh.md`、`docs/methodology_report_en.md`（详细）、`outputs/report_stats.json`、`outputs/report_table.md`

## 18. 交接说明

当前 P0：用户审阅精简报告 PDF 后发给 Jia Liu。不要伪造任何 AI 回答或结果；r3_ds_holdout 和 r4_qwen_crossmodel 都已被看过，若后续用它们的 extra 改表或改名，必须另跑新的留出/跨模型检验。
