# 集成裁决：WebNovelOps（另一 agent 的可运行交付物）→ web-novel-writing skill

> 日期：2026-06-27。来源：另一个 agent 独立交付的 `webnovel_ops`（可 pip 装的 Python CLI 包 + 2 章完整 demo 跑通 + pytest 9 项全绿）。
> 原始物料已存：`docs/research/external-webnovelops-deliverable/`（`code-v0_1/` 源码 + `demo-final/` 跑通产物 + `test_report.txt`）。
> 本文是**逐项 INTEGRATE / ADAPT / REJECT 裁决**，是后续改动的依据。

## 0. 最重要的事实：两个 agent 独立收敛到同一架构

两份工作**互不可见**，却都得出：

| 共识点 | 我的 skill | WebNovelOps |
|---|---|---|
| 长篇崩坏根因 = AI 自我一致性随篇幅衰减，贵模型修不了 | ✅ README 明写 | ✅ README 明写 |
| 记忆 = 文件化 typed 状态账本，不是会泄漏的 memory.md | ✅ 7 YAML 文档 | ✅ config/bible/plan/state JSON 账本 |
| 确定性 context packer，**未来剧透绝不进 writer 上下文** | ✅ compile_prompt.py | ✅ context.py（且单测保证） |
| LLM 绝不直接覆盖 canon，只能提交结构化 delta | ✅ §3 第 9 步 | ✅ apply_state_delta 唯一提交路径 |
| 章节闭环：编译→生成→审校→定向改稿→状态结算 | ✅ 9 步表 | ✅ run_chapter 流水线 |
| inkos 是头号 prior-art；拒绝 10-agent/向量库 overengineering | ✅ 04-github-prior-art | ✅ GITHUB_RESEARCH.md |
| 反 AI 味词表 + 审校 rubric | ✅ antislop_lint + 04-rubric | ✅ ai_smell_lexicon + rubric.json |

**结论**：架构本身被独立复现 = 强信号它是对的。集成不是「推翻重来」，而是**把两边各自更强的那一轴嫁接到一起**：
- 我更强在**叙事/知识层**（Canon 五态 + 双时态可见性、反 AI 味三桶、12 篇 craft 知识库、认知边界/misbeliefs）。
- 它更强在**可执行状态机层**（幂等章节事务、**编码化的 state_delta 合并代数**、**acceptance_criteria 带显式关键词**= 确定性判分桥、provider 抽象、整树 schema 校验）。

我的 skill 终审时自曝的头号反模式是**伪约束**（把硬约束写进 prompt 当已执行）。WebNovelOps 恰好把我留给 agent 自律的那几步**真正代码化**了——尤其是 state 变更，这正是最会漂移的一环。所以集成主线 = **拿它的「可执行硬化」补我的「伪约束缺口」，用我的「叙事架构」校验它的「扁平 schema」**。

---

## 1. 逐项裁决

### ✅ INTEGRATE-1 ｜ `acceptance_criteria` 带显式关键词（**最高价值**）
**它做了什么**：`intent.json` 里每条 must_happen 配 `{requirement, keywords}`，每条 must_not 配 `{requirement, forbidden_keywords}`；audit.py 据此**确定性**核验——所有 keywords 在正文出现 → must_happen 达成；任一 forbidden_keyword 出现 → must_not 违反（blocker）。
**为什么收**：这是把「验收标准」变成「确定性判分器」的**具体桥**（正是 CLAUDE.md「convert acceptance criteria into deterministic graders」原则）。我的 skill 谈 acceptance_criteria 但没给这个可执行形态——`output_check.py` 因此无法真正核验 must_happen/must_not，只能靠 reviewer LLM。这是我伪约束缺口的直接堵法。
**落地**：
- `templates/chapter-outline-template.json` 增 `acceptance_criteria` 块。
- `scripts/output_check.py` 增两个硬门：`must_happen_present` / `must_not_absent`（读 outline.acceptance_criteria）。

