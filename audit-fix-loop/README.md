# audit-fix-loop

> Multi-round code-quality pass on recent changes. Runs `code-reviewer` audits and parallel fix agents in a loop until no high-confidence issues remain. Each round adds tests for fixed code and incremental doc updates.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The convergent companion to `codebase-sweep`. Where `codebase-sweep` is for the whole repo, `audit-fix-loop` is scoped to recent changes — the diff you just shipped, the PR you just opened, the feature you just finished. Loops until clean, capping at 5 rounds to prevent infinite spiraling.

## When to use

- "Audit and fix"
- "Review and fix all issues"
- "Keep fixing until clean"
- "Iterative fix cycle"
- After finishing a feature, before opening a PR
- After a multi-file refactor where you want to be sure nothing slipped

## When NOT to use

- Whole-codebase scope → use `codebase-sweep`
- Just want a single review pass → use `code-review` directly without the loop
- PR-stage CI/review feedback → use `pr-fix-loop` (handles `@claude` review comments + CI)

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/audit-fix-loop ~/.claude/skills/audit-fix-loop
```

## Per-round contract

Each round:
1. Run `code-reviewer` audit
2. Aggregate findings, dedupe
3. Spawn parallel fix agents (one per cluster of related findings)
4. Each fixed file gets unit + integration test scaffolding
5. Incremental doc updates (route lists, env tables, integration guides)
6. Re-audit; if zero high-confidence findings → exit; otherwise → next round

Caps at 5 rounds. If still not converged, escalates remaining issues to a fresh opus subagent rather than deferring.

See [SKILL.md](./SKILL.md) for the convergence criteria and severity-routing rules.
