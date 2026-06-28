# GitHub 高星/活跃 AI 写小说项目 prior-art 调研（workflow wxt0ryhxp）

> 21 agents 用 gh CLI 拿真实 star/pushed 拆解。下半部分是逐项深拆，顶部是整合报告。

## 整合报告

# 现有项目 Prior-Art 整合报告：约束 AI 写好中文网文连载

> 服务对象：一个跑在 **Codex CLI + Markdown 文件**、反 overengineering 的「约束 AI 写好中文网文连载」skill（game-script-creation 的姊妹）。
> 核心结论先行：这 14 个项目里，**只有 3 个真正在解我们的问题**（oh-story-claudecode / webnovel-writer / inkos）；其余要么是**记忆/RP 基础设施**（mem0、graphiti、SillyTavern、generative_agents——范畴不同，只能偷算法），要么是**桌面编辑器 schema 博物馆**（novelWriter、manuskript——偷数据模型、代码零复用），要么是**带营销水分的 demo/研究件**（LongWriter、AI_NovelGenerator、Long-Novel-GPT——文档吹的能力代码里是空壳）。**贯穿全报告的一条主线：偷它们的数据契约与循环纪律，绝不偷它们的实现体量。** 我们的 substrate 决定了正确形态是「纯文本账本 + 几个确定性兜底脚本」，而不是事件溯源 monorepo / 向量库 / 图数据库。

---

## 1. 全景表（按对本 skill 借鉴价值排序）

| # | 项目 | Star | 活跃 | 成熟度 | 一句话：偷 / 避 |
|---|---|---|---|---|---|
| 1 | worldwonderer/oh-story-claudecode | 3182 | active | 可用 skill 包 | **偷**：substrate 完全同构（已适配 Codex CLI）——文件系统即记忆、每实体一文件、带状态枚举的 typed 追踪表、写后确定性退化脚本兜底；**避**：把硬约束写成散文、gaps 分支爆炸、四运行时三四倍复制 |
| 2 | lingfengQAQ/webnovel-writer | 5307 | active | 可用工具(Claude Code) | **偷**：CHAPTER_COMMIT 单一真源 + 派生只读投影（event sourcing/CQRS 心智）、chapter_directive 写前合同（必覆盖节点/禁区/倒计时）、write-gate 三关卡、读/写/审三 agent 单一写入权；**避**：照抄 190 模块全套重基建、单 pass 审查不复检 |
| 3 | Narcooo/inkos | 7617 | active | 可用工具(本领域最高★) | **偷**：双时态 SPO 事实账本（validUntilChapter）、伏笔生命周期治理（准入+欠债逼还）、LLM 只吐 JSON delta + 代码 Zod 校验、编译式章节契约(intent/context/rule-stack/trace)、净改善≥ε 才采纳；**避**：37 维塞单次 LLM、8 文件伏笔子系统、三重状态同步缝 |
| 4 | ExplosiveCoderflome/AI-Novel-Writing-Assistant | 1796 | active | 可用工具 | **偷**：BookContract（第3/10/30章承诺+绝对红线）、CharacterState 同存 knownFacts+**misbeliefs**、PayoffLedger 带兑现窗口+overdue 状态机、章节义务合同、不调 LLM 的确定性连续性诊断；**避**：100 表巨型 monorepo、Drama/Comic/占星垂直线、Worker 重 infra |
| 5 | NousResearch/autonovel | 1210 | semi-active | 可用工具(真出过 79k 字书) | **偷**：双免疫系统（确定性 slop 正则 + 异模型 LLM-judge，**终分=判分−机械扣分**）、git keep/discard 门控、canon 硬事实库 + 伏笔账本、评审反喂生成；**避**：整本灌进 1M-context 的非连载架构、英文-only 词表、propagation-debt 账本（文档吹了代码没实现） |
| 6 | getzep/graphiti | 28055 | active | 生产级基础设施 | **偷**：双时态「只失效不删除」事实账本 + provenance + point-in-time 查询 + 「矛盾=LLM 只出 idx、Python 做区间失效」+ MinHash/LSH 确定性优先去重——L2 的设计蓝本；**避**：图数据库/向量/cross-encoder 重栈（用 SQLite/JSON 重写） |
| 7 | SillyTavern/SillyTavern | 29928 | active | 生产级(RP 前端) | **偷**：World Info 条目 schema（关键词/selective 逻辑/position/order/budget）、sticky/cooldown 伏笔时序激活、增量滚动摘要、token 预算硬截断；**避**：裸关键词触发脆弱性、probability 随机注入、多级递归引擎、260KB god-file、零自动审校 |
| 8 | YILING0013/AI_NovelGenerator | 5456 | active | 可用工具(赛道标杆) | **偷**：五层落盘 + 写前只读/写后回写状态机、当前章·下一章双合约、多模型路由、雪花式可续跑 checkpoint；**避**：prompt 里的相似度%/伏笔回收当成已执行（**伪约束**）、伏笔 ledger 空壳、状态全自由文本无 schema |
| 9 | MaoXiaoYuZ/Long-Novel-GPT | 1161 | semi-active | 可用工具 | **偷**：自顶向下分层扩写 + 上下层双向同步防漂移、滑窗控成本、主副模型分工；**避**：用 LLM 维护字符 slice 对齐的脆弱重工程、**RAG 名存实亡 + review 评分「暂未实装」的空壳** |
| 10 | mem0ai/mem0 | 59599 | active | 生产级基础设施 | **偷**：extract→reconcile→dedup 两阶段 + ADD/UPDATE/DELETE 真冲突消解(V2) + event-sourced history + UUID→整数反幻觉；**避**：偏好向 fact schema、V3 的 ADD-only 只累积、把整个 SDK/25 向量库拖进来 |
| 11 | joonspk-research/generative_agents | 21661 | **stale** | 研究代码 | **偷**：分层人物卡(innate/learned/currently)、带 poignancy+出处链的只追加记忆流、recency×importance×relevance 三因子检索、重要度触发的反思压缩；**避**：整个模拟器脚手架 + bottom-up 涌现范式（缺我们最要的 top-down 大纲/伏笔层） |
| 12 | olivierkes/manuskript | 2352 | active | 可用工具(纯手工) | **偷**：10 年验证的 schema——角色四要素(motivation/goal/conflict/epiphany)+三级雪花摘要、`{C:ID}` 稳定-ID 引用 token、场景契约字段(POV/status/compile/goal)；**避**：PyQt5 焊死架构、类别藏文件夹的隐式契约 |
| 13 | vkbo/novelWriter | 2989 | active | 生产级(纯手工编辑器) | **偷**：纯文本 `@tag/@ref + %synopsis` 契约 + 可全量重建的场景级派生索引（ItemIndex+反向 TagsIndex）、`@mention`(出场但本场不在)；**避**：Qt 强耦合代码、advisory-only 一致性（必须升级成硬门禁） |
| 14 | THUDM/LongWriter | 1868 | semi-active | **研究代码(ICLR 论文件)** | **偷**：plan-first 大纲分解 + 代码强制的每单元字数契约 + 可断点续跑顺序循环 + 「省略开放式结尾」拼接防断指令；**避**：**全文重灌式无状态记忆**（零人物卡/时间线/伏笔）、append-only 无在环修订——扛不住连载 |

**诚实标注（哪些不是「真能用的连载引擎」）**：
- **LongWriter** 是一篇 ICLR 论文的造数据脚本（plan.py+write.py 约 120 行），目标是给 SFT 造长文样本，**不是连载工具**；它的「一致性」就是每段重灌全文，O(n²) 膨胀，超 ~1.5 万字必崩。1868★ 的论文光环不等于可挪用。
- **generative_agents** 是 **stale 的斯坦福研究代码**，是社会模拟器不是写作器，~90% 是迷宫/寻路/Django/精灵脚手架，且刻意没有授权写作必需的 top-down 控制层。
- **AI_NovelGenerator（5456★ 赛道标杆）实为「伪约束」**：prompt 里写「相似度>40% 必须重构」却没有任何代码测相似度；README 宣称的 plot_arcs 伏笔 ledger 在 finalize 里**从不写入**、一致性检查里硬编码为空字符串——**文档与代码漂移**。
- **Long-Novel-GPT** README 宣称「基于 LLM 和 RAG / 拆书提取人物关系」，但代码**无任何向量依赖**，那段检索 prompt **在所有 .py 里从未被 import**，是死代码；review 评分机制源码注释明写「暂未实装」。营销级 RAG。
- **mem0/graphiti/SillyTavern** 根本**不是写作工具**（记忆中间件 / RP 前端）。把它们当「写作框架」找会落空——它们只提供状态读写层，章节循环与审校全得自建。

---

## 2. 五层架构横向归并：每层的业界最优解

### L0 作者宪法（怎么写 + 不可逾越的红线）
- **最优解：inkos 的「持久控制文档」 + ExplosiveCoderflome 的 BookContract**。inkos 把 `author_intent.md`(长期)+`current_focus.md`(近期) 做成**可长期编辑、参与每章规划**的文件，而非建书时一次性 prompt——这是 L0 的正确形态。
- **可结构化锁死的承诺**：ExplosiveCoderflome 的 `BookContract{readingPromise, protagonistFantasy, chapter3Payoff/chapter10Payoff/chapter30Payoff, escalationLadder, absoluteRedLinesJson}` 几乎逐字对应网文「前 30 章承诺 + 爽点节奏 + 红线」，**直接当开书契约模板**。
- **框架/内容物理隔离**：autonovel 把 CRAFT/ANTI-SLOP/ANTI-PATTERNS（怎么写）放 master 永不变、故事内容放 per-novel 分支（写什么）——理念对，但它自己没守干净（Bells 内容硬编码进 prompt）。**借鉴理念，引以为戒。**

### L1 StoryBible（设定/人物/世界观结构化）
- **schema 教科书：manuskript**（角色=motivation/goal/conflict/epiphany 四要素 + 三级雪花摘要；比「自由文本人设」对 LLM 约束力强一个量级）。
- **条件触发注入：SillyTavern World Info**（key/selectiveLogic/position/order/constant/characterFilter）——`constant`=世界观铁律常驻，普通条目按当前章节关键词按需注入，**不把整本设定灌进去**。
- **类型化抽取：graphiti 的 Pydantic 自定义实体/边类型**（给设定上类型）。
- **最优组合**：用 manuskript 的**字段切分**当内容 schema、用 SillyTavern 的**按需注入**当装配策略、每实体一文件（novelWriter / oh-story-claudecode 的「文件系统即数据库」）。**我们的 substrate 下，L1 = 一组 Markdown 设定文件 + frontmatter 字段，不需要数据库。**

### L2 StateLedger（状态/时间线/伏笔——本报告重点，见 §3）
- **最优解：graphiti 的双时态账本** + **inkos/ExplosiveCoderflome 的伏笔生命周期治理** + **webnovel-writer 的单一真源+派生投影心智**。三者叠加就是最优 L2。

### L3 ChapterContract（章节级硬约束）
- **最干净的落地：ExplosiveCoderflome 的「义务合同」**——`mustHitNow / mustPreserve / requiredPayoffTouches / requiredCharacterAppearances / forbiddenCrossings`，**单份合同被 writer/审核/修复/重规划共同消费**，避免各自解释章节职责。
- **字段表最完整：webnovel-writer 的 chapter_directive**——`goal / time_anchor / countdown / must_cover_nodes(必覆盖) / forbidden_zones(禁区) / chapter_end_open_question`，**禁区违反即不通过（代码 gate，非靠 LLM 自觉）**。
- **承上启下：AI_NovelGenerator 的「当前章+下一章」双合约**——带上 N+1 章合约显著降低断裂/伏笔失衔。
- **编译式产物：inkos**——先编译成 intent/context/rule-stack/trace 四个可审计文件再写，**而非一坨 prompt**；trace.json 的可调试性尤其值得抄。

### L4 生产闭环（生成→审校→提交）
- **审校最优解：autonovel 双免疫系统**——确定性正则 slop 扫描 + 异模型 LLM-judge，**终分=判分−机械确定性扣分**（judge 管不到机械扣分）。完全对应 engineering rule「硬不变量用代码 append、不交给 LLM」。
- **采纳门槛：inkos「净改善≥ε 才采纳，否则回退」**+ autonovel「git keep/discard、post≥pre 才 commit」。
- **关卡：webnovel-writer 三关卡（prewrite/precommit/postcommit）**+ 确定性 gate。
- **人机分工：webnovel-writer 三 agent 单一写入权**（context-agent 读 / data-agent 写 / reviewer 只返 JSON 不持 Write）。

---

## 3. 状态 / 记忆 / 一致性最佳实践萃取（我们最关心的一层）

**业界主流怎么存——共识与最优解：**

**(1) 设定/人物：显式分表 + 稳定 ID，绝不一坨自由文本。**
- 最优组合：manuskript 的角色「四要素+三级摘要」字段切分 + manuskript/`{C:ID}` 稳定-ID 引用 token + ExplosiveCoderflome 的**角色硬事实**（identityLabel/factionLabel/powerLevel/realm/currentLocation/prohibitions）。
- **正文里用 ID 而非名字引用**（manuskript `{C:ID}`、novelWriter `@tag`），改名不断链、可反查「第 N 章触及哪些设定/伏笔」——这是伏笔回收与一致性的**索引底座**。
- **反例：AI_NovelGenerator 状态全 .txt 无 schema**，唯一「校验」是再喂回 LLM 问一遍——一致性是「感觉对」不是「被证明对」。

**(2) 时间线 + 角色认知：双时态 + 知道什么/错信什么。**
- **双时态是最强武器（graphiti / inkos）**：每条事实带 `validFrom/validUntil` 生效区间，**变更只失效不删除**，支持 point-in-time 查询——生成第 N 章时只喂「截至第 N 章为真」的事实，**天然防剧透/防伏笔提前泄底/防前后打架**。inkos 用它精确抓「角色拿出两章前已丢失的武器」「记起从未见过的事」。
- **被多数项目忽略、但网文刚需：ExplosiveCoderflome 的 CharacterState 同存 `knownFactsJson` + `misbeliefsJson`**（知道什么 + 错误地相信什么）+ `secretExposure` + InformationState（谁持有哪条信息）——支撑**信息差与戏剧反讽**的一致性，强烈建议吸收。

**(3) 伏笔：做成有生命周期、有截止章数、会逾期报警的账本。**
- **最优解：ExplosiveCoderflome PayoffLedgerItem + inkos HookRecord**——`ledgerKey 唯一 + 状态机(setup→hinted→pending_payoff→paid_off/failed/overdue) + targetStart/EndChapterOrder 兑现窗口 + halfLife + 逾期主动报警`。inkos 更进一步：**准入控制**拒绝「无回收信号的伏笔」「重复家族伏笔」，`collectStaleHookDebt` 算出「欠债伏笔」**逼 planner 处理**——「欠债逼还」的反向压力是连载最痛点。
- **伏笔即事件（webnovel-writer / mem0 思路）**：埋设强制写 `open_loop_created`、回收写 `promise_paid_off`，闭环可审计、可被压缩器追踪。
- **反例：AI_NovelGenerator 的 plot_arcs 是空壳**，伏笔只静态写死在章节蓝图字样里，从不被追踪。

**(4) 记忆压缩：分级 + 阈值触发，不是无限增长。**
- 最优算法组合：
  - **分层视图**（oh-story-claudecode）：近 5 章详记 / 每 10 章概要 / 卷级总览，30 章以上触发。
  - **分级压缩器**（webnovel-writer compactor）：超阈值才触发 → 同 key 只留最新 → 删已回收伏笔 → 距当前>50 章旧 timeline 合并成一条 → 仍超限按 active 优先+新鲜度全局截断。
  - **增量滚动摘要**（SillyTavern）：用「上段摘要+新增缓冲」重摘要，promptInterval/promptForceWords 双触发。
  - **重要度触发反思**（generative_agents）：累计重要度越阈值 → 提焦点问题 → 检索 → 蒸馏 5 条高层洞察存回。

**(5) 一致性校验：混合「确定性 oracle 兜底 + LLM 软判」，矛盾判定必须代码做。**
- **教科书结构（graphiti）**：LLM 只输出 `duplicate_facts/contradicted_facts` 两个 idx 列表，**真正的失效判定由纯 Python 做时间区间运算**——「LLM 当子程序、确定性代码立刻夺回方向盘」。
- **确定性连续性守卫（ExplosiveCoderflome / oh-story-claudecode）**：completedMilestones（已完成里程碑禁止再追求）、recentScenePatterns 场景黑名单（时间+地点+动作三要素去重）、卷级 keyMilestoneGuards（防高潮提前写）、关键词组重复检测——**不调 LLM，把最常见崩点拦在生成前或低成本检出**。
- **反幻觉手段（mem0 / generative_agents）**：UUID→小整数映射喂 LLM（只在 0/1/2 上引用、代码映射回真实 id）；每条派生结论强制引用源节点 ID（filling/provenance）——审校引用「第几条设定矛盾」时直接套用，避免幻觉出不存在的条目。

**谁做得最好？** **L2 的「数据模型」最优解是 graphiti（双时态只失效不删）**；**「伏笔治理」最优解是 inkos+ExplosiveCoderflome**；**「角色认知边界」唯一做对的是 ExplosiveCoderflome（misbeliefs）**；**「单一真源心智」最优解是 webnovel-writer（accepted commit + 派生只读投影）**。把这四样拼起来，用 SQLite/JSON 或纯 Markdown 表轻量重实现，就是我们的 L2。

---

## 4. 章节生产循环最佳实践萃取

**主流编排（收敛后的最优骨架）：**
```
写前合同(L3) → 编译上下文(确定性优先级+预算截断) → 起草(只依合同/纯正文)
   → 审校(确定性 oracle + LLM rubric 并行打分) → 必要修复(局部 patch 优先)
   → 结算回写状态(只失效不删) → 章节级 commit/快照
```
各项目对应：webnovel-writer 6 步带硬关卡、inkos plan→compose→write→audit→revise→settle、ExplosiveCoderflome 热/冷双通道、AI_NovelGenerator 写前只读/写后回写。

**几条已被反复验证的纪律：**
1. **「怎么写」与「写了什么」彻底分离**（webnovel-writer）：文笔节奏放开发挥，但事实必须登记/过审/存档。
2. **草稿纯函数读、定稿才回写**（AI_NovelGenerator）：draft 阶段只读 state 绝不 mutate，只有显式定稿才回写——草稿可反复重生成而不污染长程状态。
3. **热路径快写、冷路径一次低温结构化调用抽全部状态 delta**（ExplosiveCoderflome）：正文生成不被状态抽取阻塞，状态抽取只调一次低温模型——既省 token 又保一致性。这是章节循环的核心节流设计。
4. **plan-first 永不一把梭**（LongWriter / Long-Novel-GPT）：先出结构化大纲再逐单元填，每单元=（要点+字数预算），字数由代码 string-replace 强制注入。
5. **审校→生成的闭环**（autonovel）：把 evaluator 早期 flag 的 AI 味反喂进后续章 prompt 的「PATTERNS TO AVOID」，写之前就规避已知失败模式。
6. **可断点续跑/幂等**（LongWriter write_cache、ExplosiveCoderflome content-hash checkpoint、AI_NovelGenerator partial checkpoint）：长任务挂掉重跑不重写已完成产物。

**多 agent vs 单循环的取舍——结论：单循环 + 多 rubric，而非多 agent 并行。**
- webnovel-writer 明确选择**单 reviewer 内含 5 维**（非多 agent 并行），blocking issue 定点修复不重跑——成本权衡。
- inkos「10 个专职 agent」是**叙事夸大**，多数是同一 LLM client 上的 prompt 变体 + 确定性胶水。
- 真正需要多 agent 的只有 autonovel 的「reader_panel 4 人格取共识 + Elo 锦标赛」这类**小说级**审校（抓单一 rubric 抓不到的「角色单薄/全员点头无摩擦」）——但它也承认这是有界单本的奢侈，连载承担不起。
- **对我们的 Codex CLI substrate**：单主循环串行逐章（oh-story-claudecode 明令禁止多章并发，因为章节依赖上一章正文+追踪文件）+ **一个审校步内跑多 rubric** + 确定性脚本兜底，是成本/可靠性最优。多 agent 是 token 黑洞且非确定性。

**审校是「找问题」不是「验证正确」**（oh-story-claudecode / webnovel-writer 都把这条写成铁律）；reviewer **只返 JSON、不评分文笔、不建议改情节、不持 Write**。

---

## 5. 反模式与 Overengineering 清单（我们该砍什么）

**A. 伪约束——把硬约束写进 prompt 当成已执行（最危险、最普遍）**
- AI_NovelGenerator：「相似度>40% 必须重构」无代码测量；apply_content_rules 只用正则按章距打标签冒充语义查重。
- oh-story-claudecode：绝大多数「必须/不得」是 LLM 须自觉遵守的散文，会随模型漂移。
- webnovel-writer：大量硬纪律压进超长 SKILL.md，靠 LLM「读懂并照做」。
- **教训：任何 MUST-hold 不变量（禁区、字数区间、伏笔到期、设定矛盾）必须 code/schema/lint 强制，不能写进 prompt 当已执行。**

**B. 文档/代码漂移（doc drift）**
- autonovel：propagation-debt 传播账本被 README 大书特书，`debts` 在 runner 里只 init 成 `[]` 全程不读写。
- Long-Novel-GPT：营销级「RAG」无向量依赖，检索 prompt 从未被调用；review 评分「暂未实装」。
- AI_NovelGenerator：plot_arcs 伏笔 ledger 空壳。
- inkos/webnovel-writer：审计维度数量在 overview 与 agents 文档里对不上。
- **教训：单一真源；宣称的能力必须有对应代码，否则不写进文档。**

**C. 在不重要处过度工程、在关键处欠工程**
- Long-Novel-GPT：把复杂度押在「用 LLM 维护两列字符级 slice 对齐」（writer.py 400+ 行 assert/TODO），却在状态层完全留空。
- LongWriter：plan/write 120 行精确，但零状态层。
- **教训：复杂度预算花在 L2 状态账本 + L4 审校 gate，不花在花哨的对齐代数/字符级配额。**

