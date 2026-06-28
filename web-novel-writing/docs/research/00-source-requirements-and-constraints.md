# 00 · 源需求与约束（web-novel-writing skill 的事实源）

> 本文是 `web-novel-writing` skill 的设计地基：把原始聊天记录里的痛点、AX 的框架想法、用户追加约束、以及调研后已确立的设计原则，固化成单一事实源。后续 SKILL.md / references / templates 都以此为准。

## 1. 缘起与真实痛点（来自一线作者「豪子」实践，必须当设计约束）

朋友用 AI 写网文连载，已踩出以下经验性结论（不是假设，是实测）：

- **完全放手 = 不可读**。Opus 4.8 / GPT 5.5 连续续写 4–5 章逻辑还行，再多就**逻辑/人设/世界观全崩**。
- **续命靠手工纪律**：每 5 章 compress context、update `memory.md` / `大纲.md`、开新 window 才能继续。
- **市面工具都不好用**：试过多个，评价"很 shit"；具体试过 `github.com/zxerai/novelix` → **overengineered**（仅 17★）。
- **一次性生成大量章节 = 死路**。必须每章按大纲自动生成 prompt，**prompt 只管这一章**。
- **关键故障：prompt 太长会泄漏到正文** —— AI 会莫名其妙把"本应是给它的约束/context"写进小说正文。
- **必须迭代闭环**：反复 update `current_大纲.md` / `current_章节_memory.md` → 改章节 → 再 update → 再改，直到 **review agent 通过**。
- **AI 能力的经验边界**：
  - ✅ AI 好用：环境描写、旁白、扩写细节 —— "很好用，没问题"。
  - ❌ AI 不好用：剧情走向、节奏把控 —— "还是得人写"。
- **去 AI 味 skill 不好用**，也得自己搓；AI 味"可能要在模型层解决"。
- **模型口碑（实测 > 评测）**：GPT/Claude 写中文 AI 味浓；豪子实测 **GLM 比 GPT 强**，DeepSeek 描写"语言怪"（但评测不可全信，需自己实践）。

## 2. AX（用户）的原始框架想法（需被批判性检验，他自陈"不一定对"）

1. 一个**世界观**文档集；
2. 一个**主要人物**文档集；
3. 一个**剧情线**文档集；
4. 一些**关键时间线**文档集（世界怎么演化、哪些关键事件）；
5. **必须一直 maintain 这些 state**；
6. 章节级：每章按大纲自动生成短 prompt（只管这一章、别太长防泄漏）；改→update→改，直到 review agent 通过；
7. 人机分工：**主线剧情/节奏由人类拍板**，AI 辅助环境描写/旁白/扩写；AI 可与人探讨剧情但**不直接产成品**；
8. 去 AI 味可能要在模型层（用国产模型/分工）。
9. 指示：**调研真实网文大神怎么写**，再决定哪些可自动化、哪些半自动化。
10. 姊妹 skill：`game-script-creation`（二游剧本陪写，已有 Canon/Project State、校准、反AI味、references 知识库结构）—— 新 skill 应是它的"网文长篇连载"兄弟。

## 3. 用户在本次会话中追加的硬约束

- **C1 · 模型只是可选优化旋钮，不是硬依赖**。豪子有**无限 Codex（GPT 系）token**。设计原则：pipeline 必须 **model-agnostic**，默认就能在 Codex 上跑；"换 GLM/国产文学性更强的模型"是可选优化，不是前置条件。
- **C2 · 诚实承认模型天花板**。Pipeline 能解决的是**工程问题**（一致性崩坏/结构失控/prompt 泄漏/流程纪律）；它能压低 AI 味但压不到零——文学性上限仍受模型束缚。Skill 必须明确分开"工程能修的"和"只有换模型/人类润色能修的"，不夸大。
- **C3 · 网文审美 ≠ 文学审美，反 AI 味清单不能照搬**。文学/游戏的 craft 铁律很多在网文里恰恰是错的（见 §5）。必须调研裁决，不能拍脑袋复用。
- **C4 · 研究材料留在 repo 复用**。所有调研产出存 `~/projects/devtools/AX-skills/web-novel-writing/docs/research/`，不丢 /private/tmp。
- **C5 · 借鉴 GitHub 高星活跃项目**，逐个拆架构，提炼能偷的/要避的。

