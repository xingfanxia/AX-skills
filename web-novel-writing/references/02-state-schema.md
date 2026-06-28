# 02 — 状态层 schema（7 文档 = 1 顶层契约 + 6 状态文档：字段、填法与治理机制）

> Purpose: 这是**状态层(state layer)**的字段字典与治理规则手册。它回答两个问题：①这 7 个 `templates/*.yaml`（1 顶层契约 `contract.yaml` + 6 状态文档）每个字段填什么、怎么填、最容易填错在哪；②让"几百万字不崩"从"靠勤奋 maintain"变成"靠架构强制"的那套机制——Canon 五态、冲突三选项、按卷可见性、双时态 valid_until、行为锚点+认知边界、增量 append+数值单调代码校验。主要用在**阶段0 初始化状态层（顶层契约 + 6 状态文档）**与**章节循环第 9 步 state-updater 回写**。与 `references/08-foreshadow-timeline.md`（伏笔台账/时间线的工艺细节）、`references/07-sao-engine-emotion.md`（情绪债/爽点排布的写法）互补——那两份讲"内容怎么写好"，本份讲"状态怎么被存、被标、被强制"。Canon 机制复用姊妹 skill `game-script-creation` 的 ref11 §1，并在网文场景补齐可见性 + 双时态 + 认知边界三层。

---

## 0. 一句话原理：存储 ≠ 强制执行

AX 原框架的直觉——"外部文档当单一事实源、必须一直 maintain 这些 state"——方向对，但**"一直 maintain"是个 vibe**。它把一致性当成 **reference problem**（存储 + 注入 + 信任模型用对），从不做 active enforcement。这正是 Sudowrite / NovelCrafter / NovelAI Lorebook 六万字必崩的共同根因：靠人工 diligence，维护负担随章数线性增长，且**未被触发的词条系统无从发现矛盾**（来源：批判备忘录 §一；prior-art §3）。

防漂移的真正机制不是勤奋，是四件事，全部由 schema/代码承载、不写进 prompt 当已执行：

| 机制 | 怎么强制 | 防的崩坏 |
|---|---|---|
| **Canon 五态标签**（每条事实必带） | 状态字段 + 晋升需人确认 | AI 把"未确认推断"当事实写进正文（幻觉式自相矛盾） |
| **按卷可见性** `visible_from_volume` | compiler 过滤：`> 当前卷`一律不进 prompt | 提前剧透幕后黑手/最终反转 |
| **双时态** `valid_until_chapter`（只失效不删） | 生成第 N 章只喂"截至 N 章为真"的事实 | 时效矛盾（拿出两章前已丢的武器/境界倒退） |
| **增量 append + 数值单调代码校验** | state-updater 抽 delta 追加、不整体覆盖；脚本验阶位不倒退 | 长线设定漂移、战力崩坏 |

> **元铁律**：上表任何一条都**不能写成 prompt 里的 prose 让 LLM 自觉**。"prompt 里写『请保持设定一致』"是会随模型漂移的伪约束——AI_NovelGenerator（5456★）就是反面教材：prompt 写"相似度>40%必须重构"却无任何代码测相似度，伏笔 ledger 在 finalize 里从不写入（prior-art §1/§5·A）。本 skill 的硬约束一律落在 schema 字段 + `state_check.py` 上。

---

## 1. 七文档总览（1 顶层契约 + 6 状态文档 · 一条事实只住一个地方）

每条事实强制带两个治理标签：`canon_status`（确认状态）+ `visible_from_volume`（防剧透）。这两个标签**正交**——一条事实可以是 Canon 但 `visible_from_volume: 3`（已定稿但第 3 卷前不许进正文）。

