---
name: big-task
description: Engineering workflow router — picks direct / light / full superpowers cycle based on RISK, not file count. AUTO-INVOKED for tasks touching 3+ files or creating new functionality, but defaults to LIGHT process unless the work has real architectural risk (concurrency, atomicity, protocol, schema). One entry point over the superpowers engine + audit/pr/sweep loops. Skip for bug fixes, typos, single-function changes, and questions. RUNS AUTONOMOUSLY by default — only pauses on Critical Decision Triggers (see Phase -1).
---

# /big-task

One skill to route engineering work. Wraps `superpowers:*`, `/audit-fix-loop`, `/pr-fix-loop`, `/codebase-sweep`, `/think-ultra`, etc. under a single memorable name.

**Auto-trigger:** user describes work touching 3+ files, new functionality, a system/module refactor, or anything involving schema changes / migrations (always Tier 4). Skip for bug fixes, typos, single-function changes, and questions.

**Override:** User says "skip workflow", "just do it directly", "quick and dirty" → drop to direct execution.

**Default bias: LIGHTER process.** A full plan-doc + multipass-review cycle only pays off when it catches real bugs that direct implementation would ship. For locked-design UI work, well-understood patterns, and single-responsibility additions, the full cycle is pure overhead. Use risk, not file count, as the primary decision axis.

**Tier 4 engine: superpowers throughout.** Match the depth of the cycle to the work shape — don't always run every stage:

| Work shape | Cycle | Why |
|---|---|---|
| Multi-phase implementation, 10+ tasks, clear dependency graph, expected runtime hours | Full superpowers (`brainstorming` → `writing-plans` → `subagent-driven-development` → `requesting-code-review` → `verification-before-completion`); set up `using-git-worktrees` + parallel `Task()` for disjoint-file waves | Subagents self-load the plan doc from disk, parallel `Task()` runs disjoint waves; orchestrator stays lean. Built for long autonomous runs. |
| Pattern N+1 at scale (20-screen locked-design migration, API rename across 50 files) | `using-git-worktrees` + parallel `Task()` implementers off a `writing-plans` checklist | Mechanical parallel work across disjoint files — worktree isolation removes the shared-state bar. |
| Exploratory feature, novel pattern, architecture decisions required, spec unclear | Full superpowers cycle (as above) | Strong on judgment and two-stage review gates. Catches spec drift before ship. |
| User says "brainstorm this" / "not sure where to start" | `superpowers:brainstorming` first | Its strength. |

The planning overhead (a real plan doc + `plan-design-review` pass) is worth paying for genuinely risky Tier 4 work, but skip it for small Tier 4 work — go straight to a checklist plan + execution. The execution engine itself (`subagent-driven-development` / parallel worktrees) is lean; don't penalize it for the planning-phase cost when long autonomous runs are the actual need.

---

## Phase -1 — Autonomous-by-default mode (DEFAULT ON — overrides every "ask once" elsewhere in this skill)

Once `/big-task` is invoked, the entire flow runs autonomously through to PR-merged. **Do NOT pause for confirmation between phases, between fix loops, between commits, between detection routings, or between audit rounds** unless one of the **Critical Decision Triggers** below is hit.

The user already opted into autonomous execution by invoking this skill — every additional checkpoint is friction they explicitly do not want. If the skill's wording elsewhere says "ask once" / "surface to user" / "wait for confirmation", **this section overrides it** unless the situation matches a Critical Decision Trigger.

### Critical Decision Triggers (the ONLY 4 reasons to pause)

Pause and ask the user ONLY if the next action falls into one of these classes:

1. **Irreversible architectural choice** — picking a database engine, ORM, primary framework, monorepo tool, deployment target, auth provider, or anything else that future code will copy and that costs >1 day to undo.
2. **Money / secrets / PII boundary** — code that moves money (charges, refunds, credits), introduces or rotates secrets, exfiltrates PII, or alters access boundaries (auth scopes, RBAC, row-level security, payment paths).
3. **Requirements ambiguity that would invalidate already-shipped work** — the user's prompt has multiple readings AND picking the wrong reading would mean reverting a meaningful chunk of already-committed code. Surface ONLY when re-reading the prompt twice still doesn't disambiguate AND there's no safer "do both / do neither" middle path.
4. **User-facing breaking change** — public API contract change, data migration that requires user action, removal of a documented feature, force-push to a shared branch.

If the next action is NOT in one of those 4 classes, **proceed without asking.** Pick the more conservative path silently and log the choice in a `## Autonomous decisions` section of the final PR description so the user can audit after-the-fact.

### Auto-resolutions (replace every "ask once" prompt with these silent defaults)

