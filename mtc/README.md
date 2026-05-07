# mtc

> **More Than Coding** — full product workflow from concept to code. Iterates design / story first, generates aligned data, builds the app, then polishes. For games, demos, prototypes, and interactive experiences.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The signature AX workflow for building things that aren't just CRUD apps. The premise: most code-first AI workflows produce technically-working but emotionally-flat output. MTC inverts the order — get the design and story right, generate aligned reference data, *then* build, then polish until it actually feels like the thing it should feel like.

## When to use

- "Build a game / demo / interactive experience"
- "Make a prototype of X"
- Anything where vibe / story / pacing matters as much as functionality
- "/mtc <description>"

## When NOT to use

- Standard CRUD apps, dashboards, or APIs — the design-first overhead doesn't pay off
- Bug fixes or feature additions to existing apps
- Anything where the "design" is already fixed and the work is purely implementation

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/mtc ~/.claude/skills/mtc
```

## Workflow shape

The skill orchestrates a 4-phase loop:

1. **Design / Story** — concept, narrative, aesthetic direction (no code)
2. **Aligned data** — fixtures, copy, scenarios that match the design
3. **Build** — implementation against the data, not against a blank page
4. **Polish** — pass after pass until the *feel* is right (this is where most AI workflows quit too early)

See [SKILL.md](./SKILL.md) for the full prompting contract and per-phase checklists.

## Origin

Distilled from building three found-phone puzzle games (ClassOS, Inside Job, Dead Signal, Shadow Access) with zero handwritten code, plus production work on AI companion / oracle / e-commerce apps. The pattern recurred enough to formalize.