### ✅ INTEGRATE-2 ｜ 编码化的 `state_delta` 合并代数 + 幂等（**最高价值，最大工程缺口**）
**它做了什么**：`state.py::apply_state_delta` 把「定稿→回写状态」做成代码：按 id 幂等去重（事件/钩子/bug 重跑不重复）、结构化操作（character_changes 的 set/add/remove、resource_changes 的 set/delta/add）、钩子生命周期状态机（opened/advanced/closed + 章号）、canon_version 单调自增、每 5 章 checkpoint 快照、`compact_state` 只快照不删（= 我的「只失效不删」）。
**为什么收**：我的 skill 把「回写 delta」描述成 agent 步骤——而这恰恰是**最会漂移**的一步（agent 手动 merge YAML 极易重复/丢钩子/忘 bump 版本）。把它代码化 = 关掉 state-mutation 侧的伪约束。
**落地**：写第 5 个硬化脚本 `scripts/state_apply.py`，**借它的合并代数、适配我的 schema**（Canon 五态 + valid_until_chapter + visible_from_volume；YAML 而非 JSON；伏笔台账状态机对齐我的 foreshadow-ledger）。幂等 + checkpoint + 版本自增照搬。

### ✅ INTEGRATE-3 ｜ 章末钩子「尾段关键词」确定性核验
**它做了什么**：audit.py 取 `ending_hook` 的关键词，检查它们出现在正文**最后 300 字**内，否则 blocker（ENDING_HOOK_MISSING）。
**为什么收**：章末钩子是网文追读的命脉，我之前只在 rubric 里软评。把「钩子必须落在尾段」变确定性硬门，便宜且强。
**落地**：`output_check.py` 增硬门 `ending_hook_in_tail`（读 outline.ending_hook.text 的关键词）。

### ✅ INTEGRATE-4 ｜ 章节「事务」+ 幂等续跑 + run_manifest
**它做了什么**：`pipeline.py::run_chapter` 每个产物 load-if-exists-else-generate（intent/beat_sheet/draft 存在就读，不存在才生成）→ 可安全重跑/续跑；末尾写 `run_manifest.json` 记录本章所有产物路径 + audit 是否过 + 是否 commit。
**为什么收**：把「章节生产闭环」从一串叙述步骤升级成**可恢复事务**——崩在第 7 步重跑不会重生成前 6 步。run_manifest 给每章一个可审计快照。这与我 workflow.md 的「per-chapter 可恢复」一致。
**落地**：SKILL.md §3 章节闭环补「事务/幂等续跑」语义 + 约定每章目录产物清单（含 run_manifest）。**不强制脚本**（agent 驱动默认即可遵循该约定），但 state_apply.py 的 commit 走「audit 过才提交」硬门。

### ✅ INTEGRATE-5 ｜ commit 硬门：audit 不过则不结算 canon
**它做了什么**：`run_chapter` 里 `if commit and (final_audit["passed"] or allow_failed_commit): apply_state_delta(...)`——审校有 blocker 就**不把状态合进 canon**，除非显式 `--allow-failed-commit`。
**为什么收**：这是「坏章不污染 canon」的关键闸。我的 §3 有「定稿才回写」但没把「audit 过」设成代码闸。
**落地**：`state_apply.py` 默认要求传入的 audit 报告 `passed=true`（或 `--allow-failed` 显式放行）；SKILL.md §3 写明此闸。

### ✅ ADAPT-6 ｜ 模型分阶段路由 = `config/models.json`（数据化「模型是可选旋钮」）
**它做了什么**：`models.json` 把 planner/context_packer/drafter/auditor/rewriter/extractor 各路由到不同模型，且 `auditor: "builtin"`（确定性审校永远不靠模型）；openai_compatible 用 env 注入 base_url/key/model。
**为什么收**：这把我「模型是可选优化旋钮、不写死 model ID、确定性审校是硬闸」的原则**数据化**了——路由是配置，审校永远 builtin。比我 10-model-orchestration.md 的散文更可操作。
**落地**：ADAPT 进 `templates/` 加一份 `model-routing.example.yaml`（对齐我的 contract 风格，YAML，env 注入，注明 auditor 恒为确定性脚本而非模型）；10-model-orchestration.md 引用之。**不引入运行时依赖**。

