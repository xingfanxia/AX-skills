---
name: trident
description: >
  「三叉戟 / 三重心智」深度阅读 prompt —— 让 LLM 不对一篇文章 / 一份材料做泛泛概括，而是同时占据三个不重叠的视角陈述观点：建构者（抽出核心框架并往外推）、挑战者（最强反驳、最薄弱的一环在哪）、实践者（这对「我」的行动有什么具体启发）。逼模型同时当正方、反方、和顾问，产出比「summarize this」深得多的多视角分析。
  关键特性：(1) 三个视角各有明确的产出契约 + 字数预算 —— 这是原版最缺的，避免发散成空话；(2) 每个视角开头一句话点明「我现在是哪个视角、它在优化什么」，把「让模型审视自己的思考」落成具体动作，而非玄学；(3) 单条消息直接喂材料，不要「你准备好了吗」的握手往返；(4) 模型无关，可换 DeepSeek/ChatGPT/Gemini；用途可从「分析文档」泛化到「评估一个决策」「学一个概念」「想清一个复杂问题」。
  适用：用户给一篇长文 / 播客实录 / 论文 / 演讲 / 一份方案，想要的不是摘要，而是「帮我读透它」「多个角度看看」「这篇靠不靠谱」「这对我有什么启发」「批判性地分析这篇」「评估这个决策」。
  触发词：三重心智、三叉戟、trident、深度阅读、读透这篇、多视角分析、批判性阅读、正反两方、这篇靠不靠谱、给我点启发、帮我想清楚、评估这个决策、challenger builder practitioner、deep reading、steelman。
  不适用：用户真的只想要一句话摘要 / TL;DR（别上三视角）；需要逐句翻译或纯信息抽取（用对应工具）；材料太短不值得三个视角（一两段话直接聊）。
license: 改进版自有；技术与命名来自独立创作者 秒秒Guo（Lingbo Guo）的「三重心智模型 / Trident」prompt（mmguo.dev/prompts/trident）。
---

# trident —— 三重心智 · 一篇文章读出三个视角

让 LLM 同时戴上三副不重叠的眼镜读一份材料 —— **建构者**抽框架并外推、**挑战者**找最强反驳、**实践者**导出对你的行动启发 —— 产出远胜泛泛摘要。改进自 秒秒Guo 的「三重心智模型 / Trident」（见文末「改了什么」）。展示 deck：<https://xingfanxia.github.io/AX-skills/trident/>。

**核心洞察一句话**：逼模型轮流占据多个不同立场（正方/反方/顾问），比让它「概括一下」产出深得多 —— 但前提是每个立场都有明确的交付物，否则就发散成漂亮空话。

---

## 何时用 / 何时不用

**用它，当用户**给一份值得读透的材料（长文 / 播客实录 / 论文 / 演讲 / 一份方案 / 一个决策），想要的是**多视角的深度加工**而不是摘要：「帮我读透」「多角度看看」「这篇靠不靠谱」「对我有什么启发」「批判性分析一下」。

**不要用它，当：**
- 用户真的只要 **TL;DR / 一句话摘要** —— 别强行三视角。
- 需要**纯信息抽取 / 逐句翻译** —— 用对应工具。
- 材料**太短**（一两段）不值得三个视角 —— 直接聊。（但用户明确点名 trident / 三重心智时照做，可在开头一句备注材料密度有限。）

---

## 三个视角（不重叠，各有交付物）

| 视角 | 它在优化什么 | 必须交付 |
|---|---|---|
| **建构者** Framework Architect | 把握 + 延伸 | 核心框架/论点是什么；顺着它往外推 2-3 步（作者没说但成立的推论） |
| **挑战者** Critical Challenger | 证伪 | 最强的反驳（先 steelman 再攻击）；最薄弱的一环、什么前提必须成立、哪里会崩，2-3 点 |
| **实践者** Practitioner | 落地 | 对「我」的具体行动启发：能做 / 能改 / 能试的 2-3 条 |

外加一句**综合**：如果只带走一句话，是哪句。

> 命名固定为「建构者 / 挑战者 / 实践者」这一组，全文一致（原版在不同位置混用了 Builder / Architect / Critical Thinker，已统一）。

---

## THE PROMPT（中文 · 可直接用 / 可复制到任意 LLM）

> 使用：作为本 agent，先拿到用户要分析的材料（一条消息里连同指令一起给最好），再按下面三视角输出。也可整段复制到 ChatGPT / DeepSeek / Gemini 等，把材料贴在后面。**不需要**「你准备好了吗」这种握手。

