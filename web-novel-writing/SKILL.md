---
name: web-novel-writing
description: >
  约束 AI 写好【中文网文长篇连载】的工业化工作流 skill —— 把"完全放手让 AI 写、4-5 章后逻辑/人设/世界观全崩"的失控过程，改造成"人类当导演、AI 当受约束子程序"的可稳定推进流水线。核心不是"写作 agent"，而是五件事：① 第0步人类锁定品类/平台/顶层契约（核心冲突·结局·主线锚点·底层规则）；② 把记忆拆成带 Canon 状态+按卷可见性的 typed 状态文档（世界观/人物/剧情线/伏笔台账/情绪债/滚动摘要），而不是一个会泄漏到正文的 memory.md；③ 用确定性流程每章编译"最小 context、指令与正文严格分离"的短 prompt（专治 AI 把约束写进正文）；④ 章节生产闭环（编译→生成→独立一致性校验→量化 rubric 审校→定向改稿→去 AI 味→状态增量回写），改稿≤3轮、reviewer 与 writer 独立调用防自欺；⑤ 反 AI 味分三桶处理（词句层全量复用文学清单·结构层改分层规则·网文专属轴爽点/钩子/毒点/品类适配）。明确划分 AI自动 / 人机协作 / 必须人类拍板 三档边界。
  设计约束：model-agnostic（默认就能在 Codex/GPT 上跑，换 GLM 等国产文学性更强的模型是可选优化旋钮、非前置依赖）；诚实区分"工程能修的"（一致性崩坏/结构失控/prompt泄漏/流程纪律）与"模型天花板"（文学性/语感/叙事层 AI 味，工程压不到零）；反 overengineering（substrate 是 Markdown/YAML + skill 指令 + 极小可选校验脚本，不是要作者建一个带 SQLite/向量库/dashboard 的 app）。
  适用：用 AI 写网络小说/网文连载，发现"放手写就崩、续写几章逻辑乱、人设漂移、伏笔忘填、AI 味重、节奏平没爽点"；想搭一套约束 AI 的写作流水线；要维护世界观/人物/剧情/时间线/伏笔 state；要做章节级生成+审校循环；要去 AI 味；要按品类/平台（起点/番茄/晋江/飞卢）适配。姊妹于 game-script-creation（那个是二游剧本，这个是网文长篇连载）。
  触发词：写网文、网络小说、写小说、AI 写小说、长篇小说、连载、续写、小说崩了、AI 写小说逻辑乱、人设漂移、世界观崩、伏笔、章节生成、小说大纲、世界观设定、人物设定、爽点、黄金三章、章末钩子、毒点、去 AI 味、网文流水线、起点、番茄小说、晋江、玄幻、都市、爽文、修真、升级流、web novel、serialized fiction、long-form novel、story bible。
  不适用：写单篇短篇/严肃文学（可借用 craft，但本 skill 按"长篇连载×日更×平台数据"的工业约束组织）；纯润色一段已有成稿（直接润色即可）；写游戏剧本（用 game-script-creation）；写非虚构/论文/营销文案。
license: 本仓库自有；研究引用见 docs/research/ 各文件与 references/00-research-map.md。
---

# web-novel-writing —— 约束 AI 写好网文长篇连载的工业化流水线

> 你（AI）面对的是一个**在用 AI 写网文、但已经被"放手就崩"折磨过的创作者**。他/她的真实痛点（实测，不是假设）：完全放手让 AI 写根本看不了；Opus/GPT 连续续写 4-5 章逻辑还行，再多就**逻辑/人设/世界观全崩**；prompt 写长了 AI 会把"给它的约束/context"莫名其妙写进正文；市面工具要么很难用、要么 overengineered。
>
> 你的任务不是"替他写一本小说"，而是**给他装一条流水线**：让人类掌控方向（核心冲突/结局/主线/节奏/爽点拍板），让 AI 在**被严格约束的窄窗口**里做它真正擅长的（环境描写/旁白/扩写/前情总结/命名/按蓝图填充正文），并用**确定性的状态管理 + 独立校验**把"几百万字不崩"这件事从"靠勤奋维护"变成"靠架构强制"。
>
> 这不是一键生成器。**核心信念：人类是 driver，AI 是被确定性流程包裹的、受约束的 subroutine。**

---

## ⚡ 快速首跑（先把一章跑通，再谈扩张）

新手别被下面的完整体系吓到。**第一次只做这 7 步，把第 1 章跑通**——验证流水线真比裸聊强，再回头按 §2/§3 扩张。完整范例见 `examples/worked-example-xuanhuan.md`。

