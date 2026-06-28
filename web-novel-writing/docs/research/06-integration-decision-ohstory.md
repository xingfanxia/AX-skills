# 借鉴裁决：oh-story-claudecode → web-novel-writing skill

> 日期：2026-06-27。来源：朋友推荐的 `github.com/worldwonderer/oh-story-claudecode`（MIT，commit 5498710）——
> 一个 13-skill 的中文网文创作 Claude Code 插件（扫榜/拆文/写作/审校/去AI味全流程），口碑「去AI味很有效」。
> 原始物料已存：`docs/research/external-ohstory-deslop/`（story-deslop SKILL + banned-words + anti-ai-writing + 3 JS 脚本 + PROVENANCE）。
> 本文回答用户的「**我们如何借鉴**」。分两部分：§1 去AI味（已落地）+ §2 其它模块（综合调研后）。

## 0. 总判断：借 craft 与检测逻辑，不搬插件架构

oh-story 是 **13-skill 插件 + hooks + CI + 多平台 adapter**；我的 skill 是**单 skill + agent 驱动 + 极小脚本**（豪子痛点正是「市面工具太重」）。所以借鉴原则：
- **吸收（INTEGRATE）**：可复用的 **craft 知识**、**确定性检测逻辑**、**具体词表/模式** → 并进我的 references/scripts。
- **改造（ADAPT）**：理念对、形态需改成我的单 skill 模型。
- **只引用（REFERENCE）**：整插件能力（扫榜浏览器自动化、多平台 adapter、封面生成）对单 skill 太重，致谢 + 指路，不搬。
- 我已有且更强的（Canon 五态/防泄漏编译/三桶框架/双时态状态）不动。

---

## 1. 去 AI 味（story-deslop）—— 已落地

朋友的核心推荐。story-deslop 是**我见过最成熟、demo 验证过的桶1+桶2 反 AI 味系统**。它不替换我的「三桶模型」（那是我的组织框架，桶3 网文专属轴=黄金三章/爽点密度/品类适配 是我的独有贡献，oh-story 没有），而是**把桶1/桶2 用它 battle-tested 的 Gate A-G + 词表 + 三遍法 + 确定性检测器灌满**。

### 1.1 已吸收进脚本（INTEGRATE，已测试）
| 借什么 | 来源 | 落到我的哪 | 状态 |
|---|---|---|---|
| 鲁棒 `不是A而是B`(★★★★★最毒) 检测——含 而是/，是/紧凑变体，排除 是不是/只是·可是·但是·还是·于是/不是A就是B/不是A也不是B/…是吗 | check-ai-patterns.js `findNotIsComparisons` | `antislop_lint.py` 移植为 `find_not_is()`（替换原脆弱 NEG_PARALLEL regex） | ✅ 9 例全过 |
| 弱化副词密度（微微/淡淡/缓缓/轻轻 >3/千字=AI 签名） | anti-ai-writing 模式2 | `antislop_lint.py` 密度门 | ✅ |
| 禁用词表（情态/表情/心理/判断/过渡/论文体/书面腔/万能结论 8 类） | banned-words.md | `antislop_lint.py` 加权桶（**不照搬 flat 罚分**——按词性进对应加权桶，避免「更是/不只是」误伤） | ✅ |
| 正文标点纪律（禁破折号 ——/—/--；省略号停顿 ……） | banned-words + SKILL 原则4 | `output_check.py` `punctuation_discipline` 硬门(破折号 blocker) + advisory(……) | ✅ |
| 工程词泄漏（细纲/卷纲/情节点/爽点/金手指…tier1 + 第X章/伏笔/读者 tier2） | check-degeneration.js | `degeneration_check.py`(新) + `output_check.py` LEAK_PATTERNS | ✅ |
| 模型退化检测（逐字复读/打转、中途截断、占位符/拒绝语、乱码） | check-degeneration.js | **新脚本 `degeneration_check.py`**（我原本完全没有这层；blocking=去AI味改不掉，回去重新生成那段） | ✅ dirty/clean 双测 |
| Gate G 解释腔/上帝视角/安排感（她不知道的是/殊不知/之所以/多年以后…最难察觉最像 AI） | anti-ai-writing 模式8 | `output_check.py` POV_INTRUSION 扩成 Gate G 词集（advisory 送 reviewer） | ✅ |
| `.deslop-whitelist` 白名单（豁免撞禁用词的世界观术语/绰号/专名） | story-deslop SKILL | `antislop_lint.py` + `output_check.py` 加 `--whitelist`；`templates/deslop-whitelist.example` | ✅（直接解掉早先评审 F7 的误报顾虑） |

