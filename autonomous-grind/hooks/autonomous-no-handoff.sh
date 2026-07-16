#!/usr/bin/env bash
# PreToolUse hook — when autonomous-grind marker is active, block Write/Edit/
# MultiEdit on filenames that indicate wrap-up doc creation.
#
# Source rule: ~/.claude/skills/autonomous-grind/SKILL.md
# Matched filename patterns (case-insensitive, basename only):
#   HANDOFF*, STATUS*, NEXT-SESSION*, NEXT_SESSION*,
#   WHERE-WE-LEFT-OFF*, SESSION-NOTES*, SESSION_NOTES*, RECAP*, SUMMARY*
#
# NOT blocked:
#   - README / CHANGELOG / DESIGN.md / PLAN.md / ROADMAP.md (project-structure
#     docs, not autonomous-loop handoff artifacts)
#   - PROGRESS* (explicitly allowed per AX 2026-05-18: within-loop stage
#     progress in docs is fine; only stopping-to-check-in is the failure mode,
#     and that's caught by the Stop hook's prose patterns)
#   - Any non-doc extension (added 2026-07-10): status.go, TicketStatus.tsx,
#     recap.py etc. are source files, not wrap-up docs — only .md/.txt/.rst/
#     .adoc/.org/.mdx/extensionless names go through the blocklist
#
# Logic:
#   1. If no transcript path → exit 0
#   2. If marker absent → exit 0 (not in autonomous mode)
#   3. If tool is not Write/Edit/MultiEdit → exit 0
#   4. If filename basename matches handoff pattern → block
#   5. Else → exit 0

set -euo pipefail

input=$(cat)

transcript=$(jq -r '.transcript_path // empty' <<<"$input")
[[ -z "$transcript" || ! -f "$transcript" ]] && exit 0

session_id="$(basename "$transcript" .jsonl)"
marker="$HOME/.claude/state/autonomous-grind/${session_id}.json"
[[ ! -f "$marker" ]] && exit 0

tool_name=$(jq -r '.tool_name // empty' <<<"$input")
case "$tool_name" in
  Write|Edit|MultiEdit) ;;
  *) exit 0 ;;
esac

file_path=$(jq -r '.tool_input.file_path // empty' <<<"$input")
[[ -z "$file_path" ]] && exit 0

base=$(basename "$file_path")

# Doc-extension gate (added 2026-07-10): only wrap-up DOCUMENTS are the
# failure mode. Source files that share a name (status.go, TicketStatus.tsx,
# OrderStatus.java, recap.py) were getting blocked by the *STATUS / SUMMARY
# globs during grind mode — never block anything with a code/data extension.
ext=""
[[ "$base" == *.* ]] && ext="${base##*.}"
ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
case "$ext" in
  ""|md|markdown|mdx|txt|rst|adoc|org) ;;  # doc-like (or extensionless) → keep checking
  *) exit 0 ;;                             # any other extension → not a handoff doc
                                           # (HANDOFF.html / STATUS.json would slip
                                           # through — accepted: agents write wrap-up
                                           # docs as .md, while status.json/.go/.tsx
                                           # are real source files we must not block)
esac

# Strip extension for pattern matching (so HANDOFF.md, HANDOFF.txt both match)
name="${base%.*}"

# Allow-list common project docs that share name prefixes
case "$name" in
  README|README.*|CHANGELOG|CHANGELOG.*|CONTRIBUTING|LICENSE) exit 0 ;;
esac

# Block-list — handoff/wrap-up artifact names
# Case-insensitive: convert to upper for comparison
upper=$(echo "$name" | tr '[:lower:]' '[:upper:]')

block=0
case "$upper" in
  HANDOFF|HANDOFF[-_]*|HANDOFF.*|*HANDOFF) block=1 ;;
  STATUS|STATUS[-_]*|STATUS.*|*STATUS) block=1 ;;
  NEXT[-_]SESSION|NEXT[-_]SESSION[-_]*|*NEXT[-_]SESSION) block=1 ;;
  # PROGRESS intentionally NOT blocked — within-loop stage progress in docs
  # is explicitly allowed per AX 2026-05-18. Stop hook still catches wrap-up
  # PROSE in chat (the actual failure mode: "stopping to check in").
  WHERE[-_]WE[-_]LEFT[-_]OFF*) block=1 ;;
  SESSION[-_]NOTES|SESSION[-_]NOTES[-_]*) block=1 ;;
  RECAP|RECAP[-_]*) block=1 ;;
  SUMMARY|SUMMARY[-_]*) block=1 ;;
esac

if [[ $block -eq 1 ]]; then
  predicate=$(jq -r '.predicate // "active"' "$marker" 2>/dev/null || echo "active")

  # Telemetry — log block event to events.jsonl
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  jq -nc --arg ts "$ts" --arg sid "$session_id" --arg fname "$base" --arg pred "$predicate" \
    '{ts: $ts, event: "write_blocked", session_id: $sid, filename: $fname, predicate: $pred}' \
    >> "$HOME/.claude/state/autonomous-grind/events.jsonl" 2>/dev/null || true

  read -r -d '' reason <<EOF || true
Anti-handoff guard (autonomous-grind active) — blocking write to "${base}".
Active predicate: ${predicate}
Wrap-up document creation during an autonomous loop is the leading indicator of premature completion. Finish the actual work first (next failing test, next commit, next phase verification).
To override:
  1. If the loop is genuinely complete: run verification (pnpm test exit 0, gh pr checks all green), then invoke Skill(skill="autonomous-grind", args="clear"). After clearing the marker, the handoff doc write is allowed.
  2. If this filename is unrelated to wrap-up (rare): use a different filename that doesn't match HANDOFF/STATUS/NEXT-SESSION/PROGRESS/RECAP/SUMMARY patterns.
EOF
  jq -nc --arg reason "$reason" '{decision: "block", reason: $reason}'
  exit 0
fi

exit 0
