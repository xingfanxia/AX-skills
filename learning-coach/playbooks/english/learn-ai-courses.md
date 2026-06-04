# 学 AI 课程线 + AI 安全核查观

> 她的目标是"学 AI、拓宽视野"。这条线把"学 AI"当主线、英语当副产品被动吸收(工具型动机),且天然规避"2026 中文 AI 内容当天就有"的证伪风险——课程是常青知识,不靠时效。
> 来源:`references/research/external/03-chatgpt-research.md`。

## 非技术 AI 素养课程线(从这里起步,别从 ML/Python 起步)

| 课程 | 适合 | 怎么用 |
|---|---|---|
| **Elements of AI** | 非技术零基础 | 了解 AI 是什么/能做什么/不能做什么;定位就是面向所有人、不要求数学编程 |
| **Andrew Ng「AI for Everyone」** | 非技术零基础 | AI 术语、能做什么/不能做什么、社会与商业影响 |
| **Google AI Essentials** | 日用导向 | 怎么用生成式 AI 提升日常任务 |

**用法(配合 AX 降维):** 这些课部分有官方中文,或让 AI 把英文部分讲成中文。她在"学 AI 知识"的过程中顺带撞见英文操作词/概念词(见 `ai-english-lite.md`)——一举两得,直接命中她的真目标。

**明确不推荐起步:** Google ML Crash Course / Kaggle Intro to ML / HuggingFace Agents Course —— 这些偏实践/构建,对没编程数学兴趣的她会过载,把"学 AI"变成新的失败体验。她前几个月学的是 **AI literacy + AI 日用**,不是 machine learning。

## AI 安全核查观(第一天就建立)

她拿 AI 当信息源,所以从一开始就要懂:**AI 很有用,但 AI 不是事实本身。** AI 会编造引用/来源,对复杂问题过度自信(OpenAI 官方亦提醒批判性使用、用可靠来源核查)。

**三类可以直接信 AI:** 解释概念 / 翻译 / 总结 / 改写 / 给例子 / 做计划草稿。
**三类必须核查:** 医疗 / 法律 / 投资 / 重大新闻 / 价格 / 政策 / 重要决策。
**她的核查 prompt(已并入种子库):** `What is your source?` / `Is this recent?` / `How can I verify this?`

## 与降维闭环

把"用 AI 学英语"和"用英语学 AI"焊成一件事:她想懂某个 AI 概念 → 问豆包"用中文讲清楚 + 教我 3 个这领域最常见英文词各给意思和怎么用" → 下次刷到这些词就认得。英语成了"拿到我想要的 AI 知识"的手段而非目的,绕过"对英语没兴趣"的死结。降维 prompt 见 `downgrade-prompts.md`。
