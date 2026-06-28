> Purpose: 本 skill 的研究蓝图与 prior-art 索引。说明结论从哪来、可信度分级、以及业界现有项目"偷什么/避什么"。做研究复盘或质疑某条论断时读这里，再下钻到 `docs/research/` 的原始材料。

# 00 · 研究地图 / Prior-Art 索引

## 1. 研究方法

本 skill 不是拍脑袋设计的，是在一个真实痛点（"完全放手让 AI 写网文，4-5 章后逻辑/人设/世界观全崩"）之上做了**批判性、可追溯**的调研后整合的。四条独立调研线：

| 调研线 | 形式 | 产物（落 `docs/research/`） |
|---|---|---|
| 六流深度调研（网文工业方法论/品类套路/AI长篇生成学术与工程/现有工具批判/去AI味与模型选择/多agent编排与章节prompt工程） | 多 agent 并行 + 批判 AX 框架 + 整合蓝图，Tavily 联网 | `01-six-stream-findings.md` / `02-critique-ax-framework.md` / `03-pipeline-design-blueprint.md` |
| 网文审美 vs 文学 craft 冲突（逐条裁决文学反 AI 味清单在网文里是否成立/反转） | 单 Opus agent，Tavily 联网中文一手来源 | `webnovel-aesthetics-vs-literary-craft.md` |
| GitHub 高星/活跃 AI 写小说项目 prior-art（21 agent 用 `gh` CLI 拿真实 star/pushed 逐个拆架构） | 多角度发现 → 深拆 → 整合 | `04-github-prior-art-survey.md` |
| 外部设计提案审视（WebNovelOps 五层架构）+ 我方批判取舍 | 整合 | `prior-art-external-proposal-webnovelops.md` |
| **外部交付物①借鉴裁决：WebNovelOps 可运行 CLI**（另一 agent 独立交付的 Python 包，pytest 全绿）——3 路对抗式评审 40 findings | 评审 + 逐项 INTEGRATE/REJECT | `05-integration-decision-webnovelops.md`（+ `external-webnovelops-deliverable/` 原始码+demo） |
| **外部交付物②借鉴裁决：oh-story-claudecode**（13-skill 网文插件，去AI味口碑强，MIT）——7-agent 全模块调研 + 综合 | 调研 6 路 + 综合 | `06-integration-decision-ohstory.md`（+ `external-ohstory-deslop/` 原始词表+检测器） |

源需求与约束的事实源：`00-source-requirements-and-constraints.md`。

> **两份外部交付物的借鉴主线（2026-06-27 补）**：① WebNovelOps 与本 skill 独立收敛到同一架构（typed 账本/防泄漏 context/无 LLM 覆盖 canon/审校闭环）=强信号；借它的**确定性 state-delta 合并代数**(`state_apply.py`)+**acceptance_criteria 判分桥**，避它的扁平 JSON/CLI-as-default。② oh-story 真正强在我**最弱的 craft 工艺层**（对话/反转 typed/情绪弧/导入崩稿/拆爆款）；借它的 **Gate A-G 去AI味 + 鲁棒「不是A而是B」检测 + 模型退化检测**(`degeneration_check.py`)+ craft 文本（→ refs 12/13/14 + enrich 02/05/06/07/08）。两者一律**只借 craft 与确定性检测逻辑，REJECT 它们的插件/CLI/抓站/parity-CI 架构**——那正是"市面工具太重"痛点本身。

**纪律**：网文 craft 优先中文一手来源（知乎/龙的天空/起点作家专区/番茄作家学院/作者访谈）；AI 方法优先 arxiv/工程博客；GitHub 数据用 `gh api` 拿真实 star/pushed 不靠记忆。论断锚定来源；查不到/推断的标 ⚠️。

## 2. 来源可信度分级

- **高**：有具名一线作者实证（唐家三少日更/王峰《天命使徒》110 万字/毛志慧）、有 arxiv 论文（Re3/DOC/LongWriter ICLR2025/StoryScope/NeurIPS2025 CoT-vs-指令遵循）、有可读源码的 GitHub 项目（真实 star/pushed 核验过）、网文编辑访谈（澎湃/骨朵）。
- **中**：单一来源数据（如"追读 top10% 约每 1.8 章一情绪高峰"）、平台留存阈值（算法不公开，属经验/内部资料推断，**作可调参数不作硬编常量**）。
- **低/⚠️推断**：模型口碑（"GLM>GPT、DeepSeek 语言怪"是单一作者实测）、"叙事层 AI 味是模型天花板"的强度（方向高可信、量级部分推断）。

