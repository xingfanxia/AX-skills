# Adaptation hints

(Extracted from SKILL.md. Per-situation adjustments to the default routing.)

## Adaptation hints

- **Tier 3** → no formal plan doc, single implicit phase, inline plan
- **No frontend changes** → skip the UI spec, skip E2E tests
- **Monorepo** → apply 8-track cleanup per package, parallelize agents per package
- **No existing tests in repo** → include a "test scaffolding" sub-phase in phase 1
- **Schema/migration involved** → bump to tier 4 regardless of file count
- **User already has a plan doc for unrelated work** → write the new milestone into its own plan doc, don't clobber existing
- **Codebase mapping** — use codegraph (`mcp__codegraph__*` / `codegraph` CLI) for symbol discovery; fan out parallel `Explore` agents per area. Tier 4 initial mapping should cover stack, conventions, test setup, and known concerns (README drift, tech debt, migration blockers) — the concerns survey is critical for downstream phase planning. Reserve a single focused `Explore` agent for targeted refreshes when one specific area changed.
- **AI-heavy phase (LLM prompts, evals, prompt engineering)** → produce an AI design doc (framework selection + eval planning + guardrails) before `superpowers:writing-plans`.
- **External design bundle** (Claude Design, Figma export, v0, prototype) → copy to `docs/{project}/reference/` **before Phase 1**. Cite persistent paths in the plan doc — never reference `/tmp/` or external URLs that will break mid-project.
- **Locked design reference (HANDOFF.md, directions/*.jsx, theme-ui.jsx, Figma URL, screenshots)** → static-grep tests only catch textual/structural drift, NOT visual drift. Every UI phase MUST run the Phase 2g visual verification pass (screenshot sweep → Claude multimodal compare → PASS/FLAG/BLOCK). For milestones with 2+ UI phases, additionally set up Playwright + pixelmatch/resemble.js pixel-diff against checked-in baseline PNGs in CI (~30-60 min setup) — stricter than Claude's visual eye, catches 1-2px subtleties. Rationale: agents interpolating "reasonable" styling off-reference is a known failure mode; screenshot → visual compare → pixel-diff is a 3-layer defense.
