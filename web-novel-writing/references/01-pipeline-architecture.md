# 01 · 流水线架构（三层结构 + 9 步 IO 契约 + 循环 driver）

> Purpose: 给整条 pipeline 画一张总装配图——三层架构怎么分、章节生产循环 9 步的输入/输出契约各是什么、确定性 for-loop 当 driver 怎么把每个 LLM 调用包成窄子程序、断点续跑/可幂等怎么落、"草稿只读 state、定稿才回写"和"审校→生成闭环"怎么接。用在**阶段3 搭循环**（决定 agent-as-driver 或硬化脚本怎么编排），是 `03-prompt-compiler`（步骤3/4）、`04-review-rubric`（步骤5/6/7）、`02-state-schema`（状态层）三篇的总纲。

---

## 0. 一句话原理

长篇崩坏的根因是 **AI 自我一致性随篇幅衰减**——这是内在衰减，**换更贵的模型修不了**。唯一可行解：把流程**原子化拆分**（每个 AI 调用做一件窄事，做完代码立刻收回控制权）+ 用**确定性校验**外部强制一致性（不靠 AI 自觉）+ 用**独立 agent**做外部验证（不自审）。这与创作者 CLAUDE.md 的 AI-pipeline 铁律同构：**LLM 是被确定性代码包裹的、受约束的 subroutine；deterministic for-loop 才是 driver**。本篇就是这个 driver 的设计说明书。

---

## 1. 三层架构（含两个边界阶段）

整条 pipeline = **2 个常驻核心层**（状态层 + 章节生产循环）+ **2 个边界阶段**（一次性的阶段0、周期性的阶段性维护）。

```
阶段0 筹备(human 为主) ─一次性─┐
                              ▼
   ┌──────────── 状态层（单一事实源 · 7 文档 · Canon 元数据）─────────────┐
   │  contract / state-world / state-characters / state-plotline /        │
   │  foreshadow-ledger / emotion-debt / rolling-summary                  │
   └──────────────────────────┬──────────────────────────────────────────┘
            草稿只读 ▲          │ 定稿才回写(delta)
                    │          ▼
   ┌──────── 章节生产循环（确定性 for-loop 当 driver · 每章跑一遍 9 步）────┐
   │  outliner→compile→writer→continuity→reviewer→revise→style→state-updater│
   └──────────────────────────┬──────────────────────────────────────────┘
                              ▼ 每卷/每 N 章边界
   阶段性维护：递归压缩摘要 · state_check.py 不变式体检 · 设定刷新/清脏 · 卷级摘要固化
```

| 层 | 是什么 | 谁主导 | 频率 | 详见 |
|---|---|---|---|---|
| **阶段0 筹备** | 锁品类/子类/调性/平台 + 顶层契约（核心冲突/结局/主线锚点/底层规则）+ 分卷大纲 → 初始化状态层 | human-only 为主 | 开新书一次 | SKILL §2 |
| **状态层** | 单一事实源；7 文档，每条事实带 `canon_status` + `visible_from_volume`（变假的带 `valid_until_chapter`） | 草稿读、定稿写 | 常驻 | `02-state-schema` |
| **章节生产循环** | 9 步 driver，每章一遍；每个 LLM 调用是窄子程序，调完代码夺回控制权 | 确定性流程当 driver | 每章 | 本篇 §2–§4 |
| **阶段性维护** | 递归压缩摘要、数值单调性体检、设定刷新/清脏上下文、卷级摘要固化、（可选）追读数据定位高跳出章 | 半自动 + human 拍板 | 每卷/每 N 章 | `11-maintenance-recap` |

> **状态层为何是 7 文档而非"一个 memory.md"**：把"已定/待定/否决/灵感/推断"混进一坨散文，正是 AI 把推测当事实写进正文、长线设定漂移的根因。7 文档 = `contract.yaml`（顶层契约，AI 无权改）+ 6 份状态文档（world/characters/plotline/foreshadow/emotion/rolling）。SKILL §1 全景把它写成"顶层契约 + 6 状态文档"，指的是同一组 7 个文件。字段 schema 见 `02-state-schema`。

---

## 2. 章节生产循环 —— 9 步 IO 契约表

每个 LLM 调用是窄子程序，**调用完代码立刻收回控制权做校验 + 写 state**。字段名以 `templates/*` 与 `scripts/*` 为准。

