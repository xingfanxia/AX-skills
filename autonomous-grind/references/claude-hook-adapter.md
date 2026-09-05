# Legacy Claude Code hook adapter

Read only when maintaining an existing Claude Code installation of these hooks
or when the user explicitly requests this adapter. Codex uses native goal
controls and must not create these marker files.

The bundled implementation is retained unchanged. Its heuristics may conflict
with current skill guidance; do not assume installing the skill installs or
enables the hooks. Inspect the live hook configuration and source before any
authorized setup change.

## Existing mechanism

The hooks read a session marker at
`~/.claude/state/autonomous-grind/<session-id>.json`, containing
`predicate`, `started_at` (ISO timestamp), and `session_id`.

Resolve the actual current Claude session from runtime-provided metadata or
the confirmed transcript path. Do not select the most recently modified
transcript in a shared project: concurrent sessions can make that wrong.
A fabricated session ID cannot activate hooks that derive a different ID.

For an explicitly selected existing adapter, `start` writes the marker for
that exact session, `status` reads it, and `clear` removes only that marker
after completion or user cancellation. Existing hook approval behavior still
applies. Do not create, remove, or modify another session's marker.

## Hook inventory and limits

- `../hooks/autonomous-keep-going.sh` scans final prose for wrap-up patterns
  during Stop events. It cannot prove the work is incomplete or complete.
- `../hooks/autonomous-no-handoff.sh` restricts selected handoff filenames;
  progress files are allowed. This is an adapter constraint, not the portable
  skill's rule.
- `../hooks/autonomous-verify-before-clear.sh` recognizes recent Bash command
  names or an explicit abort. It does not establish that a command passed or
  that the goal's acceptance criteria are met.
- `../hooks/autonomous-stale-marker-cleanup.sh` removes markers older than
  24 hours during SessionStart; this does not cancel native goal state.
- `../hooks/autonomous-grind-prompt.sh` injects legacy activation reminders
  on goal prompts. Its evaluator and unconditional pairing claims are not a
  contract for Codex or evidence about the current runtime.

Hooks use Bash and jq, Claude event payloads, transcript structure, and
`~/.claude/state/autonomous-grind/events.jsonl` telemetry. These paths and
commands belong only to the Claude adapter. Follow the actual host's event
schema when evaluating compatibility.

If a legacy hook blocks an otherwise authorized action, report the exact hook
and reason. Do not run an unrelated test command merely to satisfy its pattern,
invent verification, or silently alter the hook. Prepare any needed adapter
fix within the user's authorized scope.