| Previously asked | Now silently picks |
|---|---|
| Tier 4 cycle depth unclear (full superpowers cycle vs lighter checklist path) | **full superpowers cycle** (judgment-strong, two-stage review) |
| `light-project` task looks tier-4 (escalation exception) | **escalate to tier 4 silently**, note in PR `## Autonomous decisions` |
| Auto-detected profile looks wrong | **trust the auto-detect**; only re-route if 2+ phases produce FLAG verdicts pointing at the wrong profile |
| Tier rubric ambiguous | **pick the lighter tier** (per existing "bias toward lighter tier" rule) |
| Phase 2g visual verification: FLAG items | **open a TodoWrite follow-up**, continue to next phase. Surface ALL flagged items as a batch at end-of-milestone — never one-at-a-time mid-flight |
| Phase 2g visual verification: BLOCK items | **open a fix task and execute it inline** before declaring phase verified. NO confirmation needed — BLOCK = ship-blocking by definition, fix it |
| audit-fix-loop convergence | **run to convergence — fix every issue found, regardless of severity.** If it was worth flagging at confidence ≥80, it's worth fixing. Cap at 5 rounds. If still not converged, route remaining issues to a fresh opus subagent (one per cluster) rather than deferring. |
| pr-fix-loop "ready to merge?" | **DO ask before final merge** if no auto-merge configured (merging is itself a critical action — class 4). Otherwise proceed |
| Between-phase progression | **NEVER ask — at ANY context usage.** Proceed automatically once current phase verification is GREEN + multipass review clean. No "continue / compact / split?" menu — auto-compaction handles capacity. Before starting the next phase: update plan doc + TodoWrite + commit the milestone so post-compaction continuation has full state. See `references/review-discipline.md` |
| Between commits within a phase | **NEVER ask.** Commit per logical unit with conventional-commit messages |
| Round 1 audit produced findings | **fix them and continue to Round 2 silently.** No "should I fix these?" prompt |
| Code review findings (any severity — CRITICAL / HIGH / MEDIUM / LOW / NIT / INFORMATIONAL) | **fix all of them.** Severity controls *how* (inline vs subagent), not *whether*. See "Fix routing" below. Never defer based on severity alone — including review-bot "non-blocking" findings. The audit already paid to find it. The user does not review routine findings — the agent runs the multipass chain autonomously (`references/review-discipline.md`). |
| Plan / spec / design artifact produced (plan doc, UI spec, AI design doc, etc.) | **NEVER ask the user to review long-form artifacts.** Run `plan-design-review` autonomously and fix every finding (per severity rule). The user reviews ONLY if a sign-off gate is set (then surface a ≤10-line summary — objective, scope, risks, acceptance criteria — NOT the full doc) OR a Critical Decision Trigger fires. |
| End-of-phase commit needed | **commit autonomously** with conventional-commit message + HEREDOC body |
| Phase verification GREEN → next phase | **always invoke `neat-freak` first** (Phase 2f knowledge sync), then commit code + doc edits together. Skill is idempotent — safe to run every phase. No ask. |
| Open PR after final phase | **open it autonomously** (per Phase 6a). Don't ask "ready to PR?" |

### Fix routing — inline vs subagent (severity-agnostic)

Once an issue is flagged, it WILL be fixed. The only question is who fixes it. Pick by **cost to main thread**, not by severity:

| Route to | When (any one trigger) |
|---|---|
| **Inline (main thread)** | Touches ≤2 files · mechanical change (rename, add type, remove dead code, fix typo) · well-understood domain · estimated ≤500 lines of code to read · no new tests needed |
| **Opus subagent** (`feature-dev:code-reviewer` for review-fix, or task-scoped agent for new-code fixes) | Touches 3+ files · requires deep refactor · unfamiliar domain (new lib, new pattern) · estimated 500+ lines to read · touches concurrency / race / security / payment / auth / data-mutation logic (regardless of size — these always go to opus for the extra reasoning budget) · requires test scaffolding for new behavior |

Subagent contract: receives `{issue_id, file_paths, severity, finding_text}`, loads context from disk, applies fix, runs build+typecheck+lint+tests, returns `{status: FIXED|BLOCKED, files_touched: [...], commit_sha}` ≤200 tokens. Main thread aggregates, never sees raw fix output.

**Anti-pattern to avoid:** flagging an issue at confidence ≥80 and then "deferring as MINOR follow-up" because it's tedious. That's the exact failure mode the user called out — the audit found it, so fix it. If the fix is expensive, that's what subagents are for.

### How to ask when a Critical Decision Trigger IS hit

Format (≤ 3 sentences total):

```
[CRITICAL DECISION] <one sentence: what's at stake and why this is class N>
A) <option> — <consequence>
B) <option> — <consequence>
Pick A / B / or describe a third path.
```

No essay. Just the decision. Then **wait** — do not proceed until user answers.

### Mid-flight escape hatch (user-initiated)

User can interrupt at ANY point with: "stop", "pause", "wait", "let me look", or by hitting Ctrl-C. Respect interruption immediately. Resume on user's explicit "continue" / "go" / "proceed" / "moveon".

### Status updates + final report

While autonomous: ONE short progress line per phase boundary (≤80 chars, e.g. `✓ Phase 2b · 4/4 green · committed (a1b2c3d) · → Phase 2c`) — never a multi-paragraph essay. At PR-opened/merged: ONE summary block — phases / commits / tests / LOC, the **non-optional `## Autonomous decisions` log** (the receipt the user needs to audit autonomy after-the-fact), critical-decision pauses, deferred FLAG batch. Exact templates: `references/report-templates.md`.

