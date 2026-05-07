---
name: audit-fix-loop
description: Use this skill when the user asks to "audit and fix", "review and fix all issues", "keep fixing until clean", "iterative fix cycle", or wants a thorough multi-round code quality pass. Runs code-reviewer audits and parallel fix agents in a loop until no high-confidence issues remain. Each round includes unit test + integration/e2e test authoring for fixed code and incremental doc updates. Also covers docs update, adhoc/orphan script cleanup, and proper file archiving.
version: 2.0.0
---

# Audit-Fix Loop Skill v2

Iteratively audit, fix, test, and document code issues until the codebase is clean. Each round narrows scope — fixes from prior rounds can introduce new issues, so loop until convergence.

**v2 additions over v1:** Each round now includes test authoring (unit + integration/e2e) for every fix and incremental doc updates. Testing and docs are woven into the loop, not deferred to a final pass.

## When to Use

- User asks to fix "all issues" across a file or feature
- After a large refactor or multi-file change
- Before opening a PR on a complex feature
- When prior fixes may have introduced regressions
- When test coverage needs to increase alongside quality fixes

## Loop Structure

```
Round N:
  1. Audit    — parallel reviewer agents, one per layer/domain
  2. Merge    — deduplicate cross-layer issues
  3. Fix      — parallel fix agents, one per layer
  4. Test     — parallel test-authoring agents: unit tests + integration/e2e tests
  5. Docs     — incremental doc update for changed code
  6. Verify   — build → typecheck → lint → unit tests → integ tests → security → diff
  7. Repeat   — scope next round to changed files, or DONE
```

---

## Severity policy — fix everything, route by cost (NOT by severity)

**Every issue surfaced at confidence ≥80 gets fixed.** Severity (CRITICAL / IMPORTANT / MINOR) controls *how* the fix is dispatched, NOT *whether* it happens.

If the audit thought it was worth flagging, the loop owes it a fix. "Defer as MINOR follow-up" is an anti-pattern — it's how PRs accumulate the long-tail rot the audit was supposed to clean up. Never skip a flagged issue based on severity alone.

### Routing — inline vs opus subagent

Pick by **cost to main thread**, not by severity:

| Route to | When (any one trigger) |
|---|---|
| **Inline (main thread)** — Edit/MultiEdit + verify + commit | Touches ≤2 files · mechanical change (rename, add type, remove dead code, fix typo, add missing import) · well-understood domain · ≤500 lines of code to read for the fix · no new test scaffolding needed |
| **Opus subagent** — spawn `feature-dev:code-reviewer` (for review-driven fixes) or a task-scoped fix agent | Touches 3+ files · requires deep refactor (architecture change, new abstraction) · unfamiliar domain (new lib, new pattern) · 500+ lines of context to load · touches concurrency / race / security / payment / auth / data-mutation logic (regardless of size — these always go to opus for the extra reasoning budget) · requires new test scaffolding for fixed behavior |

**Subagent contract** (compress every fix to ≤200 tokens of return value):
```
{
  "issue_id": "<from REVIEW.md>",
  "status": "FIXED" | "BLOCKED" | "DEFERRED-NEEDS-DECISION",
  "files_touched": ["<paths>"],
  "summary": "<≤2 sentences: what was changed and why>",
  "verification": { "build": "PASS", "tests": "PASS|FAIL", "lint": "PASS" }
}
```

Main thread aggregates these, never sees raw fix output. This is what keeps long autonomous runs from blowing context on cosmetic refactors.

**Only valid reason to NOT fix an issue immediately:** the fix requires a Critical Decision (DB choice / auth boundary / breaking API / spec ambiguity) — escalate per big-task Phase -1. Then return `DEFERRED-NEEDS-DECISION` with the question. Tedium is not a valid reason.

---

### Step 1 — Parallel Audit

Split the codebase by layer/domain and spawn one `feature-dev:code-reviewer` agent per slice **in parallel** (all in the same message):

| Agent | Scope |
|-------|-------|
| server-reviewer | `apps/server/`, `packages/shared/` |
| client-reviewer | `apps/mobile/`, `apps/web/` |
| infra-reviewer | `scripts/`, config files, CI |

Adapt slices to the actual project structure. Use `claude-opus-4-6` for all reviewers.

Each reviewer:
- Classifies findings: CRITICAL / IMPORTANT / MINOR
- Reports only issues with confidence >= 80
- Includes file path and line number for each issue
- **NEW:** Flags functions/modules with <60% test coverage alongside code issues