| # | 文件 | 存什么 | 变化速度 | 谁主导 | 绝不混进谁 |
|---|---|---|---|---|---|
| 00 | `contract.yaml` | 顶层契约 + 品类/平台配置 + 防剧透红线 | 不可变 | **human-only** | AI 无权改写 |
| 01 | `state-world.yaml` | 世界事实 / 力量体系 / 势力 / 地点 / 专名表 | 慢变 | semi-auto | 别塞情节流水 |
| 02 | `state-characters.yaml` | 人物卡（行为锚点+认知边界）+ current_state | 慢变+快变混 | semi-auto | 别塞剧情 beats |
| 03 | `state-plotline.yaml` | 主线 beats / 支线 / 推进指针 | 人主导 | **human 拍板** | 伏笔/情绪债不放这 |
| 04 | `foreshadow-ledger.yaml` | 伏笔台账（独立状态机） | 流转 | automate | 别塞进剧情线散文 |
| 05 | `emotion-debt.yaml` | 情绪债账本 + 爽点排布表 | 流转 | semi-auto | 别塞伏笔 |
| 06 | `rolling-summary.yaml` | 分层递归摘要 + 上一章末段原文 | 每章滚动 | automate | 只存可压缩的流水 |

**职责不重叠是硬规定**：伏笔进 04 不进 03，因为"埋了忘回收=烂尾"是一票否决毒点、需要独立状态机自动追踪；情绪债进 05 不进 03，因为爽点密度要可机检。把它们塞回剧情线散文 = 退回 AX 那个"无从发现矛盾"的扁平 memory.md。

---

## 2. Canon 五态机制（每条事实的治理底座）

复用 `game-script-creation` ref11 §1 的四态，网文补一态 `Inferred`（AI 推断未经人确认）——因为 AI 抽 delta 回写时会产生大量"看起来对但没人拍板"的推断事实，必须和人确认过的 Canon 区分开。

| 状态 | 含义 | writer 能不能消费 | AI 的行为 |
|---|---|---|---|
| **Canon** | 创作者已确认，后续必须遵守 | ✅ 可进 prompt | 视为不可违背；新内容冲突时**必须报警** |
| **Pending** | 正在探索、尚未拍板 | ⚠️ 标注"未定"可进 | 可继续构思，但不当铁律 |
| **Rejected** | 创作者明确不要的方向 | ❌ 不进 | **不反复提**，除非人主动重启 |
| **Idea** | 暂不进主线的备选灵感 | ❌ 不进 | 不主动塞进当前剧情，合适时提醒"存过一个…" |
| **Inferred** | AI 从正文抽取、未经人确认的推断 | ⚠️ 可参考、不当定论 | 攒着等人确认晋升 Canon；冲突时优先怀疑它 |

**晋升铁律**：任何事实升 `Canon` **需人确认**（human-only）。state-updater 抽出的 delta 默认落 `Inferred` 或 `Pending`，绝不自动晋升——这是"Canon 冲突裁决=human-only"的工程落地。

### 冲突处理铁律：显式上报 + 三选项（绝不默默处理）

当新事实与某条 **Canon** 冲突，AI **不能默默采纳新的、也不能默默丢弃它**——默默处理是长线漂移头号成因。必须**显式指出冲突**并给三选项让人拍板：

1. **改新想法** —— 让它兼容已定 Canon；
2. **把旧 Canon 降级回 Pending 再调整** —— 并**提示这会波及哪些已写章节**（哪些章引用过这条）；
3. **把冲突变成剧情冲突** —— 很多"设定打架"是好故事的种子（"两份记录互相矛盾"本身可作悬念/伏笔）。

> 实现参考：graphiti / mem0 的做法是 **LLM 只输出"哪两条 idx 冲突"，真正的失效/裁决由确定性代码做**（prior-art §3·5）。本 skill 同构：`state_check.py` 扫出候选冲突 → 列给人 → 人选 1/2/3 → 代码执行，LLM 不持决策权。

---

## 3. 按卷可见性 `visible_from_volume`（防剧透红线）

**原理**：悬疑的幕后黑手、马甲文的真实身份、重生流"主角已知的未来"——这些事实**存在于状态里**（人类要掌控），但**绝不能在揭晓卷之前进 writer 的 prompt**，否则 AI 会提前把伏笔写漏。可见性标签把"剧透红线"从"靠 writer 自觉别写"变成"compiler 物理过滤"。

