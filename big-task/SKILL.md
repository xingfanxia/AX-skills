---
name: big-task
description: Coordinate an engineering workflow when the user explicitly invokes big-task or requests an end-to-end engineering cycle. Choose planning, implementation, review, and verification depth from actual risk and stop at the requested deliverable. Ordinary features, file counts, and refactors do not trigger this lifecycle by themselves.
---

# Big Task

Carry the requested engineering outcome through implementation and verification,
using the lightest workflow that protects it.

## Scope and authority

Read the user's request and standing project instructions together. Preserve
accepted phases, acceptance criteria, existing authorization, and user-owned
changes. A review or planning request remains read-only unless edits are
requested. Invoking this router does not itself request commits, push, PRs,
remote messages, merge, deployment, memory promotion, or repository cleanup.

Continue authorized phases without asking again at each boundary. Resolve
routine reversible choices using the repository's patterns. When a material
choice cannot be inferred, prepare the concrete options and recommendation,
ask once for the missing decision, and continue independent authorized work.
Respect explicit sign-off gates; elapsed time or silence is not approval.

## Establish the working contract

Inspect the applicable repository instructions, manifests, relevant source,
tests, and supplied references. Identify the actual source of truth before
editing generated files or copies. Keep the outcome, acceptance criteria,
scope, verification, and material unknowns visible in a short plan. Reuse an
existing plan; persist a new one only when dependencies or continuity need it.

Choose depth from ambiguity, reversibility, blast radius, and user/data impact:

| Work shape | Useful approach |
|---|---|
| Clear change following an established pattern | Implement directly and run focused checks. |
| Several dependent deliverables | Keep an acceptance checklist and execute dependency order. |
| Consequential architecture, persistence, concurrency, or public contract change | Resolve invariants and compatibility first; validate the risky path with focused evidence and specialist review when it adds confidence. |
| Unproven feasibility or unclear product direction | Investigate the consequential uncertainty before expensive implementation. |

File count, language, and the presence of a database do not determine process.
Use [profile-detection](references/profile-detection.md) for unfamiliar repos
and [routing-examples](references/routing-examples.md) for ambiguous work shapes.

## Execute and verify

Own the bounded implementation end to end. Follow established patterns, make
the requested behavior work, and update directly affected documentation when
the change makes it inaccurate. Keep unrelated refactors and housekeeping out
of the diff.

Use bounded parallel agents when independent work can improve speed or quality
and the environment permits delegation. Give each task explicit inputs,
acceptance criteria, and file ownership. Keep coupled changes sequential;
use isolated worktrees when shared state would conflict. Choose available
capabilities and models from the actual task, without fixed role counts.
Read returned evidence and integrate the result; delegation does not replace
ownership or require another generic reviewer.

Run checks that exercise the changed behavior and required repository
contracts. Add regression tests where they protect a demonstrated failure
mode. For visual changes, inspect rendered output against the relevant design
reference; choose screens and states affected by the change. Reuse passing
evidence until the diff or unresolved risk changes. Do not introduce coverage
targets, test scaffolding, or repeated full-suite runs merely to satisfy this
workflow.

Use [review-discipline](references/review-discipline.md) for consequential
review questions and [adaptation-hints](references/adaptation-hints.md) for
migrations, UI references, or AI behavior. A broad audit or PR-fix loop runs only
when it is part of the user's requested workflow. Each keeps its own scope and
completion contract.

## Finish at the requested outcome

All acceptance criteria must be implemented and supported by evidence, or
identified as unresolved with the concrete blocker. A phase boundary is not a
reason to stop while authorized work remains. A successful local build is not
proof of deployment or PR approval.

Honor authorized commit, push, PR, merge, and deployment phases when they are
in scope; do not add them as a default ending. Use repository conventions for
commit granularity and PR format. Remote review requests or bot messages need
explicit authorization in the session.

Report what changed, verification results, and material limitations with links
to the deliverable. Use [report-templates](references/report-templates.md) only
if a reporting format is useful. For explicitly requested cleanup, the
[cleanup reference](references/phase4-8track-cleanup.md) provides removal
checks; cleanup is not a final phase of ordinary implementation.