---

## Phase 0.0 — Project workflow profile (FIRST, auto-detects)

Profile routing happens BEFORE the tier rubric. Three-step resolution:

### Step 1 — Explicit block in `./CLAUDE.md` (highest priority)

Grep for `workflow-profile:start` in `./CLAUDE.md`. If found, extract `<name>` from the `## Workflow Profile: <name>` line inside the block. That's the profile. Skip to Step 3.

(CLAUDE.md is loaded into session context at start — usually you can just scan existing context instead of re-reading the file.)

### Step 2 — Auto-detect from repo signals (runs only when no explicit block)

Run the one-command repo scan (≤1s) and classify from the emitted signals — schema / auth-payment / components-ui / design-ref / playwright / content volume / backend-lang. Script + ordered classification rules: `references/profile-detection.md`. Output is the **repo-shape profile** (`light-project` / `heavy-project` / `ui-project` / `unknown`) — it reflects what the codebase IS, not what the current task IS.

### Step 2.5 — Task intent (judgment, NOT keyword matching)

The repo scan answers "what shape is this project?". Now you need to answer "what shape is this task?". Reason about the request — do NOT pattern-match words. You are an LLM; you can read the task holistically the way an experienced engineer would. Someone saying "I was reading about Stripe" is not the same as "integrate Stripe payments", even though both contain the word Stripe.

**The core question: what is the task actually doing to the system?**

Classify what the task modifies or introduces. These categories carry inherent risk regardless of repo shape:

**"Heavy by nature" — modification risk dominates any repo shape**
- Persistence layer changes — schema, data model, new tables, column adds, migrations
- Trust boundary changes — building or altering an auth/authz/session/permissions system
- Revenue path changes — code that actually moves money (charges, refunds, credits, paywall gating)
- Atomicity/concurrency guarantees — transactions, distributed locks, idempotency keys, race-condition fixes
- Cross-system contracts — API contract changes with external consumers, protocol versioning, webhook schemas between services
- New architectural subsystem introduction — something that doesn't exist yet in the repo and whose shape will be copied by future code

**"Light by nature" — task is content or cosmetic**
- Written prose work — articles, translations, copy edits, doc updates, typos, README changes
- Pure cosmetic visual tweaks — color, spacing, alignment, font-size — where no new UX pattern is being introduced
- Single config/script tweaks where the config schema is stable and the change is one line or one value

**"UI by nature" — rendered output, no system-risk boundary crossed**
- Building/restyling components, screens, routes that apply existing design patterns
- The N+1-th application of a pattern that already lives in the repo

**Framing questions when the above doesn't settle it cleanly:**
1. **Blast radius** — if this ships wrong, what breaks? A wrong color is a bad afternoon. A double-charge is a refund + customer anger + possible chargeback fees. Bigger blast → heavier tier.
2. **Reversibility** — can a single `git revert` undo this, or is there data migration / state mutation to unwind? Unwindable-with-data = heavier.
3. **Design vs. translation** — is the user asking for a *design decision* (which pattern? which trade-off?) or the *translation of an existing design* (apply HANDOFF.md to these 5 screens)? Decisions are heavier; translations are lighter.
4. **Pattern novelty** — is this the N+1 application of a known pattern, or does this task set a new pattern? New pattern = heavier.

### Combining rule → final profile

Apply in order, first match wins:

1. **Task is heavy by nature** (any of the 6 categories above) → `heavy` regardless of repo
2. **Task is light by nature** (pure content / cosmetic / trivial config) → `light` regardless of repo
3. **Task introduces a new subsystem or sets a new architectural pattern** → `max(repo, one-level-up)` — a blog getting a real-time comment subsystem promotes to ui or heavy, not light
4. **Task matches the repo's default shape** (UI work in a UI repo, content in a blog repo) → use the repo profile
5. **Genuinely ambiguous** — default to the lighter tier and proceed. If the task grows beyond the tier mid-flight, escalate then. Only ask the user upfront when the request is unparseable.

Print the reasoning, not a label: `Profile: heavy (repo: light; intent: task introduces a revenue boundary — Stripe paywall)`. State what you judged, not what you matched.

### Examples (showing judgment, not lookup)

8 worked examples (Stripe paywall, users-table column, Zustand-vs-Redux, footer alignment, …) → `references/routing-examples.md` — read when the combining rule doesn't settle a classification cleanly.

### Step 3 — Route by final profile

| Profile | Route |
|---|---|
| `light-project` | **Exit big-task immediately** — execute directly, no subagents, no planning. Silently escalate to the Phase 0 rubric only for schema / protocol / atomicity / concurrency work (log in PR `## Autonomous decisions`) |
| `ui-project` | **Force Tier 3 (light), skip the Phase 0 rubric.** Checkbox task-list plans; Phase 2g Playwright screenshot sweep is MANDATORY |
| `heavy-project` | Phase 0 rubric below; at Tier 4 run the full superpowers cycle (worktrees, TDD-mandatory, review gates) |
| `unknown` | Phase 0 rubric; if the project has durable character, suggest `/workflow-profile <name>` to make routing sticky |

