#!/usr/bin/env bash
# PreToolUse Bash hook — when agent tries to remove autonomous-grind marker,
# require evidence that a real verification command ran recently.
#
# Background: /goal predicates require verifiable proof, not prose. Agent can
# generate fake "tests pass" framing in chat that fools the Haiku evaluator.
# This hook adds a second gate: the marker can only be cleared when:
#   (a) user explicitly requested it (/goal clear / stop / abort), OR
#   (b) a verify command (test/build/gh checks) ran in recent Bash history.
#
# Logic:
#   1. Tool must be Bash with command matching marker rm.
#   2. If most recent user message contained /goal clear / abort / stop / cancel
#      / 停 / 清 / 取消 / 中断, allow (user-initiated abort).
#   3. Else scan last 30 Bash commands for verify pattern. If any match, allow.
#   4. Else block with directive to run verify first.

set -euo pipefail

input=$(cat)

tool_name=$(jq -r '.tool_name // empty' <<<"$input")
[[ "$tool_name" != "Bash" ]] && exit 0

cmd=$(jq -r '.tool_input.command // empty' <<<"$input")

# Only fire when removing an autonomous-grind marker
if ! echo "$cmd" | grep -qE 'rm.*\.claude/state/autonomous-grind.*\.json'; then
  exit 0
fi

transcript=$(jq -r '.transcript_path // empty' <<<"$input")
[[ -z "$transcript" || ! -f "$transcript" ]] && exit 0

# Check most recent user message for explicit abort signals
last_user_msg=$(jq -rs '
  [.[] | select(.type == "user" and (.message.content | type) == "string")] | last | .message.content // ""
' "$transcript" 2>/dev/null)

# Anchored to message/line start so "don't stop" / "stop being verbose" mid-sentence don't bypass the gate
if [[ -n "$last_user_msg" ]] && echo "$last_user_msg" | grep -qiE '^[[:space:]]*(/goal +clear|stop|abort|cancel|interrupt|停止?|停下|清除|取消|中断)'; then
  exit 0  # User-initiated abort, allow
fi

# Scan last 30 Bash tool invocations for a verify command
verify_count=$(jq -rs '
  [.[] | select(.type == "assistant")]
  | map(.message.content // [])
  | flatten
  | map(select(.type? == "tool_use" and .name? == "Bash") | .input.command // "")
  | reverse
  | .[0:30]
  | .[]
' "$transcript" 2>/dev/null | grep -cE '\b(pnpm|npm|yarn|bun) +(test|run +test|run +ci|run +build)\b|\bpytest\b|\bgo +test\b|\bcargo +test\b|\bvitest\b|\bjest\b|\bplaywright +test\b|\btsc( +--noEmit)?( |$)|\bgh +pr +checks\b|\bmake +(test|check|ci)\b|\bruff +check\b|\beslint\b|\bpnpm +build\b|\bnpm +run +build\b' || true)

if [[ ${verify_count:-0} -gt 0 ]]; then
  exit 0  # Recent verify command ran, allow clear
fi

# No verify in recent history AND not user-initiated → block
# Session id = transcript UUID (same derivation as every other autonomous-grind hook)
sid=$(basename "$transcript" .jsonl 2>/dev/null)
ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$HOME/.claude/state/autonomous-grind" 2>/dev/null
jq -nc --arg ts "$ts" --arg sid "$sid" \
  '{ts: $ts, event: "clear_blocked", session_id: $sid, reason: "no_verify_in_recent_history"}' \
  >> "$HOME/.claude/state/autonomous-grind/events.jsonl" 2>/dev/null || true

reason="autonomous-grind clear blocked: no verification command in recent Bash history (last 30 calls).

/goal predicates require verifiable proof, not prose claims of completion.
Run ONE of these (whichever fits your stack) FIRST, paste real exit-0 output, THEN clear the marker:
  pnpm test  /  npm test  /  yarn test  /  bun test
  pytest  /  go test ./...  /  cargo test  /  vitest run
  playwright test
  tsc --noEmit
  gh pr checks <PR>  (if CI is the verifier)

If the predicate is genuinely satisfied: run the command, get exit 0, THEN run the rm.
If you need to abort: ask the user to send '/goal clear' or 'stop' — that bypasses this gate.
If you ran verify in a subagent and there's no record in main transcript: rerun the command in main transcript, OR ask the user to abort the loop manually."

jq -nc --arg reason "$reason" '{decision: "block", reason: $reason}'
