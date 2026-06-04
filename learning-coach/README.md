# learning-coach

在 **Claude Code 里主动引导你学任何东西**的学习教练——一门语言、一个技术主题、一项技能。你说"我想学 X",它带着你一步步走,你只管露面、回答、往前。

为"被'背 + 考 + 被纠错'劝退过、带着'我学不好 X'焦虑"的人设计。第一目标是**不痛苦、有小赢**,其次才是进度。方法来自四方调研交叉验证(见 `references/research/`)。

## 教学循环(心脏)

1. **轻校准**(绝不考试)——学啥 / 为啥学 / 看个样本估水平
2. **喂 i-1 可理解输入**——刚好略低于你水平,把任何材料降到你能懂
3. **零评判猜读**——你用自己的话猜/复述,认出来即可,答错也接住
4. **工程化撞见**——把你见过的词/概念在后续故意复现,靠重复自然记,不背
5. **"今天懂了"**——正向小结,零打分零测验
6. **主动给下一小步**——永远递给你下一个动作,够了就停,漏天没事

详见 `data/_shared/teaching-loop.md`(含英语 + 期权两个示例 transcript,证明领域无关)。

## 红线

零背诵 · 零考试/打分/测评 · 零纠错羞辱 · 零灌输长篇 · 零施压打卡。recognition > recall;难度宁可偏易(i-1)。详见 `data/_shared/teaching-red-lines.md`。

## 领域无关 + 可选 playbook

核心对任何主题都能跑(agent 是通才 + 方法论通用)。某领域有已知难点就加 `playbooks/<domain>/`。首个是**英语**(中文母语者难点 / Hu&Nation 词汇阈值 / 窄主题 / 听读说优先级 / AI-English Lite / 学 AI 课程线)。

## 模型 & 状态

用 agent 自身,不指定模型、不调外部 API。维护轻量 session 状态(学啥/水平/撞见过的词/今天懂了清单)以支撑撞见复现 + 跨会话续学;只记正向与中性,不存任何负向/错题数据。

## 结构

```
SKILL.md                       # 主动引导式教练编排 + 教学红线 + 验收标准
data/_shared/                  # 领域无关教学内核
  teaching-loop.md             #   ★ 教学循环(心脏)+ 示例 transcript
  principles.md                #   诊断 + 8 学习/教学原则
  tutor-voice.md               #   导师 voice(鼓励不鸡汤、把难的说人话)
  reframe-scripts.md           #   "我学不会"等卡点的即时降焦虑回应
  teaching-red-lines.md        #   拒绝清单
playbooks/english/             # 首个可选垂类
references/research/           # 教学方法事实地基(先读 00)
ROADMAP.md                     # 产品族路线图(含 2026-06-02 pivot 说明)
```

## 状态

v0.2 MVP(pivot 后):主动引导式通用教练已可用(纯 prompt + data/,会话状态可选)。早期版本(陪伴者转发工具箱)已转向,历史见 `ROADMAP.md` 顶部 PIVOT 说明。

License: MIT。
