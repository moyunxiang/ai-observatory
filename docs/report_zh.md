---
title: "品牌 Category 发现与 AI 验证"
subtitle: "样例结果与方法说明"
author: "Yunxiang Mo"
date: "2026 年 10 月"
---

## 摘要

我从 Kantar BrandZ 2025 世界和中国品牌价值榜各前 100 名出发，建立了 **60 个消费品类、共 957 行**的 Category → Brand 表，并用固定问题 *"What are the best brands for {category}? List 10 brands."* 逐一验证每个品类名称。

- 补全品牌表并为 5 个品类改名后，用 DeepSeek V4 Pro 验证，**60 个品类全部通过**（Brand Recall@10 ≥ 0.8）。
- 部分品牌是看过 DeepSeek 回答后才补进的，因此我冻结品牌表，又做了两项**独立检验**：
  - DeepSeek 在 temperature 1.0 下重新采样：**44/60** 通过。
  - 换用 Qwen 3.7 Plus：**32/60** 通过，另有 12 类得 0.7，只差 1 个品牌。
  - **两项检验都通过的有 28 类。**
- 所有报告轮次的 API 总花费**约 0.34 美元**。

## 方法

**Task 1：品牌 → 品类。** 种子池为 Kantar BrandZ 2025 全球最具价值品牌前 100 名与中国最具价值品牌前 100 名，去重后共 189 个（World 88、China 101）。每个品牌归入一个主品类，并合并同义标签（30 次合并），得到 66 个品类。其中 6 个 B2B 品类（如半导体、企业软件）保留归类但不做验证，因为本项目面向消费者搜索。**未归类种子品牌数为 0。**

**Task 2：扩充品牌。** 对 60 个消费品类，逐类从公开榜单页面（Wikipedia 列表、Brand Finance、行业统计等）补充其他主要品牌，每一行都附来源链接。**每个品类均有 10 个以上品牌**（最少 10，中位数 16，最多 29）。World/China 按总部所在地划分：中国大陆、香港、澳门记为 China。

**Task 3：AI 验证。** 通过 OpenRouter 对每个品类单独提问一次（全新单轮请求）。把回答解析成品牌列表，按下式计分：

> **Brand Recall@10 = AI 给出的前 10 个品牌中出现在该品类品牌表里的个数 ÷ 10**，≥ 0.8 记为通过。

品牌名先做规范化，处理大小写、重音、标点和 Inc./Group/.com 等后缀；再用别名表合并同一品牌的不同写法，例如 *Shoo Loong Kan* = 小龙坎。AI 返回不足 10 个时，缺的位置算作未命中。

**某个品类未通过时**，我会逐一查看 AI 返回了哪些不在表里的品牌，并判断失败原因：

1. **品牌表缺失**：AI 给出的是该品类的真实品牌，只是表里没有。只有当独立来源（主要是 Wikipedia 摘要）明确说明它属于该品类时才补入；135 个候选中采纳了 119 个。补入的行都做了标记，报告中始终同时给出不含这些行的"补表前" recall。
2. **品类名被误解**：AI 回答的是另一个品类。这种情况就改名重测，共 5 例，见下表。

## 结果

| 轮次 | 模型 / temperature | 品牌表口径 | 通过 | 平均 Recall@10 |
|---|---|---|---|---|
| 第 1 轮（首次打分） | DeepSeek V4 Pro / 0 | 初始表 | 23 / 60 | 0.63 |
| 第 1 轮 | DeepSeek V4 Pro / 0 | 初始表（补表前） | 26 / 60 | 0.69 |
| 第 1 轮 | DeepSeek V4 Pro / 0 | 补表后 | 56 / 60 | 0.88 |
| 第 2 轮（5 个改名品类） | DeepSeek V4 Pro / 0 | 补表后 | 5 / 5 | 0.96 |
| **最终（每类最近一次尝试）** | DeepSeek V4 Pro / 0 | 补表后 | **60 / 60** | — |
| 留出检验（冻结表） | DeepSeek V4 Pro / 1.0 | 补表后 | 44 / 60 | 0.80 |
| 跨模型检验（冻结表） | Qwen 3.7 Plus / 0 | 补表后 | 32 / 60 | 0.72 |
| 跨模型检验（冻结表） | Qwen 3.7 Plus / 0 | 补表前 | 20 / 60 | 0.62 |

*列定义。* **轮次**：对各品类完整跑一遍。第一行使用的是最初的解析器和别名表，后来已修复，例如它曾把 Markdown 子弹点里的说明文字当成品牌。这一行保留用于透明说明，其余各行都是用最终代码对同一批已保存的回答重新打分。**品牌表口径**："补表前"不含验证后补入的 119 个品牌。**通过**：Recall@10 ≥ 0.8 的品类数。**平均 Recall@10**：各品类的平均值，取值 0–1。每轮每个品类只采样一次，未计算置信区间。