## 3. 对 AX 原框架的核心修正（一句话）

AX 摸到了正确骨架（外部文档作事实源 + 单章短 prompt + review 循环），但把"**维护文档**"当成了解药——真正的解药是：**给每条事实打 Canon 状态+按卷可见性、把校验做成独立确定性子程序、把硬约束用代码强制而非靠模型记、把品类/平台/爽点工程显式化**。完整批判见 `02-critique-ax-framework.md`。

## 4. Prior-Art 全景表（GitHub，按对本 skill 借鉴价值排序，star/pushed 为调研当日真实值）

> 核心结论：14 个项目里只有 3 个真在解我们的问题（oh-story-claudecode / webnovel-writer / inkos），其余是记忆/RP 基础设施、桌面编辑器 schema 博物馆、或带营销水分的 demo。**贯穿主线：偷它们的数据契约与循环纪律，绝不偷它们的实现体量。**

| 项目 | ★ | 形态 | 偷什么 / 避什么 |
|---|---|---|---|
| **worldwonderer/oh-story-claudecode** | 3.2k | 中文网文 Claude Code skill（substrate 同构） | 偷：文件系统即记忆、每实体一文件、带状态枚举的 typed 追踪表、写前 blocking 大纲守卫、写后确定性退化脚本兜底；避：硬约束写成散文、gaps 分支爆炸 |
| **lingfengQAQ/webnovel-writer** | 5.3k | 跑在 Claude Code 的网文工具（最同构） | 偷：CHAPTER_COMMIT 单一真源+派生只读投影、chapter_directive 写前合同(必覆盖节点/禁区/倒计时)、write-gate 三关卡、读/写/审三 agent 单一写入权、**追读力系统(Hook/爽点/微兑现/债务追踪)**；避：190 模块重基建、单 pass 不复检 |
| **Narcooo/inkos** | 7.6k | Story Creation 多 agent（本领域最高★） | 偷：双时态 SPO 事实账本(validUntilChapter)、伏笔生命周期治理(准入+欠债逼还)、LLM 只吐 JSON delta+代码校验、编译式章节契约、净改善≥ε 才采纳；避：37 维塞单次 LLM、8 文件伏笔子系统、三重状态同步缝 |
| **ExplosiveCoderflome/AI-Novel-Writing-Assistant** | 1.8k | LangGraph+Qdrant 导演式 | 偷：BookContract(第3/10/30章承诺+绝对红线)、CharacterState 同存 knownFacts+**misbeliefs**、PayoffLedger 兑现窗口+overdue、不调 LLM 的确定性连续性诊断；避：100 表 monorepo、垂直线 scope creep |
| **NousResearch/autonovel** | 1.2k | 自治写作流水线（真出过 79k 字书） | 偷：双免疫系统(确定性 slop 正则+异模型 LLM-judge，**终分=判分−机械扣分**)、git keep/discard 门控、canon 硬事实库、评审反喂生成；避：整本灌 1M-context 非连载、英文-only 词表、propagation-debt 账本(文档吹代码没实现) |
| getzep/graphiti | 28k | 双时态知识图谱记忆（基础设施） | 偷：双时态"只失效不删"+point-in-time 查询+矛盾=LLM出idx/Python做区间失效=L2 蓝本；避：图数据库/向量重栈（用 JSON 重写） |
| SillyTavern/SillyTavern | 30k | RP 前端（基础设施） | 偷：World Info 条目 schema(关键词/position/order/budget)、sticky/cooldown 时序激活、增量滚动摘要、token 预算硬截断；避：裸关键词脆弱性、probability 随机注入、260KB god-file、零自动审校 |
| YILING0013/AI_NovelGenerator | 5.5k | 赛道标杆 | 偷：五层落盘+写前只读/写后回写状态机、当前章·下一章双合约、可续跑 checkpoint；避：**伪约束**(prompt 写"相似度>40%重构"无代码测)、伏笔 ledger 空壳 |
| mem0ai/mem0 | 60k | 记忆中间件（基础设施） | 偷：extract→reconcile→dedup 两阶段、ADD/UPDATE/DELETE 真冲突消解、UUID→整数反幻觉、event-sourced history；避：偏好向 fact schema、25 向量库依赖 |
| joonspk-research/generative_agents | 22k | 斯坦福研究代码（**stale**） | 偷：分层人物卡(innate/learned/currently)、recency×importance×relevance 三因子检索、重要度触发反思压缩；避：模拟器脚手架、缺 top-down 大纲层 |
| olivierkes/manuskript · vkbo/novelWriter | 2.4k·3k | 开源写作编辑器（schema 博物馆） | 偷：角色四要素(motivation/goal/conflict/epiphany)+三级雪花摘要、`{C:ID}`/`@tag` 稳定-ID 引用、可全量重建的派生索引；避：Qt 强耦合、advisory-only 一致性(须升级成硬门) |
| THUDM/LongWriter · MaoXiaoYuZ/Long-Novel-GPT | 1.9k·1.2k | 长文生成（论文件/半成品） | 偷：plan-first 大纲分解+代码强制字数契约+可断点续跑；避：**全文重灌式无状态记忆**(扛不住连载)、RAG/review 评分空壳(营销级) |