| 步 | 角色 | 输入（契约 / 关键字段） | 输出（契约 / 关键字段） | 性质 | 频率 |
|---|---|---|---|---|---|
| 1 | **planner** | `state-plotline.yaml.mainline_beats` + 人类决策 | 本 arc 的 beats（写回 plotline / arc 草案） | semi-auto（人定） | 每卷/arc |
| 2 | **outliner** | arc beats + state（world/characters/foreshadow/emotion） | 单章 beat sheet → `chapter-outline-template.json`：`chapter_purpose`/`scenes[]`/`must_happen`/`must_not_happen`/`sao_payoff`/`ending_hook`/`on_stage_characters`/`relevant_canon_ids`/`forbidden_reveals`/`due_foreshadows` | semi-auto | 每章 |
| 3 | **prompt-compiler** | `contract.yaml` + `state-world` + `state-characters` + `rolling-summary` + 章纲 JSON | 三区分离的单章短 prompt | **纯确定性**（`compile_prompt.py`） | 每章 |
| 4 | **writer** | 单章 prompt | 纯正文草稿 | automate（**关 thinking**） | 每章 |
| 5 | **continuity-checker** | 正文 + canon/时间线/人物（**只吃事实，不吃写作 context、不吃 rubric**） | `hard_gates` 4 门（`character_consistent`/`world_canon_consistent`/`timeline_logic_consistent`/`no_forbidden_reveal_leak`）+ `violations[]` | automate（独立） | 每章 |
| 6 | **reviewer** | 正文 + 章纲 + rubric | `weighted_scores`（7 项各 `min`）+ `ai_taste_hits[]` + 末行裸 sentinel `VERDICT:PASS/REVISE` | automate（**独立上下文/异模型**） | 每章 |
| 7 | **revise** | 正文 + 定向 `violations[].fix` | 改稿 | automate；≤3 轮、**净改善≥ε 才采纳**，第 3 轮转人工 | 触发时 |
| 8 | **style/anti-slop-editor** | 正文 + 反 AI 味规则 | 去味稿 | semi-auto（**独立 pass，不喂回同源模型**） | 每章（定稿前） |
| 9 | **state-updater** | 批准稿 + 旧 state | state delta（**LLM 抽取，代码 append，Canon 晋升需人确认**） | semi-auto | 每章（定稿后） |

**夹在 LLM 步之间的纯代码闸**（能 code 判的绝不写进 prompt 让模型自觉——伪约束是头号反模式）：

| 闸 | 在哪一步前后 | 谁做 | 判什么 |
|---|---|---|---|
| 可见性/时效过滤 | 步骤 3 内 | `compile_prompt.py` `visible()` | `visible_from_volume > 当前卷`、`valid_until_chapter < 当前章`、`Rejected/Idea` 一律不进 prompt |
| 字数/POV/格式 + 残留指令符号 + 开篇阈值 | 步骤 5 前（调 LLM 前） | `output_check.py`（正文输出侧·纯正则） | `wordcount_pov_format_ok` / `no_prompt_leak` / `opening_ok` |
| 毒点黑名单词面扫 | 步骤 5/6 | `output_check.py` 扫词面，语义残留交 reviewer | `no_poison_points` |
| 机械 AI 味扣分 | 步骤 6 后 | `antislop_lint.py` | `penalty`(0-20) → `mechanical_penalty` |
| 状态不变式体检 | 每卷边界（阶段性维护） | `state_check.py` | Canon 枚举/境界单调/伏笔逾期/情绪债/glossary 别名冲突 |

> **降低人介入频率（防拖垮日更）**：不是每章都召人。**每卷/每 arc 人定 beats + canon**，中间章自动跑，**只有 reviewer 报异常（第 3 轮仍 REVISE）才召回人**。每章都让人确认章纲会拖垮日更。

---

## 3. 循环伪代码 —— 确定性 for-loop 当 driver

下面是 driver 的规格。**默认 agent 驱动 mode 下，agent（Codex/Claude Code）亲自当这个 for-loop**；硬化 mode 也**只硬化确定性步骤**（`compile_prompt.py` / `state_check.py` / `output_check.py` / `antislop_lint.py` 已落盘），**不硬编 LLM 调用**。⚠️ 注意：顶层"循环 driver"与"state-updater"在本 skill 中**按设计是 agent 驱动的角色、不提供脚本**（反 overengineering——把 for-loop 编排和 delta 抽取焊成脚本会把 LLM 调用硬编死，违背"LLM 是被代码包裹的窄子程序"原则；与 SKILL §7 一致）。要点：**每个 LLM 调用是窄子程序，return 后代码立刻夺回方向盘**；草稿阶段**只读 state 绝不 mutate**；只有显式定稿才回写 delta。