**D. 字数/比例的伪精确**
- oh-story-claudecode 情节点 per-point 字数预算（密≥250/疏≈40，Σ落在[目标,目标×1.1]）、Strand Weave 固定 60/20/20 比例——LLM 难可靠命中字符级配额，跨题材也未必成立。
- **教训：字数走「区间软目标 + 不达标定位重写」，别做字符级硬配额；节奏比例当建议不当裁决。**

**E. 巨型表面积 / scope creep / 重 infra**
- ExplosiveCoderflome：~3400 行/100+ model，把 Drama 短剧、Comic 漫画、占星塞进同一 schema（~40% 与核心无关）+ Worker 租约/双面分离重 infra。
- inkos：8 文件的伏笔子系统、三重状态表示（JSON+Markdown+SQLite，且伏笔必须豁免 SQLite 因存不下元数据）。
- webnovel-writer：465 文件/190 模块单维护者，正在 v7 推倒重来。
- mem0/graphiti：25+ 向量库 / 4 图库后端——对写作 skill 是纯负担。
- SillyTavern：world-info.js 单文件 260KB/6289 行 god-file。
- **教训：同样的概念压到 1/3 文件数；用单一 hook-ledger 模块、单一状态真源（纯文本）。**

**F. 非确定性开关 / 脆弱触发**
- SillyTavern：probability 随机注入（把「设定是否进上下文」变掷骰子）、多级递归注入引擎（调试地狱）、裸关键词触发（代词/别称漏匹配）。
- autonovel/Long-Novel-GPT：用正则从自由文本答案里抠控制信号。
- **教训：用稳定实体 ID+别名表替代裸关键词；分支基于已验证的 sentinel token 而非自由文本；杜绝随机注入。**

**G. 一致性只检测不闭环 / 全靠人**
- AI_NovelGenerator、SillyTavern、novelWriter、manuskript：一致性是 advisory（日志/波浪线/视图），没有「校验不过就阻断产出」的硬门禁。
- **教训：把 advisory 高亮升级成「校验不过就阻断章节 commit」的硬 gate——这正是我们要补的缺口。**

---

## 6. 对本 skill 的吸收建议

### ✅ 5 条最高优先级吸收（按优先级）

1. **以 oh-story-claudecode 为骨架蓝本（substrate 完全同构）。** 文件系统即记忆（对话只写不记）、每实体一文件的 StoryBible、`追踪/` 目录下「伏笔.md / 时间线.md / 角色状态.md / 上下文.md」四张**带状态枚举的 typed 追踪表**、写正文前的 **blocking 大纲守卫**、写后的**确定性退化脚本**（模型自己发现不了退化、靠模型无关脚本兜）。它已适配 Codex CLI，是最近的姊妹，但**砍掉**它的 gaps 分支爆炸和四运行时复制。*(来源：oh-story-claudecode)*

2. **L2 状态账本 = 双时态「只失效不删除」+ 伏笔生命周期账本，用纯 Markdown 表 + 一个 SQLite/JSON 实现。** 每条事实带 `validFrom/validUntil`、point-in-time 查询（生成第 N 章只喂截至 N 章为真的事实）；伏笔做成 `状态机(setup→pending→paid/overdue) + 兑现窗口 + 逾期报警 + 准入拒绝无回收信号`。**矛盾判定由确定性代码做区间运算，LLM 只输出「矛盾/不矛盾+指哪条 idx」。** *(来源：graphiti 双时态 + inkos/ExplosiveCoderflome 伏笔治理 + graphiti 矛盾=signal+code)*

3. **L3 章节契约 = 单份「义务合同」贯穿写-审-修。** 字段直接抄 webnovel-writer 的 chapter_directive（`goal / time_anchor / countdown / must_cover_nodes / forbidden_zones / chapter_end_open_question`）+ ExplosiveCoderflome 的 `forbiddenCrossings / canDefer`，**带上下一章合约**（AI_NovelGenerator）。**禁区是代码 gate，不是 LLM 自觉。** *(来源：webnovel-writer + ExplosiveCoderflome + AI_NovelGenerator)*

4. **L4 审校 = 双免疫系统 + 净改善才采纳。** 确定性**中文 AI 味词典正则**（把 autonovel 的英文 TIER1/2/3 整套换成中文：「不禁/一抹/眸子/空气仿佛凝固/不是…而是…」+ 中文 telling 检测 + 段落等长/列表结构）+ 异模型 LLM-judge 多维 rubric（逐维强制 gap+fix、反分数膨胀校准），**终分=judge 分−机械确定性扣分**；修复**净改善≥ε 才采纳否则 git 回滚**。审校只找问题、reviewer 只返 JSON 不持 Write。 *(来源：autonovel 双免疫+keep/discard + inkos 净改善门槛 + webnovel-writer 单一写入权)*

5. **L0/开书 = 持久作者宪法 + 结构化 BookContract。** `author_intent.md`(长期)+`current_focus.md`(近期) 持久参与每章规划；BookContract 锁死「前 30 章承诺 + 爽点节奏 escalationLadder + 绝对红线」。CharacterState **同存 knownFacts + misbeliefs**（信息差/反讽一致性，多数项目漏掉的）。 *(来源：inkos 持久控制文档 + ExplosiveCoderflome BookContract/misbeliefs)*

### ❌ 3 条明确不学

1. **不学事件溯源 monorepo / 向量库 / 图数据库的重基建。** webnovel-writer 的 190 模块（projection_log+覆写账本+7 桶记忆+向量 RAG+React dashboard）、graphiti 的图库四后端、mem0 的 25 向量库——对一个 Markdown skill 是负债。**用纯文本账本 + 几个确定性脚本拿到 80% 收益。** 派生视图可随时从 Markdown 真源重建，不需要持久索引服务。

2. **不学多 agent 并行写作 / 37 维单 pass 审计 / 「N 个专职 agent」叙事。** inkos 的 37 维塞单次 LLM 是维度稀释、营销味大于区分度；多 agent 多是同一 client 的 prompt 变体。**收敛成 8-12 个正交检查，确定性可查的（词汇疲劳/段落等长/列表结构）走脚本、其余走单 reviewer 的多 rubric。** 单循环串行逐章。

3. **不学把硬约束写成散文、字符级字数配额、和整本灌进 1M-context 的非连载架构。** 伪约束（AI_NovelGenerator 的相似度%、oh-story 的「必须」散文）必须改成 code/schema/lint；字数走区间软目标；**autonovel/LongWriter 的「全本/全文重灌」对几百章连载是结构性天花板**——我们必须靠 L2 检索注入 + 分级压缩替代，绝不重灌全文。

---

## 7. 来源映射（结论 → repo）

- **双时态「只失效不删除」事实账本、矛盾=LLM 出 idx+Python 做区间失效、provenance、MinHash/LSH 确定性优先去重** → getzep/graphiti
- **伏笔生命周期治理（准入+欠债逼还）、编译式章节契约(intent/context/rule-stack/trace)、LLM 只吐 JSON delta+Zod 校验、净改善≥ε 才采纳、双时态 SPO(validUntilChapter)** → Narcooo/inkos
- **BookContract（第3/10/30 章承诺+绝对红线）、CharacterState 的 misbeliefs/knownFacts、PayoffLedger 兑现窗口+overdue、章节义务合同、不调 LLM 的确定性连续性诊断、热/冷双通道** → ExplosiveCoderflome/AI-Novel-Writing-Assistant
- **CHAPTER_COMMIT 单一真源+派生只读投影、chapter_directive 写前合同（必覆盖节点/禁区/倒计时）、write-gate 三关卡、读/写/审三 agent 单一写入权、分层记忆+compactor、伏笔即事件** → lingfengQAQ/webnovel-writer
- **双免疫系统（确定性 slop 正则+异模型 LLM-judge，终分=判分−机械扣分）、git keep/discard 门控、canon 硬事实库、评审反喂生成、逐维 gap+fix+反膨胀 rubric、多人格审校栈** → NousResearch/autonovel
- **文件系统即记忆、每实体一文件、带状态枚举的 typed 追踪表、写后确定性退化脚本、写前 blocking 大纲守卫、Codex CLI substrate 同构** → worldwonderer/oh-story-claudecode
- **World Info 条目 schema、sticky/cooldown 伏笔时序激活、增量滚动摘要、token 预算硬截断、统一注入总线** → SillyTavern/SillyTavern
- **五层落盘+写前只读/写后回写状态机、当前章·下一章双合约、多模型路由、雪花式可续跑 checkpoint；伪约束/伏笔空壳反例** → YILING0013/AI_NovelGenerator
- **extract→reconcile→dedup 两阶段、ADD/UPDATE/DELETE 真冲突消解(V2)、event-sourced history、UUID→整数反幻觉、procedural memory 压缩** → mem0ai/mem0
- **分层人物卡(innate/learned/currently)、带 poignancy+出处链的只追加记忆流、三因子检索(recency×importance×relevance)、重要度触发反思压缩** → joonspk-research/generative_agents
- **角色四要素+三级雪花摘要、`{C:ID}` 稳定-ID 引用 token、场景契约字段(POV/status/compile/goal)** → olivierkes/manuskript
- **纯文本 @tag/@ref+%synopsis 契约、可全量重建的派生索引、`@mention`(出场但本场不在)** → vkbo/novelWriter
- **自顶向下分层扩写+上下层双向同步防漂移、滑窗控成本、主副模型分工；RAG/review 评分空壳反例** → MaoXiaoYuZ/Long-Novel-GPT
- **plan-first 大纲分解+代码强制字数契约、可断点续跑顺序循环、「省略开放式结尾」拼接防断；无状态全文重灌反例** → THUDM/LongWriter

---

## 逐项深拆

### mem0ai/mem0 (59599★, active, production)
https://github.com/mem0ai/mem0
- **做什么**：通用「记忆层」基础设施（不是写作工具）。把一段对话喂进去，它用一次 LLM 调用抽取出自包含的原子事实（"User 是软件工程师"、"喜欢芝士披萨"），自动去重/链接/冲突消解后存进向量库，检索时用「语义+BM25 关键词+实体匹配」三路融合再 rerank 返回。目标场景是给 AI 助手/agent 加长期个性化记忆。YC S24、Apache-2.0、pypi+npm 双发包、有托管服务，是事实标准级的记忆中间件。对网文 skill 的价值是：可直接当「人物/世界事实记忆库」的后端，不必自己造记忆轮子；但它抽的是「用户偏好」不是「剧情设定」，schema 需要改造。
- **架构**：五个解耦层 + 工厂式 provider 注入（mem0/utils/factory.py，LLM/embedder/vector_store/graph 全部按 config 字符串实例化，符合"inject the LLM client"原则）。核心数据流（V3 算法，2026-04 上线，见 mem0/memory/main.py 的 `_add_to_vector_store` 830-1153 行）分 8 个 Phase：(0) 取本会话最近 10 条消息做 context；(1) 用整段对话的 embedding 检索 top-10 现有记忆作为"已知事实"；(2) **一次** LLM 调用做 ADD-only 抽取（系统 prompt = ADDITIVE_EXTRACTION_PROMPT，agent 场景再拼 AGENT_CONTEXT_SUFFIX）；(3) 批量 embed 抽出的事实；(4-5) 每条事实算 md5 hash，与现有 hash 和本批 hash 双重去重；(6) 批量写向量库 + 写 history 审计表（event=ADD）；(7) 批量抽实体并做"实体图"链接（entity→linked_memory_ids，语义≥0.95 视为同一实体合并）；(8) 存原始消息。三个持久化后端：向量库（语义，25+ backend 可选）+ SQLite history DB（事件溯源审计）+ entity store（轻量知识图）+ 可选独立 graph DB（Neo4j/Memgraph/Kuzu/Neptune）。还有 `infer=False` 逃生通道：跳过 LLM 直接逐条原文入库。同步/异步两套实现（Memory / AsyncMemory），代码对称。
- **状态/记忆设计**：这是它最值得借鉴的部分。**记忆 = 一组自包含原子事实**，每条 payload 携带 {id(uuid)、data(15-80 词的事实文本)、hash(md5)、created_at/updated_at、user_id/agent_id/run_id 三级作用域、actor_id/role、attributed_to(user 还是 assistant 说的)、text_lemmatized(给 BM25)、categories}。**一致性靠两阶段 LLM 流水线**：先 extract（抽事实）再 reconcile（与现有记忆对账）。reconcile 有两套：V2 的 DEFAULT_UPDATE_MEMORY_PROMPT 让 LLM 输出 ADD/UPDATE/DELETE/NONE 四种事件做真正的冲突消解（"Dislikes cheese pizza"会 DELETE 掉旧的"Loves cheese pizza"），V3 改成 ADD-only + hash 去重 + 实体链接（官方说为了 token 效率和 benchmark 分数，"记忆只累积不覆盖"）。**反幻觉的关键工程手段**：检索回来的记忆 UUID 被映射成整数 "0/1/2..." 再喂给 LLM（uuid_mapping），LLM 只在小整数上操作、绝不让它生成或记 UUID，代码层再映射回真实 id——把不可靠的文本通道收敛成可靠的 id 通道。**时间线**靠 Observation Date 锚点：prompt 强制把"上周/昨天"全部 ground 成绝对日期（"去 Paris 那周=2023-05-15"），否则记忆 6 个月后失效。**伏笔/关系图**靠 entity store + linked_memory_ids（"狗 Poppy"这个实体链到所有提到它的记忆）。**剧情压缩**有专门的 PROCEDURAL_MEMORY_SYSTEM_PROMPT，逐步逐字（verbatim）总结 agent 执行史当"前情提要"。history 表是完整 event-sourced 审计日志（每次 ADD/UPDATE/DELETE 都记 old_memory/new_memory），天然支持版本回溯。**没有**显式的"设定集/人物卡/章节"结构——所有东西都是扁平 fact 列表 + 实体图，靠检索而非结构化 schema 组织。
- **章节循环**：没有。mem0 完全不做内容生成，没有大纲→章节→review 的编排，没有多 agent、没有多 rubric 审校，没有"写"这个动作。它是被生成代码包裹的记忆**子程序**，不是 driver。唯一能类比"循环"的是记忆更新闭环：retrieve(现有事实) → LLM extract(新事实) → reconcile/dedup(对账) → persist(+审计) → 下次再 retrieve。以及 procedural memory 那个"把 N 步执行史压成可继续的摘要"的总结循环。对网文场景，应当把 mem0 放在你自己的章节循环的"状态读写"那一格：每章生成前从 mem0 检索相关设定注入 prompt，生成后把本章新增/变更的设定写回 mem0——但生成与审校的编排得你自己造，mem0 一行都不提供。
- **可借鉴**：
  - [L2 StateLedger] extract→reconcile→dedup 两阶段记忆更新流水线（先 LLM 抽原子事实，再与检索回的现有事实对账，md5 hash 双重去重后入库 + 写审计） — 这是『人物/世界事实库自动维护』的现成范式。每章写完把本章产生的设定喂进这套流水线，自动沉淀成可检索的 canon，且不会重复堆积同一条设定
  - [L2 StateLedger] ADD/UPDATE/DELETE/NONE 四事件 + 冲突消解 prompt（DEFAULT_UPDATE_MEMORY_PROMPT：矛盾即 DELETE 旧的，同义即保留信息量更大的那条） — 比 V3 的 ADD-only 更适合网文：当设定变更（角色断臂/势力灭亡）或前后矛盾时，必须真正覆盖/删除旧 canon 而非累积。建议偷 V2 这套而非 V3
  - [其他/通用 AI-pipeline 工程] UUID→小整数映射喂 LLM 的反幻觉手段（LLM 只在 '0/1/2' 上做引用/编辑，代码层映射回真实 id） — 让 LLM 操作设定条目时绝不让它生成或记忆真实 id，把不可靠文本通道收敛成可靠 id 通道——审校 agent 引用『第几条设定矛盾』时直接套用，避免幻觉出不存在的条目编号
  - [L1 StoryBible] entity store：实体→linked_memory_ids 的轻量知识图（实体抽取+embed，语义≥0.95 视为同一实体合并） — 天然就是『人物-地点-物品-势力关系图』的后端：一个角色实体链到所有提到它的章节/设定，写到该角色时一次性召回全部相关 canon，做角色一致性检查
  - [L2 StateLedger] event-sourced history 审计表（每次记忆变更记 old/new/event/created_at） — 免费拿到时间线/版本回溯/『某设定何时被改过』。伏笔追踪、设定变更史、回滚到某章状态全靠它
  - [L2 StateLedger] Observation Date 时间锚点 + 强制相对时间 ground 成绝对值的 prompt 纪律 — 网文时间线管理直接复用：把『三年后』『大婚当日』全部锚定到具体故事内日期，否则跨卷检索时间线会错乱
  - [L3 ChapterContract] 多信号检索融合（语义 embedding + BM25 关键词 + 实体匹配并行打分再 rerank） — 写某章前组装『本章应遵守的设定』时，纯语义检索会漏掉专有名词（人名/地名/功法名），BM25+实体匹配补回——网文专有名词极多，这个融合是刚需
  - [L2 StateLedger] PROCEDURAL_MEMORY_SYSTEM_PROMPT：把长执行史逐字压成可继续的结构化摘要 — 改造成『前情提要/本卷剧情进展』压缩器：把已写章节压成注入下一章的剧情状态，控制 context 又不丢关键情节
  - [其他/通用工程] 工厂式 provider 注入 + infer=False 逃生通道 — 符合『注入 LLM client』原则，天然可换 GPT/DeepSeek/本地模型且离线可测；infer=False 提示并非所有写回都该过 LLM——人工录入的硬 canon 应直接入库不让 LLM 改写
- **反模式**：事实 schema 是为『个人助手偏好』调的（likes/dislikes/出生日期/职业），不是为剧情 canon 调的。直接拿来存网文会沉淀一堆『主角喜欢吃面』的琐事，而真正 load-bearing 的『第12章揭示反派真身』这种情节级 canon 它的抽取 prompt 根本不会优先识别——schema 和抽取 prompt 必须重写 / V3 改成 ADD-only『记忆只累积、永不覆盖』是为了刷 LoCoMo/LongMemEval 这类 QA benchmark 的 token 效率。对网文这是反模式：设定矛盾会越积越多而不是被消解。网文要的恰恰是 V2 那套会 DELETE/UPDATE 的真冲突消解 / 用 LLM 当去重/冲突裁判本质是概率性的。对伏笔、世界规则这种一条都不能错的硬 canon，应该用确定性 id + 人工录入 + 显式冲突检测，而不是信任 LLM 抽取的事实和 0.95 余弦阈值的实体合并 / 完全没有生成/审校编排。把它当『写作框架』找会落空——它只是状态读写层，章节循环、多 rubric 审校、人机分工全得自己造 / prompt 巨大（单 prompts.py 62KB）且明显在追 benchmark 分数，存在对 QA 任务过拟合、对长篇叙事连贯性未必有效的风险；few-shot 全是助手场景，迁移到中文网文需大改 / 25+ 向量库 + 20+ LLM provider 的巨大集成面，对一个写作 skill 是纯负担——只该取它的算法思想，不该把整个 SDK 拖进来
- **OE判定**：对它自己的定位（通用记忆基础设施 / 卖托管服务的开源引擎）不算 overengineered——25+ 向量库、20+ LLM provider、sync+async 双实现、独立 graph DB 选项都是 infra 产品该有的集成面，复杂度是值得的。但**对网文 skill 而言是严重 over-scoped**：90% 的代码（provider 适配、telemetry、client/server、reranker 矩阵）与写作无关。真正有价值的就是 mem0/memory/main.py 的 `_add_to_vector_store` 8-Phase 流水线 + mem0/configs/prompts.py 的几个 prompt 思想，约几百行的算法内核。结论：偷算法和数据结构，别引依赖。另外 V3 为刷分走 ADD-only 是一次『为 benchmark 牺牲正确性』的设计取舍，对一致性要求高的网文反而要回退到 V2 思路。
- **偷/避**：偷它的『extract→reconcile→dedup + event-sourced history + 实体链接图 + UUID→整数反幻觉』当 L1 StoryBible / L2 StateLedger 的后端算法内核；避开它的偏好向 fact schema、V3 的 ADD-only 只累积不消解、以及把整个 SDK/25 个向量库依赖拖进来——你要的是确定性人工 canon + 真冲突消解，不是 benchmark 调出来的 LLM 琐事抽取。

