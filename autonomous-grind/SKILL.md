---
name: autonomous-grind
description: Activate BEFORE starting any /goal or self-driven autonomous loop. Suppresses end-of-turn status summaries, handoff prose, and "where to pick up next session" wrap-ups that prematurely signal completion. Companion hooks block Stop events when wrap-up patterns appear mid-loop, and block writes to HANDOFF/STATUS/NEXT-SESSION files until the loop is explicitly cleared. Invoke once at loop start with `start <predicate>`; clear on completion with `clear`. Composes with /goal — does not replace it.
version: 1.0.0
---

# Autonomous Grind

Hardens autonomous loops (especially `/goal`) against the model's RLHF-trained reflex to wrap up at "natural milestones." Without this, the agent writes a clean status report at every phase boundary and stops — even when the loop has hours of work left and the user explicitly asked it to keep going.

## When to use

**Always** when:
- User typed `/goal <predicate>` and the loop is expected to span more than 1-2 turns
- User said "keep going", "don't stop", "work through the whole thing", "autonomous", "ralph mode"
- About to enter a multi-phase build, migration, or test-sweep where each phase will tempt a status report

**Optional** when:
- Single Tier 2 bug fix (one test, one commit) — wrap-up is fine here, the work IS done
- Pure brainstorming / spec writing — no execution to grind on

## What it does (mechanism)

This skill writes a session-scoped marker file at `~/.claude/state/autonomous-grind/<session-id>.json`. While that marker exists:

1. **Stop hook** (`autonomous-keep-going.sh`) scans the agent's last text on every Stop event. If wrap-up patterns appear, the hook **blocks the stop** and re-prompts the agent to continue with concrete action — no summary prose.
2. **PreToolUse hook** (`autonomous-no-handoff.sh`) blocks Write/Edit/MultiEdit on filenames matching `HANDOFF*`, `STATUS*`, `NEXT-SESSION*`, `WHERE-WE-LEFT-OFF*`, `SESSION-NOTES*`, `RECAP*`, `SUMMARY*`. These are **cross-session handoff artifacts** — distinct from within-loop progress tracking. `PROGRESS*` is **intentionally NOT blocked** (per AX 2026-05-18): logging stage progress to a doc is fine; the real failure mode is stopping-to-check-in, which the Stop hook catches via prose patterns.

The marker file is your "I'm in deep work mode" flag. Hooks read it; if absent, they exit cleanly and normal behavior resumes.

**Auto-cleanup on stale markers:** `autonomous-stale-marker-cleanup.sh` runs on every SessionStart and removes any marker file older than 24h. Crashed sessions don't permanently lock future sessions into hostile mode.

**Verify-before-clear gate:** `autonomous-verify-before-clear.sh` PreToolUse Bash hook intercepts attempts to `rm` the marker file. It allows the clear ONLY if (a) the most recent user message was an explicit abort (`/goal clear`, `stop`, `abort`, `cancel`, `停`, `清除`, `取消`, `中断`), OR (b) a verification command (pnpm test, pytest, go test, cargo test, vitest, jest, playwright test, tsc, gh pr checks, build) ran in the last 30 Bash invocations. This closes the "fake verify in prose" loophole — the Haiku evaluator reads transcript, but this hook reads actual tool-call history.

**Telemetry:** every hook fire writes a JSONL event to `~/.claude/state/autonomous-grind/events.jsonl`. Events: `stop_blocked`, `write_blocked`, `clear_blocked`, `stale_cleanup`. Use this to assess actual reliability — `tail -f` the file during a long loop to see when hooks fire, what they catch, and which patterns trip falsely.

## Activation — what to do when this skill is invoked

### `start <predicate>` (or no args — extract predicate from recent /goal in conversation)

1. Determine session ID — this is the SAME derivation the hooks use, so they agree on the marker path. Run:
   ```bash
   # Claude Code stores transcripts at ~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl
   # The session-uuid IS the session ID. Most-recently-modified .jsonl in the encoded project dir is this session.
   proj_root="${CLAUDE_PROJECT_DIR:-$PWD}"
   # Claude Code encoding: every non-word char ([^a-zA-Z0-9_]) becomes '-'. So
   # /Users/you/dev/my-app → -Users-you-dev-my-app; a '.' becomes its own '-'. lint-allow-path
   encoded="$(echo "$proj_root" | sed 's|[^a-zA-Z0-9_]|-|g')"
   proj_dir="$HOME/.claude/projects/$encoded"
   sid="$(ls -1t "$proj_dir"/*.jsonl 2>/dev/null | head -1 | xargs -I{} basename {} .jsonl 2>/dev/null)"
   # Fallback only if projects dir lookup completely fails (rare — would mean Claude Code hasn't written a transcript yet)
   [ -z "$sid" ] && sid="unscoped-$(date -u +%Y%m%dT%H%M%SZ)-$$"
   echo "$sid"
   ```
   **Do NOT use a literal `default` fallback** — it collides across concurrent sessions (observed during dogfooding). The timestamp+PID fallback is unique per invocation.
2. Run:
   ```bash
   mkdir -p ~/.claude/state/autonomous-grind
   ```
3. Write marker file at `~/.claude/state/autonomous-grind/<session-id>.json`:
   ```json
   {
     "predicate": "<the verifiable predicate the agent is grinding toward>",
     "started_at": "<ISO 8601 timestamp>",
     "session_id": "<the session id>"
   }
   ```
4. Confirm activation in ONE LINE. Example: `Grind active — predicate: "all CORE-* phases done, pnpm test green, tsc clean, or 50 turns".`
5. Then immediately do the work. **Do not write a multi-paragraph "here's what I'll do" plan.** The /goal predicate IS the plan.

