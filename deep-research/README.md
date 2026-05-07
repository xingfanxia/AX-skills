# deep-research

> Verification-style research — multi-agent parallel investigation, cross-validation across Tier 1-4 source authority levels, traceable workflow producing a decision memo.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The point of this skill is **judging the truth and credibility of claims**, not summarizing topics. Use it when you need to make a decision and want a defensible audit trail of where each fact came from.

## When to use

- "Should I pick A or B?" / "Is X reliable?" / "Evaluate Y for me"
- Technical evaluation, competitive analysis, vendor comparison
- Industry feasibility judgments
- Anything where you need to verify claims and trace sources

## When NOT to use

- You just want to learn about a topic from scratch — use a different research skill that prioritizes narrative coherence over verification
- You already trust the source — just read it directly

## How it works

1. Decomposes the question into verifiable sub-claims
2. Spawns parallel research agents per claim
3. Each finding is rated by **source tier** (Tier 1: primary / authoritative → Tier 4: anonymous / opinion)
4. Cross-validates by requiring multi-tier corroboration
5. Produces a decision memo with citations, confidence levels, and a clear recommendation

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/deep-research ~/.claude/skills/deep-research
```

See [SKILL.md](./SKILL.md) for the source tier criteria and decomposition protocol.