### SillyTavern/SillyTavern (29928★, active, production)
https://github.com/SillyTavern/SillyTavern
- **做什么**：最主流的本地部署 LLM 角色扮演/对话前端（2023-02 从 TavernAI fork，3 年独立开发、300+ 贡献者、AGPL-3.0、fork 5660）。统一接入几十家 LLM API，核心价值不是"生成长篇"，而是把"如何在有限上下文里持续注入正确设定 + 压缩历史记忆 + 检索相关过去"做成了事实标准工具箱：World Info/lorebook、Author's Note、逐段 Summarize 摘要、Vector Storage（对聊天/文档做 RAG）、Data Bank。本质是逐回合交互式 RP 前端，不是大纲→章节→审校的自动化流水线。
- **架构**：前后端分体：浏览器端 public/scripts/*.js 负责全部上下文装配逻辑+UI，Node/Express 端 src/endpoints/* 只做持久化与代理转发（worldinfo.js/characters.js/chats.js/presets.js/vectors.js）。核心数据流（每次生成前在前端跑一遍）：(1) 角色卡（character card V2/V3，含 description/personality/scenario/depthPrompt/first_mes）作底座；(2) world-info.js 的 checkWorldInfo() 扫描最近 N 条消息+递归缓冲，按关键词命中筛出 lorebook 条目；(3) memory/index.js（Summarize 扩展）把旧消息滚动压缩成一段摘要，挂在某条 message.extra.memory 上；(4) vectors/index.js 对历史做 embedding，rearrangeChat() 检索 top-K 相关旧消息重排进上下文；(5) PromptManager.js / openai.js 按固定位置枚举（before/after char、AN top/bottom、@depth、example-messages）把所有片段拼成最终 prompt，并受 token 预算约束。关键反模式：world-info.js 单文件 260KB/6289 行，引擎+UI+持久化+校验全混在一起，典型 god-file。注入点统一靠 setExtensionPrompt(tag, text, position, depth, role) 这个契约，扩展之间靠它解耦。
- **状态/记忆设计**：三套并行机制，正是我们最该研究的部分。【1 World Info/lorebook = 结构化设定库的条目级条件注入】每条目数据结构（实测 Eldoria.json + WIScanEntry typedef）：key[]（主关键词）+ keysecondary[] + selectiveLogic（AND_ANY/NOT_ALL/NOT_ANY/AND_ALL 四种布尔逻辑）+ content（注入文本）+ position（0 before/1 after char、2-3 AN 上下、4 @任意深度、5-6 example-msg、7 outlet）+ order（同位置内优先级）+ depth + constant（true=常驻"蓝光"条目，无需关键词）+ probability/useProbability（按概率随机注入）+ group/groupWeight/useGroupScoring（同组互斥，只放一个，按权重打分选）+ characterFilter（限定某角色/某 tag 才生效）+ vectorized（此条改由向量召回而非关键词）。核心思想：不把整本设定灌进去，而是按当前对话关键词命中 + token 预算（world_info_budget 默认 25% 上下文，带 budget_cap 硬上限）动态选注。【2 时序状态 sticky/cooldown/delay】（WorldInfoTimedEffects）条目被激活后可"粘住"sticky 之后续 N 轮持续注入、cooldown N 轮内禁止再触发、delay 前 N 轮不准触发；状态持久化在 chat_metadata.timedWorldInfo（按 hash+start+end 记，带 protected 标志）——这正是"伏笔在第 X 章埋下、第 Y 章必须回收"的时序控制原语。【3 滚动摘要 = 记忆压缩】memory 扩展按 promptInterval（每 N 条消息）或 promptForceWords（累计 N 词）触发，增量式：getRawSummaryPrompt 把"上一段摘要 + 自上次摘要以来的新消息缓冲"喂给 LLM 重新摘要，输出限定 {{words}} 词，结果存回 message.extra.memory，并按 token 上限裁掉超出的旧消息。默认提示词明确"若已有摘要，以它为基础扩写新事实"。【4 向量 RAG】vectors 扩展对消息分块（message_chunk_size 默认 400，splitRecursive 按分隔符递归切）、embedding 入库；rearrangeChat 保护最近 protect=5 条不动、检索 insert=3 条最相关旧消息（score_threshold 0.25）按相关度重排注入。数据结构上：设定=JSON lorebook 文件、人物=角色卡 PNG/JSON、运行态记忆=chat_metadata + message.extra.memory、长期检索=向量库。没有显式"时间线/伏笔表"实体——伏笔回收靠 sticky/cooldown 时序 + 人工维护 lorebook 关键词来近似。
- **章节循环**：几乎不存在——这是它和"网文连载 skill"目标最大的鸿沟。代码树里 grep outline/chapter/draft/reviewer/rubric/critique 全部零命中。它是逐回合交互：用户发一句→装配上下文→LLM 出一段→结束。没有大纲→章节→review 的编排，没有多 agent，没有多 rubric 一致性校验。唯一的"质量闭环"是人在环：swipes（对同一轮生成多个候选左右滑动挑选/重 roll）+ 手动编辑消息 + 手动 regenerate。一致性完全依赖人去策展 lorebook 关键词、调摘要频率、看着输出纠偏。换句话说：它把"上下文装配/记忆管理"这一层做到了极致，但"生成-审校循环"这一层整层缺席，留给人或第三方扩展。对我们的启示是反向的：ST 的 World Info+Summarize+Vector 正好可作为我们五层里 L1/L2 的注入与压缩引擎，而 L3 章节契约、L4 生产闭环（自动 review/一致性 grader）是 ST 完全没有、需要我们自建的部分。
- **可借鉴**：
  - [L1 StoryBible（设定/人物/世界观结构化为可条件触发的条目，而非一坨文本）] World Info 条目 schema：key[]+keysecondary[]+selectiveLogic(AND/NOT 四逻辑)+content+position+order+constant+characterFilter——关键词/条件触发的结构化设定注入 — 直接照搬这套条目结构当 StoryBible 的存储与检索单元；constant 字段=必出场的世界观铁律，普通条目=按当前章节关键词按需注入
  - [L2 StateLedger（伏笔/状态的时间感知激活）] sticky/cooldown/delay 时序激活（WorldInfoTimedEffects，状态持久化在 chat_metadata，带 protected） — 网文最值得偷的机制：一个设定/伏笔'激活后持续 N 章'或'回收后冷却 N 章不再提'可直接建模为 sticky/cooldown，把'第3章埋、第10章收'变成可执行的时序约束而非靠记忆
  - [L2 StateLedger（记忆压缩，长程一致性的核心）] 增量滚动摘要：getRawSummaryPrompt 用'上段摘要+新增消息缓冲'重摘要，按 promptInterval/promptForceWords 触发，token 超限裁旧 — 长篇连载必备：每章/每 N 章把已发生剧情压成滚动 state 摘要，增量扩写而非全量重读；阈值=消息数 OR 词数双触发，避免无限增长
  - [L4 生产闭环（上下文工程：确定性优先级+预算闸门）] token 预算硬约束装配：world_info_budget(占比%)+budget_cap，逐条加 content 累加 token 到预算即停，constant/ignoreBudget 优先保留 — 把'注入哪些设定'变成确定性的优先级排序+预算截断，而不是赌模型自己取舍；ignoreBudget=必保留的硬约束（如作者宪法/本章契约）
  - [L2 StateLedger 检索面 / L1 设定召回] Vector RAG over 历史：保护最近 protect 条、检索 insert 条最相关旧消息(score_threshold)重排注入 — 超出上下文的远期剧情/设定用向量召回补回；'保护最近 N + 召回 top-K'是干净的混合策略，避免摘要丢细节
  - [L1 StoryBible（互斥设定的择一注入）] inclusion group + groupWeight + useGroupScoring：同组条目互斥，按权重/匹配分只选一个注入 — 用于'同一槽位多个候选设定只能出一个'——如某角色多种心情/多版本背景，按当前最匹配的择一，省 token 又防冲突
  - [L0 作者宪法 / L3 ChapterContract] Author's Note：固定深度持久注入的导演指令（如'保持暗黑基调、推进主线'） — 在可控 prompt 深度持续注入'本章必须做到 X'的导演级指令，比塞进系统提示更靠近生成位置、更不易被稀释
  - [L4 生产闭环（可组合的上下文装配总线）] setExtensionPrompt(tag,text,position,depth,role) 统一注入契约 + 固定 position 枚举装配顺序 — 所有记忆/设定/检索片段都通过一个带 position/depth/role 的统一接口注入，装配顺序确定可预测——比各模块各塞 prompt 强，便于审计'最终 prompt 里到底有什么'
- **反模式**：关键词触发本质脆弱：代词/同义词/别称漏匹配（角色 key 写了名字，对话里说'他/她'就触发不了），vectorized 条目是补丁但引入非确定性——对一致性要求高的网文是隐患，需用稳定实体 ID + 别名表替代裸关键词 / probability/useProbability 随机注入：给 RP 增加变化性是优点，但把'设定是否进上下文'变成掷骰子，对需要确定一致性的连载是反模式，绝不照搬到设定/伏笔的注入决策 / 递归注入引擎（条目触发条目，配 excludeRecursion/preventRecursion/delayUntilRecursion 多级 + max_recursion_steps）功能强但是调试地狱、非确定性、难以预测最终上下文——对受控流水线属 overengineered，应换成显式依赖声明+一次性解析 / world-info.js 单文件 260KB/6289 行，引擎+UI+持久化+表单校验全混——典型 god-file，违反小文件/分层，新 agent 极难重建心智模型，不可作为架构范本 / 整层缺失自动化质量闸门：没有 outline→chapter→review 编排、没有多 rubric 一致性 grader，所有质量靠人 swipe/编辑——把'写崩了没'的判断完全外包给人，这恰是我们 skill 要补的 L3/L4，不能学它的'不做' / 时间线/伏笔没有显式实体表，靠 lorebook 关键词+sticky 近似+人工维护——规模一大就漂移；我们应建独立的、可被自动校验的 StateLedger 实体
- **OE判定**：分语境看。作为面向 power-user 的交互式 RP 前端，它不算 overengineered——World Info/Summarize/Vector 是经 3 年真实使用打磨的成熟原语，复杂度对得起'让人手动精控每个 token'的产品定位。但其中两处对'受控自动写作流水线'确属过度工程且非确定性，不该照搬：(1) 多级递归注入引擎（delayUntilRecursion 等级 + maxRecursionSteps + 递归缓冲），(2) probability 随机注入。同时 world-info.js 的 260KB god-file 是纯架构债、不可学。净评：偷它的数据模型与机制，别偷它的工程组织与非确定性开关。
- **偷/避**：偷：World Info 条目 schema（关键词/selective 逻辑/position/order/budget）当 L1 StoryBible 注入模型、sticky/cooldown 时序激活当 L2 伏笔时序、增量滚动摘要当 L2 记忆压缩、token 预算硬截断+统一 setExtensionPrompt 装配总线当 L4 上下文工程。避：裸关键词触发的脆弱性（用实体 ID+别名替代）、probability 随机注入、多级递归引擎、260KB god-file，以及它'零自动审校循环、全靠人 swipe'这件事——L3/L4 必须我们自建。

### getzep/graphiti (28055★, active, production)
https://github.com/getzep/graphiti
- **做什么**：为 AI Agent 构建"实时双时态(bi-temporal)上下文知识图谱记忆"的开源引擎（Apache-2.0，是商业产品 Zep 的 OSS 内核，配 arXiv 论文 2501.13956）。把非结构化/结构化输入流增量抽成 实体(节点)+事实三元组(边)+原始 episode(溯源)，每条事实带"有效期窗口"；事实变更时旧事实被 invalidate 而非删除，可查询"现在为真"或"某历史时刻为真"。关键认知：它是记忆底座，不是小说生成器——本身没有大纲→章节→审校的写作循环，也没有多 agent 写作。要把它当作 L2 状态账本来用，生成+审校的 L3/L4 闭环得自己在上面搭。
- **架构**：分层清晰、近似六边形。核心包 graphiti_core/：(1) 数据模型 nodes.py / edges.py —— Node(EpisodicNode 原始数据 / EntityNode 实体 / CommunityNode 社区聚类) + EntityEdge 事实三元组。(2) prompts/ 把每类 LLM 任务做成可版本化的 prompt 函数(extract_nodes / extract_edges / dedupe_nodes / dedupe_edges / summarize_nodes / summarize_sagas / eval)，全部用 Pydantic response_model 约束输出。(3) llm_client/ —— 注入式 LLM 客户端(OpenAI/Anthropic/Gemini/Groq/任意 OpenAI 兼容端点)，带 token_tracker、cache、ModelSize.small/medium 分级(便宜小模型做时间戳抽取这类轻任务)。(4) embedder/ + cross_encoder/ —— 向量化与重排，均为可插拔 client。(5) driver/ —— 端口/适配器：同一套 operations 接口适配 Neo4j/FalkorDB/Kuzu(已弃用)/Neptune 四种图库后端。(6) utils/maintenance/ —— 真正的"一致性引擎"：node_operations / edge_operations(含失效逻辑) / dedup_helpers(MinHash+LSH+Jaccard 确定性去重) / community_operations(label propagation 聚类 + LLM 摘要)。(7) search/ —— 混合检索(语义 embedding + BM25 关键词 + 图遍历 + cross-encoder 重排 + graph-distance rerank)，配 search_config_recipes 预设检索配方。主入口 graphiti.py 的 add_episode() 串起整条摄取管线。外围另有 mcp_server/(给 Claude/Cursor 当记忆的 MCP) 与 server/(FastAPI REST)。并发由 SEMAPHORE_LIMIT 控制以避 LLM 429。
- **状态/记忆设计**：这是它对我们最有价值的部分。三层数据结构：Episode(原始素材，溯源锚点)→ Entity(节点，带 summary 滚动摘要 + 自定义 attributes 字典)→ Fact(边，三元组，带有效期)。核心是【双时态 bi-temporal】：每条 EntityEdge 同时带两条时间轴四个字段——事件时间 valid_at/invalid_at("这事实在故事世界里何时为真/何时不再为真")+ 事务时间 created_at/expired_at("系统何时记录/何时判定其被取代")。事实【从不删除，只失效】，全历史保留，因此既能查"现在为真"也能查"第N章那一刻为真"(point-in-time 时间过滤)。实体侧：EntityNode.summary 是"周边边的区域摘要"，随新事实到来由 LLM 重新生成 = 永远新鲜的"人物当前状态卡"；attributes 由 Pydantic 自定义实体类型约束 = 可定制设定 schema(prescribed)，也支持从数据里 learned。压缩层：CommunityNode 用 label propagation 把实体聚成社区再 LLM 摘要 = "阵营/全局态势"的记忆压缩层。检索：语义+BM25+图遍历+重排的混合检索，不依赖 LLM 重新总结全文。每条派生事实都通过 episodes 字段指回产生它的原始文本 = 完整 provenance。
- **章节循环**：没有传统意义的章节生成/审校循环——graphiti 不生成内容，没有大纲→章节→review 编排，没有多 agent 写作、没有多 rubric 评分(prompts/eval.py 只是给它自己的抽取质量做评测，不是给作品审稿)。它唯一的"循环"是【摄取管线 = 一致性维护循环】：add_episode() → extract_nodes(抽实体) → resolve_extracted_nodes(确定性 MinHash/LSH 去重 + 必要时 LLM 消歧) → extract_edges(抽事实三元组+时间戳) → resolve_extracted_edges(找重复候选 + 找矛盾候选 → LLM 分类 → 纯 Python 做时间区间失效) → extract_attributes_from_nodes(刷新实体摘要/属性) →(可选)update_community(刷新聚类摘要)。换句话说，它把"每吃进一段新文本就重新对齐世界状态、把被推翻的旧设定标失效"这件事做成了流水线。对写网文 skill 的映射：这正是 L4 生产闭环里"章节落地后回写状态账本 + 检出与既有设定的矛盾"那一环的现成参考，但"生成一章""审一章是否写崩"得自己在它之上另建。
- **可借鉴**：
  - [L2 StateLedger] 双时态事实账本：每条 canonical 事实带 valid_at/invalid_at(事件时间)+ created_at/expired_at(事务时间)，变更只失效不删除，支持 point-in-time 查询 — 最该偷的一条。'谁还活着、X和Y什么关系、门派归属'这类随剧情变的事实做版本化追踪；point-in-time 让生成第N章时只喂'截至第N章为真'的事实，天然防剧透/防伏笔提前泄底，也防前后设定打架。
  - [L4 生产闭环(校验器)] 矛盾检测 = 受控信号 + 确定性兜底：LLM(resolve_edge prompt)只输出 duplicate_facts/contradicted_facts 两个 idx 列表，真正的失效判定由纯 Python resolve_edge_contradictions() 做时间区间运算(谁的有效期早于谁就给旧边写 invalid_at/expired_at) — 教科书级'LLM 当子程序、确定性代码立刻夺回方向盘'。失效这种硬不变量绝不交给 LLM 散文输出，只让它做分类。我们的章节一致性校验该照抄此结构：模型只判'矛盾/不矛盾+指哪条'，账本更新由代码做。
  - [L2 StateLedger(角色/实体注册表)] 确定性优先的实体去重：先用 MinHash + LSH 分桶 + Jaccard 做模糊名字匹配(blake2b 哈希 shingle，低熵短名过滤)，命中才退回 LLM 消歧 — 把'张三/小张/三哥/那个剑客'归并成同一角色实体，绝大多数靠便宜的确定性算法解决，LLM 只兜模糊尾巴。省 token 又稳定，可直接做人物卡的实体解析。
  - [L1 StoryBible / L3 ChapterContract] Pydantic 自定义实体/边类型(prescribed ontology) 约束抽取 — 把'人物/地点/势力/物品/功法/关系-类型'定义成 typed schema 去约束抽取，等于给设定集上类型。L1 写宪法级 schema，L3 在每章契约里收紧允许的实体/关系类型。
  - [L2 StateLedger] 实体 summary 随新事实滚动重生成 = 永远新鲜的角色状态卡 — 不用回读整本书就能拿到'某角色当前是什么状态'，喂给生成器做上下文。比把全文塞进 context 省得多。
  - [L2 StateLedger / L4 审校] 每条派生事实指回原始 episode 的 provenance 链 — 每条状态事实链接到'第几章哪段确立的'，让审校能核验'文本是否真的这么写过'，可追溯、可问责，反幻觉。
  - [L2 StateLedger(全局态势/记忆压缩)] 社区聚类(label propagation)+ LLM 摘要的分层压缩层 — 长篇连载到几百章时，用聚类+摘要生成'阵营全景/势力格局'的鸟瞰层，避免状态账本一味变长。即长程记忆压缩。
  - [其他(工程基建)] 注入式 LLM client + ModelSize 分级 + SEMAPHORE_LIMIT 并发节流 — client=None 自动建真客户端、测试传 fake；轻任务(时间戳抽取)走 small 模型省钱；信号量控并发避 429。符合我们 AI-pipeline 注入式客户端的工程规范。
- **反模式**：重基建：默认绑图数据库(Neo4j/FalkorDB/Kuzu/Neptune 四套 driver)+ embedding + cross-encoder。对单作者网文 skill 来说，为了'记设定'去起一个图库+四后端+向量+重排是巨大杀鸡用牛刀，JSON/SQLite 状态账本能拿下 80%。 / 每次摄取触发一大串 LLM 调用(抽节点/抽边/去重/属性/时间戳/摘要/社区)，token 贵且慢(故需 SEMAPHORE_LIMIT 防 429)。按章摄取一本长篇成本不低。 / 四种图库后端 + Kuzu 已官方弃用(emits DeprecationWarning)，维护面是多数用户用不上的复杂度。 / 它根本不解决'写得好不好/会不会崩'——纯记忆底座。把它当作'小说一致性'的开箱即用方案是范畴错误：它只保证'状态被准确记录与失效'，不保证生成质量。 / 抽取面向客观事实三元组(Entity-REL-Entity)，对小说里大量'情绪/氛围/单实体细节/隐喻'天然不友好(prompt 里明确要丢弃 'Alice feels happy' 这类无第二实体可锚的事实)——直接拿来记'伏笔/情绪线/主题意象'会丢信息。
- **OE判定**：就其自身目标(生产级、可规模化的 Agent 记忆)而言，复杂度是值得的且分层干净——prompts/llm_client/driver/search 都是清楚的端口与适配器，注入式 client、Pydantic 受控输出、确定性去重+确定性失效都是高质量工程。但对'单作者约束 AI 写中文网文连载'的 skill 而言，作为基建它是 overengineered：图库+多后端+向量+cross-encoder 这套栈不该照搬。正确姿势是偷它的数据模型与算法(双时态、只失效不删、provenance、point-in-time 查询、确定性优先去重、矛盾=受控信号+代码兜底)，用 SQLite/JSON 重实现一个轻量 L2 状态账本即可。
- **偷/避**：偷：双时态'只失效不删除'的事实账本 + provenance + point-in-time 查询 + '矛盾检测=LLM只出idx信号、Python做区间失效' + MinHash/LSH 确定性优先去重，拿来当 L2 StateLedger 的设计蓝本；避：别照搬图数据库/embedding/cross-encoder 这套重栈，用 SQLite/JSON 把上述思想重写即可。

### joonspk-research/generative_agents (21661★, stale, research-code)
https://github.com/joonspk-research/generative_agents
- **做什么**：斯坦福"Smallville/Generative Agents"论文（arXiv:2304.03442）的官方配套代码：在一个2D瓦片小镇里跑25个由LLM驱动的智能体，让它们各自感知环境、规划日程、对话、回忆、反思，涌现出可信的社会行为（如自发组织情人节派对）。它本质是"可信人类行为的交互式拟像"——一个多智能体社会模拟器，不是写作工具。但它是"叙事级长程记忆"的学术母范式：memory-stream + 三因子检索(recency×importance×relevance) + reflection(把零散记忆升华为高层洞察) + 分层规划，被后续几乎所有"AI长篇/agent记忆"工作引用。
- **架构**：代码分两半：environment/frontend_server（Django+瓦片地图+精灵+回放，写作场景几乎全可丢弃）和 reverie/backend_server（真正的认知引擎）。后端核心是 Persona 对象，由两类子模块组成。记忆结构 persona/memory_structures/：①associative_memory.py = Memory Stream（长期记忆），②scratch.py = 短期/工作记忆+人物卡，③spatial_memory.py = 已访问地点的树状心智地图。认知模块 persona/cognitive_modules/ 六件套：perceive→retrieve→plan→reflect→execute(+converse)。主循环在 persona.py 的 move() 里，每个game step（=10秒游戏时间）按固定顺序跑 perceive(感知周边事件)→retrieve(从记忆流取相关上下文)→plan(长期日程+短期分解)→reflect(累计重要度触发时升华洞察)→execute(落地为地图动作)。所有对LLM的调用集中在 persona/prompt_template/run_gpt_prompt.py，模型客户端封装在 gpt_structure.py（get_embedding等），prompt还按 v1/v2/v3_ChatGPT 目录分版本管理，并有 safety/ 子目录。整套是"确定性Python循环把LLM当子程序逐tick调用"，不是LLM自由发挥。
- **状态/记忆设计**：三层记忆+一张人物卡，是对我们最有价值的部分。(1) Memory Stream（associative_memory.py）：长期记忆是一串 ConceptNode，每个节点 = 一个 (subject,predicate,object) 三元组 + 自然语言 description + 元数据：created/last_accessed/expiration 时间戳、poignancy(重要度1-10，写入时由LLM打分并存盘)、keywords、embedding_key(指向embedding)、depth(0=原始event/chat，≥1=反思层级)、以及关键的 filling = 该想法所依据的源节点ID列表(出处/证据链)。三条并行序列 seq_event/seq_thought/seq_chat，外加 kw_to_* 倒排索引和 kw_strength 关键词强度，落盘为 nodes.json+embeddings.json+kw_strength.json。本质是"只追加的事件日志 + 由其蒸馏出的洞察节点"。(2) Scratch（scratch.py）既是工作记忆也是人物卡，且明确做了身份分层注释：innate=L0永久核心特质、learned=L1稳定特质/背景、currently+lifestyle+living_area=L2可变当前状态；再加当前动作状态(act_address/act_description/act_event三元组/chatting_with…)和全部超参(检索权重、衰减、反思阈值)。(3) Spatial memory：只记得去过的地方的 world:sector:arena:object 树。关键缺口：没有任何全局"大纲/时间线/伏笔/谁知道什么"的剧情账本——一致性完全靠"检索时把相关旧记忆捞回来"涌现，而非靠顶层情节控制。这对模拟可以，对受控网文连载恰恰缺了最该有的那层。
- **章节循环**：没有章节/大纲/审校循环——它是模拟器不是写作工具，最接近的是"每tick认知循环"。(1) 分层规划(plan.py)：daily_req(今日目标列表)→f_daily_schedule(每天开始时一次性生成的逐小时长期计划)→运行中按需把当前小时递归分解到分钟级动作；并保留 f_daily_schedule_hourly_org(未分解的原始版)，使得被打断时不会毁掉整体计划。即"长期计划+短期递归分解、原始计划保持完整"。(2) 反思(reflect.py)：当累计重要度跨过阈值(importance_trigger_max=150，事件到来时递减触发)→run_reflect：先让LLM从最近高重要度记忆里提~3个"焦点问题"(focal points)→对每个问题用三因子检索捞相关节点→让LLM产出5条洞察、每条洞察必须附"证据=源节点ID"→存为 thought 节点(depth+1，30天过期)。反思可对反思再反思(depth累加)，形成递归洞察树。(3) 完全没有多agent/多rubric/critic审校：单趟生成，没有"写完再审一遍"的环节，"质量校验"只隐式来自检索把相关事实捞回来做grounding。对我们而言：反思=可借鉴的"阶段性把流水账压缩成story-so-far摘要"机制；但"生成→审校→重写"这条我们最需要的闭环，这个repo里压根没有，要自己补。
- **可借鉴**：
  - [L0作者宪法 + L1 StoryBible人物卡] Scratch里把人物身份显式三分：innate(永久核心)/learned(稳定背景)/currently(可变当下)，并和动作状态、超参同存一个结构 — 直接照搬这个分层语义：永久设定/稳定背景/当前状态分开存，改'当前状态'不污染'核心设定'，正是我们人物卡该有的字段切分
  - [L2 StateLedger] ConceptNode = (S,P,O)三元组 + NL描述 + created/last_accessed/expiration + poignancy重要度 + keywords + embedding + depth + filling(证据源ID) — 把每个状态变更/事件都建成'带时间戳+重要度+出处的只追加typed记录'，这就是StateLedger的节点schema蓝本
  - [L2 StateLedger / L4生产闭环] filling/evidence出处链：每条反思洞察都强制引用其依据的源节点ID — 反幻觉利器——任何派生结论必须可溯源到原始事件，使一致性可审计；网文里'这个伏笔来自第几章'同理
  - [L3 ChapterContract] 三因子检索 recency(0.99^i指数衰减)×importance(poignancy)×relevance(embedding余弦)，各自归一化到[0,1]后加权(persona权重×全局gw=[0.5,3,2])取TopN，命中即刷新last_accessed — 写每章前别把整本设定塞进context，用三因子从StateLedger检索Top-N相关事实拼'本章需要记住的'上下文窗口；权重可调
  - [L2 StateLedger / L3 ChapterContract] importance阈值触发的反思：累计重要度越过门槛→LLM提焦点问题→检索→蒸馏5条高层洞察存回记忆 — 长连载的记忆压缩：定期把N章流水账升华成'故事至此'高层摘要节点，防context随章数膨胀
  - [L2 StateLedger] 写入时即用LLM给事件打poignancy(1-10)并存盘，而非检索时才算 — 重要度作为持久字段预存，决定哪些事实在后续更易被召回——区分'主线关键事件'与'路人对话'
  - [L3 ChapterContract / L4生产闭环] 分层规划:daily_req→逐小时schedule→按需分解到分钟，且保留未分解原版(f_daily_schedule_hourly_org) — 大纲→章节节拍→场景的递归细化，且始终保留原始大纲，使局部即兴不破坏整体弧线
  - [L4生产闭环] LLM客户端封装(gpt_structure.py)+prompt模板按v1/v2/v3目录版本化+safety子目录 — prompt当作版本化文件资产管理、模型后端可替换，符合'把LLM当可注入子程序'的工程纪律
- **反模式**：把模拟器脚手架(Django前端、瓦片maze、path_finder寻路、spatial_memory、精灵回放)当核心——这些对写作约90%无用，切勿连锅端 / 每写一条记忆都要触发多次LLM调用(打poignancy分+生成embedding+抽三元组)，逐句这么干对长篇生成又慢又贵，必须批处理 / 检索每tick都对整条扁平memory stream重新排序/重算relevance，O(n)全扫描，历史一长就退化；new_retrieve里还有大量print调试刷屏，典型研究代码 / 缺最关键的顶层剧情账本：没有大纲/时间线/伏笔/谁知道什么的结构——而这恰是受控网文最需要的；它的一致性是bottom-up涌现，不是top-down情节控制，控制方向与'授权写作'相反 / 魔法权重硬编码(gw=[0.5,3,2]、阈值150)且注释自承'将来应该用RL学'——属未经原理化的手调 / 整条流程零review/critic/rubric——没有'生成后审校'，对追求质量的写作是结构性缺失 / generate_insights_and_evidence 里 try/except 直接 return {'this is blank':'node_1'} 静默吞掉LLM解析失败——违反'错误要响亮'的工程准则
- **OE判定**：分用途看：就它自己的目标(可信多智能体社会模拟)而言，复杂度是奠基性的、值得的——memory-stream/反思/三因子检索是被反复引用的范式。但对我们的目标(约束AI写好中文网文连载)它是严重overengineered且范式错配：它是'行为模拟器'不是'故事控制器'，~90%代码(maze/寻路/Django/精灵/spatial)是死重，且刻意缺少授权写作必需的top-down大纲/伏笔/时间线控制。结论：偷它的四个IDEA(分层人物卡、带重要度与出处的只追加记忆流、三因子检索、重要度触发的反思压缩)，用精简实现重写，绝不照搬其模拟脚手架与bottom-up涌现模型。
- **偷/避**：偷四个机制：分层人物卡(innate/learned/currently)、带poignancy+出处链(filling)的只追加typed记忆流、recency×importance×relevance三因子检索、重要度触发的'反思→蒸馏洞察'压缩；避开整个模拟器脚手架和它的bottom-up涌现范式——网文要的是它故意没做的那层top-down大纲/伏笔/时间线账本。

### Narcooo/inkos (7617★, active, usable-tool)
https://github.com/Narcooo/inkos
- **做什么**：Story Creation AI Agent：已发布到 npm（@actalk/inkos）、有 Web 版+Studio(GUI)+TUI+CLI 四种入口的中文故事创作系统。覆盖长篇连载、独立短篇、剧本、同人/番外、仿写续写、开放世界互动游戏(InkOS Play)。本领域 GitHub 最高 star，入选 Kimi 开源合作伙伴。核心卖点：10+ 专职 agent 编排 + 37 维连续性审计 + 去 AI 味 + 文风克隆 + 三层长期记忆。AGPL-3.0。
- **架构**：TS monorepo（pnpm workspace），三个 package：`packages/core`（全部领域逻辑，纯净、可单测）、`packages/cli`（commander 原子命令 + TUI）、`packages/studio`（React+shadcn Web 工作台 + SSE API server）。core 内部分层清晰：`models/`（全部 Zod schema：runtime-state/input-governance/chapter/book-rules/state）、`agents/`（约 25 个 agent 文件：architect 建书、planner 规划、composer 编排、writer 写手、continuity 审计、reviser 修订、settler/observer 抽事实、state-validator 校验、polisher/normalizer、style-analyzer、radar 趋势）、`state/`（manager/state-reducer/state-projections/memory-db/state-validator）、`pipeline/`（runner + chapter-review-cycle + chapter-truth-validation + chapter-state-recovery + short-fiction-runner + scheduler 守护进程）、`interaction/`（统一 action-surface：Studio/TUI/CLI/外部 agent 都走 `inkos interact` 同一执行内核 + truth-authority 真值等级）、`play/`（开放世界 reducer/store/agents）、`interactive-film/`（互动影游图谱）、`utils/`（governed-working-set、memory-retrieval、context-filter、hook-governance 等治理层）。每本书在磁盘上是一个 `story/` 目录，权威真值全部落盘成 JSON+Markdown+SQLite。LLM 客户端经 provider bank 抽象（50+ 国内外 endpoint），支持按 agent 粒度多模型路由（writer 用强模型、auditor 用便宜模型）。
- **状态/记忆设计**：这是 inkos 最值得偷的部分，三层权威真值 + 治理层：

【三层存储】每本书：(1) `story/state/*.json` 权威结构化状态，全部 Zod schema 校验；(2) `story/*.md` 人类可读投影（current_state.md / pending_hooks.md / chapter_summaries.md / character_matrix.md）——只读投影，不是真值；(3) `story/memory.db` Node22+ SQLite 时序记忆库，做按相关性检索的加速层。

【双时态事实账本】CurrentStateFact = {subject, predicate, object, validFromChapter, validUntilChapter(nullable), sourceChapter}——即带"生效区间"的 SPO 三元组。这让审计员能精确抓"角色拿出两章前已丢失的武器""记起从未亲眼见过的事"。

【伏笔账本 + 生命周期治理】HookRecord = {hookId, startChapter, type, status(open/progressing/deferred/resolved 状态机), lastAdvancedChapter, expectedPayoff, payoffTiming(immediate/near-term/mid-arc/slow-burn/endgame), dependsOn, coreHook, halfLifeChapters, advancedCount, promoted}。配 hook-governance：admission control 拒绝"无回收信号的伏笔"和"重复家族伏笔"（用 term + 中文 bigram 重叠判重）；collectStaleHookDebt 按 halfLife/overdue 算出"欠债伏笔"逼 planner 处理。这是防"挖坑不填"的核心工程。

【delta + schema 写入】settler/reflector 不输出整份 markdown，只输出 RuntimeStateDelta(JSON)：hookOps(upsert/mention/resolve/defer) + currentStatePatch + chapterSummary。代码层 applyRuntimeStateDelta 做 immutable 更新 + validateRuntimeState 结构校验 + 单调章节守卫（delta.chapter 必须前进，否则报错）+ 重复 summary 守卫。坏数据直接 throw 拒绝，"不会滚雪球"。

【真值等级】truth-authority.ts 把 8 个核心文件分级：direction(author_intent/current_focus) > foundation(story_bible/volume_outline) > rules(book_rules) > runtime-truth(current_state/pending_hooks) > memory(chapter_summaries)——明确谁能覆盖谁。

【上下文预算】context 分 protected/compressible 两层，trace.json 记录 token 预算；memory-retrieval 从 goal+outlineNode+mustKeep 抽 query term 做相关性检索，governed-working-set 把伏笔过滤到"被选中+本章议程+最近窗口"的工作集，避免全量注入导致旧历史淹没当前指令。每章自动快照，`write rewrite` 可回滚。注意一个刻意设计：伏笔故意不走 SQLite 加速路径而留在 JSON 权威路径，因为 SQLite 表存不下 promoted/core/dependency 元数据。
- **章节循环**：长篇默认链路：规划(plan) → 编排(compose) → 写作(write) → 审计(audit) → 必要修订(revise) → 状态结算(settle/validate)，落在 pipeline/runner.ts + chapter-review-cycle.ts。

【plan】Planner 读 author_intent + current_focus + 记忆检索结果，产出 chapter intent（goal + mustKeep + mustAvoid + "Hook Agenda"：Must Advance / Eligible Resolve / Stale Debt 三组伏笔 id），写成 `runtime/chapter-XXXX.intent.md`（给人看）。

【compose】Composer 按任务从结构化状态+控制文档选上下文，编译 rule-stack（hard/soft/diagnostic 三段 + global/book/arc/local 优先级层 + override 边），输出 context.json / rule-stack.yaml / trace.json（给系统执行/调试）。"先编译，再写作"，而非把 brief+卷纲+规则糊成一坨 prompt。

【write】Writer 基于精简上下文写正文；动笔前输出自检表（上下文/资源/伏笔/风险），写完输出结算表。

【audit】Continuity Auditor 按 37 维检查（OOC、时间线、设定冲突、战力崩坏、数值、伏笔、节奏、文风、信息越界、词汇疲劳，去AI味维度 20-26：段落等长/套话密度/公式化转折/列表式结构/节奏单调，敏感词，同人/跨书一致性 28-37 等）。返回 AuditIssue[]，每条带 severity(critical/warning/info) + repairScope(local/structural/unknown) + overallScore(0-100)。

【review cycle】runChapterReviewCycle 的 assess() 把 LLM 审计 + 确定性检查（ai-tells 正则、敏感词、跨章重复、~10 条 post-write 硬规则 spot-fix、长度区间）合并打分；DEFAULT_MAX_REVIEW_ITERATIONS=1（默认只修一次，可调 writing.reviewRetries），PASS_SCORE_THRESHOLD=85，NET_IMPROVEMENT_EPSILON=3——修订只有"净改善 ≥3 分"才采纳，否则回退。长度治理独立成专门 normalize step（仅 hard-range 偏离时跑、最多 1 pass、绝不硬截断），不混进 reviser 的 issue。

【settle/validate】结算后 validateChapterTruthPersistence 用 State Validator agent 交叉比对新旧 state/hooks；失败时走 chapter-state-recovery：重试结算或把本章标 "state-degraded" 并 carry-forward 旧真值——annotate-and-continue，不中断整本书。

守护进程 `inkos up` 后台循环自动写章；非关键问题自动推进，需人判断的暂停并 Telegram/飞书/企微/Webhook 推送。
- **可借鉴**：
  - [L2 StateLedger] 双时态 SPO 事实账本：CurrentStateFact{subject,predicate,object,validFromChapter,validUntilChapter,sourceChapter}，事实带生效区间 — 用'生效到第N章'精确捕捉'用了已丢失的武器/知道还没发生的事'这类一致性崩坏；diff 便宜、可机器校验。比纯文本设定集强一个量级
  - [L2 StateLedger（账本）+ L3 ChapterContract（Hook Agenda 注入章节意图）] 伏笔账本 + 准入/陈旧治理：HookRecord 状态机(open/progressing/deferred/resolved)+payoffTiming+halfLife，admission 拒绝无回收信号/重复家族伏笔，collectStaleHookDebt 算欠债逼 planner 处理 — 防'挖坑不填'的核心机制，直接可借鉴成我们的伏笔层；'欠债逼还'的反向压力是网文连载最痛的点
  - [L2 StateLedger + L4 生产闭环] delta-not-snapshot 写入：LLM 只吐 JSON delta，代码 applyDelta 做 immutable+Zod 校验+单调章节守卫，坏数据直接拒绝 — 完全符合'硬不变量由代码追加、不信任 LLM'；把 LLM 当只能提议的子程序，状态机由确定性代码守。我们的 StateLedger 更新必须照搬这个边界
  - [L3 ChapterContract] 编译式章节契约：ChapterIntent(goal/mustKeep/mustAvoid)+ContextPackage(带 reason 的选源)+RuleStack(hard/soft/diagnostic+优先级层+override 边)+ChapterTrace(protected/compressible token 预算)，先编译成 4 个文件再写 — 这就是 ChapterContract 的成熟落地范例：把'写什么/带什么上下文/守什么规则/为什么'拆成可审计产物，而非一坨 prompt。trace.json 的可调试性尤其值得抄
  - [L2/L3] protected/compressible 上下文分层 + 相关性检索 + governed working set（伏笔只保留 选中+议程+最近窗口） — 对抗长篇 context 膨胀的具体手段，避免旧历史淹没当前指令；可直接映射到我们的记忆压缩层
  - [L0 作者宪法/L1 StoryBible/L2 的优先级契约] 真值等级 truth-authority：direction>foundation>rules>runtime-truth>memory，每个文件分级 — 把'谁能覆盖谁'显式化，解决多源设定打架——L0 作者意图能压 L2 运行状态，避免 AI 用旧状态顶掉作者新指令
  - [L4 生产闭环] 混合 LLM+确定性审计：37 维 LLM 连续性审计 与 代码级检查(ai-tells 正则/敏感词/跨章重复/~10 条硬规则 spot-fix/长度)并行，修订仅在净改善≥epsilon 才采纳且默认只 1 轮 — 审校循环的工程骨架：确定性 oracle 兜底 + LLM 软判 + '净改善才采纳'防止越改越烂。我们的章节 review 循环可照搬这套打分/采纳门槛
  - [L1 StoryBible(style profile) + L4] 去 AI 味双管：写手 prompt 内置词汇疲劳表+禁用句式+文风指纹注入（源头），审计维度 10/20-23/26 + revise --mode anti-detect（事后）；文风克隆用统计指纹(句长分布/词频/节奏)+LLM 风格指南 — '源头预防+事后检测'双层防 AI 腔；统计指纹做文风克隆是可直接复用的轻量方案
  - [L0 作者宪法] 作者宪法持久化：author_intent.md(长期)+current_focus.md(近期)是可长期编辑的控制文档，不是建书时一次性 prompt — 把'这本书长期想成为什么'落成持久文件并参与每章规划，正是 L0 的正确形态——意图不只在建书时生效一次
- **反模式**：37 维连续性审计塞进（基本）单次 LLM pass：维度严重重叠（20/26 都是节奏，21/22/23 都是 AI slop），LLM 注意力预算撑不住 37 个并行检查——'维度稀释'，37 这个数字营销味大于真实区分度。应收敛到 8-12 个正交检查，并把确定性可查的(词汇疲劳/段落等长/列表结构)从 LLM 维度里拆出去走代码 / 8 个文件的伏笔子系统(hook-arbiter/governance/health/ledger-validator/promotion/stale-detection/lifecycle/policy)——一个伏笔账本被过度拆分，认知负担高，疑似按 phase 累积出来的 / 三重状态表示(JSON 权威 + Markdown 投影 + SQLite memory.db)= 3 个同步面，且不得不让伏笔豁免 SQLite（存不下元数据）——说明加速层是半成品，pipeline-runner-memory-sync/index-notify-lazy 等测试就是同步 bug 的疤 / 大量 hotfix 疤痕：phase5-hotfix/phase7-hotfix/v13-hotfix-round4/phase5-cleanup 这类测试名 = 反应式打补丁累积，不是干净演进；3 个月冲到 7617★ 的代价是结构债 / '10 个专职 agent'的叙事夸大了实质：多数 agent 是同一个 LLM client 上的 prompt 变体 + 确定性胶水，不是真正独立的智能体 / 默认 reviewRetries=1：被大肆宣传的 37 维审计，自动闭环其实只修一轮，大量 issue 是抛给人工的 flag 而非自动闭合——成本上合理，但削弱了'autonomous'的成色
- **OE判定**：核心概念不 overengineered，反而是这个领域罕见的'对的工程抽象'：双时态事实账本、伏笔生命周期治理、delta+Zod 校验的状态写入、编译式章节契约(intent/context/rule-stack/trace)、protected/compressible 上下文预算、混合 LLM+确定性审计——这些都是'防 AI 写崩'的正确原语，复杂度值得。但实现层带明显 overengineering 疤痕：8 文件的伏笔子系统、37 个重叠维度硬塞一个 prompt、三重状态表示+同步缝、phase5/7/v13 hotfix 堆叠。结论：偷它的架构概念（高价值），别照抄它的实现规模（按 phase 累积的 sprawl）。对一个要做成 skill/workflow 而非大型 monorepo 的项目，应把同样的概念压到 1/3 的文件数。
- **偷/避**：偷：分层真值模型——双时态 SPO 事实账本 + 带准入/欠债治理的伏笔账本 + 'LLM 只吐 JSON delta、代码做 Zod 校验+不变量' 的状态写入 + 编译式章节契约(intent/context/rule-stack/trace + protected/compressible token 预算) + '净改善才采纳' 的混合审校循环。避：把 37 个重叠维度塞进单次 LLM 审计、以及 8 文件的伏笔子系统——收敛成 8-12 个正交检查（确定性 vs LLM 分流）和单一 hook-ledger 模块。

### YILING0013/AI_NovelGenerator (5456★, active, usable-tool)
https://github.com/YILING0013/AI_NovelGenerator
- **做什么**：基于 LLM 的长篇中文小说生成 GUI 工具（tkinter/customtkinter）。用"设定工坊→章节蓝图→分阶段章节生成→定稿回写状态"的四步流水线，专攻长篇一致性：把世界观/角色/三幕情节/章节目录全部落盘成 .txt，章节生成时只读这些状态、定稿时再回写。配 Chroma 向量语义检索做长程召回，consistency_checker.py 做事后一致性审校。5456★/967 fork，社区驱动；GitHubDaily 推荐过，是该赛道事实标杆。
- **架构**：核心是"分层落盘 + 写前只读/写后回写状态机"，全部用自由文本 .txt 当持久层，无数据库。模块映射：novel_generator/architecture.py = Step1 设定工坊（雪花写作法分步：core_seed→character_dynamics→world_building→plot_architecture，逐步写 partial_architecture.json 可续跑，最终合成 Novel_architecture.txt）；blueprint.py = Step2 章节蓝图（按 max_tokens 预算分块生成 Novel_directory.txt，长篇时只保留最近100章目录防 prompt 溢出）；chapter.py = Step3 章节草稿（build_chapter_prompt 把架构+目录+全局摘要+人物状态+近3章摘要+前章结尾800字+向量检索过滤结果，连同"当前章+下一章"双合约塞进 next_chapter_draft_prompt）；finalization.py = Step4 定稿（这一步才回写 global_summary.txt 和 character_state.txt 并 update_vector_store）；consistency_checker.py = 独立只读审校 pass；prompt_definitions.py(700+行) 集中所有 prompt，并有中英双份(prompt_definitions_en.py)；common.py 的 invoke_with_cleaning 做重试+剥 ```/<think> 标签；llm_adapters/embedding_adapters 是 provider 适配层；config.json 的 choose_configs 把 architecture/outline/draft/final/review 五类任务路由到不同模型。orchestration 逻辑和 UI 耦合在 ui/generation_handlers.py。
- **状态/记忆设计**：见 state_memory_design 字段（global_summary 滚动摘要 capped 2000字 + character_state 树状人物卡全量重写 + Chroma 向量库 k=2 召回；plot_arcs 伏笔 ledger 是空壳从不回写；状态全自由文本无 schema、无确定性校验）。
- **章节循环**：见 chapter_loop_design 字段（线性四步、写前只读写后回写、当前+下一章双合约、近章三件套上下文、可选独立审校 detection-only）。
- **可借鉴**：
  - [L2 StateLedger] 写前只读/写后回写状态机：草稿阶段只读 state 文件、绝不 mutate；只有显式'定稿'才回写 summary/人物卡/向量库。草稿可反复重生成而不污染长程状态。 — 我们的章节闭环应照搬：draft 是纯函数读 ledger，commit 才写 ledger，二者严格分离。
  - [L3 ChapterContract] 当前章+下一章双合约：把本章和下一章的结构化字段(定位/作用/悬念/伏笔/转折/简述)同时注入草稿 prompt，逼模型保证承上启下与伏笔衔接。 — ChapterContract 不能只给本章；带上 N+1 章的合约能显著降低断裂/伏笔失衔。
  - [L2 StateLedger] 结构化人物卡固定树状模板 + '在已有基础上增删、不改结构'的更新指令。 — 思路对(格式稳定的人物卡)，但应升级为带 schema 的 JSON+diff 更新，而非自由文本全量重写。
  - [L2 StateLedger] 滚动全局摘要硬性 capped 2000字(记忆压缩)，每次定稿融合新章重写。 — 长程记忆压缩的最简实现；可借鉴 cap 上限思路，但要分层(全书摘要 vs 卷摘要 vs 近章原文)。
  - [L4 生产闭环] 多模型任务路由 choose_configs：architecture/outline/draft/final/review 各绑不同模型——便宜模型起草、贵模型定稿与审校。 — 成本/质量分层非常实用，直接抄进我们的 skill 配置：草稿用快模型、定稿/审校用强模型。
  - [L1 StoryBible] 雪花写作法分步设定生成 + partial_architecture.json 写前检查点(逐步落盘、已完成步骤跳过、全成功后删除)。 — 可续跑的 StoryBible 构建：每一步 checkpoint，崩了能从断点继续——长流水线韧性范式。
  - [L0 作者宪法] 输出纪律：每个 prompt 结尾'仅返回X文本，不要解释' + invoke_with_cleaning 确定性剥离 ```/<think> 标签并空结果重试。 — 把 LLM 输出当子程序：代码侧确定性后处理，不信任模型自觉。符合 AI-pipeline 不变量。
  - [L1 StoryBible] 章节蓝图按 max_tokens 预算分块生成、长篇只回填最近100章目录防 prompt 溢出。 — 超长篇蓝图生成的窗口管理技巧，分块+滑窗值得借鉴。
  - [L4 生产闭环] 独立只读审校 pass：把设定/人物/摘要/伏笔/最新章一起喂一个 consistency prompt 列冲突，用便宜模型。 — 审校与生成解耦是对的；但要从 detection-only 升级成 rubric+自动触发重写的闭环。
- **反模式**：伪约束当真约束：next_chapter_draft_prompt 里写'相似度>40%必须重构、20-40%替换3要素、历史章节相似度不超20%'，但没有任何代码测量相似度——全靠 LLM 自我断言。apply_content_rules 只用正则扫章节号按'章距'打 [SKIP]/[MOD40%]/[OK] 标签，是脆弱字符串启发式，不是真语义查重。违反'硬不变量必须代码强制'。 / 伏笔管理是空壳：README 宣称 Step4 更新 plot_arcs.txt(伏笔/未解决冲突 ledger)，实测 finalize 从不写它、consistency 检查硬编码 plot_arcs=''。伏笔只静态写死在章节蓝图的'埋设/强化/回收'字样里，从不被追踪回收。文档与代码漂移。 / 状态全自由文本无 schema：character_state/global_summary 都是 .txt，无法程序化查询/校验一致性，唯一'校验'就是再喂回 LLM 问一遍——没有确定性 oracle。一致性是'感觉对'不是'被证明对'。 / 人物卡全量重写：update_character_state_prompt 让 LLM 整篇重输出，无 diff、无字段级校验，长篇下必然漂移/丢字段/token 膨胀。应做结构化 diff 更新。 / 审校只检测不闭环：consistency_checker 单 pass 单 prompt，输出打日志给人看，无分级 rubric、无 auto-fix、无重生成触发。 / retrieval_k 默认2 极小：号称'向量语义检索维护长程一致性'，实际召回面非常窄，长程一致性保障被高估。 / prompt 全硬编码在单个 700+行 prompt_definitions.py 且中英双份复制——双份漂移、难维护、难做版本化/AB。 / orchestration 与 GUI 耦合在 ui/generation_handlers.py，难以无头/批量/自动化运行，CI 与脚本化困难。
- **OE判定**：不 overengineered，反而工程深度不足。它的复杂度几乎全堆在 prompt 措辞（相似度百分比、认知颠覆星级、伏笔操作话术）而非可验证的代码机制上——典型 prototype/research 代码：用自由文本落盘+'再问一次 LLM'冒充状态管理与一致性校验。值得的复杂度是'设定/蓝图/状态/章节'四层清晰落盘 + 写前只读/写后回写的分离；不值得的是把约束写进 prompt 当成已执行、把伏笔 ledger 留成空壳。对一个 5456★ 的工具，内部一致性保障的鲁棒性明显落后于其 UI 完成度。
- **偷/避**：偷：五层落盘分层 + 写前只读/写后回写状态机 + 当前章·下一章双合约 + 多模型任务路由(便宜起草贵定稿) + 雪花式可续跑设定生成(partial checkpoint)；避：用 prompt 里的相似度%/伏笔回收当成已执行的约束、状态全自由文本无 schema、伏笔 ledger 空壳、一致性只 detection 不闭环、人物卡全量重写。

### lingfengQAQ/webnovel-writer (5307★, active, usable-tool)
https://github.com/lingfengQAQ/webnovel-writer
- **做什么**：跑在 Claude Code 上的长篇中文网文创作插件（v6.2.0，8 个 /webnovel-* 命令 + 3 个 subagent）。目标单一且与本 skill 高度同构：让 AI 写到几百章（号称支持 200 万字量级）仍记得住设定、接得住伏笔、守得住大纲，专门对抗 LLM 的「遗忘」和「幻觉」。整条流水线已串好：init 初始化设定/总纲 → plan 拆卷拆章补时间线 → write 一条龙写章（备上下文→起草→审查→润色→提取事实→提交→备份）→ review 多维审查 → query 查状态 → learn 沉淀经验 → dashboard 只读可视化 → doctor 健康自检。Python（465 文件、~190 个模块、配套数百个 pytest 用例 + 行为 eval），单维护者，正在公示 v7 重构 RFC。
- **架构**：五条主线分层清晰，核心是「写前合同 + 写后提交」的事件溯源式状态机。(1) 入口层=8 个 Claude Code Skill 命令（skills/webnovel-*/SKILL.md，纯 markdown 编排）。(2) Agent 层=3 个 subagent 各司一职：context-agent（读，产「写作任务书」）、reviewer（审，5 维事实审查只返 JSON 不写文件）、data-agent（写，从正文提取 commit artifacts）；外加 deconstruction-agent（拆书）。(3) 引擎层=scripts/data_modules/ 近 190 个 Python 模块，统一从 scripts/webnovel.py CLI 入口分发（preflight/where/project-status/doctor/write-gate/story-system/chapter-commit/story-events/memory/rag/projections）。(4) 真源层 .story-system/=唯一事实源：MASTER_SETTING.json（设定/调性/禁忌）+ volumes/（卷合同）+ chapters/（章合同）+ reviews/（审查合同）+ commits/chapter_XXX.commit.json（写后真源）+ events/（事件审计链）+ 覆写账本。(5) 投影/只读视图层 .webnovel/=state.json、index.db（SQLite 实体/状态/伏笔索引）、vectors.db（RAG）、summaries/、memory_scratchpad.json 全部是从主链 commit 派生的 read-model，由 projection writers 写出，projection_log.jsonl 记录每路投影执行日志用于定位「哪路没同步」。「防幻觉三定律」是贯穿全局的设计公理：大纲即法律（context-agent 强制加载章纲）、设定即物理（reviewer 一致性审查）、发明需识别（data-agent 自动提取并消歧新实体）。数据流向严格单向：合同→起草→审查→提取→accepted CHAPTER_COMMIT→投影到所有只读视图，事件审计链不另起第二套投影循环（仅声明式激活 writer，实际执行入口仍是 ChapterCommitService.apply_projections()）。
- **状态/记忆设计**：这是整个项目最值得抄的部分，本质是「事件溯源(event sourcing) + CQRS 读模型投影」搬到小说一致性场景。【唯一真源】=accepted CHAPTER_COMMIT（commits/chapter_XXX.commit.json）；其余 state.json/index.db/summaries/memory_scratchpad/vectors 全是派生只读视图，禁止手写，drift 由 projection_log.jsonl + doctor/preflight 暴露。【提交契约】data-agent 产 3 份 pydantic 严格校验的 artifact（chapter_commit_schema.py）：extraction_result（顶层 accepted_events/state_deltas/entity_deltas/entities_appeared/scenes/summary_text，强制扁平禁止嵌套）、fulfillment_result（planned/covered/missed/extra_nodes 大纲兑现度）、disambiguation_result（pending 待消歧实体）。事件类型用 EVENT_TYPE_ALIASES 容错归一（breakthrough→power_breakthrough、promise→promise_created、mystery→open_loop_created…），把 LLM 的自由文本收敛成有限枚举。【状态 deltas】state_deltas 子项=entity_id+field+old+new，支持点号嵌套路径（power.realm、location.current）投影器自动展开。【实体消歧】data-agent 查 index 别名表，置信度>0.8 自动采用、0.5-0.8 采用+warning、<0.5 标记人工——把概率信号变可控分支。【伏笔/追读债务】每条埋设伏笔强制同步写一条 open_loop_created 事件，回收时写 promise_paid_off/open_loop_closed，闭环可审计。【分层长期记忆】memory/schema.py 定义 semantic/episodic 两层 × 7 类桶（character_state/story_fact/world_rule/timeline/open_loop/reader_promise/relationship），每条 MemoryItem 带 status（active/outdated/contradicted/tentative）+ source_chapter + evidence 证据链，按 category 规则算去重 key。【记忆压缩】compactor.py 是亮点：超 500 条才触发，按四步压：同 key 只留最新 outdated → 删已回收伏笔 → 距当前>50 章的旧 timeline 合并成一条摘要 item → 仍超限按 active优先/章号新/时间排序全局截断。【时间线/设定一致性】reviewer 审查时直接查 state get-entity / index get-state-changes 做战力-境界、地点、时间倒计时校验。RAG：embedding+rerank，无 key 自动回退 BM25 关键词检索。
- **章节循环**：章节级闭环=带硬关卡的 6 步流水线（webnovel-write/SKILL.md），硬规则「禁止并步、跳步、伪造审查；必须用 Agent 工具真调 subagent 不得口头代替；审查只跑一轮；失败只补跑失败步不回退」。流程：准备阶段先 preflight + placeholder-scan + 刷新合同树（story-system --persist --emit-runtime-contracts 生成本章 runtime contract，并跑 write-gate --stage prewrite）→ Step1 context-agent 产「写作任务书」，排序被强制固定为：①本章硬约束(chapter_directive.goal/time_anchor/countdown/chapter_end_open_question) ②CBN/CPNs/CEN 与 must_cover_nodes（必须覆盖节点）③本章 forbidden_zones 禁区（违反即不通过）④风格指引+主角卡 OOC 警戒+anti_patterns ⑤dynamic_context 仅作风格参考不得覆盖章纲 → Step2 起草（只依任务书，纯正文无占位符）→ Step3 reviewer 审查（5 维：设定一致性/时间线/叙事连贯/角色一致性/逻辑；只返 JSON、不评分、不评文笔、不建议改情节；每维强制输出 pass 或「发现N问题」结论到 dimension_results）→ review-pipeline 把 reviewer JSON 标准化为含 blocking_count 的 review_result，供 precommit gate 用 → Step4 润色（修非 blocking issue→风格适配→排版→Anti-AI 终检，anti_ai_force_check=fail 不进 Step5，只改表达不改事实）→ Step5 提交（data-agent 提取 3 artifact→write-gate precommit→只读 git diff 写入所有权 sanity check→chapter-commit 驱动 state/index/summary/memory/vector 投影→postcommit gate）→ Step6 章节级备份。三档模式 默认/--fast(轻量审查仅查 setting/timeline/continuity)/--minimal(写 no-review artifact 跳审查)。关键编排哲学：把「怎么写」(文笔节奏放开发挥) 与「写了什么」(事实必须登记/过审/存档) 彻底分离。审查是单 agent 多 rubric（一个 reviewer 内含 5 维），非多 agent 并行；blocking issue 定点修复或 AskUserQuestion 让作者裁决，不重跑 reviewer（成本权衡）。重复执行同章会从可信断点续跑不重写已完成产物。
- **可借鉴**：
  - [L2 StateLedger] CHAPTER_COMMIT 作为唯一事实源 + 其余全是派生只读投影（event sourcing/CQRS）：写后只信 accepted commit，state/index/summary/memory 禁止手写，projection_log.jsonl 定位哪路没同步 — 直接照搬这个心智模型——它从根上解决了「多份状态互相打架」。我们的 StateLedger 应是 append-only 章节提交链，所有派生视图可随时重建
  - [L3 ChapterContract] 写前合同(runtime contract)：chapter_directive 含 goal/time_anchor/countdown/must_cover_nodes(必覆盖)/forbidden_zones(禁区)/chapter_end_open_question，违反禁区即不通过 — 这就是 L3 的标准字段表，几乎可原样定义我们的 ChapterContract schema；尤其「禁区(forbidden_zones)」=硬约束由代码 gate 而非靠 LLM 自觉
  - [L2 StateLedger] pydantic 严格校验的 commit artifact + 顶层扁平强制 + 事件类型别名归一(EVENT_TYPE_ALIASES) — 把 LLM 自由文本收敛成有限枚举+严格 schema，是 AI-pipeline『append 硬不变量 by code、tolerant 解析』的范例；我们提取事实时照做
  - [L4 生产闭环] write-gate 三关卡(prewrite/precommit/postcommit)+ doctor/preflight 健康自检 + 行为 eval — 确定性代码当 LLM 的关卡：每个自然边界一道 gate，blocking 不过就阻断。我们的生产闭环至少要 prewrite+precommit 两关
  - [L4 生产闭环] 读/写/审三 agent 分工 + 强制真调用：context-agent(读,出任务书) / data-agent(写,提取事实) / reviewer(审,只返JSON不写文件)，写入所有权单一 — 人机分工模板。每份 artifact 有唯一写入者(reviewer 不持 Write、data-agent 不写 state)，避免越权写——这是多 agent 防互相覆盖的关键
  - [L2 StateLedger] 分层长期记忆(semantic/episodic × 7 类桶) + status(active/outdated/contradicted/tentative) + evidence 证据链 + 按 category 去重 key — 记忆条目带状态机和证据，矛盾可标 contradicted 而非静默覆盖；我们的记忆层结构可直接借鉴这 7 类划分
  - [L2 StateLedger] 记忆压缩器 compactor：超阈值才触发，旧 timeline(>50章)合并成摘要 item、删已回收伏笔、按 active优先+新鲜度全局截断 — 上下文预算管理的具体算法，解决长篇记忆膨胀；分级压缩(同key去重→语义合并→硬截断)值得抄
  - [L0 作者宪法/L1 StoryBible] 追读力系统：钩子分类(危机/悬念/渴望/情绪/选择钩×强度strong/medium/weak)+爽点模式库+Strand Weave节奏(Quest60%/Fire20%/Constellation20%+断档红线)，且全部是『指导性建议不做硬性评分裁决』 — 网文领域知识的结构化沉淀。关键设计：软性追读力走『建议』通道(不 block)，硬性事实一致性才走 gate——硬软分流别一锅炖
  - [L2 StateLedger] 伏笔即事件：埋设强制写 open_loop_created、回收写 promise_paid_off，债务可被 query 和 compactor 追踪闭环 — 把『伏笔』建模成有生命周期的债务对象，是防『挖坑不填』最干净的工程手段
  - [L1 StoryBible] RAG 无 key 优雅降级到 BM25；CSV 知识库(命名规则/场景写法/爽点节奏/裁决规则)按 skill+table+genre 按需检索 — 零依赖可跑 + 领域知识外置成可检索 CSV，降低对向量服务的硬依赖
