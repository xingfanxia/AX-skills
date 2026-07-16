# Review Discipline (bundled reference)

The autonomy contract big-task assumes. Distilled from the author's global workflow rules so this skill is self-contained; adapt severities/passes to your own stack.

## Core stance

**The user is not the review gate.** The agent runs multipass review on ALL artifacts — code, plans, specs, designs — end-to-end before declaring done. Never ask "want to review?", "looks right?", "ready for your review?" — those outsource the agent's own quality gate.

The user reviews only:

- **High-level plan overviews at natural gates** — a scannable ~10-line objective/scope/approach view at plan approval or phase kickoff. Detail stays agent-side; this is skim-and-click-through, not a pause point.
- **Explicit sign-off gates** the user has set — surface a ≤10-line summary (objective, scope, risks, acceptance criteria), never the full plan doc.
- **Critical Decision Triggers** (see SKILL.md Phase -1): irreversible architecture, money/secrets/PII boundary, ambiguity that would invalidate shipped work, user-facing breaking change.

## Multipass chain — scale to tier, never below minimum

| Tier | Required passes |
|------|-----------------|
| Hotfix | Self-review checklist |
| Bug fix | Self-review + code-reviewer agent |
| Small feature | Self-review + code-reviewer agent + domain pass **only where a real domain reviewer exists** (Go/Python/database/security). TS/JS: code-reviewer alone — a second generic pass duplicates the same checklist |
| Large feature | big-task Phase 2c/3/4 already enforce multipass — do not duplicate |

**Triggered passes (any tier):** auth/secrets/user input/API endpoints → security review; frontend/UI → visual audit (screenshot sweep, device emulation for responsive changes); schema/migration → database review; new tests → verify behavior assertions, not mock-existence.

## Fix all findings — severity routes *how*, never *whether*

Every finding from any pass gets fixed — CRITICAL through NIT/INFORMATIONAL. The audit already paid the cost of finding the issue; declining to act on paid-for output is waste that accumulates as drift.

- **Inline (main thread)** — ≤2 files, mechanical change, ≤500 LOC to read
- **Subagent** — 3+ files, deep refactor, unfamiliar domain, or concurrency/security/payment/auth code regardless of size

The only legitimate defer: a pre-existing pattern in files **outside the current diff** — and that goes on a todo follow-up, never a forget-list. Review-bot "non-blocking" means "won't auto-block merge", not "skip it".

## Re-run gating (prevents infinite review loops)

Reviewers return ≥1 nit in essentially every round — a literal "loop until clean" never terminates. So:

- **CRITICAL/HIGH found → fix → re-run that pass** (the fix itself is risky enough to verify)
- **MEDIUM/LOW/NIT found → fix, done** — the fixes are the exit, not a new round
- **Hard cap: 2 re-runs.** Still finding new CRITICAL/HIGH after that → stop and surface the disputed decision or missing evidence instead of burning more rounds

## After review + fix → continue autonomously

When the chain completes, proceed to the next phase automatically — at ANY context usage. Instead of pausing, persist state: update the plan doc (phase done, commit hashes, next phase's entry conditions), keep the todo list current, commit the milestone — then start the next phase immediately. Auto-compaction plus on-disk state makes this safe; maintaining that state is the agent's job, not the user's.

## Report shape

Lead with the final decision/result, then evidence. Claims of completion must attach proof (green test output, screenshots, before/after numbers) — self-assessment prose is not evidence. Silence from the user = pass; don't write for applause.
