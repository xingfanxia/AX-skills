# 11 · 阶段性维护与复盘

> Purpose: 章节循环之外的"边界批处理"规格 —— 在**每 N 章 / 每卷边界 / 上架前 / 数据回报后**把会随篇幅漂移的东西（摘要膨胀、状态变脏、伏笔逾期、爽点平路、数据信号）批量收敛回稳态。覆盖：递归压缩摘要、状态刷新/清脏、regression 体检（对应 `scripts/state_check.py`）、数据反馈闭环、工作模式 A-E 选择器、上架付费卡点校验、平台 AI 检测合规。用在 SKILL.md 全景图最右列「阶段性维护」，工作模式选择器还用在**阶段0 §2.1 校准**。

---

## 0. 一句话原理

章节循环（步骤 1-9）只保证**单章**不崩；**跨章漂移**靠它兜不住——摘要会膨胀丢早期细节、`Pending/Inferred` 会沉积成脏上下文、伏笔会埋了忘填、爽点会连续平路、平台数据会暴露写崩的章。这些都不是每章能判的，要在**边界节点批量跑**。维护 = 把"靠勤奋 maintain"换成"靠边界批处理 + 确定性脚本强制"，节拍越长的书越值得上（"靠 agent 自律"恰恰是会漂移的那一环）。

> 铁律延续：任何 MUST-hold 不变量（伏笔到期、阶位单调、专名唯一、可见性红线）由 `state_check.py` code 强制判，**绝不写进 prompt 当已执行**。脚本只抓**机械可判**的那部分；语义级矛盾（人物瞬移、动机断裂）仍需 LLM continuity-checker。两者分工、不互相冒充。

---

## 1. 维护节拍表（什么时候跑什么）

| 节点 | 触发 | 跑哪几件 | 谁拍板 |
|---|---|---|---|
| **每章末** | 状态回写后 | `state_check.py` 快跑（伏笔临近/情绪债/阶位）+ `previous_tail` 重置为本章末段 | automate |
| **每 arc（10-15 章）** | planner 重规划前 | 压缩 `compressed_recent`、刷新 sao 排布密度、把 arc 内 `open` 伏笔过一遍 | semi-auto |
| **每卷（30-80 章）** | 卷收尾 | 全量 `state_check.py` + 卷级摘要固化 + 清脏上下文 + Canon 批量晋升 + 递归压缩降一层 | human-in-loop |
| **上架前** | 免费期转付费节点 | 首免章完整性 + 首付费章兑现校验（§7）+ 全量体检 + AI 检测合规（§8） | human-only |
| **数据回报后** | 拿到追读/完读数据 | 定位高跳出章 → 决定是否重写/换书名简介（§5） | human-only 拍板 |

**降介入频率（防拖垮日更）**：每章不召人，只有 `state_check.py` 报 `error`（退出码 1）或 reviewer 报异常才召回人；常规维护批处理压到 arc/卷边界。

---

## 2. 递归压缩摘要（防"记忆膨胀 vs 丢早期细节"两头崩）

**原理**：滚动摘要用递归式 `M_i = LLM(H_i, M_{i-1})`——新摘要 = 模型读「本段历史 H_i + 上一版摘要 M_{i-1}」重写。问题是数十万字后**累积信息丢失**（blueprint §10#2），所以不能只靠一层摘要，要**分层 + 分流**。

**分流铁律（决定哪些永不丢）**：

| 进【永不压缩的结构化 canon】(状态文档 01-05) | 进【可压缩摘要】(`rolling-summary.yaml`) |
|---|---|
| 关键设定 / 数值 / 阶位 / 专名 / 角色行为锚点+认知边界 | 情节流水、场景细节、对话过程 |
| 伏笔台账（`status` 状态机） / 情绪债账本 | 已回收伏笔的过程描写 |
| 主线 beats / 顶层契约 | 配角一次性桥段 |

