# 13 — 导入已有稿（崩稿接手）→ 反向抽取为 typed 状态层

> Purpose: 这是**接手已有稿**的标准入口，专治头号真实痛点——"我已经写了几章（自己写的 / AI 续写的），但 4-5 章后逻辑/人设/世界观开始崩，现在想用这条流水线接着写"。它回答：①怎么**定位崩在第几章**（用现成的 `degeneration_check.py` 逐章扫退化指纹 + 派独立 continuity-checker 抓语义崩）；②怎么把已有正文**反向抽取**成本 skill 的 7 个 typed 状态文档（而不是从零重开）；③反推出来的事实怎么对齐 Canon 五态（**默认全是 `Inferred`，绝不自动当 Canon**）；④拿不准的字段怎么用 `[待补充]` 纪律标注、绝不编造；⑤按什么**生成顺序**落盘（有依赖，乱序会崩）。主要用在 **SKILL.md 阶段 0.5（导入已有稿）**——接在阶段 0（从零开书）之后、章节生产循环（§3）之前。借鉴 oh-story-claudecode/story-import 的反向骨架方法与角色状态反推 6 步算法，但**迁移终点换成本 skill 的 `templates/*.yaml`**，并**不引入**它的拆文库/对标双目录树/多对标 registry。

---

## 0. 一句话原理：从已有素材开始，但反推 ≠ 定稿

阶段 0（从零开书）和阶段 0.5（导入已有稿）是**两个不同入口**，别混：

| | 阶段 0（greenfield 从零开书） | 阶段 0.5（brownfield 接手崩稿） |
|---|---|---|
| 起点 | 一个脑洞 / 一句核心冲突 | 已有几章~几百章正文（半成品或完本） |
| 顶层契约 | 人类**先验**拍板锁定 | 从已有正文**反推草案** → 人类**追认/修正** |
| 状态层 | 空模板逐字段填 | 从正文**反向抽取**预填 |
| 头号风险 | 设定先于结局硬凑 | **把"AI 从正文抽出来的推断"当成已定稿事实** |

**核心信念**：好工具从已有素材开始，不从零起步——但**反推出来的任何东西都是"看起来对、没人拍过板"的推断，一律落 `canon_status: Inferred`**（见 `references/02-state-schema.md` §2 Canon 五态的第五态，正是为"AI 抽 delta 回写产生的未确认推断"而设）。晋升 Canon 仍需人确认。这条铁律把"导入"和"伪造一份假装权威的 story bible"区分开。

> **为什么不能自动当 Canon**：导入时 AI 一次性抽出几百条事实，其中必有它"脑补"的（原文没明说、它顺手补的关系/动机）。若直接当 Canon，后续 writer 会基于这些幻觉事实续写，崩坏从导入第一刻就埋下。Inferred 是隔离层：可参考、不当定论、冲突时优先怀疑它。

---

## 1. 三步总览（定位 → 抽取 → 迁移 → 接手）

```
Phase A 确认源 + 定位崩点          Phase B 反向抽取骨架(按生成顺序)        续写接手
──────────────────────         ──────────────────────────         ──────────────
贴正文/给路径 → 切章           → ① contract.yaml(契约草案·待人追认)    → 崩点章之后
逐章跑 degeneration_check        ② state-world.yaml(glossary先钉死)       rejoin §3
  → 机械退化指纹(复读/截断/      ③ foreshadow-ledger.yaml(必先于人物卡)    章节生产循环
    工程词) 定位崩点章           ④ state-plotline.yaml(主线beats+cursor)  (compile→writer
派 continuity-checker 子agent    ⑤ state-characters.yaml(反推6步算法)      →独立校验→…)
  → 语义崩(逻辑/人设/世界观)     ⑥ rolling-summary.yaml(逐章一句+末段原文) 崩点章本身=待重写
切出【可信前缀/崩点章/弃用尾】   ⑦ emotion-debt.yaml(情绪债·可选低置信)    走重生成不走信任
```

三句话：**先用 `degeneration_check.py` 逐章定位崩在第几章**（机械退化）+ **独立 continuity-checker 抓语义崩**（逻辑/人设）；**再把可信前缀反向抽取成 7 个状态文档**（按依赖顺序，全打 `Inferred`）；**最后从崩点之后接进 §3 正常循环续写**，崩点章本身当"待重写"而非"可信史料"。

---

## 2. Phase A — 确认源 + 定位崩点（这一步是接手崩稿的命门）

