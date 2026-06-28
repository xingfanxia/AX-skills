> Purpose: 章节生产循环里"审校层"的可执行规格 —— 一张量化质检表（硬门清单 + 加权分各项最低线 + 通过阈值），加上 continuity-checker（对不对）/ quality-reviewer（好不好）的分离契约、独立调用防自欺协议、双免疫终分公式、末行裸 sentinel 容错解析、改稿循环 ≤3 轮 + 净改善门控。用在 9 步循环的**步骤 5（continuity-checker）/ 步骤 6（reviewer）/ 步骤 7（revise）**。落地产物对照 `templates/review-report-template.json`，机械扣分来自 `scripts/antislop_lint.py`。

---

## 0. 一句话原理

审校不是"通过/不通过"的 vibe，是**两个独立子程序的串联**：先用 continuity-checker 吃 canon/时间线/人物判**对不对**（硬门），再用 quality-reviewer 吃 rubric 判**好不好**（加权分）。两者都与 writer **独立上下文、最好异模型**——共享上下文的"自审"必然自欺（执行者没变，不会认真挑自己的错，腾讯复盘点破的"自审即自欺"）。终分再由代码减掉机械 AI 味扣分（双免疫），防 LLM judge 给词句层 AI 味文本打高分。

> 全部门槛、最低线、阈值都钉死在 `templates/review-report-template.json`，**reviewer 只往里填数、不持 Write、不改情节**（审校是"找问题"不是"验证正确"）。来源：blueprint §4 / prior-art §4-§5。

---

## 1. 硬门清单（任一违规 → 直接 REVISE，不可被加权分平均掉）

硬门是**一票否决**：高爽点分不能把"主角降智 + 剧透泄漏"平均成 PASS。7 个门对应 `review-report-template.json` 的 `hard_gates` 七个布尔字段，任一为 `false` 即 REVISE。

| `hard_gates` 字段 | 判什么 | 归属 checker | 吃什么（数据源） | 判定方式 | 反例（命中即 false） |
|---|---|---|---|---|---|
| `character_consistent` | 人设/行为锚点/认知边界一致 | continuity-checker | `state-characters.yaml`：`behavior_anchors` / `current_state` / `cognition` | LLM 抽取对照（F1≈0.68，只"标记可疑"，裁决靠人）⚠️ | 父母双亡却回家继承家业；二十年未立誓的人突然轻诺 |
| `world_canon_consistent` | 世界观/设定/阶位/专名一致 | continuity-checker | `state-world.yaml`：`canon_status=Canon` 事实 + `power_system` 阶位表 + `glossary` 专名表 | 混合：阶位单调性/专名唯一写法用 code，语义用 LLM | 战力倒挂越级；同一功法两种写法（专名漂移） |
| `timeline_logic_consistent` | 时间线/因果/物理一致 | continuity-checker | 双时态事实（`valid_until_chapter`，只失效不删） | 混合：区间运算 code，语义 LLM | 拿出两章前已丢的武器；公交车坐三天三夜 |
| `wordcount_pov_format_ok` | 字数区间/POV/格式 | **`output_check.py`（机械层）** | 章纲 beat sheet 的 `字数预算` / `POV` | 纯 code（`output_check.py` 数字+正则，零 LLM；POV 跳头为启发式） | 越界 30%；一场戏跳头；混入小标题/分隔线 |
| `no_poison_points` | 毒点 0 命中 | `output_check.py` 词面 + reviewer 语义 | 品类×平台毒点黑名单（见 `05-category-templates` / `06-platform-params`） | 混合：`output_check.py` 扫词面黑名单，语义判定交 reviewer | 绿帽/送女/圣母/油腻种马；该平台零容忍项 |
| `no_forbidden_reveal_leak` | 剧透红线/伏笔提前泄底 | continuity-checker | `visible_from_volume > 当前卷` 的事实 + 本章 `forbidden_reveals` + `cognition.reader_knows_char_doesnt` | 混合：可见性 code 截断在 prompt 端，泄漏语义 LLM 复检 | 角色"想起"自己尚不知道的真相；提前点破后卷反转 |
| `no_prompt_leak` | 无残留指令符号/标签/元叙述 | **`output_check.py`（regex）** + reviewer | 正文本身 | 纯 code 为主（`output_check.py` 扫标签/`<reference>`/"本章将"/"作为一个 AI"） | 正文里出现 XML 标签、大纲条目、"字数已达" |

