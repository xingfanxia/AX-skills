# 08 · 伏笔台账与时间线（防剧透 + 防吃书）

> Purpose: 把"伏笔"和"长线一致性"从靠勤奋维护的玄学，变成有状态机、有截止章、会逾期报警的台账 + 一条只失效不删的事实时间线。**主要用在状态层维护：步骤2（outliner 给章纲填 `due_foreshadows` / `forbidden_reveals`、登记新伏笔）、步骤5（continuity-checker 吃事实查吃书/剧透泄漏）、每卷边界（`scripts/state_check.py` 跑逾期/临近/密度三类告警 + 阶位单调性）。** 对应 `templates/foreshadow-ledger.yaml`、`templates/state-world.yaml`（双时态 + `power_system`）、`templates/state-characters.yaml`（`cognition`）、`templates/contract-template.yaml`（`locked_reveals`）、章纲 `forbidden_reveals` / `due_foreshadows`。

---

## 0. 一句话立场

长篇崩坏的根因是 **AI 自我一致性随篇幅衰减**（贵模型解决不了）[研究01·腾讯云复盘]。伏笔与时间线是这条衰减曲线踩得最狠的两处：埋了的坑三个月后自己忘、前一章筑基后一章练气、幕后黑手在第二卷的旁白里被说漏。**唯一可行解是把"能机械判定的一致性"交给确定性台账与脚本，不交给模型记忆**——本文给的就是这两个台账（伏笔状态机 + 双时态事实时间线）的编码规则与告警逻辑。

---

## 1. 原理一：伏笔 ≠ 钩子（最高频的混用死法）

两者方向相反，混用必翻车：

| | 钩子(hook) | 伏笔(foreshadow) |
|---|---|---|
| 读者当下的注意力 | **要读者立刻注意到**（章末三行，制造"想看下一章"） | **埋时不需要读者注意到**（藏在细节里，回收时才"啊原来如此"） |
| 兑现节奏 | 短程，下一章就接住（见 references/07 §6 钩子4型） | 长程，几十章后回收 |
| 写崩症状 | 写完再想结尾 = 自然收束 = 帮读者按退出键 | ① 埋时写太重 → 变成"预告"（角色大惊小怪）；② 埋了忘回收 = **烂尾**（一票否决毒点） |

> 铁律来源：网文666《6种伏笔类型拆解》——"别把伏笔当钩子用"（埋时无需读者立刻注意）+ "埋了忘回收=烂尾"+ 建一张追踪表[研究01·wangwen666/post200]；鱼人二代《校花》2201万字仍"有很多伏笔要一一填坑"印证账本是长线刚需。

**可复用要点**：埋伏笔时 writer 的笔触要**轻**（一句带过、不给特写、不让角色追问）；这件事必须在章纲 `due_foreshadows` 里标"本章埋 F0xx，轻埋"，否则 AI 默认会把它写成钩子。

---

## 2. 伏笔六类 + 各类 AI 最易写崩点

六类对应 `foreshadow-ledger.yaml` 的 `type` 字段（取值严格用这六个，勿自造同义词）：

| `type` | 是什么 | 示例（仅示意） | AI 最易写崩点 | 哪个状态机能兜 |
|---|---|---|---|---|
| **身份** | 某角色真实身份/血脉/来历提前埋线索 | 老乞丐随手接住飞剑的姿势 | **提前泄底**（旁白/对话说漏幕后黑手） | `cognition` + `locked_reveals` + `forbidden_reveals`（§7） |
| **语言** | 一句随口的话/谶语/承诺，日后应验 | "你会死在自己最信的人手里" | 埋时写太重（当钩子）/ 忘应验 | 台账 `status` + `planned_payoff_ch`（§3） |
| **场景** | 场景里不起眼的细节，后文成关键 | 墙上一幅缺角的画 | 场景切片化生成时前后细节漂移（画的内容变了） | 时间线 pre/post-facts（§6） |
| **数字** | 一个数字/日期/数量，后文揭意义 | 钥匙串上是七把钥匙 | 数字前后矛盾（变成六把） | 双时态 + 数值校验（§6） |
| **主题** | 反复出现的意象/母题，呼应主旨 | 反复出现的"守诺"母题 | AI 不会主动经营母题，要么没有要么硬塞 | human-only 设计，台账只登记 |
| **物件** | 一件道具（信物/法宝/旧物），后文发挥作用 | 母亲留下的半枚铜镜 | 道具凭空出现/消失 | 角色 `current_state.resources` 资源账本 |

> 依据：网文666"伏笔有6类（身份/语言/场景/数字/主题/物件）"[研究01·wangwen666/post200]。示例为本文构造，仅示意类型，不是来源原文。

**可复用要点**：六类里 **主题伏笔是 human-only**（母题经营是叙事主权，AI 写不来）；其余五类可由台账机械登记，但"埋什么/何时回收"仍是 semi-auto（人/半自动在卷-arc 边界定）。

---

## 3. 伏笔台账状态机（对应 `templates/foreshadow-ledger.yaml`）

这是 pipeline 里**最纯粹可自动化**的一层：埋设登记 → 状态流转 → 临近回收章自动提醒。**绝不能塞进剧情线散文里**（散文里的伏笔=会被模型漂移忘掉的伪约束）。

