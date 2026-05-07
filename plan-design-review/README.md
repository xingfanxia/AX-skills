# plan-design-review

> Design-completeness review for implementation plans. Rates 7 dimensions 0-10, detects AI-slop patterns, builds interaction state tables. Catches the gaps before code goes in.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A reviewer skill for `PLAN.md` / design docs / spec docs. Reads the plan, scores it across 7 design dimensions (clarity, completeness, error states, edge cases, etc.), and flags AI-slop patterns (vague hand-waving, missing error paths, "TODO" placeholders that won't actually get filled, fake interaction tables).

## When to use

- Just finished writing a plan / spec / design doc — review it before execution
- Reviewing someone else's PLAN.md before approving for implementation
- "/plan-design-review" / "review this plan"
- Any time you want a structured second opinion on a plan's completeness

## When NOT to use

- Reviewing actual code → use `code-review` or a language-specific reviewer instead
- Reviewing for *bugs* → wrong tool; this finds *gaps*, not bugs

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/plan-design-review ~/.claude/skills/plan-design-review
```

## What it produces

- Per-dimension score (0-10) with reasoning
- Interaction state table (states × triggers × outcomes) — fills gaps the plan missed
- AI-slop detector verdicts on common patterns
- Concrete fix list, ordered by severity

See [SKILL.md](./SKILL.md) for the 7 dimensions and the AI-slop patterns it screens for.