> 一句话：**事实进 canon，叙事进摘要。** canon 由独立状态机治理、永不进压缩管线；摘要可以越压越糙，丢的也只是"怎么发生的"，不是"发生了什么是真的"。

**压缩顺序铁律**：**先最大化召回，再提精度**——压缩时宁可先多留（漏掉一条到点伏笔/一个认知边界比多留一句废话代价大得多），确认无遗漏后再删冗余。反过来（先精简后补召回）会永久丢早期细节。

**分层视图**（对照 `rolling-summary.yaml` 字段，30 章以上触发降层）：

| 层 | 字段 | 粒度 | 进 prompt 时机 |
|---|---|---|---|
| 章级 | `per_chapter[].one_line/sao/hook` | 每章一句话，几乎不压 | 仅取最近若干条 |
| 近况 | `compressed_recent` | 最近 3-5 章压缩叙述，滚动重写 | 每章 |
| 续写锚 | `previous_tail` | 上一章末段**原文**（不是摘要） | 每章（writer 主记忆源，防断点跳脱）|
| 卷级 | `volume_summary[]` | 每卷一段，卷边界固化 | 跨卷 prompt |
| 全书 | `mainline_summary` | 极简常驻，对齐 `contract.mainline_anchors` | 常驻 |

**卷边界压缩动作**：①把本卷 `per_chapter` 蒸馏成一条 `volume_summary`；②`compressed_recent` 清空、重新从新卷起算；③已 `closed` 的伏笔从近况层移除（canon 台账里保留记录）；④`previous_tail` 始终只保留最新一章末段。

---

## 3. 状态刷新 / 清脏上下文 / 卷级摘要固化

卷边界是**唯一**改写 canon 治理标签的批处理窗口（章内只 append delta，不动 Canon 状态）。四个动作：

1. **重载设定、清脏上下文**：把本卷产生的 `Inferred`（AI 推断未确认）逐条过人——晋升 `Canon` 或降 `Rejected`，**不让推断沉淀成事实**（这是长线设定漂移的根因）。已 `Rejected` 的条目从注入候选里剔除，避免脏数据被 compile 误抓。
2. **Canon 批量晋升**：本卷已写进正文、读者已知的 `Pending` 事实，**人确认后**批量升 `Canon`（晋升需人确认，是硬规则）。升级后 `visible_from_volume` 重核——确保不会把下一卷才该揭的事提前放进 prompt。
3. **卷级摘要固化**：见 §2 卷边界压缩。固化后该卷流水细节不再进 prompt，只走 `volume_summary`。
4. **可见性红线复核**：`state_check.py` 校验所有 `visible_from_volume` 为正整数；人工抽查"幕后黑手/最终反转/隐藏身份"等条目的卷号是否仍 > 当前卷（渐进式披露不被破坏）。

---

## 4. Regression 体检表（对应 `state_check.py`）

每卷边界 / 上架前跑 `python3 scripts/state_check.py <book_state_dir>`（`--current-chapter N` 覆盖当前章，否则读 `contract.meta.current_chapter`）。退出码 `0`=无 error、`1`=有 error 必须人工处理。机械可判项由脚本抓，语义项由 LLM 补。