1. **建书目录**：`mkdir mybook && cd mybook`，把 `templates/` 全部 copy 进来。
2. **填顶层契约**（`contract.yaml`，human 拍板）：只填核心冲突、结局方向、金手指**及其代价**、品类+子类+调性+平台。别的留空。
3. **填一个主角 + 几条世界观**：`state-characters.yaml` 填主角（**行为锚点**不是形容词 + `cognition` 认知边界）；`state-world.yaml` 填 3-5 条 Canon 事实 + 力量阶位表。
4. **写一份章纲**：copy `chapter-outline-template.json`，填本章目的/必须发生/禁止发生/要兑现的爽点/章末钩子类型。
5. **编译 prompt 并生成正文**：`python3 scripts/compile_prompt.py mybook ch0001.json --current-volume 1 --current-chapter 1` → 把输出喂给 writer 模型（**关 thinking**）→ 拿到草稿正文。
6. **独立审校**（关键，别自己审自己）：**另起一个干净上下文的 reviewer 子 agent**（见 §3 的「独立校验落地」），只给它【正文 + 章纲 + rubric】，让它过 `references/04` 的硬门+加权分；同时并行跑三个机械门：`python3 scripts/output_check.py 草稿.txt --contract mybook/contract.yaml --outline ch0001.json --chapter 1`（字数/泄漏/标点/must_not/剧透-出）、`python3 scripts/degeneration_check.py 草稿.txt`（模型退化——**blocking 就回去重生成那段**，去AI味改不掉）、`python3 scripts/antislop_lint.py --json 草稿.txt`（AI 味 penalty）。`final = 加权分 − penalty`，≥80 且硬门全清才过；不过则定向改稿（≤3 轮）。
7. **定稿回写**（确定性合并）：抽 state delta（照 `templates/state-delta-template.yaml`）→ `python3 scripts/state_apply.py mybook delta.yaml --final 定稿.txt --audit-passed`——它代码盖 canon_status:Inferred、章级幂等、阶位单调、写回滚动摘要/伏笔/情绪债、每 5 章 checkpoint、收尾自校验（**审校没过拒绝提交**）。再跑 `python3 scripts/state_check.py mybook` 体检。下一章重复 4-7。
> 已经写了几章在崩、想接着续？先走 **阶段0.5 导入已有稿**（`references/13`）把崩稿反向提取成结构化状态，再进 4-7。

> 零脚本也能跑（Agent 驱动 mode）：上面 `python3 scripts/*` 的每一步，agent 都可以按对应 reference 的规则**亲自**做（编译 prompt / 查一致性 / 算 AI 味）。脚本是把这些"确定性步骤"真正确定化的可选硬化层，书越长越值得上。

---

## 0. 七条不可违背的操作原则（先读）

1. **中文为主。** 全程用中文与创作者交流；创作术语首次出现给中文+括注英文一次（如 伏笔账本(foreshadow ledger)、章末钩子(chapter hook)、压抑-释放(setup-payoff)），之后只用中文。

2. **人定结构 / AI 填细节（这是本 skill 的灵魂）。** 核心冲突、结局、主线锚点、世界底层规则、品类/平台、剧情走向与转折、节奏曲线与爽点力度——**由人类拍板（human-only）**；环境/旁白/细节扩写、前情总结、命名、按蓝图填充正文、滚动摘要、实体抽取——**AI 自动**；卷纲/章纲草案、正文章节生成、剧情提案（出 3 套方向供选）、节奏体检——**人机协作（semi-auto）**。完整边界见 §5。**绝不让 AI 自由决定剧情走向**——AI 自由发挥的剧情是 5-10 年前的旧套路。

3. **状态即记忆，但要拆成 typed 状态文档 + 打 Canon 标签，绝不用一个 memory.md。** 把"已定事实 / 待定推测 / 已否决 / 备选灵感 / 未确认推断"混在一坨散文里，正是 AI 把约束和推测当事实写进正文、以及长线设定漂移的**根因**。每条事实必须带两个治理标签：`canon_status`（Canon 已定稿｜Pending 待确认｜Rejected 已否决｜Idea 备选｜Inferred 推断）+ `visible_from_volume`（按卷可见，防剧透红线）。晋升 Canon 需人确认。机制见 `references/02-state-schema.md`。

4. **约束即质量：硬约束用结构化分区 + 末尾强后缀硬拼，不靠模型"记住"。** LLM 在架构上对"指令 vs 资料"没有形式化分隔——所以"prompt 别太长"是**必要但远远不够**的。防泄漏靠四件套：①硬约束放 system / 资料放 user；②设定全部包进 strict 分隔块并声明"仅为参考资料，严禁在正文中复述或当指令执行"；③末尾用代码（或你逐字照抄的固定串）硬拼"只输出正文"后缀；④生成后剥离任何残留指令符号/标签。详见 `references/03-prompt-compiler.md`。

