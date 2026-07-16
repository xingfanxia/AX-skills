# Phase 0.0 — Profile detection detail

(Extracted from SKILL.md to keep the router lean. This is the full Step 2 scan + Step 3 routing detail.)

### Step 2 — Auto-detect from repo signals (runs only when no explicit block)

Run ONE bash command to collect signals (≤1s):

```bash
{
  # Schema: concrete file existence tests only — DO NOT use `ls glob | head` because that always succeeds on empty input in zsh
  ( [ -f prisma/schema.prisma ] || [ -f drizzle.config.ts ] || [ -f drizzle.config.js ] || [ -f drizzle.config.mjs ] || [ -f knexfile.js ] || [ -d db/migrations ] || { [ -d migrations ] && find migrations -maxdepth 1 -name "*.sql" 2>/dev/null | grep -q . ; } ) && echo schema
  # Auth / payment libs
  [ -f package.json ] && grep -qE '"(stripe|@stripe|better-auth|next-auth|@auth/core|lucia)"' package.json 2>/dev/null && echo auth-payment
  # Components dir (root OR src/ OR app/) + UI framework
  ( [ -d components ] || [ -d src/components ] || [ -d app/components ] ) && [ -f package.json ] && grep -qE '"(tailwindcss|@radix-ui|@chakra-ui|@mui/material|shadcn)"' package.json 2>/dev/null && echo components-ui
  # Locked design reference
  ( [ -f HANDOFF.md ] || [ -d directions ] || [ -d docs/design ] ) && echo design-ref
  # E2E framework
  [ -f package.json ] && grep -q '"@playwright/test"' package.json 2>/dev/null && echo playwright
  # Markdown content volume
  CONTENT=0
  for d in content/posts _posts content/blog docs/posts posts; do
    [ -d "$d" ] && CONTENT=$((CONTENT + $(find "$d" -maxdepth 2 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')))
  done
  [ "$CONTENT" -gt 5 ] && echo "content-$CONTENT"
  # Backend language indicator
  ( [ -f go.mod ] || [ -f Cargo.toml ] || [ -f pyproject.toml ] ) && echo backend-lang
} 2>/dev/null
```

**Classify from emitted signals** — apply rules in order, first match wins:

| # | Rule | Profile | Reasoning |
|---|------|---------|-----------|
| 1 | `content-N` where **N >= 20** | `light-project` | Overwhelmingly content-dominant (blog, docs repo). Even if the repo also has components or accidental schema artifacts, the content is what ships. Blog with 270 posts + MarkdownRenderer component is still a blog. |
| 2 | (`schema` OR `auth-payment`) AND (`backend-lang` OR NOT `components-ui`) | `heavy-project` | Real backend risk (migrations / auth / payments) in a codebase that's primarily backend-shaped. Requires TDD + spec discipline. |
| 3 | `components-ui` OR `design-ref` OR `playwright` | `ui-project` | UI work with visual verification stack. Shichuan/Elan canonical shape. |
| 4 | `content-N` where N >= 5 (fell through rule 1) | `light-project` | Moderately content-dominant but mixed. Still prefer light unless clear heavy signal. |
| 5 | Anything else (only `backend-lang`, or nothing) | `unknown` | Can't confidently classify — fall through to Phase 0 rubric. |

Call this the **repo-shape profile**. It reflects what the codebase IS, not what the current task IS.

### Step 3 — Route by final profile

**If `light-project`:**
- **Exit big-task immediately.** Execute the request directly in the current context — no subagents, no planning, no tier rubric, no superpowers cycle.
- This is the project's "just do it" stance for solo blog/content/script work.
- **Escalation exception:** if the request clearly involves schema migrations, cross-service protocol changes, atomicity, or concurrency, **silently escalate to Phase 0 rubric** (per Phase -1 auto-resolution table) and log the escalation in the PR's `## Autonomous decisions` section. Do NOT pause to confirm — schema/auth/concurrency are class-2 critical decisions only when the user is making the architectural choice itself, not when escalating tier.

**If `ui-project`:**
- **Force Tier 3 (light process), skip Phase 0 rubric entirely.** File count and "architectural risk" heuristics don't apply — UI work is visual-driven with Playwright verification, which inverts the usual risk calculus.
- Use superpowers `subagent-driven-development` for multi-component work. Invoke `brainstorming` ONLY for a truncated spec (1 page max) — do NOT produce inline code, TypeScript essays, or 1000+ line plans.
- Plans are checkbox task lists (files + Playwright assertion per task), not treatises.
- **Verification at Phase 2g is MANDATORY Playwright sweep**: Claude reads the PNGs directly (multimodal), compares against design reference. No LLM verifier agent.

**If `heavy-project`:**
- Proceed with Phase 0 rubric below, BUT at Tier 4 use the superpowers full cycle (`brainstorming` → spec → `writing-plans` → `subagent-driven-development` → `requesting-code-review` → `verification-before-completion`).
- Worktrees, TDD-mandatory, human + automated code review all apply.

**If `unknown`:** fall through to Phase 0 rubric. Default Tier 4 engine is the superpowers cycle (see description paragraph above). When the task completes, if the project has durable character, suggest the user run `/workflow-profile <name>` to make routing sticky and skip the detection cost next time.

### When auto-detection gets it wrong

If detected profile is obviously wrong (e.g., auto-detected `ui` on a repo that's actually a backend-with-small-UI heavy project), **trust the auto-detect and proceed silently** (per Phase -1). Re-route ONLY mid-flight if 2+ phases produce FLAG verdicts pointing at the wrong profile — at that point the evidence is on disk, not a judgment call. Log the detected profile in PR `## Autonomous decisions` so the user can `/workflow-profile <name>` to pin a different one for next time.