| 体检项 | 崩坏症状 | 判定 | 数据源 / 字段 | error/warn |
|---|---|---|---|---|
| **伏笔逾期** | 埋了忘填=烂尾（一票否决毒点） | `current_chapter > planned_payoff_ch` 仍 `open/微回应` | `foreshadow-ledger.yaml` | **error** |
| 伏笔临近 | 该回收了 | `0 < planned_payoff_ch − current ≤ 5` | 同上 | warn |
| 伏笔无计划 | 埋时没回收章 | `open` 但 `planned_payoff_ch` 空 | 同上 | warn |
| **伏笔密度** | open 远超 closed（翁法罗斯式翻车） | `open ≥ 3×(closed+1)` | 同上 | warn |
| **资源/数值凭空** | 战力倒挂、越级、境界倒退 | `current_state.level` 不在 `power_system.ladder` | `state-world` + `state-characters` | warn |
| 专名漂移 | 同一别名指多个 canon_name | glossary `aliases` 冲突 / 缺 `canon_name` | `state-world.glossary` | error/warn |
| Canon 枚举非法 | 治理标签写错 | `canon_status ∉ {Canon,Pending,Rejected,Idea,Inferred}` | 全状态文档 | error |
| 可见性非法 | 防剧透标签坏 | `visible_from_volume` 非正整数 | 全状态文档 | error |
| **承诺久未兑现** | 虐点久未补偿 | 情绪债 `released=false` 且 `duration_chapters ≥ 5` | `emotion-debt.yaml` | warn |
| 释放不解气 | 打脸不够爽 | `release_intensity < intensity` | 同上 | warn |
| **连续 N 章无进展** | 平路过长、追读掉 | 连续若干章无 `sao_schedule` 条目 ⚠️ | `emotion-debt.sao_schedule` | warn |

**纯 LLM 才能判（脚本判不了，卷边界补一次 continuity-checker 全卷扫）**：人物瞬移（位置/时间矛盾）、动机断裂、misbeliefs 被无故纠正、认知边界泄漏（角色说出 `does_not_know` 的事）、注水（信息密度骤降）。

> ⚠️ 自动一致性检测精度有限（F1≈0.68、叙事连贯仅 0.51），百万字尺度只能"标记可疑"，**裁决靠人**。所以脚本只把高置信机械项判 error、其余判 warn 给人复核，不假装能全自动裁决。

---

## 5. 数据反馈闭环（追读/完读 → 定位 → 重写）

**原理**：平台用可量化留存指标分配流量，追读率是生死线、完读率决定收入高低。把指标当**信号**反向定位写崩的章，触发重写——但所有阈值**都是经验/内部流出值，平台算法不公开，一律当可调参数，不硬编成常量**。

| 指标 ⚠️（单一来源/经验值，medium） | 经验线 | 用途 |
|---|---|---|
| 番茄三章追读率 | ≥35% 及格 / ≥45% 优秀 | 黄金三章生死线 |
| 完读率（10 万字） | ≥15% / ≥20% | 决定收入高低 |
| 追更率 | ≥40% → 约 5 倍流量倾斜 | 流量分配 |
| 情绪高峰间隔 | top10% 约 1.8 章 / bottom10% 约 4.7 章；平路 >3 章追读开始掉 | 节奏体检阈值 |

**闭环动作**：①采集指标（automate）；②定位高跳出章（automate：找留存曲线断崖）；③诊断（对照 §4 体检 + reviewer rubric 找该章是毒点/平路/还是钩子失效）；④**是否重写 / 换书名简介 = human-only 拍板**（追读写崩仍可能平稳、需作者判断，且换书名是不可逆商业决策）；⑤把已暴露的失败模式反喂——写后续章 prompt 时塞进 `PATTERNS TO AVOID`，让 writer 写之前就规避（autonovel 的"审校反喂生成"）。

> MVP 不接真实平台 API（属完整版增量）；MVP 阶段由人把后台数据手动填进体检，pipeline 只负责定位+诊断+反喂。

---

## 6. 工作模式 A-E 选择器（介入深度旋钮）

阶段0 §2.1 校准时与创作者商定，**随时可切**。决定 AI 在每个半自动步骤里替人做多少。

| 模式 | 名称 | AI 做什么 | 适合 |
|---|---|---|---|
| **A** | 只给思路 | 出方向/选项清单，不落字 | 作者强、要完全掌控创意 |
| **B** | 给多方案选 | 每个决策点出 2-3 套并列方案，人选 | 作者有判断力、要效率 |
| **C** | 推荐主案+理由 | 出 1 个主推 + 理由 + 备选，人拍板 | 作者要建议但保留否决权（默认推荐起点）|
| **D** | 直接产初稿我改 | 直接出初稿，人在稿上改 | 作者擅长改不擅长起 |
| **E** | 叙事总监式全程托管 | AI 跑完整循环，只在 reviewer 报异常/卷边界召人 | 作者要产能、信任流水线 |