### 2.1 确认导入源（轻量，别学 oh-story 起一整套环境检测）

问创作者三件事，复述检测结果让其确认：① 书名/暂定名；② 品类+子类+目标平台（决定后面挂哪套约束，见 `references/05`+`06`）；③ **是否完本 / 写到第几章 + 最后一章是否残稿**（残稿=写了一半被截断）。

切章：单文件按 `第X章` / `Chapter X` / `数字.标题` 分隔符切；目录按文件名排序。**保留原文不改一字**——导入只读不重写（重写是续写阶段的事）。

### 2.2 定位崩点：两路并行（机械 + 语义）

"崩在第几章"必须**先定位、再决定哪些章可信**。两类崩，两套探针，互补：

| 崩的类型 | 探针 | 抓什么 | 工具 |
|---|---|---|---|
| **模型退化崩**（桶 0） | 机械、零 LLM、逐章跑 | 复读/打转、句子截断、占位符/拒绝语、工程词泄漏（"细纲/爽点/金手指"漏进正文） | **`scripts/degeneration_check.py`** |
| **语义崩**（逻辑/人设/世界观漂移） | 派独立子 agent | 战力倒退、人设前后矛盾、伏笔自相打架、说出不该知道的事 | **continuity-checker 子 agent**（§3 独立校验） |

**机械路（主定位器）**——逐章扫，blocking 指纹爬升处≈崩点：

```bash
for f in 正文/第*.txt; do
  echo "=== $f ==="
  python3 scripts/degeneration_check.py "$f" --json --fail-on=blocking
done
```

`degeneration_check.py` 抓的正是"**退化的模型自己报不出来**"的指纹（复读 ≥3 次 / 末尾无收尾标点 / `作为AI` / `未完待续` / `爽点`「`卷纲`」泄漏到叙述行）。它不需要世界观 context、不调 LLM，是确定性崩点定位器。**第一个连续出 blocking 的章 = 机械崩点**。

> ⚠️ degeneration_check **只抓退化指纹，抓不到"语义崩"**——一段逻辑崩坏但语句通顺、不复读不截断的正文，它判不出来。所以**必须并行派 continuity-checker 子 agent**（只喂【该章正文 + 反推出的 canon 切片 + 时间线】，judge"对不对"，返违规清单），用它定位"语句没坏但故事崩了"的那一章。两个崩点取**更早**的那个。

### 2.3 切出三段：可信前缀 / 崩点章 / 弃用尾部

定位后把已有稿切三段，决定每段怎么进状态层：

| 段 | 定义 | 进状态层的方式 |
|---|---|---|
| **可信前缀** | 崩点之前、两路探针都干净的章 | 反向抽取为状态层事实（`Inferred`），作续写的史料 |
| **崩点章** | 第一个崩的章 | **不当可信史料**；反推只取崩点前半段的事实；这一章标记为"待重写"，续写时第一件事就是重生成它 |
| **弃用尾部** | 崩点之后已经跑飞的章 | 默认**丢弃**（已是漂移产物，留着会污染 canon）；若创作者坚持保留，逐章过 continuity-checker 人审后才采信 |

**残稿处理**（最后一章写了一半）：角色状态/世界事实一律以"残稿之前最后一个完整章节"为基准，残稿内容不计入；在 `rolling-summary.yaml` 注明"残稿到第 N 章"。是否"基于残章续写 / 先补完再续"由创作者拍板，导入只记录决定、不替选。

---

## 3. Phase B — 反向抽取骨架（生成顺序有依赖，不可乱序）

迁移终点是本 skill 的 `templates/*.yaml` + 章纲 JSON，**不是** oh-story 的 `设定/大纲/正文/追踪/对标` 目录树。一条事实只住一个地方（对齐 `references/02` §1 七文档职责不重叠）。

### 3.1 生成顺序（后一个依赖前一个的产出，照此序生成）

```
① contract.yaml         ← 先反推契约草案（core_conflict/ending/goldfinger），但标 Pending 待人追认
② state-world.yaml      ← glossary 最先钉死专名（防后续抽取同名漂移）+ power_system 阶位表
③ foreshadow-ledger.yaml← 必须先于人物卡（人物卡 cognition 的"待回收伏笔"依赖它，沿用 oh-story 顺序铁律）
④ state-plotline.yaml   ← 主线 beats + cursor（cursor.last_chapter_done = 崩点-1，driver 据此知道从哪续）
⑤ state-characters.yaml ← 角色状态反推 6 步算法（见 §4），依赖 ③伏笔 + ④剧情线
⑥ rolling-summary.yaml  ← 逐章一句话 + 【上一章末段原文 previous_tail】（续写的主要短期记忆源，最关键）
⑦ emotion-debt.yaml     ← 情绪债/爽点排布反推（可选，低置信，原文常无明确证据，多数字段 [待补充]）
```