```python
patterns_to_avoid = load_patterns_to_avoid(book_dir)   # §5 审校→生成闭环：跨章累积的"已知 AI 味"

for n in range(resume_from(book_dir), last_chapter + 1):   # 断点续跑：从 checkpoint 续起(§6)
    if checkpoint_done(book_dir, n):                        # 幂等：已完成的章不重跑
        continue

    # ---- 步骤2 outliner（每章；人定 beats 后可自动起草）----
    outline = outliner(arc_beats, state_readonly)          # → chapter-outline.json
    persist(book_dir, n, "outline", outline)

    # ---- 步骤3 prompt-compiler（纯确定性，不调 LLM）----
    prompt = compile_prompt(contract, state_readonly, outline,
                            cur_vol, cur_ch=n,
                            patterns_to_avoid=patterns_to_avoid)  # 可见性/时效双过滤在此发生

    # ---- 步骤4 writer（窄子程序：进 prompt，出正文，立刻返回）----
    draft = writer(prompt)                                  # 关 thinking
    draft = sanitize(draft)                                 # 输出期清洗：正则剥残留符号/元叙述
    # 代码已夺回控制权 ↓ 草稿只读 state，绝不在此回写

    # ---- 步骤5/6 独立校验（与 writer 不同上下文/最好异模型）----
    for attempt in range(0, 3 + 1):                         # 改稿 ≤3 轮
        cont = continuity_checker(draft, canon_facts_only) # hard_gates 4 门 + violations
        gate_code = output_check(draft, outline)            # output_check.py: 字数/POV/格式/prompt_leak/毒点词面/开篇(纯code)
        review = reviewer(draft, outline, RUBRIC)           # weighted_scores + 末行 VERDICT
        penalty = antislop_lint(draft)["penalty"]           # 机械扣分 0-20(纯 code，已封顶/量纲对齐)

        report = assemble_report(cont, gate_code, review, penalty)  # 填 review-report.json
        report.final_score = report.weighted_total - penalty        # 双免疫终分
        verdict = parse_sentinel(review)                    # 末行 .strip().upper()，fail-closed

        passed = (report.final_score >= 80
                  and all(report.hard_gates.values())       # 硬门一票否决，不可被高分平均
                  and all(s >= s.min for s in report.weighted_scores))
        if passed and verdict == "PASS":
            break

        # ---- 步骤7 revise：定向 fix 回灌，非重抽同一 prompt ----
        if attempt == 3:
            escalate_to_human(n, report)                    # 第3轮仍不过 → 转人工(多半是 outline/canon 层)
            break
        new = revise(draft, report.violations)              # 用 violations[].fix 定点改
        rescore = rescore(new)
        if rescore.final_score > report.final_score + EPS:  # 净改善≥ε 才采纳(keep)
            draft = new
        # else: discard，回滚旧稿，别白改使其更糟

    # ---- 步骤8 style/anti-slop-editor（独立 pass，不喂回同源 writer）----
    final = style_editor(draft)
    light_continuity_recheck(final)                         # 去味可能损伤已过的一致性，轻量复检 ⚠️成本权衡

    # ---- 步骤9 state-updater：到这里才回写 ----
    delta = extract_state_delta(final, state_readonly)      # LLM 抽 delta
    append_state(book_dir, delta)                           # 代码 append；Canon 晋升标 Pending 等人确认
    patterns_to_avoid += report.ai_taste_hits               # §5 反喂下一章

    persist(book_dir, n, "final", final, report, delta)     # checkpoint 落盘(可断点续跑)
```

**读这段伪代码的三个锚点**：

1. **for-loop 是 driver，LLM 是子程序**：`writer(prompt)`、`reviewer(...)`、`revise(...)` 每个进去做一件窄事就 return，控制权立刻回到 Python `for`。没有任何一步让 LLM "自己决定下一步做什么"。
2. **草稿只读、定稿才写**：`state_readonly` 在步骤 2–8 全程只读；唯一的 `append_state` 在步骤 9。草稿可反复重生成（重抽 writer、改稿、去味）而**不污染长程状态**。
3. **每个"必须成立"的都有 code 兜底**：`final_score`/`hard_gates`/`min`/`verdict` 都是代码 branch 的对象，不是 prose 信任。

