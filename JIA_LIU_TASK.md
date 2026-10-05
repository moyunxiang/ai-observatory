# 品牌 Category 发现与验证任务

> 本文档整合 Jia Liu 邮件正文及附件《品牌Category发现与AI验证任务说明.docx》中的任务要求。仅整理原始要求，不额外加入执行方案。

## 背景与任务目的

该任务用于测试是否具备项目所需的市场研究能力，以及对 business / consumers 的判断能力，并为 AI Observatory 获取相关的产品/服务 sectors 及对应的 meaningful queries。

总体目标是建立一套 **Category → 品牌** 表，并确保 Category 的名称符合真实用户 / AI 搜索语义：

> 当用户询问该 Category 的最佳品牌时，AI 能够正确理解该品类，并返回该品类中的真实代表品牌。

## 当前阶段要求

当前不需要提交完整结果。

需要：

- 按照下面的 procedure 开展任务；
- 提供一些 **sample results**；
- 说明这些结果是 **如何得到的（how you derive these results）**。

完成后将结果发送给 Jia Liu，之后再安排 meeting，决定是否参与后续项目。

邮件中给出的预期时间约为 **一周**。

---

# 规模要求

最终目标：

- **不少于 1000 个通过验证的独立 Category**。
- 1000 个指的是最终通过验证的独立 Category 数量，**不是测试次数**。
- 同义词、近义词或仅措辞不同的 Category **不得重复计数**。

---

# Task 1：从知名品牌反推 Category

## 执行步骤

1. 收集**世界知名品牌和中国知名品牌**，形成知名品牌种子池。
2. 对品牌去重。
3. 判断每个品牌最主要对应的行业或产品品类。
4. 将表达相同或高度相近的品类名称合并，得到初始 **Category List**。

## 示例

| 品牌 | Category |
|---|---|
| Nike | Sportswear |
| Adidas | Sportswear |
| Lululemon | Sportswear |
| Dyson | Vacuum Cleaner |
| Roborock | Robot Vacuum |

## 验收指标

**所有种子品牌均能够被归入一个明确的主 Category，未归类品牌数 = 0。**

---

# Task 2：扩充每个 Category 下的品牌

## 执行步骤

1. 以 Task 1 得到的 Category List 为基础。
2. 逐个搜索每个 Category 中的其他主要品牌。
3. 合并 Task 1 的知名品牌与新发现品牌。
4. 最终形成统一的 **Category–Brand 表格**。

## 示例

| Category | Brand |
|---|---|
| Robot Vacuum | Roborock |
| Robot Vacuum | Ecovacs |
| Robot Vacuum | iRobot |
| Robot Vacuum | Dreame |
| Robot Vacuum | Narwal |

## 验收指标

**每个 Category 至少找到 10 个真实、明确属于该品类的品牌。**

---

# Task 3：用 AI 反向验证 Category 名称

## 固定测试问题

对每一个 Category，向 AI 提问：

> What are the best brands for {category}? List 10 brands.

例如：

> What are the best brands for robot vacuum? List 10 brands.

## 验证方法

将 AI 返回的品牌，与 Task 2 中该 Category 的品牌表进行比较。

如果 AI：

- 明显理解成了其他品类；
- 返回大量与目标品牌无关的品牌；
- 无法返回该 Category 中的代表品牌；

则说明 **Category 描述词存在问题**。

此时需要修改 Category 名称，再次测试。

例如：

```text
Cleaning Robot
↓
AI 理解不稳定
↓
Robot Vacuum
↓
重新测试
```

不断修改，直到 Category 能被 AI 正确理解。

## 验收指标

AI 返回的 Top 10 品牌中，至少 **8 个**存在于该 Category 的品牌表中。

即：

**Brand Recall@10 ≥ 80%**

达到该标准后，该 Category 名称通过验证。

未达到则继续修改 Category 名称并重新测试。

最终通过验证的 Category 数量：

**≥ 1000**

---

# 最终交付物

最终只需要一张主表：

| Category | Brand | World/China | Category验证结果 |
|---|---|---|---|
| Robot Vacuum | Roborock | China | Pass |
| Robot Vacuum | iRobot | World | Pass |
| Sportswear | Nike | World | Pass |

## 最终结果约束

- 只有**通过 Task 3 验证**的 Category 才进入最终结果。
- 最终结果中不少于 **1000 个独立 Category**。
- 每个 Category 至少有 **10 个真实、明确属于该品类的品牌**。
- 同义词、近义词或仅措辞不同的 Category 不得作为不同 Category 重复计数。
- Category 必须满足 **Brand Recall@10 ≥ 80%**。
