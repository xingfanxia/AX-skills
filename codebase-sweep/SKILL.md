---
name: codebase-sweep
description: Use this skill when the user asks to "do a full codebase audit", "sweep the whole codebase", "audit everything", "full health check", "clean up the whole project", "write architecture docs", "document the codebase", or wants a comprehensive one-time review of the entire project — not just recent changes. Covers full code audit, iterative fix loop with test authoring (unit + integration/e2e) and incremental docs, docs cleanup and reorganization, architecture documentation, and script archiving.
version: 2.0.0
---

# Codebase Sweep Skill v2

A full-project health check: audit every layer, fix all issues iteratively (with test authoring and incremental doc updates per round), clean up and reorganize docs, archive stray scripts, and produce or update architecture documentation.

**Key difference from `audit-fix-loop`:** `audit-fix-loop` scopes each re-audit to only files changed in the prior round. This skill audits the *entire codebase* in round 1, then narrows to changed files in subsequent rounds. This skill is fully self-contained — it does NOT require a prior audit-fix-loop run.

**v2 additions:** Each fix round now includes unit test + integration/e2e test authoring and incremental doc updates. Phase 3 becomes a consistency review + reorganization pass (not a first-pass doc update).

---

## Phase 1 — Full Codebase Audit (Parallel)

Discover the project structure first using the **Glob** and **Grep** tools:
- Use `Glob` with patterns like `**/*.ts`, `**/*.tsx`, `**/*.py`, `**/*.go` to enumerate source files
- Use `Grep` to search for patterns across the codebase (e.g., `TODO`, `FIXME`, deprecated API usage)
- Avoid shell `find`/`grep` commands — the built-in tools are faster and permission-safe

Split by layer and spawn **parallel** `feature-dev:code-reviewer` agents (all in the same message), using `claude-opus-4-6`:

| Agent | Scope |
|-------|-------|
| server-reviewer | backend services, API routes, DB layer |
| client-reviewer | frontend/mobile screens, components, hooks |
| shared-reviewer | shared packages, types, utilities |
| infra-reviewer | scripts/, CI config, Dockerfile, env setup |

Each reviewer:
- Audits ALL files in its scope, not just recent changes
- Classifies: CRITICAL / IMPORTANT / MINOR
- Confidence >= 80 only
- Includes file:line for every issue
- **Flags functions/modules with <60% test coverage** alongside code issues

Merge and deduplicate findings. Present full issue table to user before proceeding.

---

## Phase 2 — Iterative Fix-Test-Doc Loop

Each round follows this sequence: **Fix → Test → Docs → Verify → Repeat**

```
Round 1: full codebase audit (Phase 1 results)
Round 2+: re-audit only files changed in prior round
Terminate: zero high-confidence issues + 80%+ coverage on changed files,
           or 2 consecutive MINOR-only rounds
```

### 2a — Parallel Fix

Group issues by layer. Spawn fix agents **in parallel** (all in the same message), one per layer:
- Each agent owns distinct files — no overlap
- Use `claude-opus-4-6` for logic/architecture fixes, `claude-sonnet-4-6` for style/cleanup
- Each fix agent records what it changed — this drives test authoring

### 2b — Test Authoring (parallel after fixes)

Spawn two test-authoring agents in parallel:

**Unit Test Agent** (`tdd-guide` or stack-appropriate reviewer):
- Scope: every file modified in 2a
- For each changed function/method:
  - No test exists → write one (happy path + edge cases + error path)
  - Test exists but doesn't cover the fix → add test cases
  - Test exists and covers the fix → skip
- Coverage target: 80%+ on changed files
- Follow project test conventions (naming, location, framework)

**Integration / E2E Test Agent** (`e2e-runner` or stack-appropriate):
- Scope: fixes touching API endpoints, DB queries, auth flows, cross-service calls, UI interactions
- For each qualifying fix:
  - Integration test exists → verify coverage, add cases if needed
  - No integration test → write one covering the end-to-end flow
