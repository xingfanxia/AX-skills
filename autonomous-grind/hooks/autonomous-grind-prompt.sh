#!/usr/bin/env bash
# UserPromptSubmit hook — detects user typing /goal and reminds the agent to
# also invoke autonomous-grind (so the discipline layer activates automatically
# alongside the Haiku evaluator).
#
# Source rule: ~/.claude/skills/autonomous-grind/SKILL.md and
# ~/.claude/rules/workflow.md → /goal guardrail #5.
#
# Decision matrix:
#   "/goal <predicate>"          → inject "also invoke autonomous-grind start"
#   "/goal clear"                → inject "also invoke autonomous-grind clear"
#   "/goal" (bare, status check) → no injection
#   anything else                → no injection
#
# Output:
#   On match, JSON with hookSpecificOutput.additionalContext field — Claude
#   Code injects that text into the agent's context for the next turn.
#   On no match, exit 0 silent.

set -euo pipefail

input=$(cat)

prompt=$(jq -r '.prompt // empty' <<<"$input")
[[ -z "$prompt" ]] && exit 0

# Normalize — trim leading/trailing whitespace, get the first line only
first_line=$(echo "$prompt" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' | head -n 1)

# Match `/goal` at the start of the message
if ! echo "$first_line" | grep -qE '^/goal(\b|$)'; then
  exit 0
fi

# Extract everything after `/goal `
rest=$(echo "$first_line" | sed -E 's|^/goal[[:space:]]*||')

# Determine which sub-case
case "$rest" in
  "")
    # Bare `/goal` — status check, no injection
    exit 0
    ;;
  "clear")
    # `/goal clear` — abort case
    additional_context=$(cat <<'EOF'
AUTO-TRIGGER (autonomous-grind-prompt hook): user issued `/goal clear` to abort the active loop.
You SHOULD also clear the autonomous-grind marker so the Stop/PreToolUse hooks stop firing:
  Skill(skill="autonomous-grind", args="clear")
This is idempotent — safe to invoke even if no marker exists. After clearing, you may write any wrap-up summary the user requested.
EOF
)
    ;;
  *)
    # `/goal <predicate>` — start case
    # Escape the predicate for safe injection (the agent will paste it verbatim)
    additional_context=$(cat <<EOF
AUTO-TRIGGER (autonomous-grind-prompt hook): user just set a /goal with predicate:
  ${rest}
Per rules/workflow.md guardrail #5, you MUST also invoke autonomous-grind so the discipline layer (banned-phrase enforcement + Stop hook + PreToolUse anti-handoff hook) activates alongside the Haiku evaluator. Invoke now with the same predicate:
  Skill(skill="autonomous-grind", args="start ${rest}")
Then proceed with the work. /goal alone does not stop you from generating fake "complete" signals — the skill + hooks do.
If this /goal is expected to span ≤2 turns (very small Tier-2 bug fix), invocation is optional. For anything longer, it is mandatory.
EOF
)
    ;;
esac

jq -nc --arg ctx "$additional_context" '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: $ctx
  }
}'