> **为什么 ③伏笔 必须先于 ⑤人物卡**：人物卡的 `cognition`（认知边界）和"该角色身上还没回收的伏笔"都要查伏笔台账。伏笔没建好，人物卡的这两块就只能填空或编造。这是 oh-story-import 的硬顺序约束（`伏笔 → 角色状态 → 上下文`），本 skill 同构沿用。

### 3.2 各文档反推映射表（已有正文证据 → 落到哪个字段 → 默认 canon_status）

| 反推目标（template） | 从正文哪里抽 | 落到字段 | 默认状态 |
|---|---|---|---|
| **contract.yaml** | 通读可信前缀 + 创作者口述意图 | `core_conflict` / `ending_anchor` / `goldfinger`+代价 / `mainline_anchors` / `power_floor_ceiling` | **Pending**（契约是人类主权，反推只出草案，**必须人追认才升 Canon**） |
| **state-world.yaml · glossary** | 专名首次出现（功法/法宝/地名/称谓） | `term` / `canon_name`（钉唯一写法）/ `aliases` | Inferred |
| **state-world.yaml · power_system** | 境界/等级词的出现顺序 | `ladder`（从低到高）/ `cost_rule` / `monotonic` | Inferred |
| **state-world.yaml · world_facts** | 叙述里的世界规则/势力/地理 | `fact` + `affects`（必填：它影响谁的决定/造什么障碍） | Inferred |
| **foreshadow-ledger.yaml** | 铺垫句 / 角色秘密 / 物品首现 / 未解悬念（见 §3.3 识别表） | `type` / `text` / `planted_ch` / `status` / `planned_payoff_ch` | Inferred；`planned_payoff_ch` 无证据标 `[待补充]` |
| **state-plotline.yaml** | 章节摘要聚合出的大事件串 | `mainline_beats[{volume,arc,ch_range,beat}]` / `cursor{current_arc,last_chapter_done,next_beat}` | Inferred |
| **state-characters.yaml** | 见 §4 反推 6 步 | `behavior_anchors` / `cognition` / `current_state` | Inferred |
| **rolling-summary.yaml** | 逐章读 | `per_chapter[{ch,one_line,sao,hook}]` + `previous_tail`（崩点前最后完整章的末段**原文**） | 摘要本身不打 canon（它是可压缩流水） |
| **emotion-debt.yaml** | 憋屈→解气的因果链（原文常无明确证据） | `emotion_debts` / `sao_schedule`；无证据全标 `[待补充]` | Inferred |

> **章纲反推（可选，给续写下一章用）**：只为**崩点章及下一章**反推一份 `chapter-outline-template.json`（不是给每个已有章都补一份完整章纲——那是注水）。从摘要能稳定提取的填（`chapter_purpose`/`on_stage_characters`/`must_happen.keywords`），**设计性字段**（`ending_hook`/`sao_payoff`/`reader_emotion_curve`）一律标 `[待补充]` 让人定——这些是创作决策，反推不出来。

### 3.3 伏笔识别表（从情节点反推 `foreshadow-ledger.yaml`）

| 情节点类型 | 是伏笔的可能性 | 状态推断 |
|---|---|---|
| 铺垫句（"他不动声色记下了这个名字"） | 高 | 后续有呼应/揭示 → `closed`；无呼应 → `open` |
| 角色秘密（叙述暗示但未挑明） | 高 | 标 `open`，`type: 身份` |
| 物品首次郑重出现 | 中 | 后续被使用 → `closed`；否则 `open` |
| 未解悬念（章尾抛出未答） | 高 | `open` |
| 崩点前最后几章的铺垫 | —— | 标 `open` + `note: "接近崩点，回收计划待人定"` |

`planned_payoff_ch`（计划回收章）**反推不出来就标 `[待补充]`**——它是创作决策不是文本事实。导入只登记"埋了什么、埋在哪、回收没回收"，"打算第几章回收"留给人。

---

## 4. 角色状态反向 6 步确定性算法（adapt oh-story → 本 skill 人物卡）

对**每个需追踪的角色**（主角/主要反派/重要配角；功能角色不进），按固定顺序执行 6 步。**输入只用 Phase B 已落盘的产物 + 可信前缀正文，不重读弃用尾部**。每步抽不到证据就填 `[待补充]`。