**状态机（`status` 字段三态，单向流转）：**

```
埋设登记 ──► open ──►（中途呼应一次）──► 微回应 ──► closed
              │                                        ▲
              └────────────（直接回收）────────────────┘
```

**字段表（直接对齐模板，勿改名）：**

| 字段 | 含义 | 登记时（步骤2） | 校验时（state_check） |
|---|---|---|---|
| `id` | 伏笔 ID（F001…） | 埋设即开一条 | — |
| `type` | 六类之一（§2） | 人/半自动填 | — |
| `text` | 埋的是什么（一句话） | 填 | — |
| `planted_ch` | 埋设章节 | 填 | — |
| `planned_payoff_ch` | 计划回收章节 | **必填，没有计划=别埋**（准入门，§5） | 缺失→warning；逾期→error |
| `status` | open / 微回应 / closed | 默认 open | — |
| `visible_payoff_volume` | 回收时机所在卷 | 填（与剧透红线对齐） | 与 `visible_from_volume` 同源治理 |
| `note` | 回收想达到的效果（"啊原来如此"） | 填 | — |

**铁律**：`planned_payoff_ch` 是必填项——**没有回收计划的伏笔不许登记**（这是准入控制，见 §5）。草稿只读台账；定稿才由 state-updater 抽 delta 回写（开新条 / `status` 翻转），Canon 性质的回收需人确认。

---

## 4. 三类告警 + 阶位单调性（`scripts/state_check.py` 每卷边界跑）

脚本只抓**机械可判**的不变式，不替代 LLM continuity-checker（语义级矛盾仍需 LLM）。伏笔相关判定逻辑（与脚本逐条对齐）：

| 告警 | 触发条件（脚本判定） | 级别 | 含义 |
|---|---|---|---|
| **无回收计划** | `status ∈ {open,微回应}` 且 `planned_payoff_ch` 空 | warning | 埋了没回收计划 = 烂尾风险（应在准入就拒，§5） |
| **逾期未回收** | `current_chapter > planned_payoff_ch` 仍 `open/微回应` | **error** | 烂尾直接发生，必须人工处理（退出码 1） |
| **临近回收** | `0 < planned_payoff_ch − current_chapter ≤ 5` | warning | 本卷该安排回收了，提示 planner |
| **密度告警** | `open_n ≥ 3 × (closed_n + 1)` | warning | 伏笔密度远超闭合速度——崩铁翁法罗斯式翻车（开坑速度 >> 填坑速度） |

`current_chapter` 默认读 `contract.meta.current_chapter`，可用 `--current-chapter N` 覆盖。

**阶位单调性（防战力崩坏，同一脚本）**：脚本对每个角色查 `current_state.level` 是否 ∈ `power_system.ladder`（不在=warning，多半错字/越级）。

> ⚠️ 诚实边界：脚本**当前只查"境界在阶位表内"，不查"按章序不倒退"**（脚本注释明说"需配合历史"）。真正的"前一章筑基→后一章练气"倒退，要靠 §6 的双时态时间线（记录每章 level 历史）+ LLM continuity-checker 抓。别以为 `monotonic: true` 一个字段就自动防住了倒退——它只是声明意图，倒退检测需要历史快照。

---

## 5. 伏笔生命周期治理：准入 + 欠债逼还（借鉴 inkos / ExplosiveCoderflome）

只有状态机不够——网文连载最痛的是"开坑爽、填坑难"。两个反向压力机制（prior-art 验证过）必须上：

**(1) 准入控制（入口拦截，借鉴 inkos）**
登记一条伏笔前，强制过三道闸：

| 准入闸 | 拒绝条件 | 为什么 |
|---|---|---|
| **回收信号闸** | `planned_payoff_ch` 为空 → 拒绝登记 | 无回收计划的伏笔 = 注定烂尾，inkos 直接拒"无回收信号的伏笔" |
| **去重闸** | 与现有 open 伏笔同 `type` + 高度相似 `text` → 合并或拒 | inkos 拒"重复家族伏笔"（同一个坑挖三遍读者疲劳） |
| **轻埋闸** | 章纲未标"轻埋" → 提示风险（防当钩子用，§1） | 埋时太重 = 变预告 |

**(2) 欠债逼还（出口施压，借鉴 inkos `collectStaleHookDebt` / ExplosiveCoderflome PayoffLedger）**
每卷/arc 边界，把"久 open 未回收"的伏笔聚成一份**欠债清单**，**逼 planner 在本卷处理**（回收 / 微回应续命 / 显式标记废弃）。这正是 §4 逾期(error)+临近(warning)+密度(warning)三类告警的产品化用途——告警不是给人看完就算，是**强制进入下一卷的 planner 输入**。

> 依据：研究04 prior-art——inkos「准入控制拒绝无回收信号/重复家族伏笔 + `collectStaleHookDebt` 算欠债逼 planner 处理」、ExplosiveCoderflome `PayoffLedgerItem`「`ledgerKey` 唯一 + 状态机(setup→hinted→pending_payoff→paid_off/failed/overdue) + 兑现窗口 + overdue 主动报警」[研究04·§3(3)]。本台账把它压缩成 `status` 三态 + `planned_payoff_ch` 单字段 + 脚本三告警，避免 inkos 式 8 文件伏笔子系统的过度工程（研究04 明列"避：8文件伏笔子系统/三重状态同步缝"）。