**铁律不随模式变**：无论 A-E，human-only 项（核心冲突/结局/主线锚点/底层规则/品类平台/剧情走向拍板/节奏爽点力度/Canon 冲突裁决）**永远人定**——模式只调"半自动步骤里 AI 替人做多少"，不调"谁拥有创意主权"。E 模式不等于 AI 自由决定剧情（那是 5-10 年前的旧套路）。

---

## 7. 上架付费卡点校验（上架=第二次签约）

**原理**：上架是付费节点，等于"第二次签约"——免费期证明价值，首个付费章必须**先兑现再加压**。VIP 有效字数门槛 = 日更约 4000 字（全勤/扶持硬条件）⚠️。上架前做专门 gate：

| 校验 | 判什么 | 不过的后果 |
|---|---|---|
| 首免章完整性 | 免费区最后一章不卡半截、给读者"值得付费"的理由 | 转付费率掉 |
| **首付费章先兑现** | 第一个付费章**先还前面挖的坑/给爽点**，再制造新压力——不能拿付费章卡断章拖答案 | "付费被骗感"直接掉订阅 |
| 不水化 | 首付费章不靠回顾/注水充字数 | 同上 |
| 节拍达标 | 稳定日更有效字达平台门槛 ⚠️ | 失全勤/扶持 |
| 全量体检 | §4 跑一遍、0 error | 上架后崩更难救 |

> 阈值（4000 字门槛/各平台具体规则）⚠️ 是经验/内部资料，作可调参数；上架/换书名/是否开付费是 human-only 商业决策。

---

## 8. 合规：平台 AI 检测红线（诚实标注，这是军备竞赛）

**现实**：平台已用 AI 含量检测设红线——某平台 **<20% 不计入、>40% 直接拒稿甚至追回稿费**；番茄曾一次处置 855 个 AI 批量账号 ⚠️（来源 chinanews，各平台不一且在变）。这造成一个**未解的悖论**：

- 本 skill 内置去 AI 味（步骤 8）能压低句子层 AI 味，但**叙事层 AI 味压不到零**（模型天花板）；
- 去 AI 味**是否反而触发/规避检测红线，合规边界未知**——这是 blueprint §10#5 标记的开放风险，不假装有定论；
- 番茄等平台建议"**如实勾选是否使用 AI**"。本 skill 的立场：**诚实勾选**，把去 AI 味定位成"提升质量"而非"骗过检测器"。检测是军备竞赛，今天能过明天未必，押"骗检测"是负 EV。

| 维度 | 诚实结论 |
|---|---|
| 工程能压低的 | 句子层 AI 味（翻译腔/紫色文风/节奏匀速）—— 桶1 lint + 生成期约束 |
| 工程压不到零的 | 叙事层 AI 味（语感/留白/道德模糊"人味"）—— 模型天花板，靠人在大纲层注入 |
| 边界未知的 | 去 AI 味 vs 检测红线是否冲突、各平台阈值具体值 ⚠️ —— 当可调参数、持续跟踪政策 |
| 立场 | 如实勾选；去味为质量不为骗检测；不写死任何平台阈值 |

---

## 9. 维护 checklist（每卷边界一页纸）

```
卷收尾批处理（human-in-loop，跑一遍）：
□ state_check.py 全量 → 0 error（伏笔逾期/阶位/专名/可见性/情绪债）
□ continuity-checker 全卷扫一遍语义级（人物瞬移/认知泄漏/注水）
□ 递归压缩降层：per_chapter→volume_summary 固化；compressed_recent 清空重起
□ previous_tail 只留最新章末段；已 closed 伏笔移出近况层
□ 清脏：Inferred 逐条 → 升 Canon / 降 Rejected（不让推断沉淀）
□ Canon 批量晋升（人确认）+ visible_from_volume 复核（防剧透）
□ sao 排布密度复核：有无连续 N 章平路；情绪债有无 release_intensity<intensity
□ 工作模式 A-E 是否需调（产能/掌控权变化）
□（若有数据）高跳出章定位 → 失败模式反喂 PATTERNS TO AVOID
上架前额外：
□ 首免章完整 + 首付费章先兑现不水化 + 日更节拍达标
□ AI 检测合规：诚实勾选；确认去味为质量非骗检测
```

