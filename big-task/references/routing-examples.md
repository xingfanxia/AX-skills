# Profile-routing worked examples (Phase 0.0 Step 2.5)

Teaching examples showing task-intent judgment, not keyword lookup. Read when the combining rule doesn't settle a classification cleanly.

- Blog repo + "translate this post" → `light` — task is prose translation; repo is light; align.
- Blog repo + "add Stripe paywall for premium posts" → `heavy` — task introduces a revenue boundary; blast radius is customer money; repo shape is irrelevant.
- Backend repo + "fix a typo in README" → `light` — task is prose; no system-risk boundary; repo shape is irrelevant.
- Backend repo + "add a new column to the users table" → `heavy` — task modifies persistence; even though it's a small diff, the blast radius of a bad migration is high.
- UI repo + "build a real-time notification subsystem from scratch" → `heavy` — task introduces a new architectural subsystem that will set patterns.
- UI repo + "restyle the button to match the new design reference" → `ui` — task is translation-of-design, N+1 pattern application.
- UI repo + "decide whether to use Zustand or Redux for state management" → `heavy` — task is a design decision that will be copied across the codebase.
- Any repo + "fix alignment of the footer on mobile" → `light` — pure cosmetic tweak, no pattern change.