- **反模式**：文档漂移：architecture/overview.md 仍写 reviewer 有 6 维(含 High-point/Pacing/Reader-pull)，但当前 agents/reviewer.md 只剩 5 维事实审查(setting/timeline/continuity/character/logic)且明确『不评分不评文笔』——单一事实源原则在自家文档上没守住，追读力维度其实被迁出到 context-agent/checkers 当软建议了，但 overview 没同步 / 巨大表面积 vs 单维护者：465 文件、~190 Python 模块、事件审计链+覆写账本+7桶记忆+向量 RAG+React dashboard+行为 eval 全自研，6 个月龄、单人维护、还在 v7 推倒重来——长期维护风险高，新人/新 agent 重建上下文成本大 / 审查只跑一轮(硬规则)：blocking 定点修复后不重跑 reviewer，是成本权衡，但意味着修复引入的新问题不再过审，质量上限受限于单 pass / 事实提取与消歧塞进 data-agent 单次 LLM 调用(不额外调 LLM)：省钱但提取+消歧+摘要+场景切片四件事一把梭，复杂章节容易顾此失彼，靠 0.5/0.8 置信度阈值兜底 / SKILL.md 编排极度冗长且把大量硬约束写进 markdown 提示词(靠 LLM 遵守排序/禁止跳步)，虽有 write-gate 代码兜底，但相当一部分纪律仍依赖模型『读懂并照做』长 prompt / Strand Weave 固定比例(60/20/20)+断档章数红线是经验值硬编码，跨题材未必成立(悬疑/言情节奏结构差异大)，当默认裁决可能误伤
- **OE判定**：部分过度工程化，但『过度』集中在实现而非设计。核心架构思想——单一事实源(accepted commit) + 派生只读投影 + 写前合同/写后 gate 的状态机——是这个问题域近乎最优解，复杂度完全值得，正是我们 L2/L3/L4 想要的骨架。但落地实现明显超出『一个写作 skill』的合理体量：完整 event sourcing + projection_log + 事件审计链 + 覆写账本(override ledger) + 7 桶分层记忆 + 向量 RAG + React dashboard + 行为 eval + 数百测试，对单作者辅助工具是重型基建，190 个模块的维护面对单人团队是负债(也是它要 v7 重构的原因)。结论：偷它的契约与状态机设计(schema、三定律、三关 gate、提交链)，不要照抄它的模块规模与全套基建；我们的 skill 用『一个 append-only 章节提交 + 派生 read-model + 两道 gate』就能拿到 80% 收益。
- **偷/避**：偷：CHAPTER_COMMIT 单一真源+派生只读投影的状态机、chapter_directive 写前合同字段表(必覆盖节点/禁区/倒计时)、write-gate 三关卡、读/写/审三 agent 单一写入所有权、伏笔即生命周期事件、分层记忆+compactor 压缩、硬性事实走 gate/软性追读力走建议的分流。避：照抄它 190 模块的全套重型基建(事件审计链/覆写账本/向量 RAG/dashboard)、把硬纪律全压进超长 SKILL.md 提示词、以及单 pass 审查不复检——我们要它的契约骨架，不要它的体量。