After all reviewers return, merge results and deduplicate any cross-layer issues.

---

### Step 2 — Parallel Fix

Group merged issues by the same layer slices. Spawn fix agents **in parallel** (all in the same message), one per layer:

- Each agent owns distinct files — no overlap
- Use `claude-opus-4-6` for complex logic/race condition fixes
- Use `claude-sonnet-4-6` for style, dead code, console.log cleanup
- Frame each agent's task as file operations with explicit file list
- **Each fix agent records what it changed** — this drives test authoring in Step 3

---

### Step 3 — Test Authoring (NEW)

After fixes complete, spawn **parallel test-authoring agents** — one for unit tests, one for integration/e2e tests:

#### 3a — Unit Test Agent

Spawn a `tdd-guide` agent (or `go-reviewer`/`python-reviewer` for Go/Python projects):

- **Scope:** Every file modified in Step 2
- **For each changed function/method:**
  - If no test exists → write one (happy path + edge cases + error path)
  - If test exists but doesn't cover the fix → add test cases for the specific fix
  - If test exists and covers the fix → skip
- **Coverage target:** 80%+ line coverage on changed files
- **Naming:** Follow project conventions (e.g., `*.test.ts`, `*_test.go`, `test_*.py`)
- **Location:** Co-locate with source or in project's test directory — match existing convention

#### 3b — Integration / E2E Test Agent

Spawn an `e2e-runner` agent (or appropriate test agent for the stack):

- **Scope:** Any fix that touches API endpoints, database queries, auth flows, cross-service calls, or UI interactions
- **For each qualifying fix:**
  - If integration test exists → verify it covers the changed behavior, add cases if not
  - If no integration test → write one covering the end-to-end flow
- **Test categories:**
  - **API integration:** HTTP request → handler → DB → response (use real DB or test containers)
  - **Service integration:** Cross-service calls, message queue interactions
  - **E2E/UI:** Critical user flows affected by the fix (Playwright/Cypress/etc.)
- **Do NOT write integration tests for:** Pure utility functions, formatting helpers, type-only changes
- **Location:** `tests/integration/`, `tests/e2e/`, or project convention

#### Test Quality Rules

- Tests must be deterministic — no flaky timing, no external service calls without mocks
- Each test must have a clear assertion — not just "doesn't throw"
- Test names describe the behavior being verified, not the implementation
- Integration tests clean up after themselves (DB state, temp files)
- Use test fixtures/factories where the project already has them

---

### Step 4 — Incremental Doc Update (NEW)

Spawn a **docs-agent** (`claude-sonnet-4-6`) scoped to files changed in Steps 2-3:

- Update inline JSDoc/docstrings for changed functions
- Update API docs if endpoint behavior changed
- Update README sections if setup/usage changed
- Fix any `// TODO` references that are now resolved
- Add brief changelog entry if the project maintains one
- **Scope:** Only docs that directly describe changed code — don't rewrite unrelated docs
- **Skip if:** Round only had style/formatting fixes with no behavioral changes

---

### Step 5 — Verify

After fixes + tests + docs, run the full verification chain. Stop at the first failure and fix before continuing.

```bash
# 1. Build
npm run build        # or mvn compile / ./gradlew build / go build ./...

# 2. Type check
npx tsc --noEmit     # or pyright . / mvn compile / go vet ./...

# 3. Lint
npm run lint         # or ruff check . / ./gradlew spotlessCheck / golangci-lint run

# 4. Unit tests (with coverage)
npm run test -- --coverage   # or pytest --cov / go test -cover ./...

# 5. Integration tests
npm run test:integration     # or pytest tests/integration/ / go test -tags=integration ./...

# 6. E2E tests (if applicable and available)
npm run test:e2e             # or npx playwright test / pytest tests/e2e/

# 7. Security scan
grep -rn "sk-\|api_key\|console\.log" --include="*.ts" --include="*.js" src/ 2>/dev/null | head -10

# 8. Diff review
git diff --stat
```

Produce a verification summary:
```
Build:       [PASS/FAIL]
Types:       [PASS/FAIL]
Lint:        [PASS/FAIL]
Unit Tests:  [PASS/FAIL] (X/Y passed, Z% coverage → target 80%+)
Integ Tests: [PASS/FAIL] (X/Y passed)
E2E Tests:   [PASS/FAIL/SKIP] (X/Y passed)
Security:    [PASS/FAIL]
Docs:        [UPDATED/SKIPPED] (X files)
```