### ✅ ADAPT-7 ｜ 反 AI 味词表的「数据 vs 代码」分离 + 补充词条
**它做了什么**：`ai_smell_lexicon.json` 把 `phrases`（AI 味短语）和 `meta_terms`（prompt 泄漏元语言）externalize 成数据文件；audit.py 读它。我的 antislop_lint.py 把词表写死在代码里。
**为什么收**：词表是**数据**不是逻辑，外置便于作者按品类增删。它的几个词条（「不只是…更是」「他知道，这意味着」「某种看不见的手」「context_pack/chapter_contract」元语言）值得并入我的桶 1。
**落地**：把它的词条**并入** antislop_lint.py / output_check.py 的现有词表（取并集，去重）；评估是否把词表抽到 `templates/ai-smell-lexicon.example.yaml` 供覆盖（轻量，不强制）。

### 🔶 ADAPT-8 ｜ 场景级 `choice`（主角主动选择）字段
**它做了什么**：beat_sheet 每个 scene 有 `choice`（POV 角色本场做的**主动选择**）+ `value_shift`。我的 chapter-outline scene 有 value_shift 但没 choice。
**为什么收**：「主角持续做主动选择」是网文反「工具人主角/降智」的 craft 点。一个字段成本极低。
**落地**：`chapter-outline-template.json` 的 scene 加 `choice` 字段。

### 🟢 REFERENCE-9 ｜ 整个 WebNovelOps CLI = 可选「满配硬化实现」
**它是什么**：一个完整可 pip 装的参考实现（init/run-chapter/validate/status/compact + provider 抽象 + 整树 schema 校验 + pytest）。
**裁决**：**不并入 skill 默认**（违背我「反 overengineering / 默认 agent 驱动 Markdown+YAML」哲学，也正是豪子「市面工具 overengineered」的痛点）。但它是 6 个脚本之外**「满配硬化 mode」的现成参考**——
**落地**：物料已存 `docs/research/external-webnovelops-deliverable/`；在 `scripts/README.md` 的硬化 mode 段**指路并致谢**：「想要满配可执行 CLI（provider 抽象 + 整树校验 + 5 命令）→ 见该参考实现；本 skill 的脚本是其最小子集，默认够用」。

---

## 2. 明确 REJECT（不收，且说清为什么）

| 不收项 | 为什么 |
|---|---|
| 用扁平 `knowledge_boundary.json`（per-char known_secret_ids）替换我的认知模型 | 我的 cognition{knows/does_not_know/**misbeliefs**/reader_knows_char_doesnt} + 事件级 visible_to_reader/known_by **更richer**；它是我的子集。保留我的，借鉴它把 known_by 显式记在事件上（我已有）。 |
| 用 `canon_version` 单调计数替换我的 Canon 五态 | 不同维度，不冲突：canon_version 是「版本号」（我**收**进 current_state），Canon 五态是「每条事实的确信度」（保留）。两者并存。 |
| 用它的扁平 audit score 替换我的双免疫终分 | 我的 final = LLM 加权分 − antislop penalty（封顶 0-20）更细。它的 score 是 100−25×issues 的粗扣分。保留我的；借鉴它把 must_happen/must_not 做成确定性 issue。 |
| 把 JSON 状态格式换成它的 schema | 我用 YAML + Canon 五态 + 双时态，信息更密。state_apply.py 适配**我的** schema，不迁就它。 |
| 引入它的运行时（urllib provider、CLI 作为必跑入口） | 默认保持零搭建 agent 驱动。CLI 仅作可选参考。 |
| 把 12 篇 references 压成它的 1 篇 GITHUB_RESEARCH | 我的 craft 知识库（品类/平台/爽点/伏笔/反AI味三桶/模型）是核心价值，远超它的单篇。 |