- Test categories:
  - **API integration:** HTTP request → handler → DB → response
  - **Service integration:** cross-service calls, message queues
  - **E2E/UI:** critical user flows (Playwright/Cypress/etc.)
- Skip for: pure utility functions, formatting helpers, type-only changes

**Test quality rules:**
- Deterministic — no flaky timing, no unmocked external calls
- Clear assertions — not just "doesn't throw"
- Descriptive test names (behavior, not implementation)
- Integration tests clean up after themselves
- Use existing test fixtures/factories

**Test strategy by fix type:**

| Fix type | Unit? | Integration? | E2E? |
|----------|-------|-------------|------|
| Logic bug in pure function | Yes (3+ cases) | No | No |
| API endpoint fix | Yes (handler) | Yes (HTTP roundtrip) | Maybe |
| Database query fix | Yes (query builder) | Yes (real DB) | No |
| Auth/permission fix | Yes (guard logic) | Yes (full auth flow) | Yes |
| UI component fix | Yes (render + events) | No | Yes |
| Config/env fix | Yes (config parsing) | Yes (startup) | No |
| Race condition fix | Yes (concurrent) | Yes (under load) | No |
| Style/formatting only | No | No | No |

### 2c — Incremental Doc Update

Spawn a **docs-agent** (`claude-sonnet-4-6`) scoped to files changed in 2a-2b:
- Update inline JSDoc/docstrings for changed functions
- Update API docs if endpoint behavior changed
- Update README sections if setup/usage changed
- Fix resolved `// TODO` references
- Skip if round only had style/formatting fixes with no behavioral changes

### 2d — Verify

Run the full verification chain. Stop at first failure and fix before continuing.

```bash
# 1. Build
npm run build        # or mvn compile / ./gradlew build / go build ./...

# 2. Type check
npx tsc --noEmit     # or pyright . / go vet ./...

# 3. Lint
npm run lint         # or ruff check . / golangci-lint run

# 4. Unit tests (with coverage)
npm run test -- --coverage   # or pytest --cov / go test -cover ./...

# 5. Integration tests
npm run test:integration     # or pytest tests/integration/ / go test -tags=integration ./...

# 6. E2E tests (if applicable)
npm run test:e2e             # or npx playwright test

# 7. Security scan
grep -rn "sk-\|api_key\|console\.log" --include="*.ts" --include="*.js" src/ 2>/dev/null | head -10

# 8. Diff review
git diff --stat
```

Verification summary:
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

Test failures from newly authored tests are expected — fix the code or the test, don't delete the test.

### 2e — Repeat

Re-audit only files changed in the prior round (including new test files). Loop terminates when:
- Zero high-confidence issues, AND
- Unit test coverage >= 80% on changed files, AND
- Integration tests pass for all touched flows
- OR 2 consecutive rounds produce only MINOR issues the user chooses to skip

Round tracking:
```
Round 1: 12 CRITICAL, 15 IMPORTANT, 4 MINOR → fixing → +18 unit tests, +5 integ tests, 6 docs (full codebase)
Round 2:  0 CRITICAL,  3 IMPORTANT, 2 MINOR → fixing → +4 unit tests, +1 integ test, 2 docs (changed files only)
Round 3:  0 CRITICAL,  0 IMPORTANT, 1 MINOR → DONE
```

---

## Phase 3 — Docs Consistency Review & Reorganization

Spawn a **docs-agent** (`claude-opus-4-6`) once code issues converge. Since per-round doc updates happened in Phase 2, this phase focuses on **consistency and organization**, not first-pass updates.

### 3a — Consistency Review
- Read all doc updates from Phase 2 rounds — check for contradictions between rounds
- Verify docs reflect the final state of the code, not intermediate states
- Remove any doc references to code that was changed again in a later round

### 3b — Cleanup Outdated Docs
- Read all files in `docs/`
- Flag docs that describe removed features, old APIs, or superseded architecture
- Delete clearly stale docs; move uncertain ones to `docs/archive/`