### worldwonderer/oh-story-claudecode (3182★, active, usable-tool)
https://github.com/worldwonderer/oh-story-claudecode
- **做什么**：一套纯 prompt/markdown 的 Claude Code skill 包（13 个 skill + 7 个专业 agent + 7 个 hook），覆盖中文网文连载的全流程：扫榜选题(story-long-scan)→拆文逆向爆款(story-long-analyze)→开书/大纲/日更正文(story-long-write)→多视角审稿(story-review)→去AI味(story-deslop)→逆向导入已有小说(story-import)→封面(story-cover)。无任何编译型代码主体，核心是把"约束 LLM 可靠交付情绪"的方法论编码成文件系统结构 + 引用知识库 + 确定性脚本兜底。同时适配 Claude Code / OpenCode / Codex CLI / OpenClaw 四个运行时。
- **架构**：核心信条一句话："对话只负责创作，不负责记忆"——把设定/大纲/正文/追踪全部落到文件系统，LLM 每章只加载"不知道就会写错"的最小上下文。书目录五大块：① 设定/（StoryBible：世界观按主题拆文件、每角色一个 .md、势力、关系.md、题材定位.md）② 大纲/（三层：大纲.md 全书鸟瞰→卷纲_第X卷.md 含情绪弧线+反转规划+伏笔表→细纲_第XXX章.md 单章蓝图）③ 正文/（每章一文件）④ 追踪/（StateLedger：伏笔.md/时间线.md/角色状态.md/上下文.md）⑤ 对标/（把 analyze 拆出的爆款数据作为引用视图，文风.md/节奏.md/情绪模块.md 是情绪与节奏的 canonical 来源）。根目录 .active-book 指针文件标记当前活跃书。7 个 agent 按角色分模型：story-architect(Opus 架构)、character-designer/narrative-writer/story-researcher(Sonnet)、consistency-checker/story-explorer/chapter-extractor(Haiku 只读查询/检查)。所有 references/（100+ 份方法论 md）按需加载、不预占上下文。全链路 graceful degradation：agent 缺失→solo fallback 并显式报告 Requested/Effective/Fallback 模式。
- **状态/记忆设计**：文件系统即数据库，不靠 in-context 记忆。StateLedger 在 追踪/ 下分层、每个维度是带状态枚举的 typed table：① 伏笔.md——ID/伏笔内容/埋设章节/预计回收章节/状态(未埋·已埋·已回收·已过期)/重要度 + 回收日志表 + 过期伏笔表，跨卷级；② 时间线.md——章节/故事时间/事件/涉及角色/与主线关系 + 并行线时间对照 + "待确认疑点"，全书级；③ 角色状态.md——角色状态快照 + 追加变更记录，章节级；④ 上下文.md——进度元信息 + 三层记忆压缩（近5章详记/每10章概要/卷级总览，30 章以上触发），是 compact 恢复锚点。一致性靠 consistency-checker agent（Haiku 只读，grep-first + 推理）：第一步不硬编码题材术语，先扫 设定/ 动态构建检查词表；第二步实体/设定/时间线冲突扫描；第三步推理型审查（规则边界悖论、设定层级冲突、跨章因果链断裂、规则可滥用漏洞、代价一致性），输出 S1-S4 分级。记忆压缩还有 pre-compact/post-compact hook 保存进度快照路径。关键：每章写完"立即更新"四个追踪文件，下一章必须读取更新后的文件再开写。
- **章节循环**：开书是 Phase1(选题确认)→2(核心设定)→3(三层大纲)→4(正文)→5(质检)。连载用"日更 workflow"——主会话内串行逐章循环，明确禁止多章并发（章节依赖上一章正文+追踪文件，并发会断上下文/覆盖追踪/标题去重失效）。每章循环：Step2.1 标题预检→2.2 状态筛选(必须确认本轮 workflow 内真实读过细纲/上一章正文/伏笔/时间线/角色状态，禁止用未标来源的聊天记忆替代)→2.3 对标模块/节奏/文风召回(经 story-explorer 的 benchmark_style_load query 一次性拿 emotion_module/rhythm_reference/style_profile/matched_chapter/anchor_excerpts/gaps)→2.4 意图确认(一句话锁定情绪+节奏+模块+文风指令)→narrative-writer 写正文→字数验证(按情节点 per-point 字数预算，欠字定位密点一次性重写到配额、不挤牙膏)→钩子/爽点检查→正文元信息扫描→禁用词扫描→立即更新追踪。批量写完跑 Step3 统一质检 + 确定性脚本。审校用 story-review：多视角对抗式（full=4 agent 并行 / lean=2 / solo fallback），带平台 rubric(番茄/起点/知乎) + 内置 fallback rubric，S1-S4 分级，铁律"审查是找问题不是验证正确性"。绑定确定性脚本兜底（见 reusable_patterns）。
- **反模式**：把硬约束写成自然语言 prose 而非代码/schema：绝大多数'必须/不得/应该'是 LLM 须自觉遵守的散文，会随模型漂移（除少数确定性脚本与 guard hook 外都不可强制执行） / workflow-daily Step 2.3 的 gaps.* 分支爆炸：no_benchmark/missing_primary_contract/module_missing/rhythm_missing/conflict/profile_missing/profile_degenerate/tone_match_failed/custom_style 近十个条件嵌套，认知负荷极高、脆弱、难维护，是 prompt 层 overengineering / 四运行时可移植(Claude/OpenCode/Codex/OpenClaw)把每个 agent/hook/command 三四份复制，维护面×4，CHANGELOG 大量篇幅在抹平运行时差异(GBK 区域/symlink/hook 语义) / 情节点 per-point 字数预算的伪精确(密≥250字/疏≈40字/Σ落在[目标,目标×1.1])——LLM 难可靠命中这种字符级配额，是过度规约 / 版本churn 信号：README 同时挂 v0.6.18/19/20 三段更新说明、agents_version 门控 stale 部署，频繁打补丁本身暴露'指令即执行'的脆弱性 / 知识库重复：banned-words.md/anti-ai-writing.md 等同名文件在 5+ 个 skill 的 references 下各存一份(含 story-setup/agent-references)，违反 single-source-of-truth
- **OE判定**：架构层不算 overengineered，复杂度值得：文件系统即记忆 + 每实体一文件的 bible + 带状态枚举的 typed 追踪表 + 写后确定性退化脚本 + 写正文前 blocking 大纲守卫，正是"百万字连载一致性"这个真问题所要求的，复杂度与问题规模匹配。overengineering 集中在两处局部：① prompt 内的条件分支爆炸（Step 2.3 gaps 处理、字数 per-point 预算），把本该用 schema/code 收敛的逻辑堆成自然语言判断树；② 四 CLI 可移植带来的三四倍维护面。借鉴时取其架构骨架、砍掉这两处局部复杂度即可。
- **偷/避**：偷：文件系统即记忆(对话只写不记) + 每实体一文件的 StoryBible + 带状态枚举的 typed 追踪表(伏笔/时间线/角色状态) + 写后确定性退化脚本(check-degeneration，模型自己发现不了退化、靠模型无关脚本兜) + 写正文前 blocking 大纲守卫 hook + 多 rubric 对抗式审稿。避：把硬约束写成散文(改成 code/schema/lint 强制) + prompt 内 gaps 分支爆炸 + 四运行时三四倍复制。