If any phase fails, fix errors before starting the next round. Test failures from newly authored tests are expected — fix the code or the test, don't delete the test.

---

### Step 6 — Repeat

Start next round scoped to files modified in the previous round (including new test files).

Loop terminates when:
- Audit returns zero high-confidence issues, AND
- Unit test coverage >= 80% on changed files, AND
- Integration tests pass for all touched flows
- OR 2 consecutive rounds produce only MINOR issues the user chooses to skip

---

## Final Pass — Housekeeping (run once after code loop converges)

Spawn three parallel agents:

### Docs Agent
- Scan `docs/` and inline comments for anything outdated by the fixes just applied
- Update API docs, README sections, architecture notes, and inline `// TODO` references that are now resolved
- Verify all doc updates from per-round Step 4 are consistent and don't contradict each other
- Scope: only docs that directly describe changed code — don't rewrite unrelated docs

### Cleanup Agent
Finds and handles stray files:

1. **Adhoc scripts** — one-off `.sh`, `.py`, `.ts` files in project root or wrong dirs
   - Move to `scripts/<topic>/` or delete if truly disposable
2. **Orphan test scripts** — test files with no corresponding source, or debug scripts (`test-something.ts`, `debug-*.js`, `try-*.py`)
   - Move to `scripts/scratch/` if potentially useful, delete if clearly disposable
3. **Stray docs** — `.md`, `.txt` files in project root that aren't config (e.g., `NOTES.md`, `TODO.txt`, `analysis.md`)
   - Move to `docs/<topic>/` with a meaningful name
4. **Empty dirs** — remove any directories emptied by the above moves

Report every move/delete before executing. If unsure whether to delete, move to `scripts/scratch/` or `docs/archive/` instead.

### Typecheck + Test Agent (after docs + cleanup complete)
Run final verification to confirm housekeeping didn't break anything:
```bash
npm run typecheck && npm run test && npm run test:integration
```

---

## Round Tracking

Keep a running tally visible to the user:

```
Round 1: 6 CRITICAL, 8 IMPORTANT, 2 MINOR → fixing → +12 unit tests, +3 integ tests, 4 docs updated
Round 2: 0 CRITICAL, 4 IMPORTANT, 1 MINOR → fixing → +5 unit tests, +1 integ test, 2 docs updated
Round 3: 0 CRITICAL, 0 IMPORTANT, 2 MINOR → DONE (minor issues skipped)

TOTALS: 17 unit tests added, 4 integration tests added, 6 docs updated
Coverage: 62% → 84% (+22%)
```

---

## Test Strategy by Fix Type

| Fix type | Unit test? | Integration test? | E2E test? |
|----------|-----------|-------------------|-----------|
| Logic bug in pure function | Yes (3+ cases) | No | No |
| API endpoint fix | Yes (handler) | Yes (HTTP roundtrip) | Maybe (if critical flow) |
| Database query fix | Yes (query builder) | Yes (real DB) | No |
| Auth/permission fix | Yes (guard logic) | Yes (full auth flow) | Yes (login flow) |
| UI component fix | Yes (render + events) | No | Yes (user interaction) |
| Config/env fix | Yes (config parsing) | Yes (startup with config) | No |
| Race condition fix | Yes (concurrent scenarios) | Yes (under load) | No |
| Style/formatting only | No | No | No |

---

## Key Principles

- **Root cause, not bandaids** — if a fix just moves the problem, flag it and dig deeper
- **Test the fix, not just the code** — every behavioral fix gets a test proving the bug is dead
- **Fixes can introduce regressions** — always re-audit changed files, not the full codebase
- **Typecheck gates each round** — never start a new audit round on broken types
- **Tests gate each round** — never start a new audit round with failing tests
- **Docs stay current** — don't batch doc updates to the end; update as you go
- **Parallel fixes, sequential rounds** — fixes within a round are parallel; rounds themselves are sequential
- **Coverage is a floor, not a ceiling** — 80% is the minimum; critical paths should be higher

## Convergence

The loop converges because each round:
1. Fixes the issues its predecessor found
2. Adds tests proving the fixes work (preventing regression)
3. Updates docs so knowledge stays current
4. Introduces only smaller, more localized issues (if any)
5. Scopes the next audit to just the changed files

Typically converges in 3-5 rounds for large changesets, 1-2 for focused fixes.
