# hv-analysis

> 虎嗅 (Huxiu) 风格深度分析与叙事性研究报告 — 系统性追溯一个事件 / 公司 / 趋势的"来龙去脉"，输出结构化的叙事报告（不是验证型决策备忘录）。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The narrative counterpart to [`deep-research`](../deep-research/). Where `deep-research` is for **judging claims to make a decision**, `hv-analysis` is for **understanding a thing from zero** — what happened, why, who's involved, what comes next.

Output is a structured analytical report with sections, references, and a `schema.json` describing the document structure for downstream tools.

## When to use

- "Tell me the full story of X"
- "What's going on with company Y?"
- "Walk me through how this trend developed"
- Background research before writing a long-form piece

## When NOT to use

- Need a yes/no decision → use [`deep-research`](../deep-research/)
- Just need a summary of one article → use a simple summarization skill

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills

# Codex-side
ln -sf ~/AX-skills/hv-analysis ~/.codex/skills/hv-analysis
ln -sf ~/AX-skills/hv-analysis ~/.claude/skills/hv-analysis
```

## Output

The skill produces a markdown report following the schema in `references/schema.json`, optionally PDF-rendered via the included `scripts/md_to_pdf.py`.

See [SKILL.md](./SKILL.md) for the full analysis methodology and section structure.
