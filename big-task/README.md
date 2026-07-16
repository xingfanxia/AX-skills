# big-task

**The risk-tiered engineering workflow router.** One entry point that decides how much process a task deserves — direct execution, a light checklist path, or the full plan → parallel-subagent → multipass-review cycle — based on **risk, not file count**. A 15-file UI migration from a locked design spec is *lower* risk than a 3-file atomic credit-deduction change, and gets routed accordingly.

**54 real invocations / 23 commits of evolution** in the author's own setup (as of 2026-07) — this is the default entry for every non-trivial engineering task, refined against real regressions in both directions (over-ceremony on safe work, under-process on risky work).

## What it decides

1. **Phase 0.0 — project profile** (auto-detected from repo signals: schema/auth/payment libs, components + UI framework, content volume, e2e stack) × **task intent** (judged, not keyword-matched: does this task cross a persistence / trust / revenue / atomicity / contract boundary?) → `light` / `ui` / `heavy`
2. **Phase 0 — risk tier**: Tier 2 direct · Tier 3 light (inline plan ≤1 page, TDD, multipass review) · Tier 4 full cycle (brainstorm → plan doc → plan review → wave-based subagent execution → review gates → verification)
3. **Subagent dispatch per phase**: inline / serial-subagent / parallel-worktree / parallel-readonly — chosen by work shape, with an orchestrator-discipline contract (subagents load inputs from disk, return ≤200-token structured summaries, state lives on disk not in chat)
4. **Autonomy contract (Phase -1)**: runs through to PR-merged without confirmation pauses, EXCEPT four Critical Decision Triggers (irreversible architecture · money/secrets/PII · ambiguity that invalidates shipped work · user-facing breaking change). Every silent choice is logged in a `## Autonomous decisions` PR section — the receipt for auditing autonomy after-the-fact.

Key design positions baked in:

- **Default bias: lighter process.** Full ceremony only pays when it catches bugs direct implementation would ship. Locked-design UI work and pattern-N+1 application skip the plan-doc ritual even at 10+ files.
- **Fix all review findings** — severity routes *how* (inline vs subagent), never *whether* (see `references/review-discipline.md`).
- **Mandatory visual verification for UI phases** — screenshot sweep + multimodal compare against the design reference; static-grep tests don't catch visual drift.
- **Knowledge sync every phase** — docs/memory reconciled in the same commit as the code, not at the end.

## Dependencies

| Kind | What | Notes |
|---|---|---|
| **Required** | [superpowers](https://github.com/obra/superpowers) plugin | The Tier-4 engine: `brainstorming`, `writing-plans`, `subagent-driven-development`, `using-git-worktrees`, `requesting-code-review`, `verification-before-completion` |
| **In this repo** | [`plan-design-review`](../plan-design-review/) · [`audit-fix-loop`](../audit-fix-loop/) · [`pr-fix-loop`](../pr-fix-loop/) · [`neat-freak`](../neat-freak/) | Plan review, fix loops, per-phase knowledge sync |
| **Optional (degrade gracefully)** | `code-reviewer` / `security-reviewer` / `database-reviewer` agents, `think-ultra`, `verify`, `webapp-testing`, `frontend-design`, codegraph | Substitute your own equivalents, or run the pass inline; the routing logic doesn't change. Without codegraph, map the codebase with parallel read-only explore agents |

## Install

```bash
cp -r big-task ~/.claude/skills/big-task
```

Then either invoke explicitly (`/big-task <task>`) or add an auto-trigger rule to your `CLAUDE.md` (the author's: auto-invoke for tasks touching 3+ files, new functionality, or any schema/migration work; user overrides with "skip workflow" / "just do it").

## Shape of a run

```
Profile: heavy (repo: light; intent: task introduces a revenue boundary — Stripe paywall)
▸ Phase 1  · brainstorm + plan doc · plan-design-review clean
✓ Phase 2b · parallel-worktree (4 tasks) · 4/4 green · committed (a1b2c3d)
✓ Phase 2c · review clean (2 passes + security) · findings fixed
✓ Phase 2g · visual sweep 6/6 PASS
✓ Phase 6a · PR opened → pr-fix-loop until green
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 /big-task ▸ COMPLETE (autonomous run)
 Autonomous decisions made: · tier de-escalation on phase 3 (locked design) · …
 Critical-decision pauses: 1 (auth provider choice)
```