**分工铁律**：`character/world/timeline/forbidden_reveal` 四门是 **continuity-checker 的领地**（吃事实、不吃写作 context）；`wordcount/pov/format` 与 `prompt_leak` 主体在调 LLM 前就由 **`output_check.py`** 拦掉（外加 `opening_ok` 开篇阈值启发式）；`poison_points` 词面黑名单 `output_check.py` 先扫、语义残留交 reviewer。**能 code 判的绝不写进 prompt 让模型自觉**（伪约束是头号反模式）。

---

## 2. 加权分（总 100，各项有最低线，低于最低线也 REVISE）

加权分由 quality-reviewer 一次调用打满，对应 `weighted_scores`。**每项有 `min` 最低线**——任一项跌破最低线，即便总分够也 REVISE（防"七项里有一项崩，靠其它项抬总分蒙混"）。

| `weighted_scores` 字段 | 满分 | 最低线 `min` | 判什么 | 桶/轴归属 |
|---|---|---|---|---|
| `sao_payoff` 爽点兑现 | 20 | 14 | 对照章纲 `sao_payoff`（及所属 arc 的 `sao_target`），验"需求建立→压抑→释放"链是否闭合；释放强度 ≥ 已积压憋屈债 | 桶3 网文专属轴 |
| `ending_hook` 章末钩子 | 15 | 10 | 4 型钩子（悬念/反转/情绪炸弹/信息投放）是否成立；章节名是否被兑现 | 桶3 网文专属轴 |
| `pacing_density` 节奏/信息密度 | 10 | 6 | 无注水、主线在推进；近 3 章无连续"平路" | 桶3 网文专属轴 |
| `ai_taste` AI 味 | 10 | 7 | 看**语义层** AI 味密度（华美空洞/做加法不推进/翻译腔残留）；越低分越高 | 桶1+桶2（语义补充） |
| `emotion_immersion` 情绪/代入 | 15 | 9 | 情绪点直给到位、压释对应正确（没写串压点）；读者有唯一代入锚 | 桶2 分层（情绪反向放行直给） |
| `prose_imagery` 文笔/画面 | 15 | 9 | 画面具体、感官落地；品类适配（白文求白爽 / 古言放行辞藻） | 桶1 词句层 |
| `dialogue_natural` 对白自然 | 15 | 9 | 对白有性格区分、非"背课文"；爽点场景敢把话说死 | 桶1+桶2 分层 |

满分校验：`20+15+10+10+15+15+15 = 100`。最低线之和 `14+10+6+7+9+9+9 = 64`，故 `weighted_total ≥ 80` 不会让任一项必然达标——**最低线与总分阈值是两道独立闸**，缺一不可。

> ⚠️ 对齐提示：blueprint §4 早稿写的最低线偏松（如爽点 `≥7`）。**以 `review-report-template.json` 为准**（爽点 `min=14`），本表已采纳模板值。

---

## 3. 双免疫终分（final = LLM 加权分 − 机械确定性扣分）

加权分由 LLM judge 给；但 LLM judge **看不见也管不住自己也会犯的词句层 AI 味**——所以终分要由**代码再减一道机械扣分**（来自 autonovel 双免疫）。两道免疫**互补不重叠**：