**可复用要点**：复杂度预算花在"逾期 error 阻断 + 欠债清单逼还"，**不花在**多状态枚举/多文件同步。三态(open/微回应/closed) + 一个截止章 + 脚本告警，已覆盖连载 95% 的伏笔治理需求。

---

## 6. FACTTRACK 式时间线：事件 → pre/post-facts → 双时态查吃书

**原理**：一致性不是"当前快照对不对"，而是"**截至第 N 章为真的事实集合**对不对"。把每个关键事件拆成它**改变了哪些事实**（pre-fact = 事件前为真、post-fact = 事件后为真），按章序排在时间轴上——生成第 N 章时只喂"截至第 N 章仍为真"的事实，**天然防剧透 + 防前后打架 + 防战力倒退**。

**双时态：只失效不删（对应 `state-world.yaml` 的 `valid_from_chapter` / `valid_until_chapter`）**

| 字段 | 含义 | 规则 |
|---|---|---|
| `valid_from_chapter` | 这条事实从第几章起成立 | 事件发生章 |
| `valid_until_chapter` | 这条事实到第几章失效（被推翻/过时） | **`null` = 至今有效**；被推翻时**填失效章、不删原条** |

一条会变假的事实（"宗门掌门是甲" → 后来甲死、乙继位），**不要删原条**，而是给它填 `valid_until_chapter`，再开一条新事实。生成第 N 章时，compiler 只取 `valid_from_chapter ≤ N 且 (valid_until_chapter 为空 或 > N)` 的事实。这样：
- 写第 50 章回忆杀提到"甲掌门"——查得到（那时甲还在任），不矛盾；
- 写第 90 章当前线——只喂"乙掌门"，甲那条已 `valid_until=80` 不进 prompt。

**能查出来的吃书类型：**

| 崩坏 | 时间线怎么抓 |
|---|---|
| **战力崩坏 / 境界倒退** | 每章 `current_state.level` 入时间轴；后一章 level 的 ladder 序 < 前一章 → 倒退（需历史，脚本只查"在表内"，倒退由时间线+LLM 抓，见 §4 ⚠️） |
| **数字伏笔矛盾** | 数字事实带双时态；未登记失效却出现新值 → 矛盾 |
| **场景细节漂移** | 场景 post-fact（"画缺左下角"）登记后，后文出现冲突描述 → continuity-checker 报 |
| **物件凭空出现/消失** | 物件作为 `resources` 条目，没有"获得事件"却出现 → 来源缺失 |

> 依据：研究04——graphiti「双时态'只失效不删除'事实账本 + provenance + point-in-time 查询；矛盾判定=LLM 只出 idx、Python 做区间失效」是 L2 设计蓝本；inkos 用双时态精确抓"角色拿出两章前已丢失的武器""记起从未见过的事"[研究04·§3(2)]。**FACTTRACK（事件→pre/post-facts→时间轴）是本 skill 对这套双时态机制的命名与结构化**；底层不变量来自 graphiti/inkos，⚠️"FACTTRACK"这一具名为本框架约定，非来源原词。

**反 overengineering**：本 skill 的 substrate 是 Markdown/YAML，**不上图数据库/向量库**（研究04 明列 graphiti 的"避：图数据库/向量/cross-encoder 重栈，用 SQLite/JSON 重写"）。时间线就是带 `valid_from/until_chapter` 字段的 YAML 事实列表 + 脚本区间过滤，矛盾的语义判定交 LLM continuity-checker。

---

## 7. 认知边界与渐进式披露（防 AI 提前剧透幕后黑手/最终反转）

AI 写崩的另一头是**提前剧透**——把幕后黑手、隐藏身世、最终反转在前几卷的旁白/对话里说漏。三道防线叠加（按卷开放，越往后越多事实进 prompt）：

| 防线 | 字段 / 文件 | 作用 |
|---|---|---|
| **最终红线** | `contract.locked_reveals[]`（`reveal` + `reveal_at_volume`） | 最终反转/幕后黑手清单。**只存契约供人类掌控，绝不进 writer 的 prompt**（compiler 防泄漏） |
| **按卷可见性** | 各状态条目的 `visible_from_volume` / 伏笔 `visible_payoff_volume` | `visible_from_volume > 当前卷`的事实一律不进 prompt（防剧透红线） |
| **角色认知边界** | `state-characters.yaml` 的 `cognition` | 谁知道什么——防角色"说出他不该知道的信息" |

**`cognition` 四子字段（对应模板，勿改名）：**

| 字段 | 含义 | writer 据此 |
|---|---|---|
| `knows` | 角色已知的关键信息 | 可以让他基于此行动 |
| `does_not_know` | 角色不知道的关键信息 | **不得让他表现得知道**（命门：悬疑/马甲/重生流） |
| `misbeliefs` | 角色错误地相信什么 | 据此写他的误判反应（别人误判主角废柴=他们的 misbelief，是扮猪吃虎/打脸的引擎） |
| `reader_knows_char_doesnt` | 读者已知但角色不知 | 戏剧反讽的来源 |

