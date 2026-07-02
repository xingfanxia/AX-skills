---
name: deep-research
description: |
  验证型调研：多Agent并行、交叉验证（Tier 1-4信源分级）、可追溯的调研工作流。产出决策备忘录，核心是判断claim的真伪和可信度。
  适用场景：需要做决策的调研（"该选A还是B"、"X靠不靠谱"、"evaluate"、"帮我验证"）、技术评估、方案对比、行业可行性判断。
  不适用：纯粹想了解一个东西的来龙去脉（用 narrative-research）、想要叙事风格的研究报告（用 narrative-research）。
  触发词：深度调研、帮我调研、evaluate、该选哪个、靠不靠谱、对比一下、investigate、competitive analysis。
version: 3.1.0
---

# 深度调研工作流

## 搜索工具（Claude Code 环境强制）

本工作流全程 10-30+ 次搜索。在 Claude Code 里，主控和所有 sub-agent 一律用 **tavily-skill CLI**（file 模式，结果落盘不进上下文），不要用 Tavily MCP，也不要用裸 WebSearch——那是 CLAUDE.md → Web Search Routing 点名的 token 泄漏反模式：

```bash
~/.claude/skills/tavily-skill/.venv/bin/tavily-skill search "query" --output ./tmp/tavily/<slug>.json
```

非 Claude Code 环境（无此 CLI）再退回宿主自带的搜索工具。

## 核心原则

1. **激励感知验证**: 信息价值取决于来源的激励结构。厂商叙事有用但不能自证。每个主要 claim 都必须追溯到与发布方激励无关的独立证据。
2. **交叉验证**: 多个 sub-agent 覆盖有重叠的主题，用分歧和矛盾暴露盲区。
3. **可追溯性**: 所有引用保留 URL，关键引用保留原文摘录，不依赖总结。
4. **逐步聚焦**: 先扫描全貌，提取 claim，再分维度深入验证。
5. **单一主交付 + 可复用工件**: 最终报告一份，关键中间工件存入 session 目录。
6. **共享 research spine，分叉 reader mode**: 搜索、验证、工件留存共享；成稿前按读者决定 internal / external mode。

## 信息源层级

| 层级 | 类型 | 使用方式 |
|------|------|----------|
| Tier 1 | 厂商官方文档、blog、case study | 提取 claim，不做验证依据 |
| Tier 2 | Press coverage、sponsored review | 辅助理解市场叙事，不作为独立证据 |
| Tier 3 | 独立开发者 blog、HN/Reddit、Stack Overflow | 作为验证信号，注意社区偏差 |
| Tier 4 | GitHub issues、migration stories、production post-mortems、commit history | 最高可信度，行为证据而非态度表达 |

证据可信度递增：态度表达 < 使用场景描述 < 对比决策记录 < Migration stories < Production post-mortems < 代码/commit 级证据。优先收集后半部分。

**Claim 类型 ↔ 证据类型匹配**——来源可以很有名，但仍然是错误类型的证据：

| Claim 类型 | 对口证据类型 |
|-----------|-------------|
| 产品功能/特性 | 官方文档、源码 |
| 法规/合规 | 官方法律文本、监管机构发布 |
| 科学有效性 | 同行评审论文、meta 分析 |
| 市场趋势/规模 | 财报、监管披露文件 |
| 运营故障/可靠性 | Incident 报告、post-mortem |

## 两种 Reader Mode

**Mode A：Internal（共享上下文驱动的决策备忘录）** — 读者是自己或共享上下文的协作者。不复述共同常识；重点展开会改变结论的未知点、最可能被反对的点。

**Mode B：External（零预设上下文的可发布论证）** — 读者不是已知对象。必须显式回答 why this matters；关键定义和限定条件写在页面上。

先问三个问题再选 mode：(1) 读者是否已知且共享厚重上下文？(2) 主要价值是帮对方更快判断还是让对方理解并相信？(3) 拿掉私有背景后报告能否独立成立？

## Phase 1: 初步扫描 + Claim 提取

1. 用 Tavily 进行 2-3 次搜索，覆盖：
   - 调研对象的基本描述（Tier 1 官方信息）
   - 市场评价和媒体报道（Tier 2 市场叙事）
   - 批评、争议、已知问题（Tier 3-4 信号）
2. 总结 3-5 个需要深入调研的维度。
3. **Claim 提取**：列出关键主张，对每个 claim 标注验证通道。

**输出**: `tmp/<session_slug>/scratchpad.md`，含 claim extraction 表格：

```markdown
| Claim | 来源 (Tier) | 验证通道 | 验证状态 |
|-------|-------------|----------|----------|
| "zero-config" | Tier 1 官方 | GitHub issues 搜 setup pain | 待验证 |
```

## Phase 2: 分割与并行调研