| 用法 | 规则 |
|---|---|
| 字段位置 | `world_facts` / `factions` / `locations` / `characters` 每条都带 `visible_from_volume: N` |
| compiler 过滤 | 只抽取 `visible_from_volume <= meta.current_volume` 的事实进 prompt |
| 最高级红线 | `contract.locked_reveals`（最终反转/幕后黑手）**只存契约供人掌控，永不进 writer prompt**——揭晓那一章由人类手动解锁 |
| 与认知边界配合 | 可见性管"这条事实能不能进 prompt"；`cognition`（§5）管"在场角色知不知道"——两层都要过 |

易错：把 `visible_from_volume` 和 `canon_status` 当成一个东西。一条 **Canon**（已定稿）事实完全可以 `visible_from_volume: 5`——"我已经定死了第 5 卷揭晓他是反派"，定稿≠现在能写。

---

## 4. 双时态 `valid_until_chapter`（只失效不删，借鉴 graphiti/inkos）

**原理**：有些事实会随剧情**变假**——"主角的剑在第 12 章被夺走"。如果直接删掉"主角有剑"这条，就丢了历史（第 1–11 章他确实有剑）；如果留着不动，writer 在第 20 章可能让他凭空又拔剑。双时态的解法：**变更只失效、不删除**，每条会变假的事实带生效区间，生成第 N 章时只喂"截至第 N 章仍为真"的事实（来源：prior-art §3·2，graphiti `validFrom/validUntil`、inkos `validUntilChapter`）。

```yaml
- id: W042
  fact: "主角持有玄铁剑"
  canon_status: Canon
  valid_from_chapter: 1
  valid_until_chapter: 12    # 第12章被夺走；之后这条不得当真喂给 writer
```

| 字段 | 含义 | 默认 |
|---|---|---|
| `valid_from_chapter` | 这条事实从第几章起成立 | 1 |
| `valid_until_chapter` | 到第几章失效（被推翻/过时） | `null` = 至今有效 |

机制要点：
- **失效不等于矛盾**——"剑被夺"是合法剧情，不是 bug。双时态让 continuity-checker 能精确区分"合法的状态变更"和"非法的凭空复活"（inkos 用它抓"角色拿出两章前已丢失的武器""记起从未见过的事"）。
- 只对**会变假的事实**用双时态（持有物/位置/同盟关系/伤势）；永真的世界规则（"此界灵气稀薄"）不需要。
- `current_state`（§5）是双时态的快变版本——它只存"当下值"，历史值靠双时态事实 + `rolling-summary` 兜底，不要求每个快变字段都建生效区间（那是 overengineering，MVP 不做）。

---

## 5. 人物卡（02）：行为锚点 + 认知边界

人物卡是七个文档里字段最密、最容易写崩的一份。两条铁律：

### 铁律 A — 写行为锚点，不写形容词

"很勇敢""腹黑"这类形容词**模型无锚点必漂移**（这次写成莽，下次写成怂）。`behavior_anchors` 写**具体事件**，可检索、可自检、可演：

- ❌ `personality: 重情重义、隐忍`
- ✅ `behavior_anchors: ["七岁目睹父亲守诺被斩首，二十年未对任何人立誓"]`

辅助字段分工：`flaw_personality` 写性格瑕疵（惜命/毒舌/贪财——增记忆点）；`voice_notes` 写可演出的"声音"（口头禅/语速/第一人称/怎么称呼别人）；`wound_lie_want_need`（伤口→谎言→渴望→需要）非爽文重弧线时才填，爽文可弱化为"强且有趣"。

> ⚠️ 爽文主角设计红线：性格瑕疵（惜命/毒舌）是记忆点，但**能力/智商缺陷（降智）、道德圣母 = 毒点不是弧线**（详见 `references/09-anti-ai-slop.md`）。`flaw_personality` 只装前者。

### 铁律 B — 必填认知边界 `cognition`（四字段）

这是多数项目漏掉、网文却刚需的一层——唯一做对的开源项目是 ExplosiveCoderflome（`knownFacts` + `misbeliefs`，prior-art §3·2）。它支撑**信息差与戏剧反讽**的一致性，是悬疑/马甲/重生/扮猪吃虎的命门。