**章纲层的执行钩子**：每章章纲填 `forbidden_reveals[]`（本章禁止提前透露的伏笔/反转 id），compiler 据此从 prompt 里排除相关事实——这是把"防剧透"从"靠模型自觉"落成"靠编译期排除"的关键。

> 依据：研究01——webnovel-handbook"正典事实分级 + 渐进式披露（人物与设定按卷隐藏/开放）防 AI 提前剧透幕后黑手/最终反转"；马良写作"渐进式披露：按卷隐藏与开放"专文[研究01·关键发现]。研究04——ExplosiveCoderflome「`CharacterState` 同存 `knownFacts` + `misbeliefs` + `secretExposure`」是"角色认知边界唯一做对的"[研究04·§3(2)]。

**可复用要点**：剧透防护是**分卷单调放行**——`current_volume` 推进时，把到点的 `visible_from_volume == 当前卷`事实/伏笔放进可用集；`locked_reveals` 永远手动、永不自动进 prompt。"何时/如何揭晓"是 human-only（防剧透设计），登记与可见性过滤是 automate。

---

## 8. 与生产循环的接口（落到哪几步）

| 步骤 | 谁 | 用本文什么 | 产物 / 字段 |
|---|---|---|---|
| **步骤2 · outliner（写章纲）** | semi-auto | §1 轻埋、§2 选 type、§5 准入三闸、§7 按卷放行 | 章纲 `due_foreshadows`（本章埋/回收的伏笔 id）、`forbidden_reveals`；台账开新条 / 排回收 |
| **步骤3 · prompt-compiler** | 纯确定性 | §6 双时态区间过滤、§7 可见性 + `forbidden_reveals` 排除 | 只喂"截至本章为真 且 当前卷可见 且 非禁透"的事实 |
| **步骤5 · continuity-checker** | automate（独立，吃 canon） | §6 吃书四类、§7 角色说漏检测 | 违规清单（语义级矛盾） |
| **步骤9 · state-updater** | semi-auto（抽 delta，append，Canon 需人确认） | §3 状态翻转、§6 失效登记 | 伏笔 `status`→微回应/closed；事实填 `valid_until_chapter`、开新条 |
| **每卷边界 · `state_check.py`** | automate | §4 三类告警 + 阶位、§5 欠债清单 | 逾期(error 阻断) / 临近·密度(warning) → 进下一卷 planner 输入 |

---

## 9. 反模式（伏笔/时间线写崩的死法）

| 反模式 | 症状 | 根因 | 怎么扫出来 |
|---|---|---|---|
| **埋了忘回收** | 三个月前的坑没人填 = 烂尾 | 无台账 / 无截止章 | `state_check` 逾期 error + 欠债逼还（§4/§5） |
| **把伏笔当钩子用** | 每埋一条角色就大惊小怪，变预告 | 埋时笔触太重 | 章纲未标"轻埋" → 准入提示（§5） |
| **开坑 >> 填坑** | open 越堆越多，读者疲劳/失去信任 | 只爽开坑不结算 | 密度告警 `open ≥ 3×(closed+1)`（§4） |
| **提前剧透** | 幕后黑手在第二卷被旁白说漏 | 把 `locked_reveals` 喂进 prompt / 无可见性 | `forbidden_reveals` 排除 + `visible_from_volume` 过滤（§7） |
| **角色说出不该知道的** | 重生者/局外人莫名全知 | 无 `cognition` 边界 | `does_not_know` + continuity-checker（§7） |
| **战力崩坏 / 境界倒退** | 前章筑基后章练气 | 数值靠记忆不靠账本 | 阶位在表内(脚本) + 双时态 level 历史(时间线)（§4/§6） |
| **删旧事实致时效矛盾** | 改设定时直接删，回忆杀对不上 | 没用"只失效不删" | 双时态 `valid_until_chapter`（§6） |

> ⚠️ 本文档自身遵守三桶反 AI 味清单：全程直陈操作规则、表格化、无华美空洞、无匀速铺陈——这正是网文要的"直给"。

---

## 10. 反转工具箱（typed · 7 类反转挂在钩子/伏笔/认知/情绪债之上）（借鉴 oh-story-claudecode）

**立场**：反转是钩子(§1，短程·要立刻注意)和伏笔(§1，长程·埋时不显)之外第三种"读者认知操纵"工具——它是**已埋伏笔的一种兑现形态**：把读者一直接受的认知 A 翻成 B。本节给反转上 typed 枚举，让它和已有契约对齐（伏笔六类 §2 / `cognition` §7 / emotion-debt 账本 / sao_schedule 爽点排布），**不另起一套平行框架**。

> ⚠️ ADAPT 总纲：oh-story 的反转手册是**短篇/单篇**工艺（揭示位置按"全文 %"）。长篇连载里反转分 arc 级 / 卷级 / 书级三个尺度，本节把所有"全文 %"一律改成**按 arc/卷进度**（见 §10.3），原文的具体百分比/字数全部标⚠️经验值、可调。

### 10.1 七类反转（typed，对齐章纲 `reversal.type`）

枚举严格用这七个（与 oh-story 拆文 `_meta.json.reversal_type` 同源，勿自造同义词）：

