#!/usr/bin/env bash
# SessionStart hook — clean up autonomous-grind marker files older than 24h.
#
# Background: Marker files at ~/.claude/state/autonomous-grind/<session-id>.json
# are session-scoped, but session crashes leave them behind. A stale marker
# makes future sessions enter hostile-to-summary mode for no reason.
#
# Logic:
#   1. Find all .json markers in ~/.claude/state/autonomous-grind/
#   2. For each, check mtime — if > 24h old, remove + log telemetry
#
# Disable: comment out the SessionStart entry in ~/.claude/settings.json.

set -euo pipefail

dir="$HOME/.claude/state/autonomous-grind"
[[ ! -d "$dir" ]] && exit 0

now=$(date +%s)
threshold=$((24 * 60 * 60))  # 24 hours in seconds

removed=0
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  # GNU stat first (Linux), BSD stat fallback (macOS). Separate assignments —
  # a failed stat still emits partial stdout, which would corrupt an || chain
  # inside one command substitution.
  mtime=$(stat -c %Y "$f" 2>/dev/null) || mtime=$(stat -f %m "$f" 2>/dev/null) || mtime=0
  [[ "$mtime" =~ ^[0-9]+$ ]] || mtime=0
  age=$((now - mtime))
  if [[ $age -gt $threshold ]]; then
    sid=$(basename "$f" .json)
    pred=$(jq -r '.predicate // "unknown"' "$f" 2>/dev/null || echo "unknown")
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    jq -nc --arg ts "$ts" --arg sid "$sid" --arg pred "$pred" --arg age "$age" \
      '{ts: $ts, event: "stale_cleanup", session_id: $sid, predicate: $pred, age_seconds: ($age | tonumber)}' \
      >> "$dir/events.jsonl" 2>/dev/null || true
    rm -f "$f"
    removed=$((removed + 1))
  fi
done < <(find "$dir" -maxdepth 1 -name "*.json" 2>/dev/null)

if [[ $removed -gt 0 ]]; then
  echo "[autonomous-grind] cleaned $removed stale marker(s) (>24h old)" >&2
fi

# Rotate telemetry: events.jsonl is append-only; keep only the last 500 events
ev="$dir/events.jsonl"
if [[ -f "$ev" ]] && [[ $(wc -l < "$ev") -gt 500 ]]; then
  tail -n 500 "$ev" > "$ev.tmp" && mv "$ev.tmp" "$ev"
fi

exit 0