**一句话总纲**：维护不是"再写一遍"，是在 arc/卷/上架/数据这四类边界把漂移批量收敛——压缩防膨胀、清脏防推断沉淀、`state_check.py` 防机械崩坏、数据闭环定位写崩章、工作模式调介入深度。能机检的全机检，能机检的绝不靠模型自觉；裁决/重写/上架/合规勾选这些不可逆的留给人。

---

## Sources

- `scripts/state_check.py` —— §4 全部机械体检项的权威实现：Canon 五态枚举、`visible_from_volume` 正整数、`power_system.ladder` 阶位、伏笔逾期/临近/无计划/密度（`open ≥ 3×(closed+1)`）、情绪债 `duration_chapters≥5`/`release_intensity<intensity`、glossary 别名冲突。退出码 0/1 语义、`contract.meta.current_chapter` 默认值均以此为准。
- `templates/rolling-summary.yaml` —— §2 分层视图字段：`per_chapter[].one_line/sao/hook`、`compressed_recent`、`previous_tail`、`volume_summary[]`、`mainline_summary`；递归公式 `M_i=LLM(H_i,M_{i-1})` 与"事实进 canon、叙事进摘要 / 先召回再精度"铁律。
- `templates/foreshadow-ledger.yaml` —— 伏笔 `status: open|微回应|closed`、`planted_ch`/`planned_payoff_ch`/`visible_payoff_volume` 字段；健康度自检三项（aging/临近/密度）。
- `templates/emotion-debt.yaml` —— `emotion_debts[].intensity/duration_chapters/release_ch/release_intensity/released`、`sao_schedule[].chapter/type/level/setup_chain`；爽点工业刻度（每3章小爽/每10章中爽/每卷大爽）。
- `templates/contract-template.yaml` —— `meta.current_chapter`、`mainline_anchors` 的来源（卷级/全书摘要对齐对象）。
- `docs/research/03-pipeline-design-blueprint.md` §2.2（canon 治理标签 + 可见性）、§2.4（每 N 章/每卷边界批处理数据流）、§8（MVP vs 完整版：数据闭环属增量）、§10（开放风险 #2 递归摘要信息丢失阈值、#5 AI 检测军备竞赛与合规边界、#6 去味损伤一致性需复检、F1≈0.68/0.51 一致性精度）。
- `docs/research/01-six-stream-findings.md` —— 追读率 35/45%、完读率 15/20%、追更率 40%×5（qidianclub/snowflake，⚠️ 单一来源）、top10% 1.8 章/bottom10% 4.7 章情绪高峰（⚠️ medium）、AI 检测 <20%/>40% 与番茄 855 账号（chinanews，⚠️）、上架=第二次签约/首付费章先兑现、VIP 4000 字门槛、毛志慧"AI 仅修饰层"、工作模式与 automate/semi/human 边界。
- `docs/research/04-github-prior-art-survey.md` §3-§5 —— 分级压缩器（webnovel-writer compactor：超阈值触发→同 key 留最新→删已回收伏笔→远 timeline 合并→active 优先全局截断）、分层视图（oh-story 近5/每10/卷级）、增量滚动摘要（SillyTavern）、autonovel 审校反喂生成、双时态"只失效不删"（graphiti `validUntil`）、伪约束反模式（硬约束必须 code/lint 强制不写进 prompt）。
- ⚠️ 经验值/待核实：所有平台留存阈值与 AI 检测红线（平台算法不公开、各平台不一且在变，一律当可调参数）；连续"N 章无进展"的 N、伏笔密度系数、一致性 F1 等 —— 非写死的确定数据。