| `type` | 触发条件 | setup（埋） | reveal（揭） | 挂在哪个已有契约 |
|---|---|---|---|---|
| **身份** | 角色真身 ≠ 读者认知 | 埋 ≥3 处行为细节（**禁旁白直说**） | 一个场景同时揭身份+动机；**禁角色自报"其实我是 X"** | 伏笔 §2·身份 + `cognition.does_not_know` + `locked_reveals`/`forbidden_reveals` |
| **视角** | 叙述者视角片面，真相另一面 | 所有叙述是事实但非全部；叙述者**自己也真信**这套（不是骗读者，他也被骗） | 引入他人视角/证词，展示主角"没看到"的场景 | `cognition.misbeliefs` + `reader_knows_char_doesnt` |
| **动机** | 做某事的真因 ≠ 表面 | 给一个合理的表面动机 + 埋行为与表面动机的**微小**矛盾 | 高压场景二选一：表面指向选 A，角色却选 B，行为直接暴露真动机 | 角色卡 `behavior_anchors` + `cognition` |
| **时间线** | 实际时序 ≠ 读者理解 | 不撒谎，只调叙述顺序；用时态/季节/物品新旧当天然时间线索 | 抛一个"不可能存在"的时间矛盾（时间戳对不上 / 提到"还没发生"的事） | FACTTRACK 双时态 §6（`valid_from`/`valid_until_chapter`） |
| **信息** | 读者+主角握了一条错的关键信息 | 给一条来自"可靠来源"的假事实，众人据此行动，后果里埋矛盾证据 | 新证据直接否定旧"事实"，前文所有剧情获新解读 | `cognition.misbeliefs` + FACTTRACK（事实带双时态） |
| **认知** | 对角色/关系的**整体感情判断**被颠覆 | 全程积累一种感情色彩（这人狠/凉薄/纯坏），每个负面场景埋一个反向细节（小到当时不在意） | 一个场景/遗物让所有负面行为同时获反向解读；**不解释**，让读者自己重过一遍 | emotion-debt 账本（情绪从"恨"翻成"亏欠/意难平"）+ `cognition` |
| **无反转** | 甜宠/喜剧/反差萌/报应型本就无反转 | —（走甜度递进 或 报应铺垫） | —（甜度兑现 / 报应兑现，以彼之道还施彼身） | sao_schedule（正向爽点阶梯 / 报应对应表），**不开 reversal 条目** |

**两组易混辨析**：
- **信息反转 vs 认知反转**：信息反转翻**一条事实答案**（遗嘱归属、亲子真伪）→ 走 FACTTRACK；认知反转翻**"我对他的感觉"**（恨了全程的妈其实一直在护）→ 走 emotion-debt。前者改 canon 事实，后者改情绪债方向。
- **无反转铁律（别硬塞）**：甜宠/报应型**硬塞反转必毁节奏**。报应型爽点在反派一步步走向毁灭、每条恶行精确对应一条报应（用报应设计表：恶行→报应→爽感）；甜宠型爽点在关系一步步升温、反差萌反复"装失败"。这类章纲 `reversal.type` 填"无反转"，`setup_clues_count` 阈值跳过（§10.7），爽感全交 sao_schedule。

### 10.2 setup→reveal 三铁律（reviewer 据此验，对齐 §11 与 rubric 维度1/5）

把 oh-story 的合理性/冲击力/公平性自检压成 reviewer 可裁决的三条：

1. **回看 ≥3 处铺垫**：揭晓后倒查，至少 3 处暗示指向反转；反转**不靠巧合**，由角色选择推动。验法 = reviewer 数 planted clues ≥ 章纲 `setup_clues_count`。
2. **不靠独白解释**：揭示用行动/场景让读者自己明白，**禁大段独白"其实我是 X"**。揭示段 ≤300 字（⚠️经验值，长篇可放宽到"一个完整揭示场景"）。
3. **反转后情绪强度 > 反转前**：反转必须**同时改变情绪判断**，不只改信息；且改变读者对前文所有剧情的理解。验法 = 对照 emotion-debt，reveal 章情绪峰值 > setup 段。

> 反模式（对齐 §9）：天降反转（无铺垫）、解释过多（大段独白）、反转无感（只改信息没改情绪）、反转作弊（引入前文不存在的信息）。任一出现 → §11 的 finding。

### 10.3 揭示窗口：ADAPT 成"按 arc/卷进度"（不是全文 %）

oh-story 给的"最佳揭示位置"是**短篇全文 %**（身份 65-75%、视角 70-80%、动机 75-85%、时间线 80-90%、信息 70-80%、认知 75-90%）。长篇直接套全文 % 无意义（几百章的书，75% 可能是第二百章）。改成**三尺度**填 `reveal_window`：

| 反转尺度 | setup→reveal 跨度 | `reveal_window` 怎么填 | 对齐契约 |
|---|---|---|---|
| **arc 级** | 一个故事弧内 | 距本 arc 高潮的位置（类比短篇 %，但以 arc 长度为分母）：`arc:<arc_id>@70-85%` | 章纲 `reversal.reveal_window` |
| **卷级** | 一卷内 | 卷内进度，落在卷末高潮前：`vol:<n>@70-90%` | 章纲 + 卷大纲 |
| **书级**（幕后黑手/终极反转） | 跨全书 | **留空**——反转条目只存 `contract.locked_reveals[].reveal_at_volume`，**绝不进 writer prompt**（compiler 防泄漏，§7） | `locked_reveals` + `forbidden_reveals` |