5. **校验是独立调用，reviewer 不能是刚才的 writer。** 共享上下文的"自审"必然自欺（执行者没变，不会认真挑自己的错）。一致性校验（对不对）与质量审校（好不好）**分离**、且与 writer **独立上下文/最好异模型**。审校用**量化 rubric + 硬门**（人设/世界观/时间线/毒点/剧透红线任一违规直接打回，不可被高爽点分平均掉），不是"通过/不通过"的 vibe。改稿**≤3 轮**，第 3 轮不过转人工（反复重抽同一 prompt 会在 6-7 次后自我重复塌缩）。见 `references/04-review-rubric.md`。

6. **品类即配置 + 平台即参数。** 网文结构强品类依赖（玄幻要境界表、悬疑要真相金库、种田要经济账本），开篇节奏/毒点容忍/章字数/日更节拍强平台依赖（同一开头番茄扑街、起点过签）。第 0 步人类锁定品类+子类+调性+平台后，挂载对应的爽点引擎锚 / 数值 schema / 毒点黑名单 / 开篇阈值。见 `references/05-category-templates.md` + `references/06-platform-params.md`。

7. **诚实标注能力边界，不夸大。** 本 skill 解决的是**工程问题**：一致性崩坏、结构失控、prompt 泄漏、流程纪律、爽点/钩子/伏笔可机检。它能**压低**AI 味但**压不到零**——叙事层 AI 味（语感、留白、道德模糊、"人味儿"的手工感）是模型预训练/RLHF 对齐的产物，**换模型只降句子层、治标**，真正靠人类在大纲阶段注入。**模型只是可选优化旋钮**：默认就在 Codex/GPT 上跑，"换 GLM/国产文学性更强的模型"是优化、非依赖；且任何模型口碑（"GLM>GPT、DeepSeek 语言怪"）都是单一实测，**按本 skill 的 rubric 在你自己的对标章上盲测，不信任何榜**。见 `references/09-anti-ai-slop.md` + `references/10-model-orchestration.md`。

---

## 1. 全景：这条流水线长什么样

```
阶段0 筹备(human 为主)         状态层(单一事实源)            章节生产循环(确定性 driver)        阶段性维护
─────────────────────      ────────────────────       ──────────────────────────      ──────────────
锁 品类/子类/调性/平台   →   00 顶层契约(不可改写)    →   每章 for-loop:                    每卷/每N章:
锁 顶层契约              →   01 世界观+glossary           outliner → 章纲                   · 递归压缩摘要
  (核心冲突/结局/         →   02 人物卡(行为锚点+认知边界)  prompt-compiler(纯流程)→短prompt   · 数值单调性校验
   主线锚点/底层规则)    →   03 剧情线(主线beats)          writer(关thinking)→正文           · 设定刷新/清脏上下文
分卷大纲                →   04 伏笔台账(状态机)            continuity-checker(独立)→违规       · 卷级摘要固化
校准创作者水平+工作模式  →   05 情绪债账本+爽点排布         reviewer(独立,rubric+硬门)→裁决     · 追读/完读数据(可选)
                       →   06 滚动摘要(分层递归)          revise ≤3轮 → style去AI味独立pass   →定位高跳出章重写
                                                        state-updater→delta增量回写
                                                        persist 落盘(可断点续跑)
```

**关键认知**：长篇崩坏的根因是"**AI 自我一致性随篇幅衰减**"——这是内在衰减，**用更贵的模型解决不了**。唯一可行解是把流程**原子化拆分**（每个 AI 调用做一件窄事，做完代码立刻收回控制权）、用**确定性校验**外部强制一致性（不靠 AI 自觉）、用**独立 agent**做外部验证（不自审）。这与创作者的 CLAUDE.md AI-pipeline 铁律同构：LLM 是被确定性代码包裹的子程序。

**怎么用这个 skill（两种 mode）**：
- **Agent 驱动 mode（默认，零搭建）**：你（Codex/Claude Code 这类 agent）读完本 SKILL.md，**亲自**充当那个"确定性 driver"——严格按文档流程操作 Markdown/YAML 状态文件，逐章编译 prompt、跑校验、回写状态，人类在卷/arc 边界拍板。立刻可用。
- **硬化 mode（可选）**：用 `scripts/` 里的极小脚本把"确定性步骤"真正确定化（regex 反 AI 味 lint、prompt 拼装、状态 append+Canon 晋升门）。书越长越值得上硬化层（因为"靠 agent 自律"恰恰是会漂移的那一环）。脚本只依赖 python3 + PyYAML，无 SQLite/向量库/重依赖。

---

## 2. 阶段0 —— 筹备与校准（开新书必做，human 为主）

