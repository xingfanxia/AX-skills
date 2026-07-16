# autonomous-grind

**The discipline layer for autonomous loops.** Hardens `/goal` (and any self-driven multi-turn run) against the model's RLHF-trained reflex to wrap up at "natural milestones" — the clean status report at every phase boundary that quietly ends a loop with hours of work left.

The most-invoked skill in the author's own setup: **182 real invocations** across ~500 sessions (as of 2026-07), paired with `/goal` on essentially every autonomous run.

## The failure mode

You start an overnight loop. Three phases in, the agent writes:

```
CORE-1 Part 2 complete — commit 680235a

Stats
- 226/226 tests green
- ...

Where to pick up next session
1. CORE-2 — game state machine...
```

…and stops. The evaluator saw plausible "done" prose; the loop died at 30% with a beautiful handoff nobody asked for.

`/goal` alone can't prevent this — its evaluator reads the transcript, and the transcript is written by the same model that wants to stop. autonomous-grind is the **writer-side** fix: it makes the wrap-up prose itself impossible to emit.

## Mechanism

Invoking the skill writes a session-scoped marker file. While it exists, five hooks enforce discipline; when it's cleared (or goes stale), everything returns to normal:

| Hook | Event | What it does |
|---|---|---|
| `autonomous-keep-going.sh` | Stop | Scans the turn's last text for 8 wrap-up pattern groups (EN + 中文 — phase-complete headers, stats blocks, "next session" narrative, ready-to-merge claims, 做完了/告一段落/下次继续…). On match: **blocks the stop** and re-prompts for a concrete tool call. |
| `autonomous-no-handoff.sh` | PreToolUse (Write/Edit) | Blocks creation of `HANDOFF*`, `STATUS*`, `NEXT-SESSION*`, `RECAP*`, `SUMMARY*` files. `PROGRESS*` is deliberately allowed — in-loop progress ledgers are fine; stopping-to-check-in is the failure mode. |
| `autonomous-verify-before-clear.sh` | PreToolUse (Bash) | The marker can only be removed if the user explicitly aborted OR a real verification command (test/build/`gh pr checks`) ran in recent Bash history. Closes the "fake 'tests pass' in prose" loophole — this hook reads actual tool-call history, not claims. |
| `autonomous-stale-marker-cleanup.sh` | SessionStart | Removes markers older than 24h so a crashed session never locks future sessions into hostile mode. |
| `autonomous-grind-prompt.sh` | UserPromptSubmit | Detects `/goal <predicate>` and auto-reminds the agent to activate the grind alongside it (and to clear it on `/goal clear`). |

Every hook fire logs a JSONL telemetry event (`stop_blocked`, `write_blocked`, `clear_blocked`, `stale_cleanup`) to `~/.claude/state/autonomous-grind/events.jsonl` — `tail -f` it during a long loop to see exactly what gets caught.

## Install (Claude Code)

1. Copy the skill:
   ```bash
   cp -r autonomous-grind ~/.claude/skills/autonomous-grind
   ```
2. Copy the hooks:
   ```bash
   mkdir -p ~/.claude/hooks
   cp autonomous-grind/hooks/*.sh ~/.claude/hooks/
   chmod +x ~/.claude/hooks/autonomous-*.sh
   ```
3. Wire them in `~/.claude/settings.json` (merge into your existing `hooks` object):
   ```json
   {
     "hooks": {
       "UserPromptSubmit": [
         { "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/autonomous-grind-prompt.sh", "timeout": 5 }] }
       ],
       "SessionStart": [
         { "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/autonomous-stale-marker-cleanup.sh", "timeout": 5 }] }
       ],
       "PreToolUse": [
         { "matcher": "Write|Edit|MultiEdit", "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/autonomous-no-handoff.sh", "timeout": 5 }] },
         { "matcher": "Bash", "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/autonomous-verify-before-clear.sh", "timeout": 5 }] }
       ],
       "Stop": [
         { "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/autonomous-keep-going.sh", "timeout": 10 }] }
       ]
     }
   }
   ```

Requires `jq` (`brew install jq` / `apt install jq`).

## Usage

```
/goal all CORE-* phases done, pnpm test green, or stop after 30 turns
Skill(skill="autonomous-grind", args="start <same predicate>")
... loop runs ...
# predicate provably met (real test output, not prose):
Skill(skill="autonomous-grind", args="clear")
```

- **Always pair with `/goal`.** grind without a goal has no evaluator or exit; a goal without grind gets fooled by wrap-up prose.
- Every `/goal` predicate needs a turn cap (`or stop after N turns`) — the cap is the runaway backstop.
- Do **not** stack on loops that carry their own convergence contract (e.g. PR-fix / audit-fix loops with built-in round summaries).

## Cross-platform note

The **discipline contract** in `SKILL.md` (banned wrap-up patterns, every-turn-ends-in-a-tool-call, verify-before-clear protocol) is harness-neutral — usable as prompt-level discipline on Codex, OpenCode, or any agent harness. The **enforcement** (the five hooks) is Claude Code-specific; on other harnesses you get the discipline without the teeth.
