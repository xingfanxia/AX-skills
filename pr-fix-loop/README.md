# pr-fix-loop

> Autonomously respond to GitHub PR review feedback until all comments are resolved and CI is green. Max 5 rounds. Polls all four PR comment surfaces (formal reviews, inline comments, issue-thread comments, CI checks) — bots like `@claude` post to the issue thread, not formal reviews, so polling only one surface misses them.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The PR-stage convergence skill. After opening a PR with `@claude` review request + Qodo + CodeRabbit + CI hooks, this skill runs the self-healing loop: poll → fix → push → reply to resolved comments → re-request review → repeat until merge-ready.

## When to use

- "Fix PR comments"
- "Address review feedback"
- "Get PR green"
- "Fix CI and review comments"
- "Loop until PR passes"
- After opening a PR, want to autonomously close out before merge

## When NOT to use

- Pre-PR audit → use `audit-fix-loop` instead
- One-off comment response → just reply manually, the loop is overkill
- PR not yet opened → open it first (with `commit-commands:commit-push-pr` or similar)

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/pr-fix-loop ~/.claude/skills/pr-fix-loop
```

## What it polls (the key insight)

Most PR-loop scripts only check `gh api repos/{owner}/{repo}/pulls/<pr>/reviews` — the **formal review** surface. But `@claude` posts as an **issue comment**, not a formal review. So you need all four:

```bash
gh pr checks <pr>                                   # CI
gh api repos/{owner}/{repo}/pulls/<pr>/reviews      # formal reviews
gh api repos/{owner}/{repo}/pulls/<pr>/comments     # inline file:line comments (Qodo, CodeRabbit)
gh api repos/{owner}/{repo}/issues/<pr>/comments    # PR-thread comments — @claude bot posts HERE
```

Skipping the last one is the most common reason people falsely declare "no review yet" and fail to converge.

## Re-trigger gotcha

To re-trigger `@claude` after fixes, **POST a new comment** to `issues/<pr>/comments`. Replies-to or edits-of existing comments do NOT re-trigger the bot.

See [SKILL.md](./SKILL.md) for the full poll-fix-reply protocol and severity routing.