### `clear`

1. Run: `rm -f ~/.claude/state/autonomous-grind/<session-id>.json`
2. Confirm in ONE LINE. Example: `Grind cleared.`
3. Now (and only now) you may write a wrap-up summary if the user asked for one.

### `status`

1. Read marker file if present and print predicate + started_at.
2. If absent: print "no active grind".

## Agent-side discipline while marker is active

These are not suggestions. The Stop hook will catch violations and re-prompt.

### Banned end-of-turn patterns (block triggers)

English:
- "Where to pick up next session" / "Where to leave off" / "Next session" / "Next steps for tomorrow"
- "HANDOFF.md updated" / "STATUS.md is current" / handoff file references
- "Phase X complete — commit <hash>" framing where the next line is a stats block
- `## Stats` / `## Summary` / `## Results` / `## Coverage` headers as the dominant section of the turn
- "Ready to merge / ready for review / ready for PR" without an active gh pr command in the same turn
- "Natural milestone / good handoff point / clean stopping place"

中文 (Chinese — added 2026-05-21 after dogfood showed CN sessions slipped through English-only patterns):
- 做完了 / 搞定 / 搞掂 / 完事 / 大功告成
- 告一段落 / 收尾 / 收工 / 可以放一放 / 准备收尾 / 准备结束
- 大致(完成|搞定) / 差不多了 / 这次就到这 / 今天就到这 / 先到这
- 总结一下 / 小结一下 / 回顾一下 / 复盘一下
- 这(一|个)?(阶段|期|轮|环节)(完成|结束|搞完|交付) / 阶段性(完成|成果|结束|交付) / 本期任务(完成|结束)
- 下次 ?session / 下个 ?session / 下次会话 / 下回继续 / 下次继续 / 留给下次 / 留到下次
- 下次再(做|搞|继续|跑|写) / 改天再 / 明天再 / 接下来你可以 / 后续(工作|任务)是 / 后面要做的

### Allowed end-of-turn patterns

- A tool call (Write, Edit, Bash, etc.) — this IS the turn's content
- A SINGLE-LINE continuation note when context has to be carried: `Next: write failing test for round.ts dealing logic.`
- A SINGLE-LINE blocker if something is genuinely blocked: `Blocked: pnpm install hanging — need user to check network.`
- Tool output (test pass, build green, gh checks green) followed by IMMEDIATELY the next tool call

### Structural rules

1. **Every turn ends in a tool call OR a one-line continuation note.** Not both. Not a paragraph.
2. **Commit messages are not summaries.** Use conventional-commit + brief body. Don't repeat the commit body in chat.
3. **Phase boundaries are HIGH RISK, not safe.** When you just committed phase N and are about to start phase N+1, the temptation to "report progress" is at its peak. Resist. The next action is reading the next phase's first task, not summarizing the last one.
4. **Estimates are traps.** If you find yourself sizing "phase N+1 will take 4-5 days," you've already mentally stopped. The relevant unit is the next 30 minutes (the next failing test). Write it.
5. **Status reports go in PR descriptions, not chat.** When the loop ends and you `gh pr create`, the PR body is the right place for stats. Mid-loop chat is the wrong place.

### When to legitimately end the loop

The hook blocks wrap-ups; you end the loop by:

1. The /goal predicate is **provably** satisfied — meaning the LAST tool output in your turn is `pnpm test` exit 0 (or equivalent verifiable proof), NOT prose claiming completion.
2. After that tool output: invoke `Skill(skill="autonomous-grind", args="clear")`.
3. Then a one-line confirmation: `Grind cleared — predicate met.`
4. Now (and only now) summary prose is allowed if asked.

## Composition with /goal

`/goal` is the Claude Code built-in that runs a Haiku evaluator after each turn to decide if the predicate holds. `autonomous-grind` is the discipline layer on top.

- **/goal** = the evaluator (decides done/not-done by reading the transcript)
- **autonomous-grind** = the writer-side discipline (stops the agent from generating fake "done" signals that fool the evaluator)

Together: the agent writes only tool calls and one-line notes; the evaluator sees only real progress; the loop runs until the predicate genuinely trips or the turn cap is reached.

**Always pair them.** Don't `/goal` without `autonomous-grind`. Don't `autonomous-grind` without `/goal` (you'll have no evaluator and no exit condition).

## Composition with /big-task and other workflows

`/big-task` Tier 4 (superpowers engine): invoke `autonomous-grind` at the start of each phase. Clear between phases (so wrap-up commit + neat-freak-reminder can run normally) then re-activate for the next phase.

`/pr-fix-loop`, `/audit-fix-loop`: these have their own convergence logic; do NOT add `autonomous-grind` on top (would conflict with their internal end-of-round summaries).

## Failure modes this prevents

The specific failure pattern the user reported:

```
CORE-1 Part 2 complete — commit 680235a

Stats
- 226/226 tests green
- ...

Where to pick up next session
1. CORE-2 — game state machine...
```

This block triggers ALL FIVE Stop-hook patterns (phase-complete header, stats section, commit hash + completion framing, handoff narrative, "next session"). With this skill active, the agent would be re-prompted before that block could close out the turn.

## Anti-patterns

- Invoking this skill but then writing a 5-paragraph "here's my plan" before the first tool call — the skill is anti-prose. Plan in tool calls.
- Forgetting to `clear` after the loop is done — subsequent turns will be hostile to legitimate summaries until cleared.
- Using this for single-turn work — overhead with no benefit. The mid-loop wrap-up reflex is the failure mode; single-turn work has no mid-loop.
