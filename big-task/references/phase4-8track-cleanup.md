# Phase 4 — 8-track final cleanup (Tier 4 only) — full spec

Read this when Phase 4 fires. Spawn **parallel** `feature-dev:code-reviewer` agents, one per track. Each agent returns a structured report; implement only high-confidence + low-regret changes.

| # | Track | Tools | Confidence bar |
|---|-------|-------|----------------|
| 1 | Dedupe/consolidate code (reduce complexity without obscuring intent) | manual read | High |
| 2 | Consolidate shared type definitions where drift causes inconsistency | manual read | High |
| 3 | Unused code — verify with `knip` / `ts-prune` / `depcheck` then **manually verify** before removing | tool-assisted | Very high |
| 4 | Circular deps — `madge`; prioritize cycles affecting maintainability/correctness | tool-assisted | High |
| 5 | Strengthen typing — replace unsafe `any`, narrow overly-broad types. **Preserve legitimate `unknown` at boundaries.** | manual read | High |
| 6 | Error handling — remove ONLY unnecessary/misleading defensive patterns. **Keep try/catch at real boundaries** (recovery, logging, cleanup, user-facing errors). | manual read | High |
| 7 | Legacy/dead/fallback paths — remove only clearly obsolete. Verify NOT needed for: compatibility, migration, config, active users. | manual read | Very high |
| 8 | AI artifacts — stubs, placeholder logic, redundant comments, TODO-narration, edit-history comments. **Keep intent-explaining comments.** | manual read | Very high |

## Rules (non-negotiable, apply to all tracks)

- **No speculative rewrites.**
- **No public behavior changes** unless clearly intended and justified.
- **Small reviewable commits**, grouped by concern.
- **Before removing anything**: check dynamic usage, configuration, reflection, registration, hooks, codegen, framework conventions.
- **Preserve compat** unless you can prove removal is safe.
- **Flag medium- and high-risk findings separately — do NOT auto-implement them.** Report them for human decision.
- **For each implemented change**: one-line "why safe" justification in the commit message.

## Per-track validation after changes

Each track's agent runs: build, type check, lint, unit tests, integration tests (if touched).

Report per-track:

```
TRACK N — [name]
Issues found: CRITICAL:X / IMPORTANT:Y / MINOR:Z
Implemented: [count] (list with why-safe)
Deferred: [count] (list with risk rationale)
Validation: build=[pass/fail] types=[pass/fail] lint=[pass/fail] tests=[pass/fail]
```