---

## 4. ASCII 数据流图（一章的完整旅程）

```
            ┌─────────── 阶段0 human（一次性）───────────┐
            │ 锁 品类/子类/调性/平台 + 顶层契约          │
            │ + 分卷大纲 → 初始化 7 个 state 文档        │
            └───────────────┬───────────────────────────┘
                            ▼
   ┌──────── 每卷/arc 边界（human 拍板 beats + canon 晋升）────────┐
   │                                                               │
   ▼                  章节生产循环（代码 for-loop）                 │
[outliner]→章纲JSON─┐                                              │
                    ▼   selective inject + 可见性/时效双过滤        │
 state(只读)──▶[compile_prompt 纯代码]──三区分离+硬后缀──▶          │
                    │   ▲ patterns_to_avoid(§5)                     │
                    ▼   │                                           │
              [writer LLM]──正文──▶ sanitize(正则清洗)              │
                    │                                               │
        ┌───────────┴───────────┐                                  │
        ▼                       ▼                                  │
[continuity-checker]      [reviewer rubric+硬门]                   │
 吃canon/时间线/人物        出 weighted_scores                     │
 → hard_gates 4门          + 末行 VERDICT sentinel                 │
        └───────────┬───────────┘   + [antislop_lint 纯code]扣分   │
                    ▼                                              │
          final = 加权分 − 机械扣分 ；硬门全清且各项≥min？          │
                    │                                              │
         PASS ──No──▶[revise ≤3轮 定向fix 净改善才keep]──▶(回writer)│
          │Yes（第3轮仍No → 转人工）                               │
          ▼                                                       │
   [style/anti-slop-editor 去味独立pass]──▶ 轻量 continuity 复检   │
          ▼                                                       │
   [state-updater]──delta──▶ append 回写 state（Canon晋升标Pending）│
          │              └──ai_taste_hits──▶ patterns_to_avoid ────┘(反喂下一章)
          ▼
   persist 落盘（稿+评分+state delta，可断点续跑）──── n+1 ─────┐
          │                                                     │
   ┌──────▼ 每N章/每卷：递归压缩摘要 + state_check.py 体检 +      │
   │        设定刷新/清脏 + 卷级摘要固化                          │
   └─────────────────────────────────────────────────────────◀─┘
```

---

## 5. 审校→生成闭环（把已知 AI 味反喂进后续章 prompt）

**原理**：reviewer 早期 flag 出的 AI 味（`ai_taste_hits[]`）不是用完即弃——把它累积成一份书级 **PATTERNS-TO-AVOID** 清单，由 prompt-compiler 注入后续章的 `<hard_rules>`，让 writer **写之前就规避已知失败模式**（来自 autonovel 的"审校→生成闭环"）。这把"事后挑错"升级成"事前避坑"，是把审校信号变成生成约束的关键回路。

**怎么接（最小实现）**：

| 环节 | 做什么 | 落点 |
|---|---|---|
| 采集 | reviewer 每章产出 `ai_taste_hits[]`（命中的具体指纹句式） | `review-report-template.json` |
| 累积 | state-updater 把本章高频 `ai_taste_hits` append 进书级 `patterns_to_avoid` | 书目录一份 `patterns-to-avoid.md/yaml`（去重 + 限长，只留 top-N 高频） |
| 注入 | prompt-compiler 把 `patterns_to_avoid` 渲染进 `<hard_rules>`（如"禁用以下已被判定为 AI 味的句式：…"） | `<hard_rules>` 末条 |

> ⚠️ cross-file：`compile_prompt.py` 当前**未读取** patterns-to-avoid，伪代码里的 `patterns_to_avoid=` 参数是**待接的增强点**。要启用需：①新增书级 `patterns-to-avoid` 文件；②`state_update`/state-updater 往里 append；③`compile_prompt.py` 读取并 emit 进 `<hard_rules>`。三处齐改才不漂移。注入时**只放词句层指纹**（桶1），不要把"做加法不推进"这类语义判断塞进去——那是 reviewer 的活，prompt 约束不住。

---