| 字段 | 存什么 | writer 据此做什么 |
|---|---|---|
| `knows` | 角色【已知】的关键信息 | 可以让他基于此行动/说话 |
| `does_not_know` | 角色【不知道】的关键信息 | **不得让他表现得知道**（防"说出不该知道的事"） |
| `misbeliefs` | 角色【错误地相信】什么 | 写他基于错误认知的反应（别人误判主角废柴=他们的 misbelief → 据此写他们看走眼，为打脸蓄势） |
| `reader_knows_char_doesnt` | 读者已知但**角色不知** | 戏剧反讽来源（读者替角色捏把汗） |

`misbeliefs` 是扮猪吃虎/打脸引擎的状态底座：反派的"以为主角好欺负"不是临时写的，是台账里登记的状态，打脸时才有据可依、前后一致。

### current_state（快变层，state-updater 每章回写）

`current_state` 是人物卡里唯一**每章可能变**的块：`location` / `level`（对照 `world.power_system.ladder`，脚本校验不倒退）/ `injury` / `emotion` / `goal_now` / `resources`（钱/法宝/技能/债务/冷却——资源账本，防"凭空出现"）/ `relations[{with, stage}]`。慢变块（行为锚点/伤口/弧线）一旦 Canon 几乎不动；快变块每章走 delta 回写。

---

## 6. 其余各文档字段速查

### 00 contract.yaml（顶层契约 · human-only · AI 无权改写）

三大块：`meta`（含 `current_volume`/`current_chapter`——驱动可见性与双时态的"当前时点"）、`config`（品类→平台配置，把 `references/05`+`06` 的参数固化进来供机检：`opening_rules.conflict_before_chars`、`chapter_length{target,min,max}`）、`contract`（人类拍板的不可变锚点）。契约块关键字段：

| 字段 | 填什么 | 易错 |
|---|---|---|
| `core_conflict` | 整本书在对抗什么（一句话） | 方法：**先有结局/核心冲突，再倒推大事件串**，别先有酷设定硬凑 |
| `protagonist_want` / `need` | 外部渴望（驱动行动）/ 内部需要（成长弧） | 爽文可弱化 need，但别没有 |
| `goldfinger` | 金手指是什么 + **代价/规则** | **无代价升级 = 毒点**，代价必填 |
| `power_floor_ceiling` | `floor`/`ceiling`/`progression_rule` | 开局锁死天花板防战力崩坏 |
| `sao_engine` | 品类爽点引擎单句锚（注入每章 prompt） | 如"凡人苟道步步谋算后碾压打脸" |
| `forbidden` | 全书禁区 | 这是 reviewer 硬门的来源 |
| `locked_reveals` | 最终揭晓的反转 + `reveal_at_volume` | **只存契约、不进 writer prompt**（见 §3） |

### 03 state-plotline.yaml（剧情线 · human 拍板）

`mainline_beats[{volume, arc, ch_range, beat, sao_target, volume_double_ending{resolve, open}, canon_status}]`——`volume_double_ending` 是卷尾双重收尾（`resolve` 给闭合感 + `open` 给追更动力），是连载防"卷末空洞"的硬字段。`sidelines` 每条必填 `serves_mainline`（这条支线如何服务主线，否则=注水）。`cursor{current_arc, last_chapter_done, next_beat}` 是 driver 判断"该写到哪"的推进指针，由 state-updater 维护。

### 04 foreshadow-ledger.yaml（伏笔台账 · 独立状态机）

`foreshadows[{id, type, text, planted_ch, planned_payoff_ch, status, visible_payoff_volume, note}]`。`type` ∈ 身份/语言/场景/数字/主题/物件；`status` 状态机 = `open`（已埋）→ `微回应`（中途呼应过）→ `closed`（已回收）。`planned_payoff_ch` **必填**——没有计划回收章=别埋。机检三告警（`state_check.py` 每卷边界跑）：逾期未回收（当前章 > `planned_payoff_ch` 仍 `open`）、临近提醒、**密度告警**（`open` 数 >> `closed` 数且持续上升 = 崩铁翁法罗斯式"伏笔密度超过闭合速度"翻车）。工艺细节见 `references/08`。