| 免疫 | 谁做 | 抓什么桶 | 来源 |
|---|---|---|---|
| LLM `ai_taste` 维度（0-10） | quality-reviewer（语义） | 桶2/桶3：做加法不推进、华美空洞的语义判断 | rubric 加权项 |
| `mechanical_penalty` 机械扣分 | `scripts/antislop_lint.py`（确定性正则） | 桶1：固定频率反复出现的 AI 指纹（机械连接词/翻译腔/形容词叠罗汉/否定平行/节奏匀速） | 代码硬减 |

`antislop_lint.py` 输出两个数：`ai_taste_score`（无界原始密度分，看密度不看单次，**仅作展示/调试**）和 `penalty`（已 `min(20,…)` 封顶到 0-20、量纲对齐 0-100 加权分的**机械扣分**）。**判分公式**（写进 driver，不交给 LLM）：

```python
weighted_total   = sum(weighted_scores)          # LLM 给，0-100
mechanical_penalty = lint_json["penalty"]         # 脚本给(0-20，已封顶/量纲对齐)，代码直接减
final_score      = weighted_total - mechanical_penalty   # = weighted_total − penalty(0-20)
```

`mechanical_penalty` 与 `final_score` 直接写回 `review-report-template.json` 同名字段。**通过条件（`_pass_condition`）三者全满足**：

```
PASS ⟺ final_score >= 80
        且 所有 hard_gates == true
        且 每个 weighted_scores 项 >= 其 min
```

> ✅ 量纲已对齐、无需再校准：直接用脚本 emit 的 `penalty` 字段（已 `min(20,…)` 封顶到 0-20、量纲对齐 0-100 加权分），不再乘 `k` 系数、不再手调阈值。`ai_taste_score` 是无界原始分，**仅作展示/调试**，不进终分公式。

---

## 4. continuity-checker vs quality-reviewer —— 两个子程序，分开调

| | continuity-checker（步骤 5） | quality-reviewer（步骤 6） |
|---|---|---|
| 判什么 | **对不对**（一致性/逻辑/泄漏） | **好不好**（爽点/钩子/节奏/文笔） |
| 吃什么 | canon / 时间线 / 人物 / 可见性（**只吃事实，不吃写作 context、不吃 rubric**） | 正文 + 本章章纲 + rubric（**不吃 canon 全量**） |
| 产出 | `hard_gates` 中的 4 门（`character`/`world`/`timeline`/`forbidden_reveal`）+ `violations[]`（定位到段/句） | `weighted_scores` + `ai_taste_hits[]` + `violations[]` |
| 用什么 | 独立 LLM 角色做语义对照 + `scripts/state_check.py` 机械兜底（Canon枚举/境界/伏笔逾期/情绪债，仅机械不变量；**无 continuity_check.py，语义一致性是 LLM 角色不是脚本**） | rubric 量化打分 |
| 性质 | automate，独立 | automate，**独立上下文 / 异模型** |

为什么必须拆：一致性是**确定性问题**（能 code 兜底，矛盾判定靠区间运算），质量是**语义问题**（靠 rubric）。混在一次调用里，模型会用"这章很爽"冲淡"时间线错了"。两者各产 `violations[]`，**汇流后任一硬门 false 或任一项跌破 min → REVISE**。

---

## 5. 独立调用防自欺（共享上下文 = 自欺）

铁律：**reviewer 不能是刚写完这章的 writer。**

- **新会话/新上下文**：reviewer 的 prompt 只给"正文 + 章纲 + rubric"，不带 writer 的思考链、不带"我刚才是这么构思的"。带了 = 它在为自己的稿子辩护。
- **异模型优先**：writer 与 reviewer 用不同模型/不同 provider（`client` 可注入：换 `base_url + model` 即可），减同源盲点。同源模型互洗 AI 味无效（改写后仍 96–98% 被检测）。
- **style/anti-slop-editor 同理**：去 AI 味是**独立 pass，不喂回同源模型重写**（步骤 8）。
- 来源：prior-art §4-§5（oh-story-claudecode / webnovel-writer 把"审校是找问题不是验证正确""reviewer 单一不持 Write"写成铁律）；blueprint 设计哲学支柱 3。