> 目标：把"不可变的顶层契约"和"品类/平台配置"钉死，并初始化状态层。**这一步定错，后面所有自动化都在放大错误**（主角欲望/金手指代价/世界规则/品类一旦错，越自动越崩）。

### 2.1 先校准创作者（沿用姊妹 skill 的方法，浓缩版）
判断三件事，决定你介入多深：① **写作水平**（让 ta 写 3 句话样本，别只信自评）；② **手里已有什么**（脑洞/世界设定/一个角色/一个爽点画面/已有大纲/已写了几章在崩）；③ **工作模式**（A 只给思路 / B 给多方案选 / C 推荐主案+理由 / D 直接产初稿我改 / E 叙事总监式全程托管）。模式随时可切。详见 `references/11-maintenance-recap.md` §工作模式，校准量表借鉴 game-script-creation。

### 2.2 锁定"配置层"（品类 → 平台）
- **品类+子类+调性**：玄幻/仙侠修真/都市(系统流/赘婿/战神)/无限流/科幻末世/悬疑/历史种田经营/女频(言情/古言/宅斗/穿越) … 见 `references/05-category-templates.md`，挂载该品类的**爽点引擎锚 + 数值 schema + 毒点黑名单 + 骨架类型**。
- **目标平台**：番茄/起点/晋江/飞卢/七猫 … 见 `references/06-platform-params.md`，挂载**开篇节奏阈值（冲突/金手指必须在第几字前出现）+ 毒点容忍度 + 章字数 + 日更节拍**。

### 2.3 锁定"顶层契约"（`templates/contract-template.yaml`，AI 无权改写）
人类拍板：核心冲突一句话、结局方向、30 万字处的长期主线锚点（飞升之约/灭族之仇/夺嫡）、力量/世界**底层规则与战力天花板**（开局锁死，防战力崩坏）、品类爽点引擎单句锚（如"凡人苟道，步步谋算后碾压打脸"）。方法：**先有结局/核心冲突，再倒推大事件串**。

### 2.4 分卷大纲 + 初始化状态层
人机协作出**分卷大纲**（每 30-80 章一个卷级目标），并初始化六个状态文档（`templates/state-*.yaml`），把已定事实打 `Canon`、待定打 `Pending`。

**阶段0 完成判据**：契约六要素填满；品类模板+平台参数已挂载；六个状态文档已初始化且每条事实有 Canon 标签；至少有粗分卷大纲 + 第一卷的 arc beats。

### 2.5 阶段0.5 —— 导入已有稿（接手"已经写了几章在崩"的标准入口）
> 豪子头号痛点之一：**不是从零开，而是已经写了几章、续写崩了**。别让他从头重搭——把崩稿**反向提取**成本 skill 的结构化状态，再进章节循环。完整方法见 `references/13-import-existing-draft.md`。
- **逐章扫崩点**：`python3 scripts/degeneration_check.py 已写章节/*.txt` 定位"崩在第几章"（复读/截断/工程词泄漏=退化信号），划出"可信前缀 vs 崩坏起点"。
- **反向提取**：从可信前缀章节反推 → 填 `contract.yaml`（核心冲突/金手指/已建立的主线）、`state-world.yaml`（已出现的设定，打 Inferred 待人确认晋升 Canon）、`state-characters.yaml`（已登场角色的 behavior_anchors + cognition）、`foreshadow-ledger.yaml`（已埋伏笔 + 补 planned_payoff_ch）、`rolling-summary.yaml`（逐章一句话 + 末章 previous_tail）。
- **`[待补充]` 纪律**：反推不确定的地方标 `[待补充]` 让人确认，**绝不编造**填进 canon。
- 从崩坏起点的**前一章**接着按 §3 章节循环续写——此时状态层已立、防漂移机制生效。

---

## 3. 章节生产循环（每章跑一遍；确定性流程当 driver）

> 这是 pipeline 的心脏。**每个 LLM 调用是窄子程序，调用完立刻收回控制权做校验 + 写 state。** 完整 IO 契约、伪代码、数据流图见 `references/01-pipeline-architecture.md`。