Full per-profile detail + when auto-detection gets it wrong (trust it and proceed; re-route only after 2+ phases produce FLAG verdicts pointing at the wrong profile): `references/profile-detection.md`.

### Overrides

- User says "skip workflow" / "just do it" / "quick and dirty" → drop to direct execution regardless of profile.
- User says "use superpowers" / "just brainstorm it" → override the cycle depth for this one task.
- User wants durable override: run `Skill(skill="workflow-profile", args="<light|ui|heavy>")` to write an explicit block (wins against auto-detect forever after).

---

## Phase 0 — Risk-tier decision (≤ 30s)

**Risk is the primary axis. File count is secondary.** A 15-file UI migration from a locked design spec is LOWER risk than a 3-file atomic credit-deduction change. Route accordingly.

### Decision rubric

| Tier | Signals | Process |
|------|---------|---------|
| **Tier 2 (Direct)** | Bug fix, typo, one-liner, single-function change, isolated refactor | Fix on branch → test → merge. No big-task scaffolding. |
| **Tier 3 (light)** | Feature addition on existing primitives, locked-design UI work, new endpoint in well-trodden pattern, component from design reference, 3-10 files, design / spec / acceptance already clear | Inline plan (≤1 page) → TDD → multipass review (`code-reviewer`; + domain pass only where a real domain reviewer exists — `go-review`/`python-review`; +`security-reviewer` / `database-reviewer` if triggers fire; TS/JS: `code-reviewer` alone, no duplicate generic pass) → PR. Skip the formal plan doc + design-review loop. See `references/review-discipline.md`. |
| **Tier 4 (Full cycle)** | Atomicity / concurrency / schema / protocol change, unfamiliar domain, cross-phase dependencies, genuinely ambiguous requirements, 10+ files across multiple packages, regression-sensitive migrations | Full superpowers cycle: `brainstorming` → `writing-plans` → `plan-design-review` → `subagent-driven-development` (parallel `Task()` + worktrees where deps allow) → `requesting-code-review` → `verification-before-completion`. Multi-wave parallelism pays off here. |

### When the full Tier-4 cycle is PURE OVERHEAD (drop to the lighter path even at tier-4 file count)

- **Locked-design UI migration:** design reference (HANDOFF.md, Figma export, `directions/*.jsx`, etc.) already specifies pixel-exact layout. Most of the "what are we building?" scaffolding is redundant ceremony. Use the Tier 3 light path instead.
- **Repetitive pattern application:** adding the N+1-th screen that follows the same shape as the existing N. Copy the pattern, adjust for new content, ship.
- **Solo dev + short horizon:** traceability / handoff artifacts exist to coordinate a team. If no one else will read them, they're writing docs for yourself at significant token cost.
- **Design already validated:** if a feasibility experiment or UI mockup pass already produced findings, don't re-plan those findings through another design-review loop. Apply them directly.

### When the full Tier-4 cycle is WORTH IT (insist on tier 4 even at low file count)

- **Atomic / concurrent / transactional logic:** the planning + review gates catch race conditions before execution. Cheaper than debugging production.
- **Schema changes / migrations:** compile-time types can pass while the live DB is broken. Full verification gates matter.
- **Multi-plan wave parallelism:** 2+ independent workstreams benefit from explicit dependency declaration + parallel executor agents.
- **Revenue-path code:** payment, credits, unlock flows — correctness > velocity.
- **Cross-cutting protocol changes:** shifting a message format or API contract across many call sites — the plan's coverage audit earns its keep.

**Tier ambiguity → silently pick the lighter tier and proceed** (per Phase -1 auto-resolution + the existing "bias toward lighter tier" rule). Log the chosen tier + the alternative considered in PR `## Autonomous decisions`. Do NOT ask the user mid-flight — if the lighter tier turns out wrong, escalate by promoting the *next* phase to a higher tier rather than backtracking the current one.

Default = proceed at the rubric-matched tier. **Bias toward the lighter tier when in doubt.**

---

## Phase 0.5 — Optional pre-phase (tier 4 only)

Use when an idea is unproven OR UI-heavy with unclear direction. Capture the findings before discarding the throwaway work, so the learnings persist after exploration.