---

## 6. 末行裸 sentinel —— 容错解析，把自由文本变可靠 boolean

reviewer 输出 = 结构化 JSON（填 `review-report-template.json`）**+ 末行一个裸 sentinel**：`VERDICT:PASS` 或 `VERDICT:REVISE`（对应 `verdict_line` 字段）。driver 不去解析 prose、不 JSON-parse 整段散文判定，只**容错读末行**：

```python
last = report_text.strip().splitlines()[-1].strip().upper()
passed = last.startswith("VERDICT:PASS")   # 容错: 大小写/前后空白/句末标点都吃得下
# 任何非 PASS（含解析失败/缺末行）一律按 REVISE 处理（fail-closed，宁可多改一轮）
```

原理：把模型一个**无界文本通道**收敛成可靠的二值控制信号——deterministic 代码 branch 的是验证过的 sentinel，不是 prose。这与 CLAUDE.md AI-pipeline 铁律"branch on a validated control signal, not free-text"同构。**末行缺失/格式歪 = 当 REVISE**，绝不当 PASS 放行。

---

## 7. 改稿循环 ≤3 轮 + 净改善 ≥ ε 才采纳（keep / discard）

REVISE 不是"重抽一遍同 prompt"——那样 6–7 次后内容会自我重复塌缩。正确做法：把 `violations[]` 里**具体的、定位到段/句的 `fix` 指令**定向回灌 writer（可换 prompt/换模型/出改写候选）。

每轮改完，**用同一套 rubric 重新打分，只有净改善才采纳**（来自 inkos「净改善≥ε」+ autonovel git keep/discard「post≥pre 才 commit」）：

```python
for round in (1, 2, 3):
    new = revise(draft, violations)              # 定向 fix，非重抽
    rescore(new)                                  # 重跑 continuity + reviewer + lint
    if new.final_score > draft.final_score + EPS: # 净改善 (EPS 小阈值 ⚠️经验值~2)
        draft = new                               # keep
    else:
        pass                                      # discard，回滚旧稿，别白改使其更糟
    if new 通过(§3 三条件):
        break
else:
    转人工   # 第 3 轮仍不过 → 召回人类（多半是 outline/canon 层问题，改稿改不动）
```

要点：
- **净改善门控防"越改越糟"**：改稿可能修了 A 又踩坏 B，`final_score` 不升就回滚。`revise_round` 字段记录轮次。
- **≤3 轮是经验值（Trae 实测 ⚠️）**，第 3 轮转人工——某些 violation（叙事跳跃/主线方向错/伏笔结构性失衔）靠局部改稿改不动，只能回 outliner 或人裁。
- 改稿优先**局部 patch** 而非整章重写（成本+不破坏已过门的部分）；style-editor 改写后**建议再过一遍轻量 continuity-check**（去味可能损伤已通过的一致性）⚠️ 成本权衡见 blueprint 开放问题 6。
- **regenerate-vs-patch 分叉（关键，借鉴 oh-story）**：`degeneration_check.py` 报的 **blocking（复读/打转/截断/占位符/工程词泄漏/字节地板）不走 patch 改稿**——它们是模型退化，局部 fix 改不掉，要**回去重新生成那一段/那一章**（把 finding 当约束喂回 writer，cap N 次重生成）。patch+净改善只对"质量/一致性 violation"，别拿净改善门去磨一段退化文本。
- **反应篇幅比 ≥1.5（可选判据）**：重大事件后"角色反应/后果"的篇幅应 ≥ 事件本身（防 AI"事件一笔带过、不给情绪落点"）；reviewer 半机检，跌破提示 pacing 欠账。⚠️经验值。

---

## 8. reviewer 的边界（只返 JSON，不持 Write，不替你改）