---

## 3. 落地清单（→ 后续改动）

1. `templates/chapter-outline-template.json`：加 `acceptance_criteria`{must_happen_evidence:[{requirement,keywords}], must_not_evidence:[{requirement,forbidden_keywords}]} + scene 加 `choice`。
2. `scripts/output_check.py`：加 3 硬门 `must_happen_present` / `must_not_absent` / `ending_hook_in_tail`（+ forbidden_reveals 词面外泄扫描，剧透-出 防线）。
3. `scripts/state_apply.py`（**新，第 5 脚本**）：借 WebNovelOps 合并代数，适配我的 YAML/Canon-五态/双时态 schema；幂等去重 + 钩子生命周期 + canon_version 自增 + 每 N 章 checkpoint + audit-pass 提交闸 + compact 只快照不删。
4. `scripts/antislop_lint.py`：并入 ai_smell_lexicon 词条（并集去重）。
5. `templates/model-routing.example.yaml`（**新**）：分阶段路由 + auditor 恒确定性 + env 注入；10-model-orchestration.md 引用。
6. `SKILL.md`：§3 补「章节事务/幂等续跑 + run_manifest 产物清单 + audit-pass 提交闸」；§7 脚本索引加 state_apply；§4/§5 视情况微调。
7. `scripts/README.md`：硬化 mode 段指路 + 致谢 WebNovelOps 参考实现；列 state_apply。
8. `README.md` / `references/00-research-map.md` / `docs/research`：把「两 agent 独立收敛」与本裁决记入 provenance。
9. 全脚本回归（含新 state_apply 自测）→ 必须全绿才提交。

---

## 4. 评审修正（3 路对抗式评审 40 findings 后，覆盖 §1–§3 的就近条目）

> 2026-06-27 跑了一轮 3 路并行对抗评审（完整性扫描 / 对抗式批判 / schema 适配正确性，见 workflow `webnovelops-integration-review`）。评审**背书了核心方向**（架构独立收敛属实；state_delta 合并代数 + acceptance_criteria 是真缺口、REJECT 表正确），但抓出若干**照搬即灾难**的点。以下修正**优先级高于上文** §1/§3 的对应描述。

### 4.1 craft / 正确性（必修）
- **ending_hook 门降级为 ⚠️ 启发式 warning，不是 blocker**（修正 INTEGRATE-3）。交付物自己的 demo ch0002 证伪了「尾段关键词硬门」：`derive_keywords` 从整句钩子截出 6 字残块 → 误报 ENDING_HOOK_MISSING → 唯一「修复」是把 intent 原句 verbatim 粘到结尾（=桶2 反对的 on-the-nose 告知）。落地：`ending_hook_in_tail` 只标记送 reviewer，**只认作者显式提供的【具名实体】关键词**（`ending_hook.keywords`），**严禁 derive_keywords 兜底**。
- **must_happen 关键词门 = 必要非充分**（修正 INTEGRATE-1）。`all(k in text)` 只能证「漏写」（关键词缺→事件没发生），证不了「写对」。output_check 与 SKILL.md 必须明示它是**必要前置**、不替代 LLM reviewer 的语义判定；关键词**只用稳定具名实体（人/物/地名），禁用动作/情绪动词**（否则同义改写误伤）。
- **杀位置耦合**：把 `must_happen` 从 `[str]` 升级为 `[{text, keywords:[]}]`、`must_not_happen` 升级为 `[{text, forbidden_keywords:[]}]`——requirement 只存一次、关键词内联，取消平行数组下标对齐（one-source-of-truth）。缺 keywords 时 output_check 出 **WARN**（让伪约束-by-omission 可见，不静默放过）。

