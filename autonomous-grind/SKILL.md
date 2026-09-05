---
name: autonomous-grind
description: Maintain follow-through during an explicitly requested persistent goal or autonomous run. Keep the current objective, evidence, and stop conditions intact across phases and interruptions. Use native goal controls where available; optional legacy Claude hooks are a separate adapter.
metadata:
  version: "1.0.0"
---

# Autonomous Grind

Continue the user's authorized work until its completion condition is verified,
the user stops it, or a concrete blocker requires input.

## Active contract

Use this skill for an explicitly requested persistent run or when the user
invokes it, not for every ordinary multi-step task. Identify the intended
outcome, acceptance evidence, authorized actions, and user-set limits from the
conversation. Reuse the active contract; do not invent a new goal or broaden
scope at each phase.

A request to keep working preserves momentum, not permission for additional
commits, remote messages, merges, deployments, deletions, or memory promotion.
Honor those actions when already authorized. Follow later corrections without
dropping unfinished earlier requirements unless the user cancels or replaces
them.

## Native goal lifecycle

Inspect the current runtime's available goal controls and obey their actual
contracts. In Codex, use the native goal read/create/update capabilities when
available:

- Read an existing goal before creating another.
- Create a persistent goal only when the user explicitly requests one.
- Preserve its objective and user-set budgets. Do not invent token budgets or
  treat a budget limit as successful completion.
- Mark complete only after every acceptance criterion has supporting evidence.
- Mark blocked only under the runtime's documented blocked-status conditions;
  a quiet monitor, phase boundary, or hard task alone is not a blocker.
- Use the runtime's supported cancellation mechanism when the user stops.
  If the tool cannot cancel, stop task actions and state that limitation;
  never mislabel cancellation as completion.

`start <predicate>` identifies the contract to pursue; `status` reports its
current evidence and remaining work; `clear` means end this skill's active
discipline, with native goal state handled according to the actual outcome.
Do not interpret `clear` as proof the goal was achieved.

If native persistence is unavailable, keep working within the session and
state that cross-turn continuation is not guaranteed. Do not emulate native
goal state with Claude transcript paths or marker files in Codex.

## Working discipline

Give concise progress updates while continuing concrete work. A status answer,
passing test, or milestone commit does not end an unfinished objective.
Continue into the next authorized task without a phase-approval question.

Keep acceptance criteria and unresolved questions visible. Use a durable
ledger only when continuity or drift needs it, and follow the project's
location conventions. A useful progress note or user-requested handoff is
allowed; a handoff artifact cannot substitute for completing work.

Run meaningful checks for the changed behavior and required project contracts.
Reuse passing evidence until changes invalidate it. The last command need not
be a test if evidence already establishes completion, and running a command
with a test-like name is not proof of success.

When a decision cannot be inferred, prepare concrete options and ask for the
missing input after completing independent authorized work. For monitoring,
use available event/status/wait mechanisms, remain responsive to steering, and
do not classify unchanged external state as failure.

## Completion and adapters

Conclude with the outcome and evidence when the contract is satisfied. If
stopped or blocked, say what remains and why; do not claim success to exit a
loop. Normal communication is compatible with persistence.

The existing [Claude hook adapter](references/claude-hook-adapter.md) applies
only to a Claude Code installation already configured to use these hooks, or
when the user explicitly requests that setup. Read it only in that situation.
The bundled hooks are legacy heuristics, not Codex goal controls or proof that
the acceptance criteria hold. This skill does not install or modify hooks.