诚实标注（非"真能用的连载引擎"）：**LongWriter** 是 ICLR 论文造数据脚本(每段重灌全文 O(n²)，~1.5 万字必崩)；**generative_agents** 是 stale 的社会模拟器；**AI_NovelGenerator/Long-Novel-GPT** 有显著 **文档/代码漂移**(README 吹的 RAG/伏笔 ledger/相似度检测 代码里是空壳)。逐项深拆见 `04-github-prior-art-survey.md`。

## 5. 五层映射：业界最优解 → 本 skill 落地

| 层 | 业界最优解（来源） | 本 skill 落地 |
|---|---|---|
| L0 作者宪法 | 持久控制文档(inkos) + BookContract 第3/10/30章承诺+红线(ExplosiveCoderflome) | `templates/contract-template.yaml`（顶层契约 + reader_promise + forbidden + locked_reveals） |
| L1 设定库 | manuskript 字段切分 + SillyTavern 按需注入 + 每实体一文件 | `templates/state-world.yaml` / `state-characters.yaml`（行为锚点+认知边界），`references/02` |
| L2 状态账本 | graphiti 双时态只失效不删 + inkos/ExplosiveCoderflome 伏笔治理 + webnovel-writer 单一真源 | `foreshadow-ledger.yaml` 状态机 + `valid_until_chapter` + `scripts/state_check.py`，`references/08` |
| L3 章节契约 | webnovel-writer chapter_directive + ExplosiveCoderflome 义务合同 + 当前/下一章双合约 | `templates/chapter-outline-template.json`（must/must_not + forbidden_reveals + next_chapter_sketch） |
| L4 生产闭环 | autonovel 双免疫(终分=判分−机械扣分) + inkos 净改善≥ε + webnovel-writer 三关卡/单一写入权 | 9 步循环 + `scripts/antislop_lint.py` + `templates/review-report-template.json`，`references/01`/`04` |

## 6. 我们刻意不学的（反 overengineering）

不学事件溯源 monorepo / 向量库 / 图数据库重基建（webnovel-writer 190 模块、graphiti 图库四后端、mem0 25 向量库）——对 Markdown skill 是负债，纯文本账本+几个确定性脚本拿到 80% 收益。不学多 agent 并行写作 / 37 维单 pass 审计 / "N 个专职 agent"叙事。不学把硬约束写成散文（伪约束）、字符级字数硬配额、整本灌进 1M-context 的非连载架构。

## 7. 头号反模式（贯穿全 skill）

**伪约束**：把 MUST-hold 不变量写进 prompt 当成已执行（AI_NovelGenerator 的"相似度>40%重构"无代码、oh-story 的"必须"散文、webnovel-writer 硬纪律压进超长 SKILL.md）——会随模型漂移。**本 skill 的对策**：硬门由 `scripts/` 代码强制（伏笔逾期/Canon 枚举/境界单调/AI 味词句层/可见性过滤），prompt 只承担"软引导"，绝不把"代码该做的校验"交给模型自觉。

## Sources

- 调研原始材料：本目录同级 `../docs/research/` 各文件（六流发现 / 批判备忘录 / 设计蓝图 / 网文审美裁决 / GitHub prior-art 深拆 / 外部提案取舍 / 源需求约束）。
- 关键外部来源（择要，完整见各 research 文件 Sources）：Anthropic《Effective context engineering for AI agents》；arxiv：Re3、DOC、LongWriter(ICLR2025)、StoryScope、CoT-vs-指令遵循(NeurIPS2025)；网文编辑访谈（thepaper 澎湃 / 骨朵）；龙的天空、知乎网文写作、番茄作家学院、起点作家专区；GitHub 项目源码（真实 star/pushed 经 `gh api` 核验）。