### 05 emotion-debt.yaml（情绪债 + 爽点排布 · AX 原框架缺失，必补）

`emotion_debts[{debt_id, text, intensity, incurred_ch, duration_chapters, release_ch, release_intensity, released}]`——核心约束 **`release_intensity >= intensity`**（释放强度必须 ≥ 已积累的憋屈债务，否则不解气，可机检）。`sao_schedule[{chapter, type, level, setup_chain}]`——工业刻度：每章≥1小爽 / 每3-5章1中爽 / 每卷1大爽；`setup_chain` 写"需求建立→压抑→释放"链条，验"爽点不是免费的"。机检：连续 N 章无 `sao_schedule` 条目=平路过长预警。写法见 `references/07`。

### 06 rolling-summary.yaml（分层递归摘要）

`per_chapter[{ch, one_line, sao, hook}]`（章级一句话，几乎不压缩）+ `compressed_recent`（最近 3–5 章压缩，滚动重写）+ **`previous_tail`（上一章末段原文）**——这是 writer 续写的**主要短期记忆源**，防断点跳脱 + `volume_summary` + `mainline_summary`（极简常驻，对齐契约 `mainline_anchors`）。递归式 `M_i = LLM(H_i, M_{i-1})`。分层铁律：**关键设定/数值/伏笔进永不压缩的结构化 canon（01–05）；情节流水才进可压缩摘要（本文件）**。

---

## 7. 防漂移机制：草稿只读、定稿才回写、增量 append、数值代码校验

state-updater（第 9 步）的纪律，全部对齐 prior-art §4 的"已被反复验证的循环纪律"：

| 纪律 | 规则 | 来源 |
|---|---|---|
| **草稿纯函数读** | draft 阶段**只读 state，绝不 mutate**；草稿可反复重生成而不污染长程状态 | AI_NovelGenerator（prior-art §4·2） |
| **定稿才回写** | 只有人批准定稿，才把 delta 写回 state | webnovel-writer 单一写入权 |
| **增量 append 不整体覆盖** | LLM 抽 delta（低温一次调用）→ **代码 append**，不让 LLM 重写整个文件 | 批判备忘录 §一 |
| **Canon 晋升需人确认** | delta 默认落 `Inferred`/`Pending`，不自动升 Canon | 本 skill 铁律 |
| **数值单调由代码校验** | `power_system.monotonic: true` → `state_check.py` 验 `current_state.level` 在 `ladder` 上不倒退 | ExplosiveCoderflome 确定性连续性守卫（prior-art §3·5） |

**为什么"代码 append"而非"LLM 重写整个 state 文件"**：让 LLM 整体重写 YAML，它会顺手"优化"措辞、丢字段、改 id——这正是漂移。LLM 的职责收窄到"从本章正文抽出哪些字段变了"（结构化 delta），落盘动作交给确定性脚本，是"LLM 当子程序、代码立刻夺回方向盘"在状态层的落地。

---

## 8. 可复用要点（速记）

- **存储 ≠ 强制执行**：AX 的"一直 maintain"是 vibe；防漂移靠 Canon 五态 + 可见性 + 双时态 + 代码校验四件套，不靠勤奋。
- **每条事实两个正交标签**：`canon_status`（确认到哪一态）+ `visible_from_volume`（哪一卷起可进 prompt）。少任何一个都退回扁平 memory.md。
- **冲突一律显式上报 + 三选项**（改新/降级旧/变剧情），默默处理是长线漂移头号成因；LLM 只标冲突 idx，裁决归人、执行归代码。
- **双时态只失效不删**：会变假的事实带 `valid_until_chapter`，生成第 N 章只喂截至 N 章为真的事实——天然防剧透 + 防伏笔提前泄底 + 防前后打架。
- **人物写行为锚点不写形容词**；`cognition` 四字段（knows/does_not_know/misbeliefs/reader_knows_char_doesnt）是信息差与扮猪吃虎的状态底座，必填。
- **职责不重叠**：伏笔→04、情绪债→05、关键 canon→01-05、情节流水→06；草稿只读、定稿才回写、增量 append、数值代码校验。
- **任何 MUST-hold 不变量都落 schema 字段 + 脚本，绝不写进 prompt 当已执行**——这是和 AI_NovelGenerator 式伪约束的根本分界。