时机铁律（ADAPT 自 oh-story，百分比均⚠️经验值·可按 arc 长度调）：
- 禁在跨度前 **50%** 揭示（铺垫不够，反转没力度）。
- 禁在跨度末 **95%** 后揭示（揭示后没展开空间）。
- 最优区间约跨度 **70-85%**；双反转：第一个 55-65%，第二个 80-90%。

### 10.4 嵌套反转：双层/三层，间隔递减

- **双层**：读者以为 A → 第一层翻成 B（**给 1-2 段消化时间**）→ 第二层翻成 C（**能同时解释 A 和 B**，比第一层更震撼）。
- **三层（慎用）**：间隔递减（第一层 50-60%、第二层 75-80%、第三层 90-95%）；第三层最短最狠（一句话就够）；最后一层回答前面所有疑问；**每层都要情感冲击**，不只是信息冲击。
- ADAPT：短篇"15000 字以上才装得下三层"——长篇里三层反转跨多 arc/多章，"间隔递减"= 层与层之间的**章距递减**（如相隔 40 章 → 20 章 → 8 章，越往后越密集）。题材限制：只适合高智商悬疑 / 精心设计的复仇（对齐品类）。⚠️ 字数/章距为经验值，可调。

### 10.5 误导技巧：两路径 + 红鲱鱼铁律

误导要**引导读者自己走向错误结论，不能欺骗读者**（对齐 §11·C1 公平性）：

- **加法路径（分层法）**：在真信息上叠假信息。同一线索既可用逻辑 A 解释为 A'（误导方向·常见故事），也可用 B 解释为 B'（真相·不常见故事）。误导读者以为 A' 时，**必须同时暗埋 B' 相关线索**——这正是"回看 ≥3 处铺垫"的来源。
- **减法路径（信息残缺法）**：不加假信息，**隐藏关键信息的一部分**，只让主角得知成功的那半。对齐 `cognition.does_not_know`——主角"不知道"的那半，writer 不得让他表现得知道。
- **红鲱鱼铁律**：假线索（红鲱鱼）**必须在故事里有自己的功能**（推进情节/塑造人物/增加趣味），只是不是反转答案。无功能的纯误导红鲱鱼 = §11·C5 的 finding。

五技巧速查（直接复用，写章纲选一即可）：选择性叙述 / 情绪引导 / 假线索 / 刻板印象利用 / 信息分层。

### 10.6 打脸三方式（对齐 sao_schedule 与 emotion-debt 兑现）

| 方式 | 特点 | 适用 |
|---|---|---|
| **主动挑衅 → 打脸** | 简单粗暴 | 小白文/低门槛爽点 |
| **对手挑衅 → 被打脸再反击** | 压主角同时给读者安全感 + 反击暗示 | 需积蓄仇恨时（= emotion-debt 欠债累积） |
| **借他人之手打脸** | 支持者代为回击，无损主角形象 | 保持主角高逼格时 |

打脸节奏铁律（挂在 sao_schedule + emotion-debt）：
- 压抑别太长（连输 8 场写 3 万字不行 → 改连输 4 场 + 略写）。⚠️ 经验值。
- 压的同时**给读者信心暗示**（主角自信到自大）；读者比起主角被欺负，更厌恶主角自暴自弃。
- 大高潮**不要险胜**——充分铺垫后尽情碾压，干净利落。
- **打脸是 emotion-debt 的兑现**：压抑=欠债累积、打脸=还债；欠债章数对齐 emotion-debt 账本的 `due`，别让债逾期不还（= §5 欠债逼还在情绪轴上的对应）。

### 10.7 章纲字段建议：`reversal{type, setup_clues_count, reveal_window}`

给章纲（对齐 §8 步骤2 outliner + `templates/chapter-outline-template.json` 的 `due_foreshadows`/`forbidden_reveals`）加一个**可选** reversal 块：

```yaml
reversal:
  type: 身份 | 视角 | 动机 | 时间线 | 信息 | 认知 | 无反转   # 枚举,对齐 oh-story _meta.json.reversal_type
  setup_clues_count: 3          # 本反转累计已埋铺垫线索数(有反转必 ≥3;"无反转"跳过此阈值)
  reveal_window: vol:2@70-90%   # 揭示窗口,按 arc/卷进度(§10.3);书级反转留空→走 locked_reveals
  linked_foreshadows: [F012, F031]  # 关联伏笔台账 id(反转兑现 = 这些伏笔的 payoff)
```

约束（对齐准入 §5 + reviewer §11）：
- `type=="无反转"` → `setup_clues_count` 阈值跳过（甜宠/报应型，§10.1 铁律）。
- 有反转且 `setup_clues_count < 3` → reviewer 报 **S2**（铺垫不足/天降反转，§11.3）。
- 书级反转 `reveal_window` **留空**，条目挂 `contract.locked_reveals`，**绝不进 prompt**（防泄漏）。
- `linked_foreshadows` 把反转和伏笔台账打通：反转揭晓 = 这些伏笔 `status` → closed（state-updater 在步骤9 抽 delta 回写）。

