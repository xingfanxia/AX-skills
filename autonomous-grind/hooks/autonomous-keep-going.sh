#!/usr/bin/env bash
# Stop hook — when autonomous-grind marker is active, blocks Stop events
# that contain wrap-up patterns. Forces the agent to continue with concrete
# action instead of writing status reports and stopping.
#
# Source rule: ~/.claude/skills/autonomous-grind/SKILL.md
# Safe to chain with other Stop hooks (runs independently; exits 0 when inactive).
#
# Logic:
#   1. If stop_hook_active=true (harness loop guard) → exit 0
#   2. If no transcript path → exit 0
#   3. If marker file absent → exit 0 (not in autonomous mode)
#   4. Scan last assistant text for wrap-up patterns
#   5. If 1+ strong wrap-up pattern matches → block with continuation directive
#   6. Else → exit 0 (let /goal evaluator decide normal flow)

set -euo pipefail

# CJK regexes below degrade to byte-matching under C locale — pin UTF-8.
export LC_ALL=en_US.UTF-8

input=$(cat)

# Loop guard
if [[ "$(jq -r '.stop_hook_active // false' <<<"$input")" == "true" ]]; then
  exit 0
fi

transcript=$(jq -r '.transcript_path // empty' <<<"$input")
[[ -z "$transcript" || ! -f "$transcript" ]] && exit 0

# Derive session marker path
session_id="$(basename "$transcript" .jsonl)"
marker="$HOME/.claude/state/autonomous-grind/${session_id}.json"

# Marker absent → not in autonomous mode → normal stop
[[ ! -f "$marker" ]] && exit 0

# Read predicate (best-effort — falls back to "active")
predicate=$(jq -r '.predicate // "active"' "$marker" 2>/dev/null || echo "active")

# NOTE (2026-07-10): review-ask-blocker.sh and neat-freak-reminder.sh carry a
# stale-text guard (skip grading when tool activity follows the last text
# entry — transcript-flush race). It is DELIBERATELY absent here: in grind
# mode a false "keep going" nudge is harmless (continuation is what the loop
# wants), while the guard would let wrap-up prose evade the hook entirely by
# appending one trivial tool call before stopping. Asymmetric costs, opposite
# choice. Do not "fix" this by copying the guard over.