### vkbo/novelWriter (2989★, active, production)
https://github.com/vkbo/novelWriter
- **做什么**：开源纯文本长篇小说编辑器（Python + PyQt6 桌面应用），把一部小说拆成大量小文档（场景/章节/笔记），每个文档以人类可读的 .nwd 纯文本（类 Markdown + 一套元数据语法）存储，天然适配 git 与文件同步。核心卖点是 Tags & References 交叉引用系统 + Outline View 大纲视图。明确声明"由真人开发维护"，CONTRIBUTING 明令拒绝 AI 生成内容。注意：它完全没有任何 AI/LLM/生成能力，对我们的价值 100% 在它的"一致性数据模型"，而非生成/审校流程。
- **架构**：分层清晰：(1) 存储层 storage.py / document.py / projectxml.py —— 每个文档一个纯文本 .nwd 文件，项目结构（树）存 nwProject.nwx XML，纯文本是唯一事实源（source of truth）。(2) 解析层 formats/tokenizer.py + text/formats.py —— processHeading() 解析 #/##/### 标题级别，processComment() 解析 % 注释行与 %~synopsis/%short/%note:key/%footnote:key/%story:key 注释修饰符。(3) 索引层 core/index.py + core/indexdata.py —— 这是一致性引擎的心脏，见下。(4) 视图层 itemmodel.py/novelmodel.py 派生出 Outline View / References 面板（Qt model）。(5) 构建层 core/docbuild.py + buildsettings.py + formats/to*.py —— 确定性把碎片编译成完整书稿（html/docx/odt/markdown）。整条链路靠 SHARED 单例广播 Qt 信号（emitIndexChanged*）联动 UI，所以核心逻辑与 GUI 强耦合，不能当 headless 库直接 import。
- **状态/记忆设计**：这是全项目最值得抄的部分。两件事组合：(A) 纯文本里的元数据契约 —— 实体在 Character/Plot/Location/Timeline/Object/Entity/Custom 等"根文件夹"下的笔记里用 `@tag: Jane | Jane Doe` 声明（一个标题只能有一个 tag、全项目唯一、可带 display name 别名）；实体的"类别"不写在文本里，而是由它所在的根文件夹类型隐式决定。引用侧关键字：@pov/@focus/@char/@plot/@time/@location/@object/@entity/@custom/@mention/@story，每个场景标题下用一行声明本场景涉及的实体。特别值得注意 `@mention` = "被提到但本场不出场"（专为后续一致性检查设计，如某场透露了某角色信息但他没出现）。(B) Index 索引 —— 一个由纯文本"派生、可随时重建"的交叉引用图，缓存成项目 meta 目录里的 JSON。内部两张表：ItemIndex（每文件一个 IndexNode → 每标题一个 IndexHeading，存 level/title/line/tag声明/refs{tag→关键字类型集合}/comments{synopsis,story.key,note.key}/字数三元组 char-word-para）；TagsIndex 反向索引（tag → {handle, class}）做 O(1) 的"这个实体在哪定义"查询。关键工程点：① 引用挂在最近的"标题(场景)"而非整篇文档上 —— 状态粒度是场景级；② 索引是 cache 不是事实源，load 时校验，坏了就 _indexBroken=True 然后从纯文本全量 rebuild()，F9 手动重建；③ 增量更新 —— 每次保存文档触发 scanText() 只重扫该文件并广播"哪些引用变了"；④ 编辑器实时高亮把指向未定义/类别不符的引用画波浪线 —— 一个实时一致性 linter。等于把"设定集(Story Bible) + 出场状态台账(State Ledger)"都用纯文本声明 + 派生索引实现，没有人物卡表单、没有记忆压缩、没有向量库。
- **章节循环**：没有任何 AI 意义上的"大纲→章节→review"生成/审校循环 —— 它是编辑器不是生成器，人来写每一个字。最接近的工程类比有三处，对我们设计闭环有参考价值：(1) Manuscript Build 构建管线（core/docbuild.py）：确定性"编译" —— buildItemFilter 按 tag/class/status/importance 过滤要纳入的碎片 → 按项目树顺序迭代 → Tokenizer 解析元数据并按规则保留/剥离注释与 synopsis → to{Html,Docx,Odt,Markdown,QDoc} 渲染。可按标签/状态构建"部分书稿"（如只导出某 plot 线、只导出 Draft 完成的场景）。纯单向 compile，无打分、无 rubric、无 agent。(2) Status/Importance 标签（core/status.py）：每文档手动贴工作流状态（如 Draft/1st Edit/Done）与重要度，是人肉看板式进度台账。(3) Outline View + References 面板：从 Index 派生出"每个场景的 POV/角色/情节/地点矩阵"，是人工做一致性审计的界面（一眼看出"某角色连续 10 场没出现""某条副线断了"）。结论：审校循环是"给人提供派生视图让人自查"，不是"自动门禁卡住不合格产出"——波浪线高亮是 advisory（建议性）的，不会让 build 失败。
- **反模式**：核心索引逻辑与 PyQt6/SHARED 单例强耦合，靠 emitIndexChanged* 等 Qt 信号驱动 UI —— 无法当作 headless 库直接 import，给 skill 用只能照着数据模型重写，不能复用其代码。 / 实体'类别'由所在根文件夹类型隐式决定，而不在文本里显式声明（隐藏契约）。对人方便，但对'让 LLM 写一篇笔记'是坑：模型只看文本不知道它属于哪个文件夹，就不知道这是角色还是地点。AI 管线里类别必须 inline 显式声明。 / '项目结构从标题推断而非从文档推断' + '一个标题只能一个 tag、全项目唯一' 是又一层隐藏耦合，靠人类纪律维持；自动化生成时容易违约且不易自检。 / 一致性检查全是 advisory（波浪线/视图），没有任何'校验失败就阻断构建'的硬门禁 —— 它解决的是'给作者看'的人类问题，没解决'强制模型别写崩'的生成约束问题，这正是我们要补的缺口。
- **OE判定**：不 overengineered，相反是"恰到好处的轻"。一致性层就是"纯文本声明 + 派生 JSON 缓存索引 + 几个 dataclass(IndexNode/IndexHeading)"，没有数据库、没有向量、没有记忆压缩，每行代码价值密度高，作为单用户桌面编辑器的体量完全匹配。唯一不易迁移的"复杂度"是 Qt 信号管线与 class-from-folder 的隐式指向，那是 GUI 应用的产物，不是过度设计。对我们的真正价值：它证明了"设定集+出场台账"可以用极轻的'纯文本契约 + 可重建派生索引'实现，不需要重型状态机。
- **偷/避**：偷它的'纯文本 @tag/@ref + %synopsis 注释契约 + 可全量重建的场景级派生索引(ItemIndex+反向 TagsIndex)'作为 StoryBible+StateLedger 的底层范式；但别抄代码(Qt 强耦合)、别抄'类别藏在文件夹'的隐式契约、更要补上它缺的那一环——把它 advisory 的一致性高亮升级成'校验不过就阻断章节产出'的硬门禁。

### olivierkes/manuskript (2352★, active, usable-tool)
https://github.com/olivierkes/manuskript
- **做什么**：老牌开源桌面写作工具（Python3 + PyQt5，GPLv3，跨 Linux/macOS/Windows，打包到 snap）。给小说作者一整套"先搭设定、再写初稿、再精修"的结构化环境：雪花法逐层展开梗概、角色卡、情节/子情节、世界树、大纲（Outline 模式 + Index Cards 卡片视图）、Story line 故事线视图、重要物品追踪、专注写作模式、frequency analyzer，以及导出 HTML/ePub/ODT/DocX/PDF（走 pandoc）。注意：它是纯手工工具，全仓零 LLM/AI、零自动生成——对我们的价值是它沉淀了 10 年的"小说状态该切成哪些字段"的 schema 教科书，而不是任何生成/审校代码。
- **架构**：经典 Qt MVC 桌面应用，对我们有用的全在 manuskript/models/ + enums.py。核心数据流：① enums.py 用一组 IntEnum 把每类对象的字段定死（列号即字段身份）——Character(name/importance/motivation/goal/conflict/epiphany/三级摘要/notes/pov/infos)、Plot(characters/description/result/steps/summary)+PlotStep、World 树(description/passion/conflict)、Outline(title/type/POV/status/label/compile/goal/wordCount/revisions...)、FlatData(项目级雪花五层:Situation→Sentence→Paragraph→Page→Full)。② 每类对象一个 Qt model：characterModel(扁平 list+键值 infos 子项)、worldModel/plotModel(QStandardItemModel 树)、outlineModel/outlineItem(书>部>章>场景 的树)。③ references.py 提供跨对象引用 token。④ load_save/version_1.py 把整个项目落成"每个场景/角色一个纯文本/Markdown 文件 + MultiMarkdown 风格 key:value 头"的目录（或单 zip）。架构反面：model 直接继承 QAbstractItemModel/QStandardItemModel、到处调用全局 mainWindow()，领域状态和 GUI 框架彻底焊死，无法 headless 复用——只能偷 schema 不能偷代码。
- **状态/记忆设计**：这是它最值钱的部分，且全是"显式分表 + 稳定 ID"而非记忆压缩（没有向量/检索/记忆压缩概念，纯手工结构化）。(1) 设定分表：角色/情节/世界/大纲各一张表，字段在 enums.py 里硬切分——角色不是一坨自由文本，而是 motivation/goal/conflict/epiphany 四要素 + 三级摘要(一句→一段→完整) + 自由键值 infos 逃生舱；世界是可嵌套的树(description/passion/conflict)；情节有子步骤 PlotStep。(2) 雪花法两处落地：项目级 FlatData 五层(situation→sentence→paragraph→page→full)、角色级三层(summarySentence→summaryPara→summaryFull)，强制"先一句话再逐层展开"。(3) 一致性胶水=稳定 ID 引用 token：references.py 定义 {C:ID}/{T:ID}/{P:ID}/{W:ID} 正则，可嵌进任意正文，渲染成带悬浮详情的超链接；引用按 ID 而非名字字符串——改名不断链，且能反查"哪些场景引用了角色 X"；删了目标则显示"Unknown reference"(暴露悬空引用，但不自动校验)。(4) 场景级元数据当轻量 ledger：每个 outlineItem 带 POV(指向角色 ID)、status(todo/draft/final)、label(色标)、compile(是否进导出)、goal/setGoal/goalPercentage(字数目标，文件夹目标=子项之和)、wordCount/charCount(写文本时自动重算)。(5) revisions：outlineItem.setData 改正文时自动 addRevision()，每个场景留版本快照可回滚。(6) 持久化即一致性：version_1.py 明确"纯文本/每对象一文件"是为了 git 版本控制 + 协作 + 第三方编辑——单一可 diff 真相源。
- **章节循环**：无。这是纯手工 GUI 工具，不存在大纲→章节→review 的自动编排，没有任何 agent、rubric、生成或校验循环。它能提供的"循环"只有人肉工作流：雪花法逐层展开(situation→…→full)、场景 status 看板(todo→draft→final)、per-scene goal 字数达标条、revisions 手动回滚。换句话说——它给了"章节契约该有哪些字段"(POV/status/label/compile/goal)和"摘要该分几层"，但把"写 + 审"全留给人。对我们的 L4 生产闭环：它只贡献状态机的"状态定义"(每个场景的 status/goal/compile 字段)，不贡献驱动器；驱动器(LLM 生成→rubric 审校→重写)要我们自己造。
- **可借鉴**：
  - [L1 StoryBible] enums.py 把每类对象字段硬切分成 IntEnum（角色=motivation/goal/conflict/epiphany+三级摘要；情节=description/result/steps；世界=description/passion/conflict）——一份 10 年验证过的'小说设定该存哪些字段'清单 — 直接抄成我们 StoryBible 的 JSON schema 起点；尤其角色'四要素+三级摘要'比'自由文本人设'对 LLM 约束力强得多
  - [L1 StoryBible / L3 ChapterContract] 雪花法分级摘要：项目级五层(situation→sentence→paragraph→page→full) + 角色级三层 — 每层是上一层的可校验展开，天然适合让 LLM 逐层生成并在每层做一致性 gate；也能当 context 压缩的多分辨率视图
  - [L2 StateLedger] {C:ID}/{T:ID}/{P:ID}/{W:ID} 稳定-ID 引用 token 嵌进正文 — 最该偷的机制：正文里对人物/伏笔/设定用 ID 引用而非名字，改名不断链，可反查'第N章触及了哪些设定/伏笔'，是连载一致性与伏笔回收的索引底座
  - [L3 ChapterContract] 场景级契约元数据：POV(→角色ID)、status(todo/draft/final)、label、compile(是否进导出)、goal/goalPercentage(字数目标，父=子之和) — 几乎就是 ChapterContract 的现成字段表；POV 强制单视角、compile 标记草稿可控进出，对网文连载很贴
  - [L2 StateLedger / L4 生产闭环] 每次改正文自动 addRevision() 留场景级快照 — AI 重写章节时保留每版快照，便于 A/B、回滚、和'这版比上版改了啥'的 diff 审校
  - [L2 StateLedger] version_1.py：每对象一个纯文本/Markdown 文件 + MMD key:value 头，显式为 git/协作/第三方编辑设计 — 状态用可 diff 的纯文本落盘=单一真相源、agent 可读、可版本化；别用不透明二进制/单大文件
  - [L1 StoryBible] 角色 infos 自由键值子项作为结构化字段之外的逃生舱 — schema 之外留一个 extra 键值表，平衡'机器可校验'与'作者随手补设定'
- **反模式**：领域 model 直接继承 QAbstractItemModel/QStandardItemModel 并到处调用全局 mainWindow()——状态与 PyQt5 GUI 彻底焊死，无法 headless 运行/单测/被 agent 调用；我们必须反着来：纯数据 core 与任何框架解耦 / 字段身份=整数列号(enums 里 motivation=3)，是隐式 stringly-typed 契约的变体，加删字段易错位、跨版本脆；偷字段清单可以，存储别用列号当 key，用具名字段 / 引用 token 只在渲染时报'Unknown reference'，没有任何自动一致性校验/悬空引用检测/时间线冲突检查——一致性全靠人眼。对 AI 写作这恰恰是必须补的那一层(把 manuskript 留给人的校验变成代码 gate) / 无生成、无审校、无 rubric、无 agent——别指望从它身上偷到任何'防写崩'的工程手段；它只定义状态，不驱动状态 / 576 个 open issues、十年 Qt 遗留代码，整体不是可借鉴的工程范本，只是数据建模范本
- **OE判定**：对它自己的定位(单机 FOSS 写作 GUI)不算 overengineered——数据 model 反而相当精炼，enums 是一张极克制的 schema。真正的问题不是"过度复杂"而是"复用性为零"：把领域状态焊死在 PyQt5 + 全局 mainWindow() 上，导致这套优秀 schema 无法被任何非-Qt 程序(包括我们的 skill)直接 import。所以对我们而言它是"对的抽象，错的耦合"。结论：偷它的 schema(零成本)，绝不碰它的代码架构。
- **偷/避**：偷它的 schema——角色四要素+三级雪花摘要、场景契约字段(POV/status/compile/goal)、尤其 {C:ID} 稳定-ID 引用 token 当一致性/伏笔索引；避开它的 GUI 焊死架构，并补上它完全没有的那层：把"靠人眼校验一致性"换成代码 gate(悬空引用/时间线/设定冲突自动检测)。