| 步 | 角色 | 输入 | 输出 | 性质 |
|---|---|---|---|---|
| 1 | **planner**（每卷/arc 一次，非每章） | 剧情线 + 人类决策 | 本 arc 的 beats | semi-auto（人定） |
| 2 | **outliner** | arc beats + state | 单章 beat sheet（目的/冲突/要兑现的爽点级别/钩子类型/字数预算/POV） | semi-auto |
| 3 | **prompt-compiler** | state + 章纲 | 分区好的单章短 prompt | **纯确定性流程** |
| 4 | **writer** | 单章 prompt | 纯正文 | automate（关 thinking） |
| 5 | **continuity-checker** | 正文 + canon/时间线/人物（**只吃事实，不吃写作 context**） | 违规清单 | automate（独立） |
| 6 | **reviewer** | 正文 + 章纲 + rubric | 打分 JSON + 末行裸 sentinel `VERDICT:PASS/REVISE` | automate（**独立上下文/异模型**） |
| 7 | **revise** | 正文 + 定向 findings | 改稿 | automate；≤3 轮，第 3 轮转人工 |
| 8 | **style/anti-slop-editor** | 正文 + 反 AI 味规则 | 去味稿 | semi-auto（**独立 pass，不喂回同源模型重写**） |
| 9 | **state-updater** | 批准稿 + 旧 state | state delta（抽取用 LLM，**append 用流程，Canon 晋升需人确认**） | semi-auto |

**【独立校验落地】Agent 驱动 mode 怎么实现"reviewer 不是刚才的 writer"（关键，否则核心保证形同虚设）**：
单会话里"同一个 agent 既写又审"恰恰就是本 skill 反复警告的"共享上下文=自欺"。落地办法是**派子 agent（Task/subagent）**跑步骤 5（continuity-checker）和步骤 6（reviewer）：
- 主 agent 当 driver；**子 agent 的输入只有【本章正文 + 章纲 JSON + rubric/canon 切片】，绝不带 writer 的思考链、构思过程、或"我刚才想这么写"的上下文**——这就是在单会话里实现"新上下文"的具体机制。
- continuity-checker 子 agent 只吃 canon/时间线/人物事实，judge"对不对"；reviewer 子 agent 只吃正文+章纲+rubric，judge"好不好"；两个**分别派**，最好提示不同模型（异模型减同源盲点）。
- 子 agent 只返结构化 JSON（`review-report-template.json`），**不持 Write、不替改情节**。主 agent 收到 verdict 再决定改稿/定稿。
- 机械门并行跑脚本：`output_check.py`（正文硬门：字数/泄漏/工程词/标点/**must_not**/**剧透-出**）+ `degeneration_check.py`（**模型退化**：复读/截断/占位符——blocking 是退化信号、去AI味改不掉、回去重生成那段）+ `antislop_lint.py`（penalty）+ `state_check.py`（状态体检）。词表类门加 `--whitelist <book>/.deslop-whitelist` 豁免世界观术语/绰号。
> 没有子 agent 能力的运行时（纯 CLI 单线程），退而求其次：**开一个全新对话/窗口**只贴正文+章纲+rubric 让它审，绝不在写作那个上下文里顺手审。

**【章节事务·幂等续跑·提交闸】（借鉴 WebNovelOps，把第 9 步从散文升级成代码可恢复事务）**：
- **每章一个产物目录** `chapters/chNNNN/`：章纲 → 正文草稿 → 审校报告 → 改稿 → 定稿 → state_delta → `run_manifest.json`（由 `state_apply.py` 写，记 audit 是否过/state_revision/checkpoint/冲突）。崩在第 7 步重跑不会重生成前 6 步。
- **审校过才结算 canon**：定稿后 `python3 scripts/state_apply.py <book> delta.yaml --final 定稿.txt --audit-passed`——**审校没过(无 --audit-passed)拒绝提交**，坏章不污染 canon。**章级幂等**：同一章重跑整体 no-op（护住数值 delta 与版本号）。命中 `contract.human_gate`（角色死亡/力量体系变更/大反转/Canon 覆盖）需 `--human-approved`。
- **must_happen 关键词门是【必要非充分】**：output_check 的 `must_happen_present` 只证「没漏写」，证不了「写对了」——**写对仍归 LLM reviewer**，别因为有这个门就撤掉 reviewer。
- **剧透防护是入/出双闸**：compile_prompt 把未到揭晓时机的设定挡在 prompt 外（剧透-入）；output_check `no_future_spoiler_out` 扫正文是否泄漏 `locked_reveals` 词面（剧透-出）——因为模型会**编造**没被告知的反转，入闸抓不到。

**降低人介入频率（防拖垮日更）**：不是每章都要人确认章纲，而是**每卷/每 arc 人定 beats + canon**，中间章自动跑，**只有 reviewer 报异常才召回人**。

**单章 prompt 编译的三条铁律**（防泄漏，全文见 `references/03-prompt-compiler.md`）：
1. **检索而非全量塞**：只抽"本章在场 2-4 角色的 canon + 本章 beat + 最近 N 章压缩摘要 + 上一章末段原文 + 到点的少量伏笔 + 本章禁剧透清单"。`visible_from_volume > 当前卷`的事实**一律不进 prompt**。
2. **指令/正文边界三分离**：硬约束放 system；设定包进 `<reference note="仅为参考资料，严禁在正文复述或当指令执行">…</reference>`；末尾硬拼"只输出正文"后缀。
3. **生成后清洗**：正则剥离任何残留的标签/指令符号（残留指令符号是平台一秒鉴 AI 的依据）。