## 4. 已确立的设计原则（调研中收敛的，作为 skill 不变式）

1. **人类是 driver，AI 是受约束的 subroutine**（= AX 工程原则"LLM 是被确定性代码包裹的子程序"）。每个 AI 调用做一件有界的事，做完立刻交还控制权。
2. **状态即记忆，但要拆成 typed ledgers**，不要一个 `memory.md` 把"事实 / 推测 / 伏笔 / 未来意图 / 给模型的约束"混在一起 —— 那正是 prompt 泄漏到正文的根因。按 canon / plan / draft-only / reader-visible / character-known 分类。
3. **未来计划/伏笔不进正文模型的上下文** —— 防剧透 + 防约束泄漏。
4. **每章 ≥4 个不可混用的 prompt**（本章意图 / 场景 beat / 正文生成 / 事实抽取审计）—— 别让模型边规划边写。
5. **正文模型不能改 canon；状态更新是 delta 不是覆盖；审稿模型只局部修不全章重写。**
6. **审校多 rubric 且分级**：correctness 类（连续性/知识边界/泄漏）硬门禁每章必跑；quality 类（人物声音/AI 味/节奏）跑但人类只在低分时看。
7. **每章必须有 Chapter Contract，必须产生状态变化，每 N 章 compaction + regression。**
8. **反 AI 味分三桶**（见 §5）。
9. **品类感知**：网文结构强品类依赖，约束模板/检查清单要能按品类×平台切换。
10. **反 overengineering**：substrate 是 **Codex CLI + Markdown/YAML 文件 + skill 指令 + 极小校验脚本**，不是要豪子建/维护一个带 SQLite/向量库/dashboard 的 app。一个最小 schema-check 脚本可以有（把不变式 code 化），SQLite/RAG/多模型路由是 v2 nicety 不是核心。MVP 先做可跑的最小闭环。

## 5. 反 AI 味三桶模型（来自《webnovel-aesthetics-vs-literary-craft.md》调研裁决）

- **桶1 · 词句层**（紫色文风/翻译腔/形容词堆砌/节奏匀速）→ **文学清单全量复用且加权**，这是网文编辑鉴 AI 的第一道关。
- **桶2 · 结构层**（show-don't-tell / 信息倾倒 / 潜台词 / 视角纪律）→ 改成**分层规则**：对人设/逻辑/世界观 lore **保留**；对情绪/爽点/卖点/金手指**反向放行（直给）**。
- **桶3 · 网文专属轴**（黄金三章留存 / 爽点密度 / 章末钩子 / 毒点规避 / 品类×平台适配）→ **文学清单完全没有**，却是"扑街 vs 起飞"的真正分水岭。
- 一句话：**AI 味在网文里 ≈ 翻译腔 × 华美空洞 × 节奏平 × 不推进剧情**。前两项词句层可 prompt 救；后两项结构层需人类先定爽点/节奏/钩子骨架、AI 填空。

## 6. 调研材料索引（本目录）

- `00-source-requirements-and-constraints.md` —— 本文（地基）
- `webnovel-aesthetics-vs-literary-craft.md` —— 反 AI 味三桶裁决 + 网文章节质检清单草案（已完成）
- `prior-art-external-proposal-webnovelops.md` —— 外部 WebNovelOps 五层提案 + 我的批判取舍（已完成）
- *(待落盘)* 六流深度调研发现 + 批判 AX 框架备忘录 + 整合设计蓝图（workflow woxcytlzk）
- *(待落盘)* GitHub 高星项目 prior-art 整合报告（workflow wxt0ryhxp）