## 6. 断点续跑 / 可幂等（长篇是跨月多 session 工程）

长篇连载是跨月、跨 session、可能中途挂掉的工程。每章的中间产物**全程落盘**，挂掉重跑**不重写已完成产物**（来自 LongWriter write_cache / ExplosiveCoderflome content-hash checkpoint / AI_NovelGenerator partial checkpoint）。

**最小书目录布局**（把"可断点续跑"从抽象承诺钉成具体物理约定）：

```
<book_dir>/
├── contract.yaml                 # 顶层契约（human-only）
├── state-world.yaml              # ┐
├── state-characters.yaml         # │
├── state-plotline.yaml           # ├ 6 状态文档（单一事实源）
├── foreshadow-ledger.yaml        # │
├── emotion-debt.yaml             # │
├── rolling-summary.yaml          # ┘
├── patterns-to-avoid.yaml        # （可选）审校→生成闭环累积的已知 AI 味（§5）
└── chapters/
    └── NNNN/                     # 每章一目录（0001 / 0002 / …）
        ├── outline.json          # 步骤2 章纲
        ├── draft.txt             # 步骤4 writer 草稿（可反复重写，不算 done）
        ├── final.txt             # 步骤8 定稿（**存在即该章 done**）
        ├── report.json           # 步骤5/6 审校报告
        └── delta.yaml            # 步骤9 state delta（已 append 回 state）
```

**done 判据 / resume 锚点**：`chapters/NNNN/final.txt` **存在即该章已完成**；`resume_from = 最大的有 final.txt 的章号 + 1`。草稿目录可反复重写，唯有 `final.txt` + `delta.yaml` 是"已提交"状态——这就是下表"逐章 checkpoint / 幂等跳过"的物理落点。

| 机制 | 怎么做 | 防什么 |
|---|---|---|
| **逐章 checkpoint** | 每章落盘 `{outline, draft, final, report, delta}`；`final` 写成即标 done | 跨 session 丢进度 |
| **幂等跳过** | for-loop 起步 `resume_from()` 读最后 done 的章号；`checkpoint_done(n)` 为真则 `continue` | 重跑覆盖已定稿 |
| **草稿/定稿分离** | 草稿目录可反复重写；只有定稿 `final` + state delta 是"已提交"状态 | 半成品污染长程 state |
| **content-hash 去重** | 用 outline+prompt 的 hash 当 key，输入没变就不重跑 writer | 同输入重复烧 token |
| **state delta append-only** | 状态用 append 不就地改写；Canon 晋升只标 `Pending` 等人确认 | 回写中途崩坏破坏单一事实源 |

**铁律**：禁止多章并发（oh-story-claudecode 明令）——第 n 章依赖第 n−1 章的**正文末段**（`rolling-summary.previous_tail`）+ 追踪文件，并发会读到未定稿的 state。续跑是**串行 resume**，不是并行回填。

---

## 7. 多 agent vs 单循环的取舍（结论：单循环串行 + 单 reviewer 多 rubric）

**复杂度预算放在"状态结构 + 确定性校验"，不放在"agent 编排"。** novelix 反例：10 个串行 agent + 33 维审计 + 22 改写规则——每多一个 agent 多一处可漂移/可泄漏的接缝；防退化的上限是**架构约束**而非机制数量。

| 方案 | 结论 | 依据 |
|---|---|---|
| **单主循环串行逐章** | ✅ 采用 | 章节依赖上一章正文 + 追踪文件，禁多章并发（oh-story-claudecode）；串行才能 resume |
| **单 reviewer 内含多 rubric** | ✅ 采用 | webnovel-writer 明确选"单 reviewer 5 维"而非多 agent 并行，blocking issue 定点修复不重跑（成本权衡） |
| **10 个专职 agent 并行** | ❌ 拒绝 | inkos"10 agent"是叙事夸大，多数是同一 client 上的 prompt 变体 + 确定性胶水；真并行是 token 黑洞且非确定性 |
| **reader_panel / Elo 锦标赛审校** | ⚠️ 仅有界单本可奢侈 | autonovel 的多人格共识能抓"全员点头无摩擦"，但它自己承认这是有界单本的奢侈，**连载承担不起** |

