# codebase-sweep

> Full-codebase audit + cleanup loop. For when you want a *one-shot* comprehensive review of the whole project — not just recent changes. Covers code audit, iterative fix loop with test authoring, docs cleanup, architecture documentation, and orphan-script archiving.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The "fix everything that's been bugging me" skill. Scans the entire repo (not just `git diff`), runs parallel-agent audits across multiple concerns, applies fixes in a rounds-based loop until the codebase is clean, then writes/refreshes architecture docs and archives the random one-off scripts that accumulated in the root dir.

## When to use

- "Do a full codebase audit"
- "Sweep the whole codebase"
- "Full health check"
- "Clean up the whole project"
- "Write architecture docs"
- "Document the codebase"
- After inheriting a project you didn't write
- After a long sprint where docs / code-quality drifted

## When NOT to use

- Small recent changes → `audit-fix-loop` does the same shape but scoped to the diff
- Just want to write docs → `neat-freak` is lighter
- Just want a code review → use `code-review` directly

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/codebase-sweep ~/.claude/skills/codebase-sweep
```

## What it does, in order

1. **Full code audit** — parallel reviewers across security / types / tests / logic / error-handling / dead-code
2. **Iterative fix loop** — rounds until convergence; each round adds tests for fixed code + incremental doc updates
3. **Docs cleanup + reorganization** — kills stale docs, merges duplicates, normalizes structure
4. **Architecture documentation** — writes/refreshes the high-level picture if absent or drifted
5. **Script archiving** — adhoc/orphan scripts in repo root get categorized and moved to `scripts/<topic>/`

See [SKILL.md](./SKILL.md) for the convergence criteria and the per-phase contract.