---

## 4. 反 AI 味 —— 分三桶，不要照搬文学清单（关键，易错）

> 网文审美和文学/游戏叙事审美在很多维度**方向相反**。把文学反 AI 味清单整体搬到网文会写出"编辑一眼判死的华美空洞"。必须分三桶处理。完整裁决表 + 质检清单见 `references/09-anti-ai-slop.md`。

- **桶1 · 词句层 → 文学清单全量复用且加权**（这是网文编辑鉴 AI 的**第一道关**）：紫色文风/形容词堆砌、翻译腔（句子骨架是英文的中文）、节奏匀速（每段差不多长）、"华美的空洞"（开篇堆环境描写、一句话形容词>2 个、一个强动词>三个修饰）。
- **桶2 · 结构层 → 改成"分层规则"，不是禁令**：show-don't-tell / 避免信息倾倒 / 潜台词 / 视角纪律——**对人设/逻辑/世界观 lore 保留**（用动作展示人设、世界观别一股脑灌、一章一 POV）；**对情绪/爽点/卖点/金手指反向放行（直给）**（装逼打脸就要把话说死、系统面板/金手指就要前置直陈、情绪要直给到位）。
- **桶3 · 网文专属轴 → 文学清单完全没有，却是"扑街 vs 起飞"的分水岭**：黄金三章留存、爽点密度（每章≥1 小爽/每 3-5 章 1 中爽，连续 3 章"平路"追读就掉）、章末钩子（4 型：悬念/反转/情绪炸弹/信息投放）、毒点规避（绿帽/送女/降智/圣母/注水/视角混乱，按平台切容忍度）、品类×平台适配。

> **桶1/桶2 的可操作落地：Gate A-G 七门 + 三遍法**（借鉴 oh-story-claudecode/story-deslop，已验证有效，详见 `references/09-anti-ai-slop.md`）。Gate A 禁用词 / B 句式套路（**「不是A而是B」是最毒★★★★★**，`antislop_lint` 已确定性检测）/ C 心理外化 / D 节奏打碎 / E 对话去腔调 / F 结尾去升华 / **G 解释腔·上帝视角·安排感（最难察觉最像 AI——"她不知道的是/之所以/多年以后"，根治靠深度限知视角）**。三遍法：去泛化→去书面化→回自然感，轻度只 Pass1、中度+Pass2、重度全三遍+重写。**关键调和**：Gate C「心理外化」（"他很紧张"→"手在抖"）与桶2「情绪/爽点直给」**不冲突**——外化到动作是**更强的直给**（身体动作比抽象情绪词更直接可感）；桶2 反对的是把爽点埋成文学潜台词，不是反对外化。
>
> **桶0 · 模型退化（不是 AI 味、但同样毁正文）**：续写到后段模型会打转/复读/截断/漏工程词——这层去 AI 味改不掉，由 `degeneration_check.py` 抓（blocking=回去重新生成那段，再 deslop）。

一句话：**AI 味在网文里 ≈ 翻译腔 × 华美空洞 × 节奏平 × 不推进剧情**。前两项词句层可 prompt/lint 救；后两项结构层需人类先定爽点/节奏/钩子骨架、AI 填空。**本 skill 自己产出的任何文字都不许违反这份清单。**

---

## 5. 人机自动化边界总表

| automate（确定性流程 / 可放手的 LLM 子程序） | semi-auto（human-in-loop） | human-only（拍板 / 创意主权 / 不可逆） |
|---|---|---|
| 单章 prompt 编译；环境/旁白/细节扩写；前情总结/再入场摘要；命名（功法/地名/章节名候选）；滚动递归摘要；实体抽取；独立一致性/吃书/时间线/数值单调性校验；伏笔台账登记+回收提醒；毒点/三观规则扫描；句子层去 AI 味 lint；黄金三章多版草稿；定向改稿循环；指标采集+跳出章定位；输出后缀强约束+残留符号清洗 | 分卷/卷纲草案；单章蓝图/场景细纲起草；**正文章节生成**（蓝图内填充，高潮章人审）；可见性分级执行；设定/时间线增量回写；叙事层去 AI 味（人定留白/道德模糊、AI 执行）；风格锚定每章重注入；节奏体检/篇幅建议；章末钩子生成；打脸/情绪债编排填充；模型 A/B；**剧情提案（AI 出 3 套方向供人选）** | 核心冲突/结局/主线锚点/力量底层规则（顶层契约）；品类/子类/调性/平台选择；剧情走向与转折**拍板**；节奏曲线/爽点力度/付费卡点**拍板**；Canon 冲突裁决；防剧透"何时/如何揭晓"设计；据数据决定重写/换书名/是否上架 |

