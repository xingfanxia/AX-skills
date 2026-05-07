# khazix-writer

> 卡兹克风格中文公众号长文写作 skill — 强口语化、叙事驱动、四层自检（L1 硬性规则 → L2 风格 → L3 内容 → L4 活人感）。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Write Chinese WeChat-style long-form posts in the voice of [卡兹克 (Khazix)](https://mp.weixin.qq.com/) — a popular AI/tech blogger known for conversational tone, narrative drive, and "活人感" (felt-by-a-real-human). The skill includes a 4-layer self-check pipeline catching the AI-slop patterns most ZH content generators fall into.

## When to use

- "用卡兹克风格写一篇关于 X 的公众号长文"
- "Write me a Chinese deep-dive in khazix's voice"
- "帮我写一篇有活人感的中文长文"

## When NOT to use

- Need formal/corporate ZH tone → use a different skill
- Industry analysis / company breakdown → use [`wandian-writer`](../wandian-writer/) (晚点 LatePost style)
- Short-form (XHS / Twitter) → use a short-form skill

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/khazix-writer ~/.claude/skills/khazix-writer
```

## Coverage

The full SKILL.md (~30KB) includes:
- 5 article archetypes (调查实验 / 产品体验 / 现象解读 / 工具分享 / 方法论)
- Style internals (节奏感、文化升维、契诃夫之枪、英雄之旅 etc.)
- AI-slop kill list + 翻译腔 prevention
- L1-L4 self-check protocol with concrete pass/fail criteria

See [SKILL.md](./SKILL.md) for the full prompting contract.

## Credit

Style profile distilled from [数字生命卡兹克](https://mp.weixin.qq.com/) public posts. Used here as a writing-style reference, with full credit to the original author. The skill encodes the *style*, not the author's specific opinions or claims.