---

## 9. 人物设计工艺：怎么"设计"人物卡（区别于 §5 怎么"存"）（借鉴 oh-story-claudecode）

§5 给的是**字段字典**（`behavior_anchors`/`cognition`/`flaw_personality`/`current_state` 里**存什么**）。本节给的是填这些字段**之前**的设计方法——怎么想出该填进去的具体内容。**铁规：本节不新增任何 schema，全部挂在 §5/§6 已有的 typed 字段上当"填法指导/裁决细化"**，避免回到"另起一套人设框架"的 overengineering。一句话分工：§5 = 仓库格式；§9 = 往格子里装什么、怎么装才立体。

挂载关系一览（每个方法落到哪个已有契约）：

| 设计方法 | 挂在哪个已有字段/契约 | 作用 |
|---|---|---|
| 三层标签反差法 | `behavior_anchors`（§5 铁律A） | 产出"可演的反差事件"的脚手架 |
| 配角功能化 / 白手套 | 配角卡的 `behavior_anchors` + `voice_notes` | 让配角卡编码"对主角的功能"而非泛泛性格 |
| 立体 vs 扁平决策 | 是否填满 `cognition` / `wound_lie_want_need` | 决定一个角色值不值得花字段成本立体化 |
| 金手指绑架人设 | `contract.goldfinger`（代价/规则） | 用规则绑架行为塑造品格，不靠旁白夸 |
| 可原谅 vs 不可原谅的错误 | `flaw_personality` 红线 + `contract.forbidden` + reviewer 硬门 | 把"降智红线"细化成可裁决表 |
| 安全感 / 核心情绪 | `contract` 题材核心情绪 + reviewer 标记 + 05 情绪债 | "靠山过度"可标记反模式 |
| 角色行为自洽检查（四步） | reviewer rubric 的人设维度闸 | 防"剧情硬推角色"、防人设偏移 |

### 9.1 三层标签反差法 = `behavior_anchors` 的设计脚手架

三层标签**不是新字段**，是"先想清楚、再落成 behavior_anchors"的工作步骤：

| 层 | 含义 | 例（豪门弃妇） |
|---|---|---|
| 身份标签 | 外界看到的身份 | 豪门弃妇 |
| 表现标签 | 角色展示给外界的行为 | 隐忍不发、逆来顺受 |
| 内核标签 | 角色真正的内心 | 冷静、有计划、步步为营 |

执行：身份与表现可相似（强化刻板印象），**内核必须反转表现**——反差 = 立体。每个重要角色至少一层反差；反差越大，"亮牌时刻"越震撼。关键是**别把三层写成形容词存进卡里**，要把"内核 vs 表现的反差"具象成一两条可演事件落进 `behavior_anchors`：

- ❌ `behavior_anchors: ["腹黑"]`（又退回 §5 铁律A 禁止的形容词）
- ✅ 三层（豪门弃妇 / 逆来顺受 / 步步为营）→ `behavior_anchors: ["被当众赶出家门不还一句口，回房悄悄录音、收集证据、提前转移财产"]`

即：三层标签是脑内推导工具，`behavior_anchors` 是它唯一的落盘出口。**进阶反差**：关系进入亲密层后，早期（身份/表现层）能做的行为反而做不出来了（爱调戏的辣妹进入亲密关系后反而不敢表白）——"行为退化 = 感情深化"，这种阶段性反差也写进 `behavior_anchors`，别让角色在亲密期仍维持早期行为（否则反差失效）。

### 9.2 配角功能化 + 白手套角色 → 配角卡先定功能再填字段

主角卡从"内核"出发，**配角卡从"对主角的功能"出发**：先确定功能（替主角说话 / 替主角发狠 / 提供信息 / 适时搞笑），再贴 1-2 个反差标签，最后把功能**直接编码进配角的 `behavior_anchors`**（而非写泛泛性格）。复合型"白手套"角色：