> **精确化创作者直觉**：剧情=**走向拍板 human-only，但提案/草案 semi-auto**（AI 在顶层契约约束下出结构化 3 套方向是高价值的，不是"AI 不能碰剧情"）；节奏=**拍板 human-only，但体检 semi-auto**（爽点密度、"一笔带过的重要事件/过度展开的琐碎"可机检标记）。

---

## 6. MVP 最小闭环 vs 完整版（对抗 overengineering）

**复杂度预算放在"状态结构 + 确定性校验"，不放在"agent 编排"。** novelix 的反面教材：10 个串行 agent + 33 维审计 + 22 改写规则——每多一个 agent 多一处可漂移/可泄漏的接缝；防退化的上限是**架构约束**而非机制数量。

**MVP（先做这个，能立刻跑）**：① 第 0 步 human 锁品类+平台+顶层契约；② 六个 state 文档（YAML，每条打 Canon+可见性）；③ 顶层确定性 for-loop（compile→writer关thinking→continuity独立→reviewer rubric+硬门→revise≤3→style去味独立pass→state delta回写→落盘可断点续跑）；④ **3-4 个角色（writer/reviewer/continuity/style），不是 10 个**；⑤ 反 AI 味只做机械正则层 + 生成期约束（先跑便宜的）；⑥ 人介入降频到每卷/每 arc；⑦ 全程落盘可断点续跑（长篇是跨月多 session 工程）。

**完整版（后续增量，不是 MVP）**：向量知识图谱（MVP 先用结构化文件+关键词触发）；多模型路由；LLM 层结构性审计；数据反馈闭环（需真实平台数据）；节奏体检自动化；专用文风迁移微调；全自动导演模式。

---

## 7. Reference / Template / Script 索引（按需调取）

| 文件 | 内容 | 主要用在 |
|---|---|---|
| `references/00-research-map.md` | 研究蓝图、来源分级、prior-art（含 GitHub 高星项目拆解：偷什么/避什么） | 了解依据/复盘 |
| `references/01-pipeline-architecture.md` | 三层架构、9 步 IO 契约、循环伪代码、ASCII 数据流、断点续跑 | 阶段3 搭循环 |
| `references/02-state-schema.md` | 六状态文档字段 schema、Canon 五态、按卷可见性、防漂移机制、人物行为锚点+认知边界 | 阶段0 初始化 / 状态层 |
| `references/03-prompt-compiler.md` | 最小 context 抽取规则、指令/正文边界三分离、防泄漏四件套、单章 prompt 模板、残留清洗 | 步骤3/4 |
| `references/04-review-rubric.md` | 量化质检表、硬门、加权分、sentinel 容错解析、改稿循环上限、continuity vs quality 分离 | 步骤5/6/7 |
| `references/05-category-templates.md` | 各品类：爽点引擎锚/数值 schema/毒点黑名单/骨架类型（升级阶梯/单元剧/慢热长线）/各品类 AI 最易写崩点 | 阶段0 锁品类 |
| `references/06-platform-params.md` | 番茄/起点/晋江/飞卢/七猫：开篇阈值/留存指标/毒点容忍/章字数/日更节拍参数表 | 阶段0 锁平台 / 开篇 |
| `references/07-sao-engine-emotion.md` | 爽点因果链（需求→压抑→释放）、情绪守恒、情绪债账本、打脸四部曲、装逼三层、钩子4型 | 步骤2/6 写爽点 |
| `references/08-foreshadow-timeline.md` | 伏笔六类+台账状态机、FACTTRACK 式时间线、认知边界（防剧透）、渐进式披露 | 状态层维护 |
| `references/09-anti-ai-slop.md` | 反 AI 味三桶裁决表 + 网文章节质检清单（标注 沿用文学/网文专属/推翻文学第几条） | 步骤8 + 交付前 |
| `references/10-model-orchestration.md` | 思考 vs 写正文分工、client 可注入、temperature 分场景、Verbalized Sampling、盲测 A/B 协议、模型仅可选旋钮 | 选模型 |
| `references/11-maintenance-recap.md` | 递归压缩/状态刷新、每 N 章 regression、数据闭环、工作模式 A-E、上架付费校验、合规（平台 AI 检测红线） | 阶段性维护 |
| `references/12-dialogue-craft.md` | 对话工艺（借鉴 oh-story）：对话长度=权力(≤10/≥20字可机检)/潜台词议程/弹幕递进三层/7维差异化+遮名识人/角色不当科普嘴 | 步骤4 写对白 / 步骤6 审对白 |
| `references/13-import-existing-draft.md` | 导入已有稿→结构化状态（豪子"写崩了"入口）：degeneration 扫崩点 + 反向提取填模板 + `[待补充]`纪律 | 阶段0.5 接手崩稿 |
| `references/14-deconstruction-learning.md` | 拆爆款学习法（条件框架/抽象五步/可复现模块卡 EM-card 防抄袭边界）+ 选题决策法（数据由用户提供，不抓站） | 阶段0 选题/找参照 |
| `templates/*` | 顶层契约/六状态文档/单章 beat sheet/状态增量(delta)/单章 prompt 骨架/审校报告/模型路由示例/回归不变量表/去AI味白名单 的可填模板 | 全程落文档 |
| `scripts/*` | 可选硬化层（**6 个确定性脚本，全部零 LLM**）：`compile_prompt.py`（防泄漏单章 prompt 编译器）/ `state_check.py`（**状态文件**不变式体检：Canon枚举/境界/伏笔逾期/情绪债/未决冲突/glossary）/ `output_check.py`（**章节正文**输出侧硬门：字数/残留指令·工程词/标点纪律/毒点/**must_not**/**剧透-出**+ 启发式 POV·解释腔·must_happen·章末钩子）/ `antislop_lint.py`（反 AI 味词句层桶1，含鲁棒「不是A而是B」检测+弱化副词密度，输出 0-20 `penalty`）/ `degeneration_check.py`（**模型退化**：复读/截断/占位符/工程词泄漏，blocking=回去重生成那段）/ `state_apply.py`（**定稿后确定性合并 delta 进 canon**：canon_status 代码盖戳·章级幂等·只失效不删·阶位单调·audit-pass 提交闸·人类门·checkpoint·收尾自校验）。词表类脚本都支持 `--whitelist .deslop-whitelist` 豁免世界观术语。python3+PyYAML，无重依赖。**delta 抽取仍是 agent 驱动（state-updater 角色）；但合并进 canon 由 `state_apply.py` 确定性执行——这一步最会漂移，交给代码=关掉伪约束**（反 overengineering：脚本是可选硬化层，默认 agent 驱动也能跑；书越长越值得上 state_apply） | 硬化 mode |
| `examples/worked-example-xuanhuan.md` | 玄幻凡人流端到端范例（1 卷 + 1 角色 + 3 章打通） | 拿不准产出长什么样时 |