- reviewer / continuity-checker **只返填好的 `review-report-template.json`**：打分、列 violations、给 fix 指令——**不持 Write、不改正文、不建议改情节走向**。
- 改正文是 writer（步骤 7）的活；改情节走向是 human-only。审校层越权改稿 = 把"找问题"偷换成"验证自己改得对"，回到自欺。
- continuity 的一致性裁决在 F1≈0.68 的现实下**只能"标记可疑"**，最终 Canon 冲突裁决是 human-only（晋升 Canon、判定哪条事实为真都要人确认）。

---

## 9. 落地速查（driver 每章按此跑）

```
步骤5 continuity-checker(独立):  吃 canon/时间线/人物 → 填 hard_gates 4 门 + violations
       └ 机械兜底: state_check.py / 可见性 code 截断 / 专名·阶位单调性
步骤   机械门(code, 调 LLM 前):   wordcount_pov_format_ok / no_prompt_leak(regex) / 毒点黑名单扫
步骤6 quality-reviewer(异模型):  吃 rubric → weighted_scores(各≥min) + ai_taste_hits + 末行 VERDICT
步骤   antislop_lint.py(纯code):  penalty(0-20) → mechanical_penalty  (ai_taste_score 仅展示/调试)
       judge:  final = weighted_total − penalty(0-20)
       PASS ⟺ final≥80 且 hard_gates 全 true 且 各项≥min；末行 sentinel 容错解析(fail-closed)
步骤7 REVISE:  定向 fix 回灌 → 重打分 → 净改善≥ε 才 keep；≤3 轮，第3轮转人工
步骤8 style/anti-slop-editor:  独立 pass 去味，不喂回同源模型；改后轻量复检 continuity
```

**一句话总纲**：硬门是一票否决的确定性闸，加权分各有最低线、不可互相平均，终分再由代码减机械 AI 味；reviewer 与 writer 独立异模型、只返 JSON、末行裸 sentinel 容错 branch；改稿净改善才采纳、≤3 轮转人工。把"几百万字不崩"从靠勤奋维护变成靠架构强制。

---

## Sources

- `templates/review-report-template.json` —— 硬门 7 字段 / 加权分 7 项及各 `min` / `mechanical_penalty` / `final_score` / `_pass_condition` / `_revision_accept_rule` / `verdict_line` 的权威定义（本文一切数值以此为准）。
- `scripts/antislop_lint.py` —— 桶1 词句层机械扣分来源（终分用 `penalty` 0-20，已封顶/量纲对齐；另 emit 无界 `ai_taste_score` 仅作展示/调试，看密度不看单次，默认阈值 10）。
- `templates/emotion-debt.yaml` / `templates/foreshadow-ledger.yaml` —— `sao_target`/`sao_schedule`/释放强度门、伏笔 `status: open|微回应|closed` 的字段依据。
- `docs/research/03-pipeline-design-blueprint.md` §4（审校 rubric/硬门/改稿循环）、§2.3（9 步循环契约）、§6（异模型分工）、§10（开放风险：F1≈0.68 / ≤3 轮经验值 / 去味损伤一致性）。
- `docs/research/04-github-prior-art-survey.md` §4-§5 —— autonovel 双免疫（终分=判分−机械扣分）、inkos 净改善≥ε、autonovel git keep/discard、webnovel-writer reviewer 只返 JSON 不持 Write、"审校是找问题不是验证正确"、伪约束反模式。
- `docs/research/webnovel-aesthetics-vs-literary-craft.md` C/D/E —— 加权分各项的网文专属判据（爽点密度/章末钩子 4 型/毒点清单/华美空洞/品类适配）、反 AI 味三桶归属。
- ⚠️ 标注项：F1≈0.68 一致性精度、≤3 轮上限、ε（净改善阈值）、`state_check.py`/`output_check.py` 接口细节 —— 均为经验值/待与脚本实测对齐，非写死的确定数据。（机械扣分 `penalty` 已由脚本封顶/量纲对齐，不再需要 `k` 系数校准；语义一致性是独立 LLM 角色，无 continuity_check.py 脚本。）