> ⚠️ **追踪范围阈值是经验值**：oh-story 用"出现章节 ≥50%=主角 / ≥20%=核心配角"——那是**完本导入**的比例阈值。**崩稿只有几章时按比例会全员落选**，改用**绝对出场次数**：主角+主要反派必追；配角出场 ≥2 次才追（⚠️经验值，可调）。

| 步 | 抽什么 | 落到 `state-characters.yaml` 字段 | 取值规则 |
|---|---|---|---|
| **1 当前身份/处境** | 时序**最晚**（崩点前最后一章）的身份/职业/位置 | `current_state.location` / `identity` | 取最新值，不取历史值 |
| **2 当前能力** | 最后出现的境界/实力描述 | `current_state.level`（对照 `world.power_system.ladder`） | 取最新；与 ladder 对不上标 `[待补充]` |
| **3 关键关系** | 与各角色关系的**当前**状态 | `current_state.relations[{with,stage}]` | 取最新阶段；演变写进变更记录 |
| **4 行为锚点**（本 skill 特有，替换 oh-story 的"公众形象"） | 正文里**具体事件**（不是形容词！） | `behavior_anchors`（2-4 条具体事件） | ✅"七岁目睹父亲守诺被斩首，二十年未立誓"；❌"重情重义" |
| **5 认知边界**（本 skill 特有，oh-story 没有） | 信息差证据：谁当面知道/不知道某事、谁误判了谁 | `cognition.knows` / `does_not_know` / `misbeliefs` | 反推不出的别瞎填；扮猪吃虎/打脸的 misbeliefs 是命门，有证据才登记 |
| **6 状态变更记录 + 待回收伏笔** | 各章状态变化（身份/能力/关系）；查 ③伏笔台账中涉及该角色且 `open` 的条目 | 变更进 `rolling-summary` 的 per_chapter；伏笔在台账里关联 | 变更 >10 条时压缩（最早的合并进字段，留最近 10 条） |

**与 oh-story 6 步的差异（关键 ADAPT）**：
- oh-story 第 4 步是"公众形象"、终点是扁平的 `角色状态.md`；**本 skill 第 4/5 步换成 `behavior_anchors`（行为锚点不写形容词）+ `cognition`（认知边界四字段）**——这是本 skill 人物卡的两条铁律（`references/02` §5），导入时就必须按这套抽，不能抽成一句"他很强很腹黑"。
- **全部落 `canon_status: Inferred`**：oh-story 反推完就当项目数据用了；本 skill 反推完是 Inferred，要么人确认升 Canon，要么续写中被 continuity-checker 怀疑。

**半成品基准**：残稿时所有"当前值"以残稿前最后完整章为准，人物卡头部注 `# 基于第 N 章状态，残稿第 N+1 章未计入`。

---

## 5. `[待补充]` 纪律（拿不准的标记，绝不编造）

导入最大的诱惑是"把空字段补满让它看起来完整"。**反着来：原文没给的证据，一律标 `[待补充]`，宁缺毋造**。

| 字段类别 | 反推得出？ | 处理 |
|---|---|---|
| **文本事实**（谁在哪、有什么、说了什么） | 能 | 直接抽，标 `Inferred` |
| **设计决策**（章首/章尾钩子、爽点级别、计划回收章、情绪曲线目标） | **不能** | 标 `[待补充]`，留给人定 |
| **关系/动机**（A 为什么帮 B、副线走向） | 多数不能 | 有明说才写；暗示而未明 → `[待补充]`，不脑补 |
| **顶层契约**（结局、核心冲突） | 草案能、定稿不能 | 标 `Pending`，**人追认才升 Canon** |

三条铁律：
1. **`[待补充]` 不是 bug，是诚实**——它让"这里没证据"显式可见，比编一个假值好一万倍（假值会被当真喂给 writer）。
2. **`Inferred` ≠ `Canon`**——反推的事实即使"看起来铁定对"也只是 Inferred；冲突时优先怀疑它（对齐 `references/02` §2）。
3. **契约字段反推=`Pending`**——`core_conflict`/`ending_anchor`/`goldfinger` 这些是人类创意主权（`references/02` §0 表 00 contract = human-only），AI 反推只出草案供追认，**绝不自动锁死**。这与本 skill"剧情走向人拍板"的根本边界一致（SKILL.md 原则 2）。

---