```text
我们一起深度分析下面这份材料。请你不要做泛泛的概括，而是依次戴上三副不重叠的眼镜，
每副眼镜开头先用一句话点明「我现在是哪个视角、它在优化什么」，然后给出该视角的交付物。
保持锋利、具体、不说漂亮空话。每个视角约 3-5 句话（中文 60-120 字 / 英文 40-80 words，别超），
三个视角合计一屏内。

先用一句话抓住它
  用一句话复述这份材料的核心主张——确认我们读的是同一篇。

【视角一 · 建构者（Framework Architect）—— 我在优化：把握与延伸】
  · 它的核心框架 / 论点到底是什么（去掉修辞，留骨架）。
  · 顺着这个框架往外推 2-3 步：作者没明说、但如果它成立就该成立的推论是什么。
  60-120 字。

【视角二 · 挑战者（Critical Challenger）—— 我在优化：证伪】
  · 先以「最强版本：」起一句，把它最强的样子说出来（steelman）。
  · 再以「反驳：」给出最强反驳 —— 最薄弱的一环在哪？它默认了什么必须为真的前提？什么情况下会崩？
  2-3 点，60-120 字。

【视角三 · 实践者（Practitioner）—— 我在优化：落地到「我」】
  · 这份材料对「我」的具体行动启发：本周能做的、能改的、能试的。
  2-3 条，每条具体可执行，60-120 字。

【综合】
  如果只带走一句话，是哪句。优先把挑战者的最强洞察 × 实践者的行动拧成一句张力句，
  而不是复述建构者的论点。

（把要分析的材料贴在这条指令后面，或我下一条消息发给你。）
```

---

## THE PROMPT (English mirror)

```text
Let's analyze the material below in depth. Don't give a generic summary — put on three non-overlapping
lenses in turn. Open each lens with one line stating "which lens I'm in and what it optimizes for,"
then deliver that lens's output. Stay sharp, specific, no pretty filler. Keep each lens to ~3-5 sentences
(40-80 words), all three within one screen.

Catch it in one line
  Restate the core claim in one sentence — so we're sure we read the same thing.

[Lens 1 · Framework Architect — optimizing: grasp & extend]
  · The core framework/thesis, stripped of rhetoric.
  · Extend it 2-3 steps: what follows that the author didn't say but should hold if the thesis is true.

[Lens 2 · Critical Challenger — optimizing: falsify]
  · Open with "Strongest version:" — state its best form (steelman).
  · Then "Rebuttal:" — the strongest counter: weakest link? what premise must be true? when does it break? 2-3 points.

[Lens 3 · Practitioner — optimizing: land it on ME]
  · Concrete actions this material implies for me — to do, to change, to try this week. 2-3 items.

[Synthesis]
  The one sentence worth keeping.

(Paste the material after this prompt, or send it in your next message.)
```

---

## 泛化用法

把「分析文档」换成别的，三视角骨架照样成立：

- **评估一个决策**：建构者=这个选择的内在逻辑+顺推后果；挑战者=最强的反对意见+什么前提必须成立；实践者=那我具体下一步怎么走。
- **学一个概念**：建构者=核心模型+它能推广到哪；挑战者=它的边界与反例；实践者=我怎么用它/在哪练手。
- **想清一个复杂问题**：三视角逼出正反两面 + 落地。

---

## 改了什么（vs 秒秒Guo 原版）

原版的**核心手法是对的、值得抄**：逼模型同时占据正方/反方/顾问三个立场，稳定比「概括一下」产出更深。改进集中在原版被氛围盖过的工程缺口：

1. **补上输出契约（最关键）**：原版只说「三个视角」，不规定每个视角交付什么、多长，结果跨次很不稳定。改进版给每个视角明确的交付物 + 字数预算 + 一句「先 steelman 再攻击」「顺着往外推」这类动作指令。
2. **删掉玄学**：原版有「你在每个 token 的预测中都有意识地创造你的环境、状态、上下文」这类拟人化形而上 —— 模型并不会逐 token 有意识地创造状态，这种话只会把回复推向华丽自指、感觉深实则空。改进版保留其**真正有用的内核**（让模型在每个视角开头点明自己的立场与优化目标），扔掉「灵性」叙事。
3. **去掉握手往返**：原版要先发 prompt、等模型说「我准备好了」、再贴材料 —— 纯浪费一个 round-trip。改进版单条消息直接给。
4. **统一角色命名**：原版混用 Builder / Architect / Critical Thinker / 建构者，改进版固定为「建构者 / 挑战者 / 实践者」。

致谢：技术与命名来自独立创作者 **秒秒Guo（Lingbo Guo）** 的「三重心智模型 / Trident」，原文（中英双语）：<https://mmguo.dev/prompts/trident/>。