### 4.2 state_apply.py 重写绑定层（评审把工作量从「改字段名」纠正为「重写绑定 + 新增 2 op + 1 guard」）
「借合并代数骨架（单写入路径 / 按 id 幂等 append / 结构化 op / audit-pass 闸 / checkpoint / compact 只快照不删），但**字段绑定全换**」。逐条：
- **canon_status 盖戳（critical）**：state_apply 写的每条新事实/事件/伏笔由**代码盖 `canon_status: Inferred`**；Pending→Canon 晋升只走独立人确认入口，绝不在 apply 路径发生。这是不在状态层重开伪约束的命门。
- **章级 applied-guard（critical，幂等）**：`cursor.applied_chapters` 记已结算章；apply 开头若 `chapter_id` 已在其中则**整体 no-op**。WebNovelOps 只对带 id 的集合幂等——数值 `delta`、`state_revision++` 重跑会双倍计数/多跳版本。「幂等」措辞收敛为**「章级一次性 + id 去重」**，不承诺「重跑任意次安全」。
- **hooks ≠ 伏笔（critical，不可对齐 foreshadow-ledger）**：`foreshadow_changes` 只收**长程轻埋伏笔**（字段用我的 planted_ch/planned_payoff_ch、3 态 open|微回应|closed、六类型白名单；缺 planned_payoff_ch 一律拒收）；**章末短钩子**写 `rolling-summary.per_chapter[].hook`，不进台账。`advance`→翻 `status=微回应`（非仅 append）。
- **事件无独立文件 = 不新增 timeline 文件**：episodic「发生了什么」落 `rolling-summary.per_chapter[].one_line`；「谁知道」落角色 `cognition`（不设 per-event known_by——撤回裁决 §2「known_by 我已有」的空头支票，诚实改为：我的模型把「谁知道」放角色、「发生什么」放摘要，**不设独立事件表**，合 anti-overengineering）。
- **「只失效不删」需新 op**：`world_fact_changes` 子 op = `add`（盖 valid_from + Inferred + 必填 visible_from_volume）/ `invalidate`（按 id 写 valid_until_chapter，**永不删原条**）；**禁用** world_facts 的 set/remove。current_state 快变层仍允许 set 覆盖（历史靠 rolling-summary 兜底）。
- **character 字段白名单 + 路由**：按 list 扫 id 定位；未知 cid→**报错**（不自动造 stub）。路由 location/injury/emotion/goal_now/level→`current_state.*`；knowledge→`cognition_changes:[{bucket:knows|does_not_know|misbeliefs|reader_knows_char_doesnt, add|remove}]`；relations 按 `with` upsert；level 入库前查 `power_system.ladder` 单调性。**硬禁**写 canon_status/behavior_anchors/identity/role/visible_from_volume。
- **resources 拆数值账本**：`current_state.resources` → `items:[]`（法宝/技能，add/remove）+ `balances:{}`（灵石等数值，`delta` 累加，受 applied-guard 幂等保护）——保住最值钱的「原子计数器合并」op。
- **possible_conflicts 不静默入库（合我「冲突→人三选项」铁律）**：state_apply **返回** conflicts 给 driver 以三选项呈人；未决的存 `cursor.pending_conflicts`（与已结算 canon 分离），绝不当 Inferred 混进事实账本。state_check 在卷边界 surface 它。
- **原子写 + 收尾自校验**：每个 YAML 写经 tmp+os.replace；apply 后立即跑 state_check 不变量，**破则非零退出、不提交**。
- **checkpoint 用我的文件集**：glob/存在性而非硬编码名单（我无 knowledge_boundary.json）；目录 `mybook/checkpoints/after_chNNNN/`；interval 读 `contract.config.checkpoint_interval`（默认 5）。compact 只快照不删。
- **previous_tail ≠ chapter_summary**：previous_tail 取 `final.md` **尾段原文**（state_apply 额外接收 final 路径）；chapter_summary→per_chapter.one_line。绝不用摘要充当续写锚点。
- **canon_version 改名 state_revision**（避与每条事实的 canon_status 撞名），落 `state-plotline.cursor`（AI 可写的机器维护层）；`last_chapter_id`→`cursor.last_chapter_done`（已存在）。