**唯一例外的"多调用"是 writer/reviewer/style 的异模型分离**——但那不是"多 agent 并行协作"，而是同一串行循环里**换 client（`base_url + model`）做独立调用防自欺**（见 `04-review-rubric` §5、`10-model-orchestration`）。串行单循环 + 一步内多 rubric + 确定性脚本兜底，对 Codex CLI substrate 是成本/可靠性最优。

> **审校是"找问题"不是"验证正确"**（oh-story-claudecode / webnovel-writer 都写成铁律）：reviewer/continuity-checker **只返 JSON、不评判情节走向、不持 Write**。越权改稿 = 把"找问题"偷换成"验证自己改得对"，回到自欺。

---

## 8. 可复用要点 / 失败模式速查

- **for-loop 是 driver，LLM 是窄子程序**：每个 AI 调用做一件窄事，return 后代码立刻夺回控制权——这是对抗"一致性随篇幅衰减"的唯一结构性解。
- **草稿只读 state、定稿才回写**：步骤 2–8 全程只读 state，唯一 `append_state` 在步骤 9。草稿可随便重生成而不污染长程记忆。
- **能 code 判的绝不写进 prompt**：可见性/时效/字数/POV/prompt_leak/伏笔到期/境界单调 全部 code 强制；prompt 里的 hard_rules 只是"软请求"，每条都有下游 code/独立 LLM 兜底。
- **硬门一票否决 + 各项最低线 + 双免疫终分**：`final = 加权分 − 机械扣分`，`PASS ⟺ final≥80 且 硬门全清 且 各项≥min`；末行裸 sentinel `fail-closed`。
- **改稿净改善才采纳、≤3 轮转人工**：定向 fix 非重抽（重抽 6–7 次自我重复塌缩）；`final_score` 不升则回滚。
- **审校→生成闭环**：`ai_taste_hits` 累积成 PATTERNS-TO-AVOID 反喂后续章 prompt，事后挑错升级成事前避坑（⚠️ 当前待接，见 §5）。
- **断点续跑串行 resume**：逐章 checkpoint + 幂等跳过；禁多章并发（章依赖前章末段）。
- **不堆 agent**：单循环串行 + 单 reviewer 多 rubric + 异模型独立调用，复杂度预算花在状态层和校验门，不花在编排花活。

---

## Sources

- `SKILL.md` §1（三层全景图 + 两种 mode）、§3（9 步循环表 + 单章 prompt 三铁律）、§6（MVP 最小闭环 vs 完整版）、§7（reference/script/template 索引）。
- `references/03-prompt-compiler.md`（步骤3/4：最小 context、可见性/时效双过滤、三分离、输出期清洗——本篇的步骤 3 锚点）。
- `references/04-review-rubric.md`（步骤5/6/7：硬门 7 字段、加权分 7 项 min、双免疫终分、末行 sentinel 容错、净改善≥ε 改稿≤3 轮——本篇的步骤 5/6/7 锚点）。
- `references/02-state-schema.md`（状态层 7 文档字段 schema、Canon 五态、`visible_from_volume`/`valid_until_chapter` 治理标签）。
- `scripts/compile_prompt.py` / `scripts/state_check.py` / `scripts/antislop_lint.py` / `scripts/README.md`（已落盘的确定性硬化层 + "在循环里怎么接"图）。
- `templates/chapter-outline-template.json`（步骤2 输出契约）、`templates/review-report-template.json`（步骤5/6 输出契约）、`templates/rolling-summary.yaml`（`previous_tail` 续写锚 + 分层递归摘要）。
- `docs/research/03-pipeline-design-blueprint.md` §2.1（三层结构）、§2.3（9 步循环契约表）、§2.4（ASCII 数据流）、§8（MVP vs 完整版、对抗 overengineering）。
- `docs/research/04-github-prior-art-survey.md` §4（章节生产循环最佳实践：草稿纯函数读/定稿才回写、审校→生成闭环 PATTERNS-TO-AVOID、可断点续跑/幂等、单循环+多 rubric vs 多 agent 取舍、"审校是找问题不是验证正确"）、§5（伪约束/doc-drift/在关键处欠工程的反模式）。
- ⚠️ 标注项：循环 driver 与 state-updater **按设计是 agent 驱动的角色、不提供脚本**（SKILL §7：反 overengineering、不硬编 LLM 调用，非"未实现"）、`patterns_to_avoid` 注入待接进 `compile_prompt.py`、EPS/≤3 轮/最近 3 章上限均为经验值——见 §3/§5/§7 cross-file 注。