> 依据：oh-story-claudecode `reversal-toolkit.md`（7 类反转 setup/reveal + 揭示位置表 + 嵌套 + 误导两路径 + 红鲱鱼铁律 + 打脸三方式）。**本节为长篇连载定位做的 ADAPT**：全文 % → arc/卷进度（§10.3）；短篇字数门槛 → 跨章/跨 arc 章距（§10.4）；并把 7 类反转逐一挂回本 skill 既有契约（伏笔六类/`cognition`/emotion-debt/sao_schedule/`locked_reveals`），不新建框架。

---

## 11. 推理型一致性：continuity-checker 的可裁决输入规范（借鉴 oh-story-claudecode）

**立场**：§6/§7 给的是"吃书四类 + 角色说漏"的语义级一致性。但**悬疑/推理/复仇/打脸**品类还有一类**推理一致性**——证据、信息差、不在场证明、公平性，崩了读者会直接"骂作弊"。本节把 §3 步骤5 `continuity-checker` 的产出从"vibe 违规清单"升级成**带类型 + 严重度 S1-S4 的可裁决 finding**，让改稿能定向、能排期。对齐 §8 步骤5、rubric 审校（维度1 核心一致度 / 维度5 逻辑连贯）。

### 11.1 推理 5 类一致性（悬疑/复仇品类，continuity-checker 额外查这 5 项）

| # | 一致性类型 | 查什么 | 崩坏症状 | 对齐契约 |
|---|---|---|---|---|
| **C1** | **公平性(fair-play)** | 谜底所需关键线索，是否在揭晓前给过读者 | 揭晓时才冒出前文没有的信息 = 作弊/天降反转 | §10.2 铁律 + 反转自检"没引入新信息" |
| **C2** | **证据链闭合** | 每个推理结论是否有证据支撑，证据是否有前文铺垫 | 结论无据 / 证据天降 | §11.2 证据链四要素 |
| **C3** | **信息差一致** | 推理者用的信息，是否在他的 `cognition.knows` 内 | 角色用"不该知道"的信息推理（重生者/局外人莫名全知） | `cognition.knows`/`does_not_know` §7 |
| **C4** | **时间线/不在场一致** | 案件时序、不在场证明，与 FACTTRACK 双时态是否对齐 | 嫌疑人同时在两地 / 不在场证明与事实时间线打架 | FACTTRACK §6（`valid_from`/`valid_until`） |
| **C5** | **红鲱鱼有功能且被否证** | 假线索是否有自身功能、是否最终被明确否证 | 纯误导红鲱鱼 / 红鲱鱼埋了不收（留悬空） | §10.5 红鲱鱼铁律 |

> 烧脑剧情补充：视角只跟推理者走、**不写反派视角**（对齐 cognition——不让 prompt 喂入反派全知事实），避免破坏悬念。

### 11.2 证据链四要素（C2 的展开，复仇/打脸/推理品类）

每条进入推理的证据，按四要素查：

| 要素 | 要求 | 缺失 = 哪级 finding |
|---|---|---|
| **来源(provenance)** | 证据有明确获得事件（谁/何时/何地拿到），对齐 FACTTRACK 事件→post-fact | 缺来源 = **S1**（凭空证据） |
| **铺垫(setup)** | 前文埋过线索，非揭晓时天降 | 天降 = **S2** |
| **释放节奏(cadence)** | 分章释放（⚠️ ≥3 次为经验值，别一次全给）；先扬后抑（反派先得意再被打脸） | 一次全给 / 先抑后扬 = **S3** |
| **致命性递增(escalation)** | 终证最致命、改变全局认知；至少 1 个"定时炸弹"证据（主角提前布局） | 终证不致命 = **S3** |

> ADAPT：oh-story 证据链是**短篇复仇文**工艺（"分章"=分段）。长篇连载里"分章释放"= 跨多章/跨 arc 释放，节奏对齐 sao_schedule 的爽点间隔；"定时炸弹"证据对齐伏笔台账（主角提前布局 = 一条 `planned_payoff_ch` 较远的伏笔）。

### 11.3 严重度 S1-S4（把 finding 变可裁决，对齐 §4 脚本级别与 rubric severity）

`continuity-checker` 每条 finding **必须带一个 S 级**，决定改稿优先级（对齐改稿 ≤3 轮纪律）：

| 级别 | 含义 | 典型 finding | 改稿动作 | 对齐 |
|---|---|---|---|---|
| **S1** | 致命·必改 | 公平性破坏(C1)、推理用不该知道的信息(C3)、凭空证据(C2 来源缺)、因果链断裂 | **当轮必修，阻断定稿** | §4 error 退出码1 / rubric critical |
| **S2** | 高·改稿轮内必修 | 天降反转/铺垫<3、证据天降无铺垫(C2)、红鲱鱼无功能(C5)、时间线矛盾(C4) | ≤3 轮改稿内修掉 | rubric high |
| **S3** | 中·可排期修 | 释放节奏差(C2)、先抑后扬错位、推理跳步、终证不够致命 | 本卷边界前修；进 planner 输入 | rubric medium / §5 欠债清单 |
| **S4** | 低·记录可选 | 揭示靠独白偏多、表达层啰嗦、红鲱鱼略悬空 | 记录，去 AI 味/polish 顺手修 | rubric low / polish |