# Get last assistant text block
last_text=$(jq -rs '
  ([.[] | select(.type == "assistant" and ((.message.content // []) | any(.type? == "text")))]
   | last
   | (.message.content // [])
   | [.[] | select(.type? == "text") | .text]
   | join(" "))
  // ""
' "$transcript" 2>/dev/null || echo "")

# No assistant text → nothing to evaluate, normal stop
[[ -z "$last_text" ]] && exit 0

# Recent window — last 2500 chars of last assistant text
recent=$(echo "$last_text" | tail -c 2500)

wrapup=0
matched=()

# Pattern 1 — handoff narrative
# "Where to pick up next session", "next session", "handoff", "HANDOFF.md"
if echo "$recent" | grep -qiE 'where to (pick up|leave off|continue|resume)|next session|hand[- ]?off|HANDOFF\.md|STATUS\.md|next[- ]session'; then
  wrapup=1
  matched+=("handoff narrative")
fi

# Pattern 2 — phase-complete header
# "CORE-1 Part 2 complete", "Phase X done", "Stage X complete"
if echo "$recent" | grep -qE '\b([A-Z][A-Z0-9]*-[0-9]+|Phase [0-9]+|Stage [A-Z]|Part [0-9]+|Step [0-9]+) +(Part +[0-9]+ +)?(complete|done|shipped|finished)\b'; then
  wrapup=1
  matched+=("phase-complete header")
fi

# Pattern 3 — stats / summary / coverage / results section header
# Detects multi-line section headers, not just any mention of "stats"
if echo "$recent" | grep -qE '(^|\n)[ ]*(#{1,3} +)?(Stats|Summary|Results|Coverage|Recap|Status)([: ]*$|\n[- *])'; then
  wrapup=1
  matched+=("stats/summary section header")
fi

# Pattern 4 — ready-to-merge signal
if echo "$recent" | grep -qiE '\bready (to|for) (merge|ship|review|PR|push|deploy)\b|all (green|done|tests pass)[, .]{0,5}(ready|merged|shipped|done)\b'; then
  wrapup=1
  matched+=("ready-to-merge signal")
fi

# Pattern 5 — commit hash + completion framing
if echo "$recent" | grep -qE '\bcommit +[0-9a-f]{7,40}\b' && \
   echo "$recent" | grep -qiE '\b(complete|shipped|finished|merged|done|ready)\b'; then
  wrapup=1
  matched+=("commit hash + completion framing")
fi

# Pattern 6 — checkbox/bullet summary block (≥3 lines starting with - or numbered)
# Indicates the agent is enumerating past accomplishments rather than doing work
bullet_count=$(echo "$recent" | grep -cE '^[ ]*(-|\*|[0-9]+\.) +(\S)' || true)
if [[ ${bullet_count:-0} -ge 4 ]] && echo "$recent" | grep -qiE '\b(done|complete|shipped|tests pass|green|coverage|merged)\b'; then
  wrapup=1
  matched+=("bullet-summary enumeration")
fi

# Pattern 7 — Chinese wrap-up prose
# "做完了 / 搞定 / 告一段落 / 收尾 / 总结 / 下次 session / 阶段性完成"
if echo "$recent" | grep -qE '做完了|搞定了?|搞掂|完事了?|大功告成|告一段落|可以收(工|尾)了?|收工了?|大致(完成|搞定)|总结一下|小结一下|回顾一下|复盘一下|下次 ?session|下个 ?session|下次会话|下回继续|下次继续|这(一|个)?(阶段|期|轮|环节)(完成|结束|搞完|交付)|阶段性(完成|成果|结束|交付)|本期任务(完成|结束)|可以放一放|准备收尾|准备结束|这(里|个)就告一段落|这次就到这|今天就到这|先到这(里|儿)?(吧|了)?([[:space:]。!！,，]|$)'; then
  wrapup=1
  matched+=("CN wrap-up prose")
fi

# Pattern 8 — Chinese "next steps for next session" narrative
# "下次继续 / 接下来你可以 / 下次再做"
if echo "$recent" | grep -qE '下次再(做|搞|继续|跑|写)|改天再|明天再|下次会话(继续|做|搞)|留给下次|留到下次|留到下个 ?session|接下来你可以|后续(工作|任务)是|后面要做的'; then
  wrapup=1
  matched+=("CN handoff narrative")
fi

# No wrap-up patterns → exit 0, let /goal evaluator decide
[[ $wrapup -eq 0 ]] && exit 0

# Build reason
joined=$(IFS=', '; echo "${matched[*]}")

# Telemetry — log block event to events.jsonl
ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$HOME/.claude/state/autonomous-grind" 2>/dev/null || true
jq -nc --arg ts "$ts" --arg sid "$session_id" --arg matched "$joined" --arg pred "$predicate" \
  '{ts: $ts, event: "stop_blocked", session_id: $sid, matched: $matched, predicate: $pred}' \
  >> "$HOME/.claude/state/autonomous-grind/events.jsonl" 2>/dev/null || true

read -r -d '' reason <<EOF || true
AUTONOMOUS-GRIND ACTIVE — wrap-up patterns detected: ${joined}.
Active predicate: ${predicate}
Wrap-up prose mid-loop is the failure mode this hook exists to catch. The next turn MUST be a TOOL CALL (write the next failing test, run pnpm test / tsc / go test, edit the next file, commit). It MUST NOT be:
  - another status summary
  - a "Where to pick up next session" section
  - a Stats / Coverage / Recap block
  - a phase-complete announcement
  - prose claiming the work is done
If the predicate is genuinely satisfied, the LAST item in your turn must be tool output (test exit 0, build green, gh checks green) — not prose. To end the loop legitimately:
  1. Run the verification command (pnpm test, gh pr checks, etc.) — paste real exit-0 output
  2. Invoke Skill(skill="autonomous-grind", args="clear")
  3. Then a one-line confirmation
Right now: identify the SINGLE next concrete action and execute it via a tool call. No prose.
EOF

jq -nc --arg reason "$reason" '{decision: "block", reason: $reason}'