### 3c — Reorganize Hierarchy
Enforce this structure (adapt to project conventions — if the project already has an established docs layout, work within it rather than forcing this hierarchy):
```
docs/
├── architecture/       # system design, data flow, service maps
├── features/           # one subdir per major feature
│   └── <feature>/
├── api/                # endpoint references, request/response schemas
├── guides/             # how-tos, onboarding, runbooks
├── reports/            # audit outputs, analysis, one-off findings
└── archive/            # outdated docs preserved for reference
```

Move any flat files in `docs/` root into the appropriate subdirectory. Never flatten a well-organized subdirectory.

---

## Phase 4 — Architecture Documentation

Check if these exist. Create any that are missing, update any that are stale. Adapt filenames and structure to existing project conventions — these are defaults, not mandates:

### `docs/architecture/overview.md`
- High-level system diagram (ASCII or Mermaid)
- Services/apps and their responsibilities
- Data flow between layers
- Key technology choices and why

### `docs/architecture/data-model.md`
- Entity relationships
- Key schemas and their purpose
- Notable constraints and invariants

### `docs/features/<name>/README.md` (one per major feature)
- What the feature does and why it exists
- Key files and entry points
- State machine or flow diagram if complex
- Known edge cases and design decisions

### `docs/guides/development.md`
- How to run the project locally
- Environment setup
- Common development tasks

### `docs/guides/testing.md` (NEW)
- How to run unit tests, integration tests, and e2e tests
- Test conventions (naming, location, frameworks)
- How to add tests for new features
- Coverage targets and how to check them

Spawn parallel writer agents — one per document — using `claude-sonnet-4-6`. Each agent reads the relevant source files before writing.

---

## Phase 5 — Script & File Cleanup

Spawn a **cleanup-agent** in parallel with Phase 4:

1. **Adhoc scripts** — `.sh`, `.py`, `.ts`, `.js` files in project root or wrong dirs
   - Move to `scripts/<topic>/`
2. **Orphan test/debug scripts** — `test-*.ts`, `debug-*.js`, `try-*.py`, scratch files with no corresponding source
   - Move to `scripts/scratch/` if potentially reusable, delete if clearly disposable
3. **Stray docs** — `.md`, `.txt` in project root (except `README.md`, `CHANGELOG.md`, `LICENSE`)
   - Move to `docs/<topic>/`
4. **Empty directories** — remove after moves

Report every move/delete before executing. Archive instead of delete when uncertain.

---

## Phase 6 — Final Verification

```bash
npm run typecheck && npm run test && npm run test:integration
```

Report a final summary:
```
CODEBASE SWEEP COMPLETE
=======================
Code issues fixed:    X CRITICAL, Y IMPORTANT, Z MINOR across N rounds
Tests added:          X unit tests, Y integration tests, Z e2e tests
Coverage:             A% → B% (+C%)
Docs updated:         X files (per-round) + Y files (consistency pass)
Docs created:         X new architecture/feature/testing docs
Docs archived:        X outdated files
Scripts organized:    X files moved
Files deleted:        X orphaned files removed

Build: PASS  Types: PASS  Lint: PASS
Unit Tests: PASS (X/Y)  Integ Tests: PASS (X/Y)  E2E: PASS/SKIP
Security: PASS
```

---

## Key Principles

- **Self-contained** — does not require a prior audit-fix-loop run; works on any repo from scratch
- **Full audit first, narrow on repeat** — round 1 sees everything; later rounds stay focused
- **Test the fix, not just the code** — every behavioral fix gets a test proving the bug is dead
- **Docs stay current per round** — don't batch all doc updates to the end
- **Docs reflect reality** — only update docs for code that actually changed; don't speculate
- **Archive over delete** — when uncertain, archive. Deletion is irreversible.
- **Parallel within phases, sequential across phases** — fixes don't start until audit is done; Phase 3 doesn't start until code loop converges
- **Coverage is a floor, not a ceiling** — 80% is the minimum; critical paths should be higher
