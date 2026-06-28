# web-novel-writing

> 约束 AI 写好【中文网文长篇连载】的工业化工作流 skill。把"完全放手让 AI 写、4-5 章后逻辑/人设/世界观全崩"的失控过程，改造成"**人类当导演、AI 当受约束子程序**"的可稳定推进流水线。
>
> 姊妹 skill：[`game-script-creation`](../game-script-creation)（那个是二游剧本陪写，这个是网文长篇连载）。

## 它解决什么

真实痛点（来自一线作者实测，不是假设）：

- 完全放手让 AI 写根本看不了；Opus/GPT 连续续写 **4-5 章逻辑还行，再多就逻辑/人设/世界观全崩**。
- prompt 写长了，AI 会把"给它的约束/context"**莫名其妙写进正文**。
- 市面工具要么很难用、要么 overengineered（novelix 等）。
- 去 AI 味 skill 不好用。

根因：长篇崩坏是 **AI 自我一致性随篇幅衰减**——这是内在衰减，**用更贵的模型解决不了**。

## 核心思路（5 件事）

1. **第 0 步人类锁定**品类/平台/顶层契约（核心冲突·结局·主线锚点·底层规则）。
2. **把记忆拆成带 Canon 状态 + 按卷可见性的 typed 状态文档**（世界观/人物/剧情线/伏笔台账/情绪债/滚动摘要），而不是一个会泄漏到正文的 `memory.md`。
3. **确定性流程每章编译"最小 context、指令与正文严格分离"的短 prompt**（专治 AI 把约束写进正文）。
4. **章节生产闭环**：编译 → 生成 → 独立一致性校验 → 量化 rubric 审校（双免疫：LLM 分 − 机械扣分）→ 定向改稿（≤3 轮）→ 去 AI 味 → 状态增量回写。reviewer 与 writer 独立调用防自欺。
5. **反 AI 味分三桶**：词句层全量复用文学清单 · 结构层改分层规则 · 网文专属轴（爽点/钩子/毒点/品类适配）。

明确划分 **AI 自动 / 人机协作 / 必须人类拍板** 三档边界。

## 怎么用（两种 mode）

- **Agent 驱动 mode（默认，零搭建）**：让 Codex / Claude Code 读 `SKILL.md`，亲自充当确定性 driver，按流程操作 Markdown/YAML 状态文件，逐章编译 prompt、跑校验、回写状态，人类在卷/arc 边界拍板。立刻可用。
- **硬化 mode（可选）**：用 `scripts/` 把确定性步骤真正确定化（prompt 编译 / AI 味 lint / 状态不变式校验）。书越长越值得上——因为"靠 agent 自律"恰恰是会漂移的那一环。只依赖 `python3 + PyYAML`，无重依赖。见 `scripts/README.md`。

## 设计约束

- **model-agnostic**：默认就在 Codex/GPT 上跑；换 GLM 等国产文学性更强的模型是**可选优化旋钮**、非前置依赖；不写死任何模型 ID。
- **诚实区分**"工程能修的"（一致性崩坏/结构失控/prompt 泄漏/流程纪律）与"模型天花板"（叙事层 AI 味/语感，工程压低但压不到零）。
- **反 overengineering**：substrate 是 Markdown/YAML + skill 指令 + 极小可选脚本，**不是**要作者建一个带 SQLite/向量库/dashboard 的 app。

## 文件地图

```
SKILL.md                     # 编排器主轴（先读这个）
references/00-14             # 深度知识库 15 篇（架构/状态schema/防泄漏编译器/审校rubric/品类/平台/爽点/伏笔/反AI味三桶+Gate A-G/模型/维护/对话工艺/导入崩稿/拆爆款学习）
templates/                   # 顶层契约 + 6 状态文档 + 状态增量(delta) + 章纲 + prompt骨架 + 审校报告 + 模型路由 + 回归不变量表 + 去AI味白名单 + 对标模块卡
scripts/                     # 可选硬化层 6 脚本 + 1 回归测试：compile_prompt / output_check（正文硬门含 must_not/剧透-出/标点）/ degeneration_check（模型退化）/ antislop_lint（词句层+鲁棒不是A而是B）/ state_check / state_apply（确定性合并delta）/ test_lint_fixtures.sh（python3 + PyYAML）
examples/worked-example-xuanhuan.md   # 玄幻凡人流端到端范例
docs/research/               # 全部调研材料（六流发现/批判AX框架/设计蓝图/网文审美裁决/GitHub prior-art + 两份外部交付物借鉴裁决 05-WebNovelOps / 06-oh-story + 原始物料）
```

## 依据

设计经过批判性、可追溯的调研（见 `references/00-research-map.md` + `docs/research/`）：网文工业方法论与平台机制、网文审美 vs 文学 craft 的逐条裁决、AI 长篇生成的学术与工程方法、以及 GitHub 上高星/活跃项目的逐个架构拆解（偷什么/避什么）。头号反模式是**伪约束**——把硬约束写进 prompt 当成已执行；本 skill 把这些不变量交给 `scripts/` 代码强制。

两份外部交付物经对抗式评审后定向借鉴（见 `docs/research/05`、`06`）：**WebNovelOps**（另一 agent 独立交付的可运行 Python CLI——两 agent 独立收敛到同一架构是强信号）贡献了 `state_apply.py` 的确定性 state-delta 合并代数 + acceptance_criteria 判分桥；**oh-story-claudecode/story-deslop**（MIT，去AI味口碑强）贡献了 Gate A-G 七门 + 鲁棒「不是A而是B」检测 + `degeneration_check.py` 模型退化检测 + 对话/导入/拆文 craft。**只借 craft 与确定性检测逻辑，不搬它们的插件/CLI/抓站架构**（那正是"市面工具太重"的痛点本身）。
