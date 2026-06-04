# AI-English Lite 种子库(给 AX 当工具用 · 不是给她背)

> 来源:`references/research/external/03-chatgpt-research.md`,经本 playbook 按内核原则过滤。
> **框架(每次取用都要带上):这是她每天操作 AI 时自然会反复用到的词,在用中眼熟(incidental),不是背诵任务。** AX 若要"生成背诵词表",按 `data/_shared/anti-monitor-guardrails.md` 劝阻并解释 Hu&Nation + 不用背几万词。

## 50 个最高价值词(操作词 / 概念词 / 游戏界面词)

她用 `summarize` 让 AI 干了 20 次活,这个词就长在脑子里了——这是"用"出来的,不是背出来的。

**AI 操作词(她指挥 AI 时会用):**
explain 解释 · summarize 总结 · translate 翻译 · rewrite 改写 · compare 比较 · generate 生成 · create 创建 · search 搜索 · check 检查 · fix 修复 · improve 改进 · list 列出 · show 展示 · teach 教 · ask 问 · answer 回答 · upload 上传 · save 保存 · export 导出 · share 分享

**AI 概念词(她读 AI 内容时反复撞见):**
AI 人工智能 · model 模型 · prompt 指令 · data 数据 · training 训练 · chatbot 聊天机器人 · agent 智能体 · tool 工具 · task 任务 · workflow 工作流 · source 来源 · bias 偏见 · privacy 隐私 · hallucination AI 一本正经胡说

**游戏界面词(她玩切英文的游戏时撞见):**
start 开始 · continue 继续 · settings 设置 · language 语言 · sound 声音 · graphics 画面 · load 加载 · weapon 武器 · shield 护盾 · health 生命值 · damage 伤害 · quest 任务 · reward 奖励 · upgrade 升级

## 10 个救命 prompt 模板(她用一个就够)

```
Explain X in simple Chinese.        用简单中文解释 X
Summarize this in 3 points.         总结成 3 点
Translate this into Chinese.        翻译成中文
Give me 5 examples.                 给我 5 个例子
Teach me step by step.              一步步教我
Use simple English.                 用简单英语(说)
Make it easier.                     讲得更简单点
Ask me one question at a time.      一次问我一个问题
What is your source?                你的来源是什么(AI 安全核查)
Is this recent?                     这是最新的吗(AI 安全核查)
```

**按内核原则剔除的两个常见模板(不放进她的清单):**
- ~~Give me a short quiz.~~ —— 自测 = 温和版考试,违反原则 7(`anti-monitor-guardrails.md`)。
- ~~Correct my English gently.~~ —— 涉及产出/被纠错,产出后置(原则 2);只有**她自己内生想说/想写**时才给,绝不主动推。

## 怎么发给她(动作 C 的转发建议)

不要一次性甩 50 个词给她——那就变成词表了。**按场景即时给一两个**:她刷到讲 agent 的视频 → 顺手说"里头那个 agent 就是'能自己干活的 AI',你以后看到它当老熟人就行,不用记"。prompt 模板由 AX 先帮她存进微信收藏,她用时复制即可。