## 6. 续写接手 + 诚实边界（工程能修的 vs 需人审的）

### 6.1 从崩点之后接进 §3 正常循环

导入完成后，状态层已就位，**续写不是"接着让 AI 自由写"，而是 rejoin 章节生产循环**（SKILL.md §3）：

1. **崩点章本身 = 第一个续写任务**——不信任旧版本，用 `compile_prompt.py` 编译它的 prompt → writer 重生成 → 独立校验 → rubric 审校 → 回写。`cursor.last_chapter_done` 设为崩点章 **-1**，driver 从崩点章重新开始。
2. **续写产出的事实正常走 delta 回写**（`state_apply.py`），此时才有机会把导入的 `Inferred` 事实在人确认后升 `Canon`。
3. **导入的状态层立即受 continuity-checker 保护**——之后每章的独立校验会拿导入的 canon 切片比对，新的漂移当场被抓（这正是导入的价值：把"裸续写必崩"变成"受约束续写")。

### 6.2 诚实说清：导入能修什么，修不了什么（对齐 SKILL.md 原则 7）

| 能修（工程问题，导入直接解决） | 修不了（需人审 / 模型天花板） |
|---|---|
| 状态散落 → 收进 7 个 typed 文档 | 已有正文的**文学性/语感 AI 味**（导入不重写正文，只抽状态） |
| 设定漂移无从发现 → Canon 标签 + continuity-checker | **崩点之后该往哪写**——这是创作决策，人定（导入只给草案） |
| 续写无短期记忆 → `previous_tail` 末段原文 | 反推的**结局/核心冲突对不对**——`Pending`，必须人追认 |
| 模型退化崩点定位 → `degeneration_check.py` 逐章扫 | **语义崩的修复**——continuity-checker 只报"哪崩了"，怎么改人定 |

一句话：**导入把"几章在崩的散稿"变成"可被流水线约束续写的工程"，但它不替创作者重写已崩的正文、不替他拍板结局**。崩点章及之后默认走重写，不走信任。

---

## 7. 质检清单 + 这一步不做什么

### 7.1 导入完成质检（对照勾选）

- [ ] 已用 `degeneration_check.py` 逐章扫，**崩点章已定位**并记录
- [ ] 已派 continuity-checker 抓语义崩，取两路更早的崩点
- [ ] 7 个 `templates/*.yaml` 已生成，**反推事实全部 `canon_status: Inferred`**（无一自动 Canon）
- [ ] 契约草案字段（core_conflict/ending/goldfinger）标 `Pending`，已请创作者**追认**
- [ ] glossary 已钉死专名唯一写法（防后续同名漂移）
- [ ] foreshadow-ledger 先于人物卡生成；人物卡 `cognition` 的待回收伏笔已关联台账实际条目
- [ ] 人物卡按**行为锚点（非形容词）+ 认知边界**抽，不是抽成形容词堆
- [ ] `rolling-summary.previous_tail` = 崩点前最后完整章的**末段原文**（续写记忆源）
- [ ] `cursor.last_chapter_done` = 崩点章 -1（driver 从崩点重新写）
- [ ] 无证据字段一律 `[待补充]`，无编造的关系/钩子/回收章
- [ ] 残稿已注明基准章节
- [ ] 跑 `python3 scripts/state_check.py <book> --current-chapter <崩点-1>` 状态体检通过

### 7.2 不做什么（明确不借 oh-story 的这些）

- **不建拆文库 `拆文库/{书名}/` 目录树**——本 skill 直接落 `templates/*.yaml`，不要"先拆一套中间产物再迁移"的两层结构。
- **不建对标双目录树 `对标/{书名}/`、不建多对标 registry（主对标书/对标书列表）**——那是 oh-story 的"对标书文风召回"机制，本 skill 文风走 `contract.style.anchors`（书级文风锚），不引入对标书体系。
- **不做完本逐章补完整章纲**——只给崩点章及下一章反推章纲，其余已写章不补（补了=注水，违反 SKILL.md §6 反 overengineering）。
- **不在导入阶段重写正文**——导入只读不改；重写是续写阶段（§3 循环）的事。

> **完本导入（罕见）**：若创作者给的是已完本的几百章（不是崩稿），逻辑相同但只为"建立可续写/可外传的状态层"，无崩点定位需求；>200 章按增量导入（首期前 50 章 + 全书摘要，其余分批），未导入章生成简化摘要（⚠️ ~200 字/章，经验值）。但本 skill 的主入口是**崩稿接手**，不是完本拆解。

---