### THUDM/LongWriter (1868★, semi-active, research-code)
https://github.com/THUDM/LongWriter
- **做什么**：ICLR 2025 论文配套仓库。核心命题：LLM 写不长(>2000字就崩)不是模型能力上限，而是 SFT 数据的输出长度天花板造成的。两条产线：(1) AgentWrite —— 用现成 LLM(GPT-4o) 通过"先规划大纲→逐段填写"的 agent 流水线批量造出超长输出，进而构建 LongWriter-6k SFT 数据集；(2) 用该数据 SFT 出 LongWriter-glm4-9b / llama3.1-8b，让模型"原生"一次生成 1万字以上，不再需要 agent 脚手架。另含两个评测基准 LongBench-Write / LongWrite-Ruler。2025-06 的 LongWriter-Zero 改用纯 RL(无合成/标注数据) 训长文。本质是"造数据 + 训模型 + 测长度"的研究工件，不是给人用的写作工具。
- **架构**：极简两阶段管线，全在 `agentwrite/` 下约120行 Python。数据流：instructions.jsonl → `plan.py` → plan.jsonl → `write.py` → write.jsonl。① plan.py：把指令套进 `prompts/plan.txt`，调 GPT-4o 产出一个编号子任务列表，每行=一段，含 "Main Point(段落要点)" + "Word Count(字数要求)"；prompt 硬性约束每段 200–1000 字、不要切太碎。② write.py：把 plan 按换行切成 steps，**顺序**遍历；每个 step 拼 prompt = template(原始指令 $INST$ + 完整大纲 $PLAN$ + 到目前为止已写全文 $TEXT$ + 当前 step $STEP$) 调 GPT-4o，结果 append 进运行中的 text。角色单一：plan 是一个 LLM 调用，每段 write 各一个 LLM 调用，无多 agent。工程兜底：plan 超过 50 步直接跳过(防爆)；write_cache.jsonl 按 (prompt, step) 缓存每段输出供断点续跑；out_file 去重已完成 prompt 实现幂等续跑。evaluation/ 是离线评测(LLM-as-judge)，与生成管线解耦。
- **状态/记忆设计**：对我们最关键、也是它最弱的一环：几乎没有任何结构化状态管理。没有设定集、没有人物卡、没有时间线、没有伏笔表、没有记忆压缩、没有任何实体抽取或检索。它唯一的"记忆"机制是——每写一段都把**到目前为止的完整全文** 整段塞回 prompt 的 "Already written text: $TEXT$" 槽位，完全依赖模型的长上下文来维持一致性；而全局结构靠把整份大纲 $PLAN$ 每段都重新喂入来维持。数据结构层面就是两个字符串(plan 文本 + 累积 text 文本)做 string-replace 拼接，外加一个扁平的 (prompt→step→response) 缓存字典。后果：上下文随字数 O(n²) 膨胀，对1万字尚可，对网文百万字连载完全不可行；一致性是"祈祷上下文窗+大纲能兜住"，没有任何能在上下文窗口之外存活的状态层。LongWriter-Zero 更进一步把一致性整个塞进模型权重(靠 RL 的长度奖励+写作质量奖励模型)，状态彻底隐式、不可检查、不可约束。结论：在"约束 AI 写好网文连载"这个目标上，LongWriter 的记忆设计是反面教材而非可抄对象。
- **章节循环**：它是"规划→顺序逐段填写"，不是真正的"章节→review→修订"闭环，且**生成环节内完全没有审校/批判/重写**。一段一旦写完就 append、永不回看修改(append-only)。唯一的 review 来自 evaluation/ 的 LLM-as-judge，但那是**纯离线评测**：judge.txt 让 GPT-4o 按 6 维度(相关性/准确性/连贯性/清晰度/广度深度/阅读体验)各打 1–5 分输出 JSON，eval_quality.py 容错解析(失败重试至5次、缺维度回退默认3分)；它只"量"不"改"，不构成生产闭环里的修订器。长度评分单独算：eval_length.py 用一个分段非对称函数 score(x,y)——输出超长(y>x)惩罚更轻 1-(y/x-1)/3、不足则 1-(x/y-1)/2——作为"长度遵循度"指标。全程单 agent、单 rubric，无多 agent 辩论、无 critic-in-loop、无大纲层级(扁平段落列表，没有卷/弧/章的嵌套)。对我们：可借的是"plan/write 分离 + 离线多维 rubric 评分"，但它缺了我们最需要的"生成→审校→重写"在环修订与章节级状态校验。
- **可借鉴**：
  - [L1 StoryBible / L3 ChapterContract] plan/write 两阶段分离：永不一把梭长文，先用一次 LLM 调用产出结构化大纲，再用 N 次调用逐单元填写。这是整个项目最值钱、最直接回答'AI越写越散'根因的模式。 — 对应我们的'先出全局骨架→再逐章生成'。但要把它的扁平段落列表升级成卷/弧/章的层级大纲。
  - [L3 ChapterContract] 每个子任务=(Main Point 要点 + Word Count 字数预算) 的二元契约，且字数由 deterministic 代码 string-replace 进 prompt 强制注入，并加'每段200-1000字、最多50步'的代码级护栏。 — 正是 ~/.claude AI-pipeline 的'用代码追加硬不变量，别信 LLM 记规则'。我们的章节契约可借此结构：每章=(剧情节拍 + 字数/节奏预算 + 必达伏笔事件)。
  - [L4 生产闭环] 可断点续跑的顺序生成循环：write_cache.jsonl 按 (prompt, step) 缓存每单元输出，out_file 去重已完成项，挂掉重跑幂等。 — 长篇连载生成必备的工程底座，朴素但正确，直接抄。
  - [L4 生产闭环 / L3] 拼接防穿帮指令：write.txt 明令'省略开放式结尾和修辞钩子(omit open-ended conclusions / rhetorical hooks)'，让每段能干净拼接而不是各写各的小高潮。 — 网文章节缝合直接可用——避免每章都像大结局/每段都强行升华，控制'段落自我封闭'导致的节奏断裂。
  - [L4 生产闭环(审校器)] 离线 LLM-as-judge 多维 rubric：固定 6 维度 1-5 分、要求严格、强制 JSON 输出、容错解析+重试5次+缺维度回退默认值。 — 可作为章节质检 grader 的现成模板;'tolerant parse + retry + 默认值兜底'是稳健的工程细节。但需从'只量不改'升级为在环修订触发器。
  - [其他(方法论)] 脚手架即教师(scaffold-as-teacher)：agent 流水线本身是用来造数据再 SFT 把能力内化进模型,而非长期跑 agent。 — 提醒我们：约束脚手架产出的好样本本身就是资产;即便不微调,'约束=质量来源'这个框架对 skill 设计成立。
- **反模式**：零持久化状态：一致性全靠'每步重灌完整全文 + 模型长上下文'，无实体/时间线/伏笔追踪。对百万字网文连载会在上下文窗口耗尽时直接崩——这是最不该抄的一条。 / Append-only、生成环内无修订：写错的一段永远留着，没有 generate→review→rewrite 在环闭环(judge 只在离线评测，改不了生产稿)。 / 上下文 O(n²) 膨胀：全文重灌策略对1万字尚可，对长篇连载是成本与质量双杀，必须用记忆压缩/检索替代，而它完全没有。 / 扁平无层级的 plan：只有'段落列表'，没有卷/弧/章的嵌套规划，撑不起长线网文的多线伏笔与节奏。 / 以'长度遵循'为头号北极星：整套框架(含基准、LongWriter-Zero 的 RL 奖励)都在优化字数达标，质量是次要/离线指标——易诱导注水水文;网文要的是'好看'不是'够长'。 / LongWriter-Zero 的纯 RL 路线：一致性被训进权重，不可检查、不可约束、不可复现，对'用工程手段约束 AI'的 skill 作者是黑箱，不可借。
- **OE判定**：完全没有过度工程——恰恰相反，对我们的目标是"工程量不足"。整条 AgentWrite 管线就是 plan.py + write.py 共约120行直白 Python，复杂度对它的真实目标(为 SFT 批量造长文数据)而言精确且划算。但它解决的是一个比我们窄得多的问题(单次1万字短篇/单文)，因此对'多章节网文连载'缺了最关键的状态层与在环修订层。一句话：它的简单对它自己是优点，对我们是缺口——别被'1868星 ICLR论文'光环误导成可直接挪用的连载引擎。
- **偷/避**：偷：plan-first 大纲分解 + 代码强制的每单元字数/要点契约 + 可断点续跑的顺序生成循环 + '省略开放式结尾'的拼接防断指令 + 离线多维 LLM-judge rubric 模板。避：它无状态的'全文重灌'式记忆(零人物卡/时间线/伏笔)、append-only 无在环修订、以及把一致性'训进权重'的 RL 黑箱——这三点决定了它扛不住多章节连载，必须由我们 L2 StateLedger + L4 审校闭环补上。

### ExplosiveCoderflome/AI-Novel-Writing-Assistant (1796★, active, usable-tool)
https://github.com/ExplosiveCoderflome/AI-Novel-Writing-Assistant
- **做什么**：面向长篇中文小说的「AI导演式」整本生产系统（中英双语，目标用户=完全不懂写作的新手，产品判断是先解决"把整本写完"再优化"写得精巧"）。从一句灵感→自动导演开书→书级方向/标题组→世界观+人物+故事宏观规划→卷战略→拆章→章节执行(写作+审校+修复)→整本主链，全程由Agent编排；世界观/人物/拆书/知识库/写法引擎/时间线/伏笔账本作为长期资产托住每一章。另含Drama(短剧)与Comic(漫画)两条改编垂直线。
- **架构**：pnpm-workspace monorepo + Windows桌面版。client=React+Vite+Plate编辑器+TanStack Query+SSE流式；server=Express+Prisma+SQLite(单文件)+Qdrant(可选RAG)；AI编排=LangChain+LangGraph。后端分层清晰(值得学)：server/src/agents(Planner→toolRegistry→AgentRuntime→Approval审批节点→ApprovalContinuationService中断恢复)、server/src/creativeHub(CreativeHubLangGraph+InterruptLangGraph，统一创作中枢，对话/规划/工具调用/执行/回合总结都收口于此)、server/src/graphs(worldBuilding/characterDesign/novelOutline/writingFormula四张图)、server/src/modules/novel/{setup,planning,production,state,characters}按"开书→规划→生产→状态"切模块、server/src/modules/timeline(独立时间线子系统：extractor/checker/repair/policy/repository/context)、server/src/llm(factory注入式client、modelRouter按链路分模型、structuredInvoke+structuredFallback+structuredInvokeRepair结构化输出修复、requestLimiter/usageTracking)。【核心架构判断=控制面/执行面双面分离】自动导演把"控制面"(Web API只接command+返回轻量projection)和"执行面"(Director Worker租约执行重链路)彻底隔开：用户动作→DirectorRunCommand入队→Worker lease→DirectorPipelineEngine/StepModule→PolicyEngine→Artifact Ledger/DirectorEvent→Runtime Projection→前端轻量轮询；服务重启不静默续跑，从真实产物断点投影可恢复范围。Prisma schema约3400行/100+ model；docs/wiki有成体系的架构/工作流/调试/prompt文档(章节生产链、自动导演runtime、角色硬事实、质量守卫、RAG组装各自成文的"决策+规则+失效模式")，是难得能被fresh agent重建上下文的代码库。
- **状态/记忆设计**：极其完整，是全项目最值得偷的部分。四类持久层：(1)宪法/契约层：NovelBible(coreSetting/forbiddenRules/mainPromise/characterArcs/worldRules) + BookContract(readingPromise/protagonistFantasy/coreSellingPoint/chapter3Payoff/chapter10Payoff/chapter30Payoff/escalationLadder/relationshipMainline/absoluteRedLinesJson——正是网文"前30章承诺+绝对红线")。(2)设定层：World/NovelWorld(世界手册/规则/势力/地点/关系/冲突，每本书有自己的"本书世界"切片)、Character+角色硬事实(identityLabel/factionLabel/stanceLabel/powerLevel/realm/currentLocation/availability/prohibitions)、StoryMacroPlan、VolumePlan。(3)状态账本层(最精华)：StoryStateSnapshot按章immutable版本化(unique(novelId,sourceChapterId))，子表=CharacterState(currentGoal/emotion/stressLevel/secretExposure/knownFactsJson/misbeliefsJson——既记角色"知道什么"又记"错误地相信什么"，支撑信息差与戏剧反讽一致性)、RelationState(trust/intimacy/conflict/dependency四维打分)、InformationState(谁持有哪条信息+状态)、ForeshadowState(setup章→payoff章+状态)、OpenConflict(未决冲突+severity+resolutionHint)、PayoffLedgerItem(伏笔账本：ledgerKey唯一+生命周期状态setup→hinted→pending_payoff→paid_off/failed/overdue+targetStart/EndChapterOrder目标兑现窗口+riskSignalsJson+confidence)。另有NovelFactEntry事实清单(chapterOrder+text+category=completed/revealed/state_changed标记不可逆状态)、ConsistencyFact(按FactCategory=world/character/timeline/plot/rule)、ChapterSummary(summary/keyEvents/characterStates/hook=记忆压缩单元)。(4)权威状态层：CanonicalStateVersion(版本号递增+snapshotJson)经StateChangeProposal(proposalType/riskLevel/validated→committed)提案-提交式落库，状态变更不直接mutate而走"验证后提案再提交"。时间线独立成模块：StoryTimelineEvent(storyDayIndex/prerequisite/consequence/stateChanges)、ChapterTimeAnchor(forbiddenEventIds=本章禁止提前发生)、TimelineHook(创建章→预期解决章+blocking)、TimelineConstraint、TimelineCheckReport。数据结构特征：大量结构化列 + 大量`...Json String`不透明blob，DB不强约束、在边界用Zod校验。
- **章节循环**：章节生产链=热路径/冷路径双通道(docs/wiki/workflows/chapter-production-chain.md)：轻量预检→整章一次性writer→结构化"接收闸门(acceptance gate)"→可选局部patch修文→时间线定稿→异步artifact_delta资产回灌。关键编排：①统一执行链硬约束——批量执行/自动导演/手动单章生成/手动单章修复全部收口到同一套runtime(novelProductionOrchestrator→ChapterExecutionStageRunner→ChapterRuntimeCoordinator)，禁止各入口复制第二套writer/修文实现。②章节义务合同(obligation contract)贯穿写作-审核-修复：mustHitNow/mustPreserve/requiredPayoffTouches/requiredCharacterAppearances/requiredGoalChanges/canDefer/forbiddenCrossings，writer/接收闸门/局部修复/重规划消费同一份。③接收闸门输出结构化missingObligations并给repairability分级(patchable_obligation_gap局部漏写/rewrite_needed需整章/plan_misalignment职责失配)；硬阻断(must_hit_now+forbidden_crossing)进修复，只影响后续的payoff/露面/目标缺口记为continue_with_risk继续推进。④修复升级有限：patch repair优先，失败(Schema/定位/命中歧义)最多自动升一次heavy_repair，再失败登记"质量债务"继续后续章节，自动修文默认最多一次不进无限重试。⑤幂等：acceptance/timeline_finalization/artifact_delta都按"同章+同正文content hash"写持久化checkpoint(ChapterArtifactSyncCheckpoint)，调LLM前抢占running标记，worker重启正文未变则复用成功结果。⑥下一章前硬序列 final_content→timeline_finalization→next_chapter，ensurePreviousChapterFinalized兜底补齐。⑦冷路径artifact_delta=一次低温结构化调用统一抽取summary/concreteFacts/stateDeltas/payoffDeltas/relationDynamics/characterKnowledgeStates/syncPlan，写完才放行后续章节组装。多审校：AuditReport(auditType=continuity/character/plot/mode_fit)→AuditIssue(severity/code/evidence/fixSuggestion/status)；QualityReport五维打分(coherence/repetition/pacing/voice/engagement/overall)；另有不调LLM的确定性连续性诊断工具audit_chapter_continuity(场景模式关键词组重复检测、开头前30字前缀聚类)。
- **可借鉴**：
  - [L0作者宪法 + L1 StoryBible] BookContract：readingPromise/protagonistFantasy/coreSellingPoint/chapter3Payoff/chapter10Payoff/chapter30Payoff/escalationLadder/absoluteRedLinesJson——把'整本要写成什么样'与'绝对红线'结构化锁死，所有下游消费同一份 — 几乎逐字对应网文'前30章承诺+爽点节奏+红线'，可直接作为skill的开书契约模板
  - [L2 StateLedger] 按章immutable StoryStateSnapshot版本化(unique(novelId,chapterId))，子表CharacterState同时存knownFactsJson与misbeliefsJson(知道什么+错误相信什么)+secretExposure+RelationState四维分(trust/intimacy/conflict/dependency)+InformationState(谁知道哪条信息) — 这是防'角色提前知道未见证信息/人设漂移'的关键数据结构；misbeliefs/信息边界是多数同类项目没有的，强烈建议吸收
  - [L2 StateLedger] PayoffLedgerItem伏笔账本：ledgerKey唯一 + 生命周期状态机 setup→hinted→pending_payoff→paid_off/failed/overdue + targetStart/EndChapterOrder兑现窗口 + riskSignals + confidence；逾期(overdue)主动报警 — 把'伏笔'变成有截止章数和逾期态的可查询账本，直接解决长篇'埋了不收/提前收'，是skill里'伏笔追踪器'的现成蓝本
  - [L3 ChapterContract] 章节义务合同 obligation contract(mustHitNow/mustPreserve/requiredPayoffTouches/requiredCharacterAppearances/requiredGoalChanges/canDefer/forbiddenCrossings)，writer/接收闸门/局部修复/重规划共消费同一份 — 单份合同贯穿写-审-修，避免规划/写作/审核各自解释章节职责；是'章节级约束'最干净的落地形态
  - [L4生产闭环] 热路径/冷路径双通道：整章快写→结构化接收闸门→局部patch(失败最多升一次heavy_repair)→时间线定稿→异步artifact_delta用一次低温结构化调用统一抽summary/facts/stateDeltas/payoffDeltas/relationDynamics/characterKnowledgeStates — 正文生成不被状态抽取阻塞、状态抽取只调一次低温模型，既省token又保一致性；是章节循环的核心节流设计
  - [L4生产闭环(审校)] 接收闸门输出结构化missingObligations+repairability分级(patchable_obligation_gap/rewrite_needed/plan_misalignment)，并区分硬阻断(must_hit_now+forbidden_crossing进修复)与质量债务(continue_with_risk继续) — 把'AI写崩了怎么办'拆成可路由的决策，而非一律重写；'质量债务'让连载不被单章卡死，对自动连载至关重要
  - [L2/L3 + L4(防崩)] 确定性连续性守卫(不调LLM)：completedMilestones(已完成里程碑禁止再追求)、recentScenePatterns场景黑名单(时间+地点+动作三要素)、卷级keyMilestoneGuards(targetChapterRange内才允许的高潮事件，防提前写崩)、audit_chapter_continuity关键词组重复检测 — 用纯规则/关键词把最常见的崩点拦在生成前或低成本检出，比纯靠模型自觉可靠得多——code层硬约束的范例
  - [L2 StateLedger] CanonicalStateVersion + StateChangeProposal：权威状态走'验证后提案→提交为递增版本号snapshot'，不直接mutate；状态变更可审计、可回溯、带riskLevel — event-sourcing式的权威状态写入，避免AI乱改设定直接污染canon；skill若做状态台账可借鉴提案-提交分离
  - [L4生产闭环(上下文工程)] 统一上下文组装+预算策略：Context Broker/Resolver负责读取/预算/过滤/摘要(Prompt模板只声明需要哪些上下文不直接查库)，block按priority/required分级，超预算optional块摘要或drop但required永不静默丢，compression log可观测 — writer预算压到2600 token仍保住角色硬事实/义务合同/上一章尾段等required块；'required永不静默丢+丢弃可解释'是RAG注入的纪律范本
  - [L1 StoryBible→L4注入] 字符硬事实required context：identityLabel/factionLabel/powerLevel/realm/currentLocation/availability/prohibitions作为writer强制注入块(即使为空也保留并提示'不得凭空改写')，token压力下可压软简介但绝不裁硬事实 — 区分'软性人物简介'与'不可违背硬事实'两类上下文、并对硬事实做不可裁剪保证，是防阵营/境界错乱的关键工程手段
  - [L4生产闭环(工程纪律)] 统一执行链+content-hash幂等checkpoint：所有入口收口到同一writer/修复runtime，acceptance/timeline/artifact_delta按同章同content-hash写持久化checkpoint，调LLM前抢占running，重启正文未变则复用 — 保证'同一章不被重复评估/重复抽伏笔'，多入口长任务的幂等范式；skill做批量连载时同样需要这层去重
- **反模式**：反应式打补丁堆叠：大量机制是为修单个LLM翻车(反复追求已完成目标、凌晨四点蹲旅馆式场景重复、卷高潮被提前写出)而临时加的guard，docs每篇都有长长的'失效模式'清单——诚实但说明'约束AI写长篇'需要的脚手架量惊人，照搬会把补丁也搬进来 / schema巨型化+垂直线scope creep：~3400行/100+ model把Drama短剧、Comic漫画、甚至astrology占星页塞进同一schema/monorepo，对'写网文'目标是纯负担，约40%代码与核心无关 / stringly-typed JSON blob泛滥：几乎所有复杂状态都是`xxxJson String`存进SQLite，DB层零约束，全靠边界Zod兜——一致性保证依赖运行时而非存储契约，drift风险高 / writer上下文预算被压到极致(stageTokenCap.writer默认仅2600 token)，导致需要priority/required分级+compression log+子集筛选一整套机器来塞进必选约束——是真问题但也反映单次注入全量设定根本不可行 / 重型基础设施(Worker租约/两面分离/DirectorRunCommand幂等/checkpoint)对'产品'必要，但对一个skill/workflow是过度工程，不应连infra一起抄
- **OE判定**：对其'让新手写完整本书'的产品目标而言，状态机器的复杂度大体是合理的——长篇连贯性确实需要按章immutable快照、伏笔账本生命周期、角色已知/误信事实、义务合同这些结构，热/冷双通道+content-hash幂等也是真实的长异步任务+worker重启需求。但有明显过度部分：(a)Drama/Comic/占星三条垂直线挤进同一仓库与schema=纯scope creep；(b)相当一部分逻辑是对LLM涌现式翻车的反应式打补丁；(c)控制面/执行面双面分离+租约+DirectorRunCommand幂等对一个'写作约束skill'是重infra过度工程。结论：数据契约与循环纪律值得，infra与垂直线不值得。
- **偷/避**：偷它的分层数据契约(BookContract绝对红线/章3·10·30承诺 + 按章immutable StoryStateSnapshot含角色knownFacts/misbeliefs + PayoffLedger带目标兑现窗口和overdue状态机 + 章节义务合同mustHitNow/forbiddenCrossing + 不调LLM的确定性连续性诊断)和它的"热路径快写、冷路径一次低温结构化调用抽全部状态delta"循环纪律；避开它的100表巨型monorepo、Drama/Comic/占星垂直线、以及Worker/双面分离重infra。