**改名的品类**（第 1 轮 → 第 2 轮，DeepSeek）：

| 原名称 | AI 的表现 | 新名称 | 改名后 Recall@10 |
|---|---|---|---|
| Real Estate Developers | 列出家电/装修品牌（Sub-Zero、Miele） | Chinese Real Estate Developers | 0.9 |
| Credit Card Networks | 混入发卡行（Chase、Capital One） | Payment Card Networks | 0.9 |
| Home Improvement Stores | 列出工具/油漆品牌（DeWalt、Benjamin Moore） | Home Improvement Retail Chains | 1.0 |
| Cigarettes | 拒绝回答 | Cigarette Brands | 1.0 |
| AI Chatbots | 列出公司名（OpenAI、Anthropic） | AI Chatbot Apps | 1.0 |

*列定义。* **AI 的表现**：我对第 1 轮回答的概括。**改名后 Recall@10**：第 2 轮补表后的得分。AI Chatbots 单靠改名没有用，回答仍是公司名；它是在加了"公司 → 产品"的映射（如 OpenAI → ChatGPT）后才通过的，这个映射是我的人工判断。

**主表样例**（完整主表 957 行，见附件）：

| Category | Brand | World/China | 验证结果 |
|---|---|---|---|
| Smartphones | Apple / Samsung / Google Pixel | World | Pass |
| Smartphones | Xiaomi / Huawei / OPPO / vivo | China | Pass |
| Baijiu | Moutai / Wuliangye / Luzhou Laojiao | China | Pass |
| Electric Vehicles | Tesla / BMW | World | Pass |
| Electric Vehicles | BYD / Li Auto / NIO | China | Pass |
| Bubble Tea Chains | Mixue Bingcheng / Heytea / Chagee | China | Pass |

*列定义。* 正式主表每行一个品牌，这里为节省篇幅，每行合并列出几个。**验证结果**：该品类最近一次尝试的结果。

## 检验说明了什么

- *观察：* 补入的品牌在新的回答上同样有效。DeepSeek 留出检验中，通过数从补表前的 29 升到 44；Qwen 从 20 升到 32。说明补表不是只迎合了某一次回答，但 60/60 偏乐观。
- *观察：* 两个模型在 40/60 个品类上结论一致：28 类都通过，12 类都不通过。都不通过的包括：宽泛的食品饮料类（Dairy Products、Beer、Energy Drinks、Processed Meat Products、Hot Pot Restaurant Chains），服务类（Insurance Companies、Hotel Chains、Supermarket Chains、Online Healthcare Platforms），以及 Cosmetics、Drones、Traditional Chinese Medicine。
- *观察（Qwen）：* Qwen 把 "Online Shopping Platforms" 理解成电商建站软件（Shopify、WooCommerce），recall 为 0.0；把 "AI Chatbot Apps" 部分理解成企业客服机器人工具（Intercom、ManyChat）。这类命名问题只用一个模型发现不了。
- *解读：* 其余未命中的大多是表外的真实品牌，包括美国区域或小众品牌（Mint Mobile、USAA、GEICO）、高端或精酿类（Aman、Westmalle），以及直营美妆（Rare Beauty）。品类名越宽，AI 每次给出的长尾品牌越不一样，改用更窄的名称（按子品类或市场）可能更稳定。这一点尚未验证。

## 局限

- 每轮每个品类只采样一次，没有计算方差或置信区间。
- 补表和部分别名是在看过第 1 轮回答之后加的。对此，报告给出了补表前的 recall，并用冻结表做了留出检验和跨模型检验作为对照。
- Task 2 中约一半的行依据的是搜索结果摘要，而不是完整网页。World/China 标签以及"明确属于该品类"都是人工判断。
- 两个验证模型的回答都偏美国市场，会影响 World/China 的平衡。

## 扩展到 1000 个品类的下一步

1. **扩大种子池**：加入 Kantar 和 Brand Finance 的分行业榜单，以及电商类目树。
2. **半自动化 Task 2**：从多个来源生成候选品牌，再人工抽检。
3. **默认多模型验证**：至少两个模型都通过才算通过；两个模型都不通过的品类改用更窄的名称。

代码、AI 原始回答、证据记录和逐类结果都在仓库中：<https://github.com/moyunxiang/ai-observatory>。本文所有数字都可以从已保存的回答重新计算。

## 附录：逐类结果

<!-- APPENDIX -->

*列定义。* **品牌数（W/C）**：品牌表行数（World / China）。**DeepSeek 第 1 轮 补表前 → 补表后**：第 1 轮的 Recall@10；5 个改名品类在括号中给出第 2 轮结果。**最终**：最近一次尝试的结果，决定是否进入主表。**留出**：冻结表后 DeepSeek 在 temperature 1.0 下的结果。**Qwen**：冻结表后 Qwen 3.7 Plus 的结果。所有 recall 取值 0–1，均为单次采样。