| 白手套功能 | 说明 |
|---|---|
| 替主角说话 | 主角不便说的话，他来说 |
| 替主角发狠 | 主角不该发的狠，他来发 |
| 绝对维护 | 对侵犯主角利益者坚决反击 |
| 适时搞笑 | 持续输出正反馈，缓解紧张 |

设计原则：光环比主角弱一线、不抢风头；惊艳出场；对主角的质疑第一时间反驳。**反模式**：配角像 NPC 站桩等主角触发——配角要有自己的动机和行动（在 `current_state.goal_now` 上给它一个独立目标）。

### 9.3 立体 vs 扁平：不是所有角色都要立体（字段成本投放决策）

立体化是有**字段成本**的（填满 `cognition` 四态 + `wound_lie_want_need` 弧线）。先看功能再决定投不投：

- **"洗白弱三分，黑化强三倍"**——高手 / 终极反派一旦被立体化、被解释，就**变弱**了；扁平 + 神秘 = 更强 / 更恐怖。
- 功能性配角（信息源 / 工具人）保持扁平：只填 1 条 `behavior_anchors` + `voice_notes`（脸谱化标签：口头禅 / 标志动作），**不填** `wound_lie_want_need` 弧线、`cognition` 也可极简。
- 需要什么工具就设计什么工具，不要把所有角色都立体化——把字段预算花在"立起来能撑戏"的关键角色上。

### 9.4 金手指绑架人设法 → 对齐 `contract.goldfinger` 的"代价/规则"

§6 的 `contract.goldfinger` 已强制填"代价/规则"（防无代价升级毒点）。本法是它的**人设延伸**：金手指的规则不只约束战力，还能**绑架主角的行为**——用规则逼出行为，让品格从行为里自然涌现，而不是旁白直接夸"主角善良/果断"。

- 机制：金手指规则约束行为 → 配角对这些行为的反应自然塑造主角形象 → 不需要直接描写品格。
- 追求**道德爽感**（最高级爽感）：让主角在行为层面成为读者心服口服的"活圣人"，靠的是金手指规则下的行为一致性，不是说教。
- 这与 §5 铁律A（写行为锚点不写形容词）同源——金手指规则是产出"品格类 behavior_anchors"的引擎。

### 9.5 主角"可原谅 vs 不可原谅"的错误（§5 降智红线的**裁决细化**）

§5 已立红线：`flaw_personality` 只装性格瑕疵（惜命/毒舌/贪财），**降智 / 圣母 = 毒点不是弧线**。但"哪些错能写、哪些不能写"过于笼统，本表把它操作化成 reviewer 可逐条裁决的标准——**比单纯一句"降智红线"更细**：

| 可原谅（能写，是弧线/张力） | 不可原谅（毒点，reviewer 硬门拦截） |
|---|---|
| **信息差**导致的错（他确实不知情） | **蠢**导致的错（智商与设定不匹配） |
| **不可抗力**导致的错（客观无法避免） | **圣母心泛滥**导致的错（该狠不狠、对仇敌妇人之仁） |
| — | **与实力严重不匹配**的错（斗帝级强者被小人物耍得团团转） |

裁决归属：这张表是 §5 红线的落地，落在 `contract.forbidden` + **reviewer 硬门**。一段"主角犯错"的情节，reviewer 据此判它是**合法成长弧线**（信息差/不可抗力→可写，甚至是好戏）还是**毒点**（蠢/圣母/降智→打回）。注意区分：可原谅的错可以、也应该制造张力；不可原谅的错会直接掉读者。

### 9.6 安全感与核心情绪：紧张题材的"靠山过度"反模式（可标记）

不同题材读者对**安全感**的需求不同，先确认题材的**核心情绪**。极道流 / 谍战 / 求生等**紧张感题材**：给主角找一个**可随时解危的强力靠山** = 危机感消失 = 核心情绪偏移。