finding 输出格式（让 reviewer 与 writer 独立、可定向改稿，对齐 §3 步骤5 独立调用）：

```
[S2][C2-证据链] 第137章 "密室钥匙"凭空出现:主角推理用到的钥匙,前文无获得事件(FACTTRACK 无 post-fact)。
建议: 在 ≤137 章补一条"获得钥匙"事件,或改推理不依赖该证据。
```

铁律：
- `continuity-checker` **只出 finding（类型 + S 级 + 章号 + 建议），不自己改稿**（对齐 §6 依据：矛盾判定 LLM 只出 idx、区间失效由 Python 做；这里 LLM 只出 finding，改稿是另一步）。
- **S1 存在 → 阻断定稿**（等价 §4 逾期 error 退出码 1）。
- **writer 与 reviewer 独立调用，防自欺**（对齐 skill 总则：reviewer 与 writer 不同次调用）。

> 依据：oh-story-claudecode `quality-checklist.md`（证据链完整性检查：分章释放/前文铺垫/先扬后抑/终证最致命/定时炸弹证据；五维评分维度1 核心一致度 + 维度5 逻辑连贯的 critical/high/medium/low severity）+ `plot-core-methods.md`（连续性追踪、悬念与伏笔技巧"谜语人 vs 伏笔"判定、烧脑剧情"视角只跟主角"）。**本节 ADAPT**：把短篇五维 severity 收敛成 continuity-checker 专用的 S1-S4，并按推理品类拆出 C1-C5 五类一致性 + 证据链四要素，全部挂回本 skill 既有契约（FACTTRACK/`cognition`/伏笔台账/§4 脚本级别），是 §3 步骤5 产出的可裁决化，不新建校验子系统。

---

## Sources

- 网文666《6种伏笔类型拆解》——伏笔6类(身份/语言/场景/数字/主题/物件) + 追踪表(出现章节/类型/回收计划/状态) + "别把伏笔当钩子用""埋了忘回收=烂尾" — https://wangwen666.com/post/200.html
- webnovel-handbook——正典事实分级（已确认/候选/待确认/冲突/废弃/推断）+ 渐进式披露按卷隐藏/开放防提前剧透 — https://github.com/miserylee/webnovel-handbook
- 马良写作——渐进式披露：让 AI 写小说不再剧透的人物设定管理法（按卷隐藏与开放） — https://maliangwriter.com/blog
- 山音编剧 master——埋种/回调登记表逐条审计为反烂尾手段 — https://github.com/Shanyin-ai/shanyin-screenwriting-master
- 腾讯云《AI 长篇质量保证体系》——AI 自我一致性随篇幅衰减、伏笔后面忘、靠外部确定性校验不靠模型自觉 — https://cloud.tencent.com/developer/article/2650227
- prior-art（研究04·§3）——graphiti 双时态"只失效不删"+ point-in-time 查询 + 矛盾=LLM 出 idx/Python 区间失效；inkos 伏笔生命周期治理（准入拒绝无回收信号/重复家族 + `collectStaleHookDebt` 欠债逼还）；ExplosiveCoderflome `PayoffLedgerItem`(状态机+兑现窗口+overdue 报警) + `CharacterState`(`knownFacts`+`misbeliefs`) — `docs/research/04-github-prior-art-survey.md`
- 本 skill 调研：`docs/research/01-six-stream-findings.md`（伏笔6类/state账本/渐进式披露/正典治理/认知边界）
- oh-story-claudecode（MIT，github.com/worldwonderer/oh-story-claudecode）——§10/§11 的 craft 来源：`reversal-toolkit.md`（7 类反转 setup/reveal + 揭示位置 + 嵌套反转间隔递减 + 误导两路径 + 红鲱鱼铁律 + 打脸三方式）、`quality-checklist.md`（证据链完整性检查 + 五维评分 severity）、`plot-core-methods.md`（连续性追踪/谜语人 vs 伏笔/烧脑视角）。**仅吸收 craft 文本**，已为"长篇连载×按卷/arc"定位 ADAPT（全文 %→arc/卷进度、短篇分段→跨章/跨 arc），并全部挂回本 skill 既有 typed 契约（钩子4型/伏笔六类/`cognition`/emotion-debt/sao_schedule/FACTTRACK/`locked_reveals`），不引入其架构
- 对齐文件：`templates/foreshadow-ledger.yaml`（`type`/`planned_payoff_ch`/`status` 三态/`visible_payoff_volume`）、`templates/state-world.yaml`（`valid_from_chapter`/`valid_until_chapter`/`power_system.ladder`/`monotonic`）、`templates/state-characters.yaml`（`cognition`: knows/does_not_know/misbeliefs/reader_knows_char_doesnt）、`templates/contract-template.yaml`（`locked_reveals`/`meta.current_chapter`）、`templates/chapter-outline-template.json`（`due_foreshadows`/`forbidden_reveals`）、`scripts/state_check.py`（逾期 error / 临近·密度 warning / 阶位在表内）