### NousResearch/autonovel (1210★, semi-active, usable-tool)
https://github.com/NousResearch/autonovel
- **做什么**：NousResearch（Hermes Agent）出品的"全自治长篇小说生产流水线"：从一个 seed 概念到印刷级 PDF / ePub / 多人配音有声书 / landing page，全程 AI agent 生成。明确致敬 karpathy/autoresearch 的 modify-evaluate-keep/discard 循环，把它从"科研"搬到"虚构写作"。已真实产出一部 19 章、79,456 字的奇幻小说《The Second Son of the House of Bells》（在 autonovel/bells 分支）。27 个 Python 脚本 + 7 份框架 Markdown，单 orchestrator 一键跑完。
- **架构**：核心是"五层共演化文档 + 四阶段门控流水线 + git 作为 keep/discard 基底"，全部由 run_pipeline.py（891行）编排，evaluate.py（835行）当裁判。
分层（master 分支 = 纯框架，永不被 pipeline 改；per-novel 分支 = 填充内容）：
- 框架层(可复用): program.md(每阶段 agent 指令)、CRAFT.md(写作技艺教育)、ANTI-SLOP.md(词级AI味)、ANTI-PATTERNS.md(结构级AI味)、voice.md Part1(永久护栏)。
- 模板层(每本填充): world.md/characters.md/outline.md/voice.md Part2/canon.md/MYSTERY.md/state.json。
四阶段：Phase1 Foundation(gen_world→gen_characters→gen_outline→gen_outline_part2 伏笔账本→voice 发现子循环→gen_canon)循环到 foundation_score>7.5 且 lore_score>7.0；Phase2 Drafting 顺序写章 draft_chapter.py，章分>6.0 才 keep 否则重写(最多5次)；Phase3 Revision 3-6 轮(adversarial_edit 砍字→apply_cuts→reader_panel 4人格→panel 共识项→gen_brief→gen_revision，plateau 检测<0.3 停)；Phase3b Opus 评审循环(最多4轮，双人格"文学评论家+小说教授")；Phase4 Export(LaTeX/ePub/封面/有声书)。
关键架构信号：writer 用 Sonnet、judge 用 Opus(刻意异模型，"避免自我表扬")；evaluate.py 在自治运行时是 READ-ONLY，只有人类调它来定义"什么是好"，agent 把它当黑盒——这是"生成上下文 vs 验证上下文分离"的工程化落地。
- **状态/记忆设计**：这是它最值得偷的部分，状态被拆成三类显式数据结构：
1) canon.md = 硬事实数据库。开篇就写明"每条都是 evaluator 检查的约束，prose 与 canon 冲突即 bug"。按类目分组(Geography/Timeline/Magic System Rules/Character Facts/Political/Cultural/Established In-Story)，每条是一句可证伪陈述 + 来源标注(world.md / ch_03 / characters.md)。刻意"扁平可扫描，不是散文，是数据库"。foundation 要求 400+ 条才能出关。每章评审输出 new_canon_entries，自动 append 回 canon——记忆从生产中增长。
2) 伏笔账本(Foreshadowing Ledger) = outline.md 里的表格 | ID | Planted | Payoff | Thread | Status |，外加 characters.md 每人 "Ch N: 种了什么(payoff: Ch M)"。从 foundation 维护到 drafting，"每个 plant 都要有 payoff"，evaluator 的 foreshadowing 维度空账本直接 0 分。
3) state.json = 流水线状态机(phase/iteration/foundation_score/lore_score/chapters_drafted/novel_score/revision_cycle/debts)。
记忆压缩：写第N章时上下文 = voice 全 + world 全 + characters 全 + canon 全 + 本章 outline 条目 + 上一章"最后2000字符" + 下一章 outline 前10行。即设定集全量入场，但相邻章只带尾部摘要而非全文——这是它处理"长文不爆context"的手法。注意：world bible 在章级评审时被截断到 4000 字符。
重大局限：canon/伏笔账本是纯文本人读式，evaluator 靠 LLM 跨引用而非结构化校验；且"五层向上向下传播、用 state.json 追踪 propagation debts"在 README/PIPELINE 被大书特书，但 run_pipeline.py 里 debts 只被初始化成 []，全程从不读写——这是文档吹了代码没实现的 drift。
- **章节循环**：章节级是"门控生成 + 多 rubric 多人格审校 + git keep/discard"：
生成：draft_chapter.py 装配上文(见 state_memory)，prompt 末尾挂一长串"PATTERNS TO AVOID（这些在前面章节被 flag 过）"——即把 evaluator 早期发现的 AI 味反喂进后续章的生成约束，闭环。目标~3200字，要求 70%+ in-scene、对话像口语会结巴、至少一个"意外"打破可预测的优秀。
评审(两套免疫系统)：
- 机械免疫(evaluate.py 无LLM)：正则扫 TIER1 禁词(delve/utilize/tapestry…)、TIER2 可疑词聚簇、虚构AI俗套(eyes widened / a sense of / heart pounded)、show-don't-tell 的"telling"动词、结构性AI tic("not just X, but Y"、三连片段)、em-dash 密度、句长变异系数、段落开头转折词比例 → 算出 slop_penalty(0-10)。
- LLM 裁判(Opus, temp 0.3)：章级 9 维 rubric(voice_adherence/beat_coverage/character_voice/plants_seeded/prose_quality/continuity/canon_compliance/lore_integration/engagement)，每维强制输出 score+weakest_moment+fix，外加三条最弱句/最强句引用、ai_patterns_detected、new_canon_entries、top_3_revisions。
关键：最终分 = judge 分 − 机械 slop_penalty，确定性扣分，judge 管不到。rubric 内置反分数膨胀("AI章中位数=6，8很罕见，9极罕见，10对初稿不存在；若你给>7就回去重读 gap 把分调低")。
keep/discard：章分≥6.0 → git commit keep；<6.0 → discard 重写(最多5次)；revision 阶段改完 evaluate.py --chapter=N，post≥pre 才 commit，否则 git reset --hard 回滚。
小说级审校：reader_panel 4 人格(editor/genre reader/writer/first reader)回答 momentum_loss/cut_candidate/thinnest_character/missing_scene 等→取 3/4 或 4/4 共识项当修订优先级；compare_chapters 跑章间 Elo 锦标赛；adversarial_edit "砍500字"分类出 OVER-EXPLAIN/REDUNDANT；Opus 双人格终审，停机条件是"无 major 未限定项 / 过半是限定性 hedge / ≤2 项"，并有定性信号"当评语从'小说有问题'变成'这些是雄心的代价'就停"。
- **可借鉴**：
  - [L0作者宪法 + L4生产闭环] 双免疫系统：确定性正则 slop 扫描器(禁词/虚构俗套/show-don't-tell/结构tic) + LLM rubric 裁判，最终分=裁判分−机械确定性扣分 — 完全对应我们 engineering rule 的'硬不变量用代码 append 不交给 LLM'。中文网文要把英文词表整套换成中文AI味词典(诸如'不禁/一抹/眸子/空气仿佛凝固')+中文 telling 检测，正则思路直接复用
  - [L4生产闭环] writer/judge 异模型分离(Sonnet 写、Opus 评)+ evaluate.py 自治运行期 READ-ONLY、只有人调参 — 生成上下文与验证上下文分离的落地；避免同模型自我表扬。我们的章节审校 agent 应固定用不同模型/不同温度
  - [L2 StateLedger] canon.md 硬事实库：扁平、可证伪、带来源标注、按类目分组、'与 prose 冲突即 bug'、每章评审产出 new_canon_entries 自动回灌 — 我们的 StateLedger 核心范式；改进点是把它从纯文本升级为可结构化校验(JSON/SQLite + 自动一致性 check)而非靠 LLM 跨引用
  - [L2 StateLedger] 伏笔账本表格 |ID|Planted|Payoff|Thread|Status|，foundation 即建、drafting 全程维护，空账本评分直接0 — 连载尤其需要——把'挖坑/填坑'做成有状态机的显式账本，未填坑可作为下章生成的强约束注入
  - [L4生产闭环] 门控阶段推进：foundation_score>7.5 且 lore_score>7.0 才进 drafting；章分≥6.0 才 keep；plateau(Δ<0.3 连续2轮)停 — 'forward progress over perfection, 6.0 够用'的阈值哲学很务实；plateau 检测避免无限磨
  - [L4生产闭环] git 当 modify-evaluate-keep/discard 基底：improved→commit，worse→reset --hard；results.tsv 记录每次 keep/discard — 用 VCS 做实验台账，每个修订可回滚、可审计；比在内存里 diff 干净
  - [L3 ChapterContract] evaluator 发现的 AI 味反喂进 writer prompt 的'PATTERNS TO AVOID（前章被flag过）' — 审校→生成的闭环；让后续章在生成时就规避已知失败模式，而不是写完再砍
  - [L4生产闭环] 逐维度强制 gap+fix 的 rubric + 反分数膨胀校准('中位数=6，>7就回去把分调低') — 防止 LLM-judge 一味给高分；强制引用 weakest_moment 原句让评分可追溯
  - [L4生产闭环] 多人格/多 rubric 审校栈：reader_panel 4人格取共识 + 章间 Elo 锦标赛 + 'cut 500 words'对抗式编辑 + Opus 双人格终审带定性停机条件 — 单一 rubric 抓不到的问题(角色单薄、节奏单调、'全员点头无摩擦')靠多视角补；停机靠'问题严重度+是否被hedge'而非'零缺陷'
  - [L0作者宪法] 框架/内容分离：CRAFT/ANTI-SLOP/ANTI-PATTERNS/voice Part1 在 master 永不变，内容在 per-novel 分支 — 作者宪法(怎么写)与故事圣经(写什么)物理隔离，复用性来源；但见反模式——它自己没守干净
- **反模式**：整本灌进 1M context 的非连载架构：full novel 评审/Opus 终审把全部章节塞进单次 1M-context 调用。这对~80k字单本可行，但对几百章的网文连载是硬天花板——超过~150k字就崩，且每轮全文重评成本爆炸。它根本不是为'连载/无限续写'设计的，是为'有界单本一次性产出'。 / 机械 slop 词表全英文：TIER1/2/3、虚构俗套、telling 动词、结构tic 全是英文正则，对中文网文零用，必须整套替换为中文AI味检测，不能直接搬。 / 'propagation debts 传播账本'文档吹了代码没实现：README+PIPELINE 反复讲'五层向上/向下传播、state.json 追踪传播债务'，但 run_pipeline.py 里 debts 只 init 成 []，全程不读不写——典型 doc/code drift，是手工时代的叙事没落进自动化 runner。 / 框架/内容分离没守干净：draft_chapter.py 把《Bells》《Cass POV》《bronze/bells 隐喻》《编号14-24的反模式规则》硬编码进 prompt，违反了它自己'master 无故事内容'的宣称——所谓'可复用框架'其实是从 bells 分支固化下来的，真要复用得先把这些抽成模板变量。 / reader_panel 共识解析脆弱：用正则从 4 个人格的自由文本答案里抠 'Ch\d+' 来定位问题章，是不稳的控制信号——违背'分支应基于已验证的 sentinel 而非自由文本'原则。 / 单一锁定 POV 假设：draft 锁死单一第三人称限知 POV，网文常见多线/快速切POV，直接套不适配。 / 无读者反馈回路：评审全是 AI 自评/AI 人格模拟读者，没有真实读者/数据驱动(网文连载的命脉是追读率/章评)——它优化的是'文学评论家会怎么看'，不是'付费读者会不会追'。 / 研究代码卫生：无 license、无测试、subprocess shell=True 跑全部工具、错误多为 WARN 吞掉继续——能跑出成品但不是生产级。
- **OE判定**：不算 overengineered，但复杂度分布失衡。值得的复杂度：双免疫系统、逐维度 gap+fix rubric+反膨胀校准、git keep/discard、门控阈值+plateau 检测、多人格审校栈——这些都直接服务于'防AI写崩'且被一部真实79k字小说验证过，复杂度配得上产出。不值得/虚的复杂度：五层共演化+propagation-debt 传播账本这套被大量文档化但根本没在 runner 里实现(aspirational 叙事)；framework/content 分离做了一半。真正的设计债不是'太复杂'而是'架构选错战场'——whole-manuscript-in-context 的有界单本模型，对连载是结构性不匹配。结论：作为'单本 AI 写作 + 防slop'的工程清单，复杂度物有所值且可直接借鉴；作为'连载生产系统'的蓝本，它的编排骨架要重做。
- **偷/避**：偷它的"双免疫系统(确定性slop正则+异模型LLM-judge，最终分=判分−机械扣分) + 逐维度 gap+fix 反膨胀 rubric + canon硬事实库/伏笔账本两本台账 + git keep/discard 门控 + CRAFT/ANTI-SLOP/ANTI-PATTERNS 防AI味清单 + 评审反喂生成的闭环"；避开它的"整本灌进1M-context 的非连载架构、英文-only词表、文档吹了没实现的 propagation-debt 传播账本、以及把故事内容硬编码进所谓'框架'的不彻底分层"。

### MaoXiaoYuZ/Long-Novel-GPT (1161★, semi-active, usable-tool)
https://github.com/MaoXiaoYuZ/Long-Novel-GPT
- **做什么**：AI 长篇网文生成器：给一句"小说简介+修改意见"，按 大纲→章节→剧情→正文 自顶向下逐层扩写，可在本地解除线程限制后多窗口并行生成百万字。带 Docker 一键部署、Web 前端（选片段/选动作/选模型）、多家 LLM（OpenAI/文心/豆包/讯飞/智谱）、MongoDB 调用缓存 + 实时费用统计，以及"天蚕土豆风格"等可投稿 Prompt 库。定位是"在用户监督下生成达到网文签约门槛"，全自动"一键成书"仍是未完成目标。
- **架构**：核心抽象是 core/writer.py 的 `Writer` 类 + `xy_pairs`：每个 Writer 维护一个 (x, y) 二元组列表，x=上一层级的"源文本"片段，y=本层级生成的"目标文本"片段，两列严格一一对齐。三个子类构成自顶向下的层级管线：OutlineWriter(x=小说简介 summary → y=章节大纲)、PlotWriter(x=章节大纲 chapter → y=分章剧情)、DraftWriter(x=剧情 plot → y=正文)。跨片段的"全局态"放在 `global_context` dict（实际每个 writer 模式只挂一个字段：outline 挂 summary、plot 挂 chapter、draft 为空）。\n数据流：用户给简介+意见 → OutlineWriter.write() 生成章节并 split_chapters 切成 xy_pairs → 每章作为 chapter 喂给 PlotWriter 扩写剧情 → 每段剧情作为 x 喂给 DraftWriter 扩写正文。每层把短 x 映射成更长的 y，扩写率≈输出窗口/x_chunk_length（outline 2000/2000、plot 200/1000、draft 500/1000）。\n关键工程点：(1) `get_chunks()` 用累积字符数 + bisect 做 chunk 切分，按"八二原则"近似划分，context_length=chunk_length//2 只取相邻片段做上下文；(2) `batch_yield()` 是生成器协程池，按 max_thread_num 轮转 next() 实现多 chunk/多 Writer 并发（"百万字快"的来源）；(3) 后端 backend/app.py 用 Flask SSE 流式把每个 chunk 的 delta 推给前端，Chunk 的 source_slice/text_slice 这套 slice 代数支撑"任意选中片段重生成 + 实时 diff"。llm_api 层做 ModelConfig 抽象 + MongoDB 缓存(mongodb_cache) + 成本统计(mongodb_cost)。
- **状态/记忆设计**：关键结论：没有显式的设定集/人物卡/时间线/伏笔数据结构，也没有向量库。一致性完全靠三个"结构化文本"机制：\n1) 两列对齐表征(xy_pairs)——剧情↔正文一一对齐就是"记忆"的载体；改了正文后用 prompts/对齐剧情和正文（LLM 输出 JSON：把每个剧情段映射到一组连续正文段序号）重建对齐，parser 里有大量手写修补保证单调映射。\n2) 滑动窗口局部上下文——创作 prompt(context_prompt.txt) 把相邻 chunk 作为 context_x/context_y 多轮注入（多轮结构是为了 Prompt Caching），只保证局部连贯。\n3) 双向层级同步(防漂移核心)——summary()/提炼 prompt 反向把 正文→剧情→章节→大纲 重新压缩回写 global_context；写作时上层纲要作为 x 硬约束下层，形成"自顶向下生成 + 自底向上回灌"的闭环。\n重要落差：README 宣称"基于 LLM 和 RAG""拆书提取人物关系"，但代码里 (a) 无 embedding/faiss/chroma 任何向量检索依赖；(b) prompts/检索参考材料 这个 LLM-rerank-topk prompt 在所有 .py 里根本没被 import/调用，是遗留/未接线死代码；(c) 提炼剧情 只把正文压成"每行≤50字一句"的剧情概括，并不抽取结构化实体。因此长程一致性（第3章 vs 第50章的人物属性、伏笔回收）没有任何工程保障，全靠人盯——这正是它最大的空缺，也是我们 L2 StateLedger 要补的地方。
- **章节循环**：编排在 Writer.batch_write_apply_text()：① write_text() 用创作 prompt（每层三个动作：新建/扩写/润色，由用户在 UI 选）生成新 y → ② batch_map_text() 把新生成的长 y 重新切块、用"对齐剧情和正文"LLM prompt 映射回 x 段，维持 xy_pairs 对齐 → ③ apply_chunks() 按 span 写回（带 overlap 断言）。\n审校循环在 batch_review_write_apply_text()：先 review_text() 跑"审阅"prompt（system 设定为"网文主编"，rubric 含场景描写/人物刻画/画面感/文笔，要求逐点一针见血）→ 把审阅意见拼上"根据审阅意见重新创作，若无需改动则原样输出"当作下一轮 user_prompt → 再 write → map → apply。\n关键限制：(a) review_text 上方源码注释明写"目前 review(审阅)的评分机制暂未实装"——所以没有打分阈值 gate、没有"不达标才重写"的判断，review 退化成无条件一轮重写；(b) 单 rubric、单 agent，无多评审/多轮辩论/多版本择优；(c) "若无需改动则原样输出"是弱控制信号，没有 sentinel token 验证；(d) 全流程强人机在环——用户逐片段选动作、选模型、看 diff，不是自动防崩。主/副模型分工：model 做创作、sub_model 做对齐映射等机械活。
- **可借鉴**：
  - [L3 ChapterContract + L4 生产闭环] 自顶向下分层扩写：简介→章节→剧情→正文，每层固定扩写率，短文本逐级扩成长文本 — 天然 token 控制 + 每层都有可校验的中间产物；我们可把'大纲→章纲→正文'同构落成每层一个 contract
  - [L1 StoryBible + L2 StateLedger] 上下层双向同步：上层纲要作为下层生成的硬输入约束(x)，下层改动后用'提炼'反向回灌更新上层纲要(防漂移) — 最值得偷的机制——把 StoryBible/大纲既当生成输入又当回写目标，编辑底层自动同步上层，是轻量一致性闭环
  - [L2 StateLedger / L3 ChapterContract] 两列对齐表征(源↔目标 xy_pairs) + LLM 输出 JSON 重建对齐 — 思想可借鉴(剧情与正文逐段绑定便于定位重写)，但 LLM 维护 slice 对齐的实现过脆，建议改用稳定 ID/锚点而非字符 slice
  - [L4 生产闭环(成本控制)] 滑动窗口局部上下文(context=chunk//2) + 多轮 context_prompt 利于 Prompt Caching — 只喂相邻 chunk + 多轮对话结构命中缓存，是控 API 成本的直接手段
  - [L4 生产闭环(章节级 review)] 审阅意见→重写闭环：把'主编 rubric 审稿意见'作为下一轮 user_prompt 注入 — 轻量 reflexion；我们要补上它缺的'打分阈值 gate + 多 rubric + sentinel 控制信号'
  - [L4 生产闭环(成本/质量分配)] 主/副模型分工：贵模型创作、便宜模型做对齐/映射/总结等机械任务 — 按任务难度路由模型，直接降本
  - [L0 作者宪法] 可投稿风格 Prompt 库(天蚕土豆风格=固定口头禅+高频词表+代表作设定) — 用可插拔的'风格卡'约束文风，社区可贡献；可作为 L0 作者宪法的具体载体
  - [L4 生产闭环(吞吐)] 生成器+协程池 batch_yield 按 max_thread_num 并发多 chunk/多章 — 章节间无状态依赖时并行生成，是'百万字快'的来源
- **反模式**：把'一致性'完全寄托在两列对齐文本 + 人盯，没有任何显式实体/状态层(人物卡/时间线/伏笔)：规模一上去长程一致性必崩——这是它最大的结构性缺陷 / README 营销级'RAG'与代码不符：无向量检索依赖，检索参考材料 prompt 在 .py 里从未被调用，是误导性死代码(文档/代码不一致) / review 评分机制源码注释明写'暂未实装'，却保留 review_text 接口 → 审校退化成无门槛一轮重写，没有质量 gate / core/writer.py 单文件 400+ 行，xy_pairs/Chunk/source_slice/text_slice/align_span 这套字符级 slice 代数极复杂、满是 assert 和 TODO，且和前端 diff 强耦合——为'任意片段重生成+实时diff'付出过高工程复杂度，可读性/可维护性差 / 对齐严重依赖 LLM 稳定输出严格 JSON 映射，parser 里堆了大量手写补丁修单调性，脆弱 / '提炼人物关系'在 README 承诺但代码只做文本概括，未兑现 / 无 license、强人机在环——把'达到签约门槛'的责任推给用户监督，并非自动防崩系统
- **OE判定**：局部 overengineered，整体方向对。核心思路（自顶向下分层扩写 + 上下层双向同步防漂移 + 滑窗控成本 + 并行）是简洁有效、值得直接借鉴的。但它把大量复杂度押在了"用 LLM 维护两列字符级 slice 对齐 + 实时 diff"这条支线上（writer.py 的 Chunk/slice 代数），这部分复杂度与收益不成正比、脆弱且难维护；同时却在最该投入的'显式状态/一致性层'上完全留空（无实体层、RAG 名存实亡、review 评分未实装）。即：在不重要处过度工程、在最关键处欠工程。
- **偷/避**：偷它的"自顶向下分层扩写 + 上下层双向同步(改正文回灌纲要防漂移) + 滑窗上下文控成本 + 主副模型分工"四件套；避开它"用 LLM 维护两列字符 slice 对齐"的脆弱重工程，并务必补上它最大的空缺——一个显式的 L2 StateLedger/人物卡实体层和带打分阈值的 review gate（它的 RAG 和 review 评分都是没兑现的空壳）。
