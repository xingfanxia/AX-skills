---
name: pr-fix-loop
description: Use this skill when the user asks to "fix PR comments", "address review feedback", "get PR green", "fix CI and review comments", "loop until PR passes", or wants to autonomously respond to GitHub PR review feedback until all comments are resolved and CI is green. Max 5 rounds.
version: 1.0.0
---

# PR Fix Loop Skill

Autonomously respond to GitHub PR review comments and CI failures. Each round: pull comments + CI status, fix issues, push, re-request review, wait, repeat. Stops when all comments are resolved and CI is green, or after 5 rounds.

---

## Prerequisites

```bash
gh pr view   # confirm PR exists and get PR number
```

If no PR exists, stop and tell the user to create one first.

---

## Loop Structure

```
Round N (max 5):
  1. Pull PR state — review comments + CI status
  2. Triage: anything actionable?
  3. If yes → parallel fix agents → commit → push
  4. Post "@claude review" comment to re-request review
  5. Wait 10 minutes
  6. Back to 1
  7. If clean → DONE
```

---

## Step 1 — Pull PR State

**CRITICAL: You must check BOTH comment APIs.** GitHub stores review feedback in two separate endpoints, and missing one will cause you to declare DONE while comments still exist:

1. **Inline review comments** (`/pulls/{pr}/comments`) — file:line annotations from review bots like Qodo, CodeRabbit
2. **Issue comments on the PR** (`/issues/{pr}/comments`) — top-level comments including review summaries from Claude bot, persistent reviews from Qodo, and CI workflow outputs

Run in parallel:

```bash
# Inline review comments (file:line annotations)
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | select(.position != null) | {file: .path, line: .line, body: .body, created_at: .created_at}'

# Top-level PR comments — THIS IS WHERE CLAUDE BOT POSTS REVIEWS
gh api repos/{owner}/{repo}/issues/{pr}/comments \
  --jq '.[] | {user: .user.login, body: .body[:500], created_at: .created_at}'

# Review decisions (CHANGES_REQUESTED, APPROVED, etc.)
gh api repos/{owner}/{repo}/pulls/{pr}/reviews \
  --jq '.[] | {state: .state, body: .body}'

# CI check status
gh pr checks {pr}

# Overall PR view
gh pr view {pr} --json reviews,reviewDecision,statusCheckRollup
```

When filtering by timestamp to find "new" comments since your last push, use the **actual push timestamp** — not a stale value from a previous round.

Classify findings:

| Type | Source | Action |
|------|--------|--------|
| Unresolved inline comment | `/pulls/{pr}/comments` (file:line) | Fix code at file:line |
| Claude/Qodo summary in issue comment | `/issues/{pr}/comments` | Fix every flagged issue |
| Change requested (review) | `/pulls/{pr}/reviews` state | Address all reviewer concerns |
| CI failing | `gh pr checks` | Fix failing check |
| CI pending | `gh pr checks` | Wait (don't fix yet) |
| All resolved + CI green | — | DONE |

---

## Step 2 — Triage

If **all** of the following are true, STOP — PR is ready:
- No unresolved inline comments
- No "CHANGES_REQUESTED" review decisions
- All CI checks passing (no failures, no pending that could fail)

Otherwise, categorize work:
- **Code changes needed** → spawn fix agents
- **CI config / infra failure** → spawn infra fix agent
- **Flaky CI** (same check failing with no code relation) → note it, don't loop on it

---

## Step 3 — Parallel Fix Agents

Group comments by file/layer. Spawn fix agents **in parallel**, one per layer:

- Each agent receives: the specific comments for its files, the full file context
- Use `claude-opus-4-6` for logic/design feedback
- Use `claude-sonnet-4-6` for style, naming, formatting feedback
- Each agent resolves all comments in its scope and edits the files

For CI failures, read the failing check logs:
```bash
gh run view <run-id> --log-failed
```
Then spawn a fix agent with the full error log.

---

## Step 4 — Verify Locally, Then Commit & Push

**Before pushing, run the cheapest local check that would catch a broken fix** — affected tests + lint/build, or the repo's `make verify` / `pnpm verify` if fast. Every push burns a full CI run and re-triggers every review bot; a push that fails CI on something a local run would have caught wastes the round. CI confirms — it never discovers.

```bash
# local gate first (affected tests / lint / build)
git add <file1> <file2> ...   # stage only the specific files you changed
git commit -m "fix: address PR review comments (round N)"
git push
```

**Important:** Do NOT use `git add -p` — it is interactive and will hang in Claude Code. Always list the specific files you modified.

---

## Step 5 — Re-request Review

Post a comment to trigger a new review pass. The comment body is configurable — the default is `@claude review`, but adjust to match your project's review bot trigger:

```bash
# Default: "@claude review"
# Change REVIEW_COMMENT to match your review bot's trigger phrase
REVIEW_COMMENT="${REVIEW_COMMENT:-@claude review}"
gh pr comment <pr-number> --body "$REVIEW_COMMENT"
```

**Prerequisite:** Your repository must have a review bot configured that responds to the trigger comment. If no bot is set up, skip this step and wait for manual review.

---

## Step 6 — Wait for CI and Review

**IMPORTANT: You MUST wait at least 10 minutes** after pushing before checking for new review comments. Review bots (Qodo, CodeRabbit, Claude) take 5-10 minutes to analyze changes and post comments. Checking too early will miss new comments and cause premature "DONE" declarations.

Do NOT use `sleep 600` — it blocks the session. Instead:

1. **Wait for review bots** — use `sleep 600` inside a background command, then check:
   ```bash
   # Run in background: wait 10 min then check for new comments
   sleep 600 && gh api repos/{owner}/{repo}/pulls/{pr}/comments \
     --jq '[.[] | select(.created_at > "TIMESTAMP_OF_LAST_PUSH")] | length'
   ```
   Use `run_in_background` for this wait so the session isn't blocked.

2. **Poll CI status** every 2 minutes using `gh pr checks` until all checks complete:
   ```bash
   gh pr checks <pr-number> --watch --fail-fast
   ```
   If `--watch` is unavailable, poll manually:
   ```bash
   # Run in a loop, checking every 2 minutes
   gh pr checks <pr-number>
   ```

3. **After the 10-minute wait**, re-fetch BOTH review comments AND CI state (Step 1) before deciding whether to loop. Never declare DONE before the wait completes.

---

## Step 7 — Repeat

Go back to Step 1. On round 5, if still not clean, stop and report remaining issues to the user instead of looping again.

---

## Round Tracking

Report status after each round:

```
Round 1/5: 4 inline comments, 2 CI failures → fixing
Round 2/5: 1 inline comment, 0 CI failures → fixing
Round 3/5: 0 comments, 0 CI failures → DONE ✓
```

---

## Exit Conditions

| Condition | Action |
|-----------|--------|
| All comments resolved + CI green | DONE — report success |
| Round 5 complete, still issues | STOP — report remaining items to user |
| CI permanently broken (same failure 3+ rounds) | STOP — flag as likely infrastructure issue |
| PR closed or merged externally | STOP |

---

## Final Report

```
PR FIX LOOP COMPLETE
====================
Rounds taken:        N / 5
Comments resolved:   X
CI checks fixed:     X
Status:              READY TO MERGE / NEEDS ATTENTION

Remaining (if any):
- [file:line] comment text
- [check name] failure reason
```

---

## Key Principles

- **Never force-push** — always `git push` (append commits, preserve history)
- **One commit per round** — keeps review history clean AND caps CI/bot usage at one run per round; never push per-finding
- **Local gate before every push** — CI confirms, it never discovers (see Step 4)
- **Don't fix what isn't broken** — only touch files with explicit comments or CI failures
- **Flaky CI ≠ your bug** — if the same unrelated check fails 3 rounds in a row, flag it and don't loop on it
- **Wait for CI before declaring done** — pending checks may still fail
