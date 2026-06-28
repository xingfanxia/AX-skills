# External Proposal — WebNovelOps 五层架构 (用户转贴的另一个agent产出)

> 来源：用户在 session "novel" 中转贴。强来源支撑(Anthropic context engineering / DOME arxiv / Novelcrafter Codex / Sudowrite Story Bible / 阅文作家助手 / 唐家三少访谈 / Royal Road / Story Grid)。作为设计输入之一，需批判性整合，不照搬。

## 核心主张
- AI写长篇的问题不是"单prompt不够好"，而是没把小说当**持续演化的状态系统**管理。
- 最佳实践 = **Human-showrunner + AI工业化辅助**，不是全自动写书。
- 命名 WebNovelOps，五层：L0作者宪法 / L1 Story Bible(慢变) / L2 State Ledger(快变,每章更新) / L3 Chapter Contract(本章合约) / L4 Generate-Review-Commit闭环。

## 关键可吸收点(verbatim要点)
1. **拆 memory.md 成 typed ledgers**，区分 canon / plan / draft-only / reader-visible / character-known。单一 memory.md 混事实+推测+伏笔+未来意图→正是"约束被写进正文"的根因。
2. **未来计划/伏笔不进正文模型上下文**(`forbidden_future_spoilers.md` 不给 writer 读)→ 防剧透+防约束泄漏。
3. **每章≥4个不可混用的prompt**：本章意图 / 场景beat / 正文生成 / 事实抽取审计。混在一个prompt里→模型边规划边写→混入说明语言、节奏松散。
4. **Chapter Contract (intent.yaml)**：pov/time/purpose/must_happen/must_not_happen/reader_emotion曲线/webnovel_payoff/ending_hook。正文模型可选表达，**不能改本章交易条款**。
5. **State as delta**：LLM 提 `state_delta.json`，人/程序 merge，旧 state 不可随意覆盖；delta 必须 schema 校验。
6. **knowledge_boundary.yaml**(谁知道什么) + **resource_ledger**(钱/法宝/伤势/技能/冷却) + **pending_hooks**(伏笔池带 aging/deadline)。
7. **多rubric审计**(不是单review agent)：Continuity / Knowledge-Boundary / Plot-Contract / Webnovel-Pacing / Character-Voice / Style-AI-Smell / Prompt-Leakage，各自打 blocking bug 或 score。
8. **局部修不全章重写**：revision 只允许改被标注段落，禁止 add_new_plot_event / change_outcome / reveal_future / rewrite_unflagged。
9. **固定 compaction checkpoint(每5章)+ regression**：未回收伏笔aging、人物瞬移、资源凭空、承诺久未兑现、连续3章无进展。
10. **Promise/Progress/Payoff (Sanderson)** 作为比三幕更贴连载的宏观框架。
11. **网文8指标rubric**：opening_hook/conflict_pressure/progress/payoff/new_question/emotion_curve/skimmability/ai_smell(越低越好)。"每章不一定打斗，但每章必须有状态变化，否则是水。"
12. **正文 output_rules 禁元语言**：不出现"大纲/伏笔/爽点/读者/设定/约束/prompt"等。
13. **AI味四段式**(前置style_guide+禁用词+few-shot / 生成中要求具体动作感官 / 审稿中标具体句子 / 修订只改句不改剧情)；**中文正文模型单独实测**(20题小benchmark测"后期人工编辑成本最低"，不信外部榜)。
14. **MVP分层 v0手工markdown→v1脚本化schema校验→v2多模型路由+dashboard**；明确"别照搬Novelix 10-agent"。
15. **不变式清单**：正文模型不能改canon / 审稿模型不能重写全文 / 状态更新是delta非覆盖 / 未来计划不进正文上下文 / 每章必须有contract / 每章必须有状态变化 / 每5章checkpoint / 人类永远控制不可逆剧情决策。

## 致命短板 / 需修正(我的批判)
A. **它是"软件工程提案"，但豪子的substrate是 Codex CLI + Markdown，不是要他建/维护 Pydantic+SQLite+LanceDB+dashboard 的app。** v1/v2 正是它自己警告的 Novelix overengineering，只是更有品味。修正：做成**skill驱动agent操作纯markdown/yaml文件**，12个"skill"是agent按SKILL.md执行的**工位/子程序**，不是12个微服务。一个极小的 schema-check 脚本可以有(把不变式code化)，但 SQLite/向量库不是核心。
B. **网文审美 vs 文学craft 的反转它没解决。** 它的 AI-smell 仍偏文学(把"缺少具体动作/物理细节"当AI味症状)——但系统流/爽文恰恰要直给情绪、要信息直陈(属性面板)。它的 pacing rubric 是网文感的(好)，但craft建议仍夹带文学规则。质检必须**品类感知**(打脸章要on-the-nose；悬疑章要克制)。等网文审美调研agent回来补。
C. **每章7 reviewer 在日更(4k-1万字)下太重**(即便Codex token无限，wall-clock+人类gate注意力是成本)。修正：**审计分级**——correctness类(continuity/knowledge-boundary/leakage)硬门禁每章必跑；quality类(voice/AI-smell/pacing)跑但人类只在低分时看；clean章走快路。
D. **逐章人类 gate intent.yaml 对日更太频。** 修正：人类定arc级合约+反转，章intent由AI提案、人类批量skim/批准，配一个"每章人类介入多深"的旋钮(类比game-script工作模式A-E)。
E. **品类层太薄。** genre_contract 一个文件不够；网文结构强品类依赖，需要可切换的品类模板/检查清单层。
F. **RAG/向量检索过早。** 单本书的"最小高信号context pack"多数能直接从结构化ledger里**选取**(agent读相关YAML条目)，结构化ledger本身就是检索索引；向量库是v2 nicety。

## 与我们已定约束的契合
- ✅ "人类driver / AI受约束subroutine" = AX的"LLM是被确定性代码包裹的子程序"原则。
- ✅ "模型仅为可选优化旋钮、自己实测不信榜" = 用户补充的约束。
- ✅ "别照搬Novelix" = 反overengineering。
- ⚠️ 但它的v1/v2自身违反了反overengineering——对豪子的真实substrate要砍到"skill+markdown+极小脚本"。