- **Feasibility unknown** ("can we even do X?"): spin a scratch branch, prototype the risky path, capture findings (what worked, what didn't, the chosen approach) in the plan doc or an `eureka` note, then throw the branch away.
- **UI direction unclear** ("what should this look like?"): `Skill(skill="huashu-design")` (or `frontend-design`) → HTML multi-variant mockups → fold the chosen direction into the plan doc / design reference.
- **Domain unfamiliar / taste unencoded** (new tech vertical, new content format, no design or 基调 precedent): run a **blindspot pass** — enumerate the user's likely unknown unknowns and the 2-3 questions actually worth asking — and/or a **variant fan-out** presented as a `[TASTE FORK]`, BEFORE brainstorming locks scope. Present 2-4 cheap divergent candidates BEFORE the expensive artifact exists — a fork elicits taste the agent cannot self-supply; presenting one finished artifact for a verdict is a review ask, not a fork.

Default = skip. Only invoke when requirements are genuinely ambiguous at the implementation or aesthetic level.

**External design artifacts (brownfield bundles):** If the user hands you a pre-made design bundle from an external tool (Claude Design, Figma export, v0 export, external spec/prototype, chat log with locked decisions), **copy it to a persistent repo path before Phase 1** — typically `docs/{project-slug}/reference/`. Do not leave references pointing at `/tmp/` or external URLs — they will break mid-project. Then cite these persistent paths in the plan doc so downstream phases always find them.

---

## Model selection (consistency across all subagents)

For quality-mode Tier 4 work, pass `model: "opus"` explicitly on ALL `Task()` invocations — research/exploration agents, plan reviewers, code reviewers, `think-ultra` — so no per-role default silently downgrades synthesis or verification; multi-week Tier-4 scope amortizes the cost. Balanced budget: Sonnet everywhere — **Sonnet 5 is the floor, never haiku** (the author's measured stance: haiku's quality floor is below acceptable even for lookups — re-runs eat the savings). To inherit: match the current session model.

---

## Subagent Dispatch Policy

Every phase below carries a **Subagent policy** line. The policy has four modes, chosen by the nature of the work, NOT by tier:

| Mode | When | Main-thread consumption |
|---|---|---|
| **parallel-worktree** | Implementation on disjoint files, no shared state | <20% — each subagent writes in its own worktree; orchestrator collects short summaries |
| **parallel-readonly** | Investigation, review, visual verification, audit, doc-check — anything that doesn't write | <20% — fan out one subagent per target; zero write-conflict risk |
| **serial-subagent** | Implementation on shared files, or sequential build-up where each task depends on the last | ~30% — `superpowers:subagent-driven-development`, one implementer at a time with fresh per-task context |
| **inline** | Single-file / single-function change, Tier 2 hotfix, trivial decision | 100% — no subagent overhead is worth paying |

**Default: NEVER inline when tier ≥ 3 AND independent task count ≥ 3.** Past that scale, inline bloats main-thread context and defeats the autonomous-run advantage of subagent architectures.

**Orchestrator discipline (applies to all subagent modes):**
- Subagents load inputs from disk themselves (plan file, design ref, diff snapshot). Do NOT inject full task text from controller into every prompt — that's how superpowers' orchestrator accidentally hoards context across a 20-task plan.
- Subagents return structured summaries ≤200 tokens (`{task, status, findings}`), not raw output.
- Orchestrator state lives on disk (the plan doc + `STATE.md` for Tier 4, TodoWrite for Tier 3) — never in main-thread chat history.
- Use `superpowers:using-git-worktrees` before any parallel-worktree dispatch. Worktree isolation is what removes the shared-state bar that `superpowers:dispatching-parallel-agents` otherwise imposes on parallel implementers.

Announce the chosen mode when entering a phase: `Phase 2b · parallel-readonly (4 routes)`. Makes routing auditable and catches inline overuse.

---

## Phase 1 — Bootstrap

Route by tier from Phase 0.

**1a — Tier 3 light (DEFAULT for most "big" tasks):**

Write a short inline plan directly in the response. Keep it ≤1 page:

```
## Plan

**Objective:** [1 sentence]
**Files to touch:** [bulleted list, 3-10 files]
**Key references:** [design spec, existing pattern file, API contract]
**Test plan:** [unit / integration / E2E scope — be specific]
**Acceptance criteria:** [3-5 verifiable conditions]
**Rollback:** [how to revert if needed — usually just `git revert <commit>`]
```

Then proceed to Phase 2 with this inline plan as the single implicit phase. **Do NOT spawn `superpowers:brainstorming` / `superpowers:writing-plans` or any formal plan-doc scaffolding.** Their value is catching ambiguity and architectural risk that isn't present in tier 3 work.

Skip straight to TDD: write failing tests based on acceptance criteria → implement → verify.

**1b — Tier 4 full cycle, new project / new milestone:**
- **Map the codebase first (brownfield):** use codegraph (`mcp__codegraph__*` / `codegraph` CLI) for symbol discovery; for repos ≥ ~500 files without an index, run `codegraph init .` first. Fan out parallel `Explore` agents for the areas the milestone touches — capture stack, conventions, test setup, and known concerns (README drift, tech debt, migration blockers). The concerns survey is what makes downstream phase planning work at multi-week scope.
- **Brainstorm + plan:** `Skill(skill="superpowers:brainstorming")` to nail down scope/intent, then `Skill(skill="superpowers:writing-plans")` to write the plan doc (phases + per-phase acceptance criteria). Put the plan doc under `docs/{project-slug}/` (or the repo root for greenfield) — a single plan doc, no separate ROADMAP-directory ceremony.

**1c — Tier 4 full cycle, existing plan doc:** if the codebase map is stale (major changes since last explored), refresh it first via codegraph + a focused `Explore` agent on the changed area, then extend the plan doc with the new milestone's phases.

**After the plan doc is written (1b or 1c):** during `superpowers:writing-plans`, declare each phase's dependencies inline (which phases must land before this one) so parallel waves can be scheduled. **Order the plan doc volatile-first:** decisions most likely to change (data model, type interfaces, user-facing flows) at the top, mechanical refactoring at the bottom — review attention lands where reversal is expensive. **Include an "open unknowns & assumptions" section** sorted by risk × irreversibility (which answers would change the implementation) — specs record what's undecided, not just what's decided.

---

## Phase 2 — Phase loop (per phase)

**Tier 3 (DEFAULT — light):** route by independent task count (see Subagent Dispatch Policy).

- **≤2 tasks on same file/module** → **inline**. TDD → implement → `code-reviewer` agent → commit.
- **3+ tasks on shared files** → **serial-subagent** via `Skill(skill="superpowers:subagent-driven-development")`. Fresh implementer + spec reviewer + quality reviewer per task.
- **3+ tasks on disjoint files, mechanical work** (locked-design migration, pattern N+1 application) → **parallel-worktree**: isolate each task with `superpowers:using-git-worktrees`, then dispatch parallel `Task()` implementers. Worktree isolation removes the shared-file bar.

Skip the formal plan-doc ceremony regardless. One phase, one commit batch, done.

**Tier 4 (full cycle):** run the superpowers cycle — `Skill(skill="superpowers:executing-plans")` (or `superpowers:subagent-driven-development` for in-session waves) drives each phase off the plan doc: implement → review → verify. Use when risk justifies the full ceremony (see Phase 0 "When the full Tier-4 cycle is worth it").

**Manual / deep mode (tier 4 opt-in):** invoke sub-skills explicitly for finer control:

- `Skill(skill="superpowers:brainstorming")` — spec refinement; use when WHAT the phase delivers is genuinely unclear, or autonomous would skip nuance the user must weigh in on. Surface implicit assumptions here BEFORE planning — the cheapest way to front-load the plan's most valuable catches. **Interview filter:** any question aimed at the user must clear a Phase -1 Critical Decision Trigger (re-read the prompt twice first; prefer a do-both/do-neither middle path) — everything below that bar gets a conservative default + `## Autonomous decisions` log entry instead of a question.
- `Skill(skill="superpowers:writing-plans")` — standalone plan-doc creation, followed by `plan-design-review` for the auto-review pass.
- `Skill(skill="code-review")` (or `/code-review`) / `code-reviewer` agent — review pass; for novel patterns or revenue-path changes add a domain reviewer.
- `Skill(skill="superpowers:subagent-driven-development")` — wave-based execution; for disjoint-file waves set up `superpowers:using-git-worktrees` + parallel `Task()` first.

**Escape hatches for over-engineered tier-4 flows:**
- **Accidentally routed a tier-2 task through big-task** → execute it inline, no subagents, no planning overhead (the Phase 0.0 `light-project` / Tier 2 paths already cover this).
- **Want commit discipline without the full ceremony** → run the lighter Tier 3 path (inline plan + atomic commits per logical unit) and skip the formal plan doc + design-review loop.

### 2a — Plan specification (by tier)

**Tier 3 (light) — minimum viable plan:**
- **Unit tests:** TDD — failing test first, then implementation. Non-negotiable.
- **Design reference:** cite the authoritative source (HANDOFF.md, Figma URL, existing pattern file) in the inline plan. No need to generate a new UI spec if one already exists upstream.
- **Acceptance criteria:** 3-5 verifiable conditions. Grep-checkable beats subjective.
- **Integration / E2E:** only if the task actually crosses system boundaries. A pure-UI component doesn't need integration tests.

**Tier 4 (full cycle) — every phase must include:**
- **Unit tests:** TDD.
- **Integration tests:** real APIs/DBs, no mocks.
- **E2E tests:** UI changes → `e2e-runner` agent.
- **UI spec:** frontend phase WITHOUT existing design reference → `Skill(skill="frontend-design")` (or `design-consultation` for a full design system). **Skip if a locked design reference already exists** (e.g., HANDOFF.md + directions/*.jsx authoritative). Don't double-spec.
- **AI spec:** AI-heavy phase (prompts, evals, guardrails) → produce an AI design doc capturing framework choice + eval plan + guardrails before planning the phase.
- **Design doc:** 2-5 sentences covering data flow + key decisions.

**Before planning (tier 4):** surface implicit assumptions BEFORE `superpowers:writing-plans` — typically inside `superpowers:brainstorming`. This is the single cheapest way to front-load the plan's most valuable catches.

### 2b — Implement

**Subagent policy:**
- Tier 3, ≤2 tasks same file → **inline**
- Tier 3, 3+ tasks shared files → **serial-subagent** via `superpowers:subagent-driven-development`
- Tier 3, 3+ tasks disjoint files (mechanical) → **parallel-worktree** (set up worktrees with `superpowers:using-git-worktrees` first, then dispatch parallel `Task()` implementers)
- Tier 4 → **parallel-worktree**, orchestrated via `superpowers:subagent-driven-development` + `using-git-worktrees` (wave-based)

Announce: `Phase 2b · <mode> (<N> tasks)`.

TDD non-negotiable: tests red → minimal impl green → refactor. Per-phase atomic commit.

### 2c — Review

**Multipass per `references/review-discipline.md`.** Tier 3+ runs ≥2 passes; never ship after a single pass. Tier 4 already enforces this via Phase 3/4. The user never reviews mid-flight — the agent runs every pass autonomously.

**Pass 1 — `code-reviewer` agent.** Reads diff, returns severity-classified findings.
- **Small diff (<500 LOC, <5 files):** single agent.
- **Large diff (≥500 LOC or ≥5 files):** **parallel-readonly** fan-out — one reviewer per concern (security / types / tests / logic / error-handling). Each returns `{concern, findings: [{severity, location, note}]}` ≤200 tokens. Aggregate, dedupe overlap.

**Pass 2 — domain reviewer.** Pick by language/stack — `Skill(skill="code-review")`, `python-review`, `go-review`, or equivalent. Catches idioms/anti-patterns Pass 1 misses.

**Triggered passes (any tier, parallel with Pass 2):**

| Trigger in diff | Pass |
|-----------------|------|
| Auth / secrets / user input / API endpoints | `security-reviewer` agent or `Skill(skill="security-review")` |
| Schema / migration | `database-reviewer` agent |
| New tests | Verify behavior assertions, not mock existence (built into Pass 1 brief) |

UI changes are covered by Phase 2g visual verification — don't double-pass.

Per Phase -1: **fix all findings**, severity controls how (inline vs subagent), not whether.

**Tier 3:** skip `think-ultra` unless the diff involves security / concurrency / data mutation.
**Tier 4:** `Skill(skill="think-ultra")` on the phase diff (`git diff <phase-base>...HEAD`) AFTER pass 1 + pass 2 + triggers. Focus: regressions, unused code, test gaps, architecture concerns, security. Address HIGH/CRITICAL before proceeding.

### 2d — Audit-fix loop (OPTIONAL for tier 3)

Only run if Phase 2c surfaced findings worth sweeping.

**Tier 3 and Tier 4:** `Skill(skill="audit-fix-loop")` — iterative fix-test-verify (code-reviewer audits + parallel fix agents). Skip entirely if review was clean.

Terminates when zero high-confidence issues remain and changed-file coverage hits 80%+.

### 2e — Reflect (SKIP for tier 3 unless something surprising surfaced)

**Tier 4:** `Skill(skill="debrief")` (or `eureka` for a genuine breakthrough) — structured extraction of what happened + what should change, for future phases.
**Tier 3:** only capture learning if it's genuinely new and cross-project-applicable (e.g., a framework gotcha, a surprising library behavior). Otherwise skip — project memory isn't a journal. Append to `~/.claude/projects/<project>/memory/` only for durable patterns.

### 2f — Knowledge sync (AUTO — runs every phase)

**Always invoke `Skill(skill="neat-freak")` at phase boundary.** Three-audience editorial pass:

1. **Agent memory** (`~/.claude/projects/<...>/memory/`) — relative dates → absolute, completed todos removed, conflicting facts merged
2. **Project root markdown** (`CLAUDE.md` / `AGENTS.md`) — routes / env vars / decisions kept current for the next session
3. **`docs/` + `README.md`** — integration-guide / architecture / runbook / handoff files reconciled against the diff (cross-project sync if upstream/downstream affected)

The skill is internally idempotent — it no-ops cleanly when there's nothing to reconcile, so running on every phase is safe. The doc edits land in the same end-of-phase commit as the code (per Phase -1 auto-resolution).

**Codemaps:** if codemaps exist AND were meaningfully affected → `Skill(skill="update-codemaps")` AFTER neat-freak. Codemap regeneration is its own concern (architecture diff visualization), not part of editorial reconciliation.

### 2g — Verify

**Tier 3, no UI changes:** **inline** UAT — list 2-3 verifiable behaviors, check each. Open the dev server and click through if frontend.
**Tier 4, no UI changes:** `Skill(skill="verify")` (or `superpowers:verification-before-completion`) — run the verification commands and confirm output before claiming the phase passes.

**MANDATORY for ANY UI phase — visual verification pass:**

1. Boot dev server (`pnpm dev` or equivalent).
2. Playwright screenshot sweep via `webapp-testing` skill or `npx playwright` — capture every changed route × every theme variant, save to `docs/reports/{phase}-visual/`.
3. **Subagent policy — scale by screenshot count:**
   - **≤3 PNGs total (route × theme)** → **inline**: Claude reads each PNG with `Read` (multimodal), compares against design reference (`HANDOFF.md` / `directions/*.jsx` source / Figma PNG). Per-screen verdict in main thread.
   - **4+ PNGs** → **parallel-readonly**: dispatch one visual-verify subagent per PNG. Each receives `{screenshot_path, design_ref_path, route, theme}`, reads both with `Read`, returns `{route, theme, verdict: PASS|FLAG|BLOCK, concerns: [string]}` ≤150 tokens. Main thread aggregates into a verdict matrix — no raw screenshot data in main-thread context.
4. Per-screen verdict: PASS / FLAG / BLOCK. For BLOCK → open a fix task before declaring phase verified. For FLAG → surface specific concerns (spacing, color, alignment, missing element) to user for decision.
5. **FLAG handling — autonomous mode (Phase -1):** Open a `TodoWrite` follow-up for each FLAG with the specific concern (spacing, color, alignment, missing element, exact letter-spacing, etc.). **Continue to next phase without pausing.** Surface the entire batch of FLAG items at end-of-milestone in the PR description (`## Visual verification flags`). User reviews them post-merge or as a single follow-up PR — not one-at-a-time mid-flight. BLOCK items still halt the phase: open a fix task and execute it inline before declaring phase verified (per Phase -1 auto-resolution table).

Static-grep tests do NOT catch visual drift. Claude's visual comparison is the primary defense; user eyeball is the backup for subtleties. See Adaptation hints → "Locked design reference" for CI-integrated pixel-diff setup.

Phase complete only when verification passes.

**Proceed to next phase.**

---

## Phase 3 — Final ultra-review (TIER 4 ONLY)

**Tier 3 skips this entirely.** The Phase 2c review already covered the diff; re-reviewing a single-phase feature through `think-ultra` on the full milestone diff is the same diff twice. Jump to Phase 5 (docs) if applicable, then Phase 6 (PR).

**Tier 4 (multi-phase milestone):**

1. Cross-phase audit — sweep all outstanding UAT and verification items across phases (`Skill(skill="verify")` over the core flows). Surface anything unverified before the ultra-review.
2. `Skill(skill="think-ultra")` on the full milestone diff (`git diff <main-or-base>...HEAD`). Flag anything slipped through per-phase reviews.
3. Address HIGH/CRITICAL. Defer MEDIUM with explicit "deferred follow-up" entries.

---

## Phase 4 — 8-track final cleanup (TIER 4 ONLY)

**Tier 3 skips this entirely.** The parallel 8-agent cleanup sweep is designed for milestone-scale accumulation of drift. For single-phase tier-3 work, the Phase 2c review + commit discipline already catches what matters. Running 8 parallel agents on a 300-LOC change is over-engineering.

**Tier 4 only:** spawn **parallel** `feature-dev:code-reviewer` agents, one per track (dedupe, shared types, unused code, circular deps, typing, error handling, legacy paths, AI artifacts). Each returns a structured report; implement only high-confidence + low-regret changes.

**Full spec — track table, non-negotiable rules, per-track validation + report template → `references/phase4-8track-cleanup.md` (read it when this phase fires).**

---

## Phase 5 — Final verification + docs/memory

1. `Skill(skill="verify")` — E2E spot-check of core flows
2. **Knowledge sync (milestone scope):** `Skill(skill="neat-freak")` — same three-audience editorial pass as Phase 2f, but scoped to the full milestone diff (`git diff <main-or-base>...HEAD`) rather than the last phase. Catches drift that accumulated across phases (cross-project sync, terminology consistency, doc-structure additions). For Tier 4 milestones that introduce user-facing behavior or new architectural primitives, additionally grep-check each new doc claim against the actual code so the docs are codebase-verified, not just editorially clean.
3. `Skill(skill="update-codemaps")` if codemaps exist and architecture meaningfully changed.

---

## Phase 6 — PR + @claude review loop

### 6a — Commit + push + open PR

**Tier 3 and Tier 4:** commit, push, and `gh pr create` directly.

Precondition: Phase 5 verification passed — this IS the PR readiness gate: tests/lint/build pass locally BEFORE the PR exists; CI confirms, it never discovers. Never open the PR early to "see CI"; every push to an open PR burns a CI run + re-triggers all review bots.

PR description template (enforce): summary bullets · phases shipped · tests added (unit / integration / e2e counts) · risks & follow-ups · test-plan checklist · closing `@claude please review.` Exact template: `references/report-templates.md`.

### 6b — PR review + CI self-healing loop

`Skill(skill="pr-fix-loop")` — polls CI, reads `@claude` review comments, fixes, re-requests review. Auto-cleanup cron on merge.

---

## Exit

When PR merges OR user says "done" / "stop": emit the COMPLETE summary block (phases / commits / tests / LOC / deferred follow-ups / PR url — exact template: `references/report-templates.md`). Delete the cron monitor. Suggest a memory append if cross-project learnings emerged.

---

## Non-goals

- Not for bug fixes, typos, single-function changes, or Q&A
- Not a replacement for the underlying `superpowers:*` skills — those remain available for direct use when the user wants finer control
- Does **not** require every project to have a formal plan doc (tier 3 uses an inline plan only)
- Does **not** override user saying "quick and dirty" or "skip workflow"

---

## Adaptation hints

Per-situation adjustments (tier 3 = no plan doc, single implicit phase; no frontend → skip UI spec + E2E; monorepo → per-package cleanup; no tests in repo → test-scaffolding sub-phase; schema/migration → tier 4 regardless of file count; codebase mapping via codegraph + parallel Explore agents; AI-heavy phase → AI design doc first; external design bundles → copy into the repo before Phase 1; locked design reference → 3-layer visual defense): `references/adaptation-hints.md`.