## 8. 挂载点（SKILL.md 新增"阶段 0.5 导入已有稿"）

本 reference 对应 SKILL.md 主流程的一个**新阶段**，建议接在 §2（阶段 0 筹备）之后、§3（章节生产循环）之前，作为"手里已有几章在崩"的标准接手入口：

```markdown
## 2.5 阶段 0.5 —— 导入已有稿（接手崩稿，已写了几章再来的标准入口）

> 适用：创作者**不是从零开书**，而是手里已有几章~几百章（自己写的 / AI 续写的），
> 4-5 章后逻辑/人设/世界观开始崩，想用这条流水线接着写。
> 不适用：从一个脑洞从零开书（走阶段 0）。

三步（完整算法见 `references/13-import-existing-draft.md`）：
1. **定位崩点**：逐章跑 `python3 scripts/degeneration_check.py 第NNN章.txt`
   抓模型退化指纹（复读/截断/工程词），+ 派独立 continuity-checker 子 agent 抓语义崩
   （逻辑/人设/世界观漂移），两路取更早的崩点；切出【可信前缀/崩点章/弃用尾部】。
2. **反向抽取**：把可信前缀按生成顺序（契约→世界观→伏笔→剧情线→人物卡→摘要）
   反推进 7 个 `templates/*.yaml`，**全部标 `canon_status: Inferred`**（反推 ≠ 定稿），
   契约字段标 `Pending` 待人追认；拿不准的字段标 `[待补充]`，绝不编造。
3. **接手续写**：`cursor.last_chapter_done` 设为崩点章 -1，从崩点章 rejoin §3 正常循环
   （compile→writer→独立校验→审校→回写）——崩点章及之后走重写，不走信任。

边界（对齐原则 7）：导入能修"状态散落/设定漂移无从发现/续写无记忆/崩点定位"，
修不了"已有正文的文学性 AI 味/结局对不对/崩点后往哪写"——后者人审、人拍板。
```

---

## Sources

> 本文反向骨架方法与角色状态反推 6 步算法借鉴 oh-story-claudecode 的 `story-import` skill（MIT，github.com/worldwonderer/oh-story-claudecode），**迁移终点、Canon 对齐、崩点定位均按本 skill 重做**，未额外联网检索。

- **反向骨架方法母本**：oh-story-claudecode `skills/story-import/SKILL.md`（Phase 1 确认源 + 篇幅分流 + 残稿处理 / Phase 3-L 结构迁移 / 追踪文件生成顺序铁律 `伏笔 → 角色状态 → 上下文`）。本 skill 取其"先定位再迁移、生成顺序有依赖"骨架，**迁移终点换成 `templates/*.yaml`**，弃其拆文库/对标双目录树。
- **角色状态反推 6 步**：oh-story-claudecode `skills/story-import/references/character-state-reverse.md`（6 步算法 / 追踪对象筛选 / `[待补充]` 纪律 / 半成品基准章 / 变更记录 >10 条压缩）+ `references/state-tracking.md`（出场 ≥3 次或独立剧情线才追踪）。本 skill **第 4/5 步换成行为锚点 + 认知边界**（本 skill 人物卡铁律），全部落 `Inferred`。
- **结构反推映射**：oh-story-claudecode `skills/story-import/references/structure-mapping-long.md`（大纲反推 / 卷划分用户确认制 / 伏笔识别表 / 时间线提取）。本 skill 取伏笔识别表与"卷划分需人确认"思想，落到 `foreshadow-ledger.yaml` + `state-plotline.yaml`。
- **崩点定位器**：本仓库 `scripts/degeneration_check.py`（本身即移植自 oh-story `story-deslop/check-degeneration.js`），逐章扫退化指纹定位"崩在第几章"。
- **Canon 五态 / `Inferred` 第五态 / 人物卡铁律 / 七文档职责**：本仓库 `references/02-state-schema.md` §0/§2/§5/§7——反推事实落 `Inferred`、契约 human-only、行为锚点+认知边界、草稿只读定稿才回写，均与之对齐。
- **迁移终点字段基准**：本仓库 `templates/{contract,state-world,state-characters,state-plotline,foreshadow-ledger,emotion-debt,rolling-summary}.yaml` + `chapter-outline-template.json`（本文反推映射逐字段对齐之）。
- **诚实边界 / 反 overengineering**：本仓库 `SKILL.md` 原则 7（工程能修 vs 模型天花板）+ §6（MVP vs 完整版，不为导入建拆文库/对标体系）。