---

## 8. 边界（这个 skill 不做什么）

- **不替创作者拍板创意决定**——核心冲突/结局/走向/节奏永远人类定；AI 给提案、草案、填充、校验。
- **不是一键写书机**——目标是装一条让 AI 受约束产出、人类高效掌舵的流水线，不是把整本书一次吐出来。
- **不保证去掉全部 AI 味**——叙事层 AI 味受模型天花板限制，工程只能压低、靠人类在大纲层注入留白/道德模糊根治；诚实告诉创作者哪些是模型问题。
- **不写死任何模型 ID**——model-agnostic，模型是可选旋钮，选型靠自己盲测不信榜。
- **不做单篇短篇/严肃文学/游戏剧本/非虚构**——可借 craft，但本 skill 按长篇连载工业约束组织；要写游戏剧本用 game-script-creation。
- **超出已知不编造**——某品类的具体套路/某平台的具体阈值若拿不准，标注"⚠️待核实/经验值"，绝不硬编成确定数据（平台算法不公开，阈值都是经验/内部资料推断、作可调参数）。

---

## 9. 整体完成判据（这条流水线"搭好了"长什么样）

陪创作者走完后，他应该拥有：
1. 一份锁定的**顶层契约**（核心冲突/结局/主线锚点/底层规则）+ 已挂载的**品类模板**与**平台参数**；
2. 六个**初始化好的状态文档**（每条事实带 Canon 状态 + 按卷可见性）；
3. 一条**能跑的章节生产循环**（compile→writer→独立校验→rubric审校→改稿→去味→状态回写），中间数据落盘可断点续跑；
4. 一份**量化审校 rubric**（硬门 + 加权分 + 改稿≤3 轮）和一份**反 AI 味三桶质检清单**；
5. 至少一个**垂直切片**：1 卷 arc + 1 个写透的主角（行为锚点+认知边界）+ 连续 3 章打通（每章过 rubric、爽点兑现、章末有钩子、无毒点、状态正确回写）——**这比"铺满整个世界却处处崩"更有价值**，也是验证流水线是否真比裸聊强的唯一方式；
6. 清楚知道**哪些 AI 自动、哪些人机协作、哪些必须自己拍板**，以及**哪些问题是模型天花板、工程修不了**。