- **可标记反模式**：建议 `contract` 记一个 `core_emotion`（题材核心情绪，如"紧张/危机感"），reviewer 规则——若主角拥有"能随时抹平危机的强力靠山" **且** 题材属紧张类 → 标 `靠山过度` 告警（对齐 §5.5 关于性格瑕疵的标记思路，是裁决标签不是新框架）。
- 与 **05 情绪债** 联动：靠山过度会让情绪债**攒不起来**——危机一冒头就被靠山瞬间抹平，憋屈债没积累就被"还"掉了，`release_intensity >= intensity` 的爽点引擎随之失效。所以"别给主角太强靠山"本质是在保护情绪债账本能正常运转。
- 通则：精力有限时**情节永远第一位，世界观只是加分项**——别为铺世界观牺牲核心情绪。

### 9.7 角色行为自洽检查（四步）→ reviewer 的人设一致性闸

这是 reviewer 一致性校验在**人设维度**的细化清单，输入就是 §5 的 `behavior_anchors` + `cognition` + `current_state.goal_now`，**挂在章节循环审校步，不新增流程**：

1. **排除外部强推**——检查角色行为是不是"恰好"在推进剧情却没有自身动机。若是 → 标 `人设偏移`，必须为该行为补一个角色层面的合理动机。（这一步正是防 AI 把"剧情需要/约束"硬塞进角色嘴里——与本 skill"指令与正文严格分离"同源。）
2. **情绪目标确认**——写每段前明确三问：本段要让读者产生什么情绪？角色的 `behavior_anchors`/`flaw_personality` 是否自然导向该情绪？该行为是否符合角色的功能定位（§9.2）？
3. **人设行为推导**——从 `behavior_anchors` + `cognition`（尤其 `does_not_know`：不得让他表现得知道不该知道的事）+ `current_state` 推导：列该角色在此场景下 2-3 种可能反应 → 评估各自与既有行为模式的一致性 → 选**最符人设且最具戏剧张力**的那一种。
4. **情绪一致性校验**——角色表达的情绪核心与场景目标情绪是否一致；不一致则调角色行为或调场景目标情绪，二选一直到自洽。

两条等价路径：A 先定目标情绪→按人设推导行为→校验；B 先按人设推导行为→反推场景目标情绪→校验。任一路径跑通即放行。

> 来源：oh-story-claudecode `skills/story-setup/.../character-design-methods.md`（三层标签反差、配角功能化/白手套、立体vs扁平、金手指绑架人设、可原谅vs不可原谅错误、安全感与核心情绪）与 `character-relations.md`（角色行为自洽四步检查）。已全部改写为"挂在本 skill 既有 typed 字段（behavior_anchors / cognition / flaw_personality / contract.goldfinger / forbidden / reviewer 硬门）上的填法指导与裁决细化"，未引入平行人设框架，未引入任何架构/脚本/抓站。

---

## Sources

> 本文所有论断取材自本仓库已落盘的调研文件与姊妹 skill，未额外联网检索。具体平台阈值（如 `conflict_before_chars`）为经验/内部资料推断，已在契约模板标 ⚠️，作可调参数。

- **批判备忘录**：`docs/research/02-critique-ax-framework.md` §一（State 模型："存储≠强制执行"、Canon 标签、可见性、双时态、行为锚点+认知边界、增量 append、数值单调、冲突三选项）。
- **设计蓝图**：`docs/research/03-pipeline-design-blueprint.md` §2.2（顶层契约 + 6 状态文档 + Canon 元数据字段 schema）、§7（craft/state 分离）。
- **prior-art 调研**：`docs/research/04-github-prior-art-survey.md` §3（状态/记忆/一致性最佳实践：graphiti/inkos 双时态、ExplosiveCoderflome misbeliefs、伏笔生命周期、确定性连续性守卫、LLM 只出 idx 代码做裁决）、§4（草稿只读/定稿回写/热冷双通道）、§5·A（伪约束反模式：AI_NovelGenerator 文档代码漂移）。
- **Canon 机制母本**：`game-script-creation/references/11-production-liveops.md` §1（Canon 四态 + Project State + 冲突三选项），本 skill 补 `Inferred` 第五态与网文可见性/双时态/认知边界三层。
- **字段对齐基准**：本仓库 `templates/{contract,state-world,state-characters,state-plotline,foreshadow-ledger,emotion-debt,rolling-summary}.yaml`（本文字段名与之逐一对齐，改 schema 时两边同步）。