**按证据功能设计维度**（不只是按主题）：
- 官方叙事（Tier 1-2）
- 独立使用体验（Tier 3）
- 失败与边界（Tier 3-4）
- 迁移行为（Tier 4）

维度之间必须有 **≥50% 的 overlap**，让不同 agent 有机会发现矛盾。

启动 3-5 个 sub-agent，每个 prompt 中明确：
1. 具体调研主题
2. 本维度相关的 claim（要求在 Tier 3-4 源中验证）
3. 优先返回行为证据，而非态度表达
4. 必须返回 URL 和原文摘录
5. 可以覆盖的其他相关维度（形成 overlap）

**Tavily 参数**: CLI 默认即为 `--max-results 6 --search-depth advanced --answer off`，无需显式传参；sub-agent prompt 里带上「搜索一律用 tavily-skill CLI --output 落盘」

## Phase 3: 整合与交叉验证

1. 对比各 sub-agent 结果：多个发现 → 可信度高；单一来源 → 标注；互相矛盾 → 特别标注
2. 对每个 claim 核查验证状态：
   - Tier 3-4 有独立证据 → 已验证
   - 仅 Tier 1-2 → "仅 vendor source，未独立验证"
   - Tier 3-4 与 Tier 1-2 矛盾 → 以 Tier 3-4 为准
3. 如发现重大矛盾，可再启动 sub-agent 针对性验证。

## Phase 3.5: 决定 Reader Mode

写进 scratchpad：`mode`、目标读者、哪些前提可默认共享、哪些必须显化。

## Phase 4: 撰写最终报告

**动笔前穿透检查**：
1. 每个主要正面判断是否至少有一个 Tier 3+ 独立证据源？
2. 找不到独立支撑的判断 → 显式标注"此点仅有 vendor source"
3. 是否同时呈现了 vendor narrative 和 independent reality？

**Internal mode 写作顺序**: 结论 → 关键依据 → 未确认点 → 建议动作

**External mode 写作顺序**: Why it matters → 核心判断 → 背景与定义 → 分维度证据 → 边界与反例 → 决策意义

**确定性引用校验（交付前必跑）**：

```bash
python3 ~/.claude/skills/deep-research/scripts/verify_citations.py <报告.md> --sources tmp/
```

脚本在本 skill 的 `scripts/` 目录下（Codex 环境把 `~/.claude` 换成 `~/.codex`）。它用 URL 签名（域名+路径前段）把报告里每条引用对到 `tmp/` 落盘的搜索结果和笔记的 URL 池，抓虚构 URL、空链接/悬空引用、汇总与正文不一致、单一来源集中（>25%）。critical 必须修复后重跑，exit 0 才能交付；warning 逐条人工判断（同域不同文的要确认是不是同一篇）。

**存储**: `contexts/survey_sessions/<topic>_survey_YYYYMMDD.md`

## 续研（Round 2+）

同一课题的后续调研不重跑全流程、不重写全文：
1. 复用 `tmp/<session_slug>/`：读旧 scratchpad 和 claim 表，明确上轮「未验证 / 仅 vendor source」的遗留点
2. Claim 表增量扩展：新 claim 追加行，旧 claim 更新验证状态（含「已验证 → 被新证据推翻」）
3. 只对新维度和新矛盾点启动 sub-agent，已验证结论不重复搜索
4. 交付 **delta memo** 而非重写全文：变化了什么 / 新证据 / 对既有结论的影响 / 剩余不确定性

## URL 留存规范

必须保留 URL：直接引用、数据来源、评价来源、官方信息。正文引用用 inline `[来源](URL)` 或如下格式，报告末尾加 `## 来源汇总` 列出全部来源 URL——引用校验脚本按此结构检查。

```markdown
**来源描述**（URL）
> 原文摘录
```

避免：无 URL 的引用（"有人评价说..."）、只总结不引用原文。

## 常见陷阱

| 陷阱 | 对策 |
|-----|------|
| 只搜到正面信息 | 专门搜 "criticism", "negative review", "scam" |
| 为反而反（强行 contrarian） | 无真实主流叙事可反驳时，不得为反而反；改为交付一个决策相关的非显然洞察 |
| 信息来源单一 | 强制要求 sub-agent 找多个独立来源 |
| 过度总结丢失细节 | 保留原文摘录 |
| 维度划分太干净没有 overlap | 故意让边缘模糊 |
| Sub-agent 返回太浅 | prompt 中强调"深度"、"具体"、"原文" |
| 调研变成 vendor marketing 汇总 | Phase 1 提取 claim → Phase 2 分维度验证 → Phase 3 核查 → Phase 4 穿透检查 |
| internal 误用为"可以不解释" | 共同常识跳过，读者不熟悉的要展开 |
