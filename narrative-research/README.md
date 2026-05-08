# narrative-research

> 横纵分析法（Horizontal-Vertical Analysis）深度调研 — 双轴叙事型研究报告。**纵轴**追溯一个对象从诞生到当下的完整生命历程，**横轴**在当下与竞品/同类做系统性对比，交叉两条轴产出独到洞察，最终输出一份排版精美的 PDF。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The narrative counterpart to [`deep-research`](../deep-research/). Where `deep-research` verifies claims to make a decision, `narrative-research` builds understanding from zero — what happened, why, who's involved, what comes next, who else is doing similar things.

## When to use

- "帮我研究一下 X / X 是什么来头 / X 的来龙去脉 / 帮我搞懂 X"
- "Tell me the full story of X" / "What's going on with company Y?"
- "Walk me through how this trend developed"
- Background research before writing a long-form piece

## When NOT to use

- Need a yes/no decision → use [`deep-research`](../deep-research/)
- Just need a one-paragraph summary → use a basic summarization skill

## How it works

The "横纵 (Horizontal-Vertical)" name comes from the dual-axis structure:

- **纵轴 (Vertical / 历时)** — lifecycle in narrative form: founding, key events, version history, funding, strategic pivots, crises
- **横轴 (Horizontal / 共时)** — competitive cross-section: identify competitors, compare features / user reception / market share / industry position
- **交叉 (Cross)** — synthesize axis findings into insights neither axis could surface alone

Method origin combines Saussure's diachronic-synchronic linguistics, social-science cross-sectional research design, business-school case study method, and competitive strategy analysis.

## Output

Markdown research report + PDF rendered via the bundled `scripts/md_to_pdf.py` (uses WeasyPrint). Schema in `references/schema.json` for downstream tools.

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills

# Codex
ln -sf ~/AX-skills/narrative-research ~/.codex/skills/narrative-research
# Claude Code
ln -sf ~/AX-skills/narrative-research ~/.claude/skills/narrative-research

# PDF dependency (one-time)
pip install weasyprint markdown --break-system-packages
```

See [SKILL.md](./SKILL.md) for the full methodology, search strategy, section structure, and prompting contract.

## Credit / Attribution

The methodology and original SKILL.md are by **数字生命卡兹克 (Khazix)** — published in [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) under MIT.

This is a **modified version**: renamed from `hv-analysis` to `narrative-research` for self-explanatory naming, trigger words updated, and packaged into the AX-skills ecosystem alongside `deep-research`. **Not maintained by the original author** — for the canonical version, follow upstream.