### 1.2 待并进 references/09（INTEGRATE craft，docs 阶段做）
- **Gate A-G 七门体系** + **8 种 AI 写作模式检测** + **三遍法（去泛化/去书面化/回自然感，按轻中重分级）**：并进我的 09-anti-ai-slop.md 桶1/桶2（致谢 oh-story）。
- **自然文本 vs AI 味 8 维对照表**（段落/对话标签/情绪/比喻/语气词/省略/排比/结尾）+ **Show-Don't-Tell 表** + **改写范例库**（情绪外化/场景/打斗/结尾/震惊分层/对话五级递进）：极强的可操作 craft，并进 09。
- **叠加式描写（同一动作掰开写三遍：发生层→感知层→反应层）**：我没有的 AI 指纹，并进 09。
- **量化打分 6 指标**（禁用词密度/连续排比/心理词占比/对话标签密度/平均段落句数/重复描写密度，各带轻中重阈值）：比我现有更细的可机检 rubric，并进 04-review-rubric + 09。
- **关键调和（必须写清，否则自相矛盾）**：oh-story Gate C「心理外化」（"他很紧张"→"手在抖"）vs 我桶2「情绪/爽点直给」——**不冲突**：心理外化是**更强的直给**（身体动作比抽象情绪词更直接可感），桶2 反对的是把**爽点埋成文学潜台词**，不是反对外化。09 要明确：外化到动作 = 直给的落地形态；"把话说死"针对的是爽点的明确性，不是要求抽象情绪词。

### 1.3 不照搬（REJECT/REFERENCE）
- normalize-punctuation.js 的机械替换（——→句号）：**不收**。oh-story SKILL 自己强调破折号要「按功能改写」（打断→动作/拖长→省略/插入→逗号），机械一律改句号会破坏节奏。我的 `output_check` 只**报告** em-dash 让人/LLM 按功能改，不机械替换。
- 整个 story-deslop 作为独立 skill：不搬（我把去AI味做成本 skill §4 三桶 + 5 个脚本的一部分，不拆独立 skill）。
- 其 rubric 里**声明却没实现**的 reviewer（character_voice 有名无 code）：不抄——伪约束。我的 reviewer 是真 LLM 调用。

---

## 2. 其它模块借鉴（综合调研后补全）

> 跑了 7-agent 调研 workflow `ohstory-borrow-study`（6 路并行读 setup-craft / setup-infra / long-write / review / scan-analyze / short-import + 综合，1.27M token）。结论：oh-story 真正强在我**最弱的 craft 工艺层**；我强在它完全没有的**状态工程/防漂移/确定性校验/Canon 治理**。借鉴边界三层、不越界。