### 4.3 新增/强化（评审补的高价值项）
- **spoiler-OUT 升为一等硬门**（F1，原仅藏在括号里）：output_check 增 BLOCKER `no_future_spoiler_out`——扫 final 正文是否泄漏 `contract.locked_reveals` / 章纲 `forbidden_reveals` 的**结构化**词面（不用 WebNovelOps 脆弱的散文切分）。模型会**编造**没被告知的反转，input 过滤抓不到——这是 skill #1 痛点（提前剧透幕后黑手）缺的另一半。剧透防护自此**入/出双闸**。
- **compile_prompt 加反编造 hard_rule**（F10）：「只用参考资料事实，不得新增核心设定/真实身份/力量规则；未注入的未来视为不存在，不要猜测隐藏真相。」spoiler-OUT 的生成期 in-band 强化。
- **human_gate 数据化**（F7）：contract 加 `human_gate.requires_approval_for: [canon_override, major_reversal, character_death, power_system_change]`；state_apply 命中即拒绝自动提交（要 `--human-approved`）。把 §5 human-only 列做成可机检触发器。
- **lexicon 修正 ADAPT-7（不照搬）**：① 扩 `NEG_PARALLEL` 正则覆盖「不只是…更是…」（去掉强制「而」）——别把「更是/不只是」当 flat 罚分词（会误伤「他更是不敢动」）；② `meta_terms`（context_pack/chapter_contract 等泄漏元语言）并入 **output_check.LEAK_PATTERNS 作 BLOCKER**（泄漏≠AI味，严重度不同）；③ 仅真正新的【具体 AI 味短语】（某种看不见的手/说不清的感觉）按词性进对应加权桶。
- **§7 文档冲突必修（one-source-of-truth）**：state_apply 是第一个【写状态】脚本，与 §7「state-updater 是 agent 驱动的角色、不是脚本」直接冲突。改写为**「state-merge 是可选确定性脚本；delta 抽取仍 agent 驱动」**。INTEGRATE-4「事务」语义由 state_apply 顺手 emit `run_manifest.json` 落到代码（不留散文空头保证）。
- **per-章产物加 revision_plan.json**（F11）：≤3 轮改稿留审计轨（round#/驱动 findings/applied rule/AI 味分 delta）。
- **model-routing.example.yaml 默认全指同一占位模型**（adversarial-F9，镜像 all-mock），注释「拆分到不同模型是可选优化」，避免暗示「必须配 6 个」。
- **golden fixture**（F9）：用**我的** schema 手写 2 章 delta + 期望后态，作 state_apply 回归（断言 Canon/伏笔/钩子/state_revision 匹配 + 重跑 no-op + no-commit 不变）。

### 4.4 评审背书的 REJECT / 决策（维持不动）
扁平 audit score（粗于我的双免疫终分）、JSON-schema 整体替换、CLI 作默认入口、knowledge_boundary 替换 cognition——**REJECT 全部成立**。canon_version↔Canon 五态正交、并存（前者改名 state_revision 收进 cursor，后者保留）——成立。借骨架不照搬扁平 JSON——方向正确。

### 4.5 范围纪律（评审警告 over-integration，故**记录而不在本轮建**）
- **显性中程悬念账本**（F5：overt promise/open-question ≠ 隐性伏笔）：本轮只做「不混淆」修正（hooks 不塞进 foreshadow-ledger，章末钩子归 rolling-summary），**不**新建独立 promise-ledger（emotion-debt 已覆盖压抑→释放承诺；中程显性问题暂记为已知限制，文档标注）。
- **regression 运行器**（F6）：只加**声明式** `eval-regression-tests.yaml`（命名不变量→强制它的 gate 名映射，知识棘轮），**不**建跑测运行器。
- **per-event 二级 known_by / 独立 timeline 文件**（SM-1）：按 4.2 决议不建（episodic→rolling-summary，knowledge→cognition）。