### 2.1 吸收（INTEGRATE/ADAPT craft → 现有 ref + ≤3 篇新 ref）
| 借什么 | 来源 | 落到我的哪 | 优先级 |
|---|---|---|---|
| **对话工艺**（对话长度=权力 ≤10/≥20字可机检 / 潜台词议程 / 弹幕递进三层 / 7维差异化+遮名识人 / 不当科普嘴）——我整套 skill 最干净的空白 | dialogue-mastery | **新 `references/12-dialogue-craft.md`** + reviewer dialogue_natural 子判据 | ★高 |
| **导入已有稿→结构化状态**——豪子头号痛点「已写几章在崩」**完全没入口** | story-import 反向骨架 + character-state 反向 6 步 | **新 `references/13-import-existing-draft.md`** + SKILL.md **阶段0.5**；用现成 degeneration_check 扫崩点；迁移终点=我的 templates | ★★最高 |
| **拆爆款学习法 + 选题决策法**（条件框架/抽象五步/可复现模块卡 EM-card 防抄袭边界 / 选题四步+样本<15不许给高） | story-long-analyze / scan | **新 `references/14-deconstruction-learning.md`** + `templates/benchmark-module-card.yaml`；数据由用户提供，**切断抓站耦合** | ★高 |
| **反转工具箱（7 型 typed + 揭示窗口 + 误导加/减法 + 红鲱鱼自身功能 + 无反转别硬塞）** + 推理一致性5类/证据链 | reversal-toolkit / plot-core-methods | enrich `references/08`（章纲加 reversal 字段；continuity-checker 输入规范） | ★高 |
| **情绪弧线/期待感管理**（6弧线 + 确定/不确定型期待 + 三层情绪分离 + 多线悬念周期）+ **章首钩子7式** + **二级装逼/震惊分层/舞台大小×高度** + 虐点三板斧 | emotional-arc / hooks-suspense / style-combat-face / hooks-chapter | enrich `references/07`（%→ADAPT 按卷/arc；保留我的钩子4型 typed 契约） | ★高 |
| **人物设计工艺**（三层标签反差 / 配角功能化白手套 / 金手指绑架人设 / 可原谅vs不可原谅错误 / 靠山过度反模式） | character-design-methods / relations | enrich `references/02`（对齐 behavior_anchors） | 中 |
| **开篇建构手册 + 剧情结构骨架 + 复仇打脸/女频爱情线 checklist** | opening-design / plot-core / genre-writing-formulas | enrich `references/05`（21 篇短篇 beat 不全搬，只取方法+差异表） | 中 |
| **平台核心取舍 + 留存代理指标 + 读者画像→爽点偏好** | genre-readers / quality-checklist | enrich `references/06`（留存指标标 advisory 不进硬门） | 中 |
| 句子级检测器（碎句号/长段落/字节地板）+ golden-fixture 回归 | check-ai-patterns / check-degeneration / test-ai-patterns | 已并进 `antislop_lint`/`degeneration_check` + 新 `test_lint_fixtures.sh`（直击豪子「误伤多」痛点） | ★已落地 |

### 2.2 明确 REJECT（这些正是豪子「太重」痛点，照搬=变成我要替代的那个东西）
- **13-skill 插件 + 25 篇 ref 并立形态** → 只吸收 craft 进现有 12 篇 + ≤3 篇新。
- **6 副本同名文件 + check-shared-files/regex-sync/prose-net-parity 等 parity CI** → 根因是它把检测正则手抄进 bash/codex/opencode 三处；**我单一事实源（逻辑只住脚本、hook 只 subprocess 调用，永不重抄正则）就永远不需要 parity 守卫**。当反面教材写进 scripts/README。
- **3-CLI adapter 部署**（codex .toml / opencode plugin.ts / openclaw / AGENTS.md.tmpl×3 / .story-deployed sentinel / 版本号 / check-*-adapter.sh）→ 单 skill 不背分发税。
- **story 路由 13-skill 分发器 + gh release 自更新 + 多书 .active-book 切换 + agent registry** → 我 Agent驱动/硬化双档已覆盖。
- **~2000 行平台 scrapers + browser-cdp 537 行 + 6-stage 并行 chapter-extractor** → 榜单/拆文数据由用户粘贴或用我已路由的 chrome-devtools-mcp/claude-in-chrome；skill 只消费不抓站。
- **story-review full/lean/solo 多模式 + 多 reviewer spawn 编排** → 我两个独立 LLM 调用（continuity + quality）已是正确粒度；只取 review-report 的 rubric_source/effective_reviewers provenance 字段。
- **hook 强制层**：唯一游走边界项。只取 Claude Code 单平台最小内核（可选 settings-hook + ~40 行 story_hook.py，**只路由、只调既有脚本**）合规；一旦抄它的 3-CLI 部署就越界，砍掉。本轮**记录不建**（默认 agent 驱动已能跑脚本）。

### 2.3 范围铁律（钉死风险）
**共享检测逻辑只住一处（脚本）、hook 只触发不重抄正则** → 永不需要 parity CI。任何引入「新 skill / 新 CLI adapter / 新抓站依赖 / agent registry / 多书切换 / 自更新版本号」的借鉴项一律 REJECT——这些是 13-skill 插件的分发税，不是单 skill 该背的。**校正**：6 路里约 1/3 的「高优先」（degeneration 全套 / not-is 加固 / Gate G POV / 弱化副词阈值）实测我已落地；真增量集中在 craft reference 侧（对话/导入/拆文/反转 typed/情绪弧/正向去味）+ 少数确定性小补丁。
