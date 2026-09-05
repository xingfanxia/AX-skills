# Adaptation hints

Read only the cases relevant to the current task.

- **Existing plan or locked design:** reuse accepted decisions and references.
  Preserve unrelated plans. Persist temporary inputs only when continued access
  is necessary and copying is within scope; stable external references are valid.
- **Visual change:** inspect the affected rendered states against the reference.
  Screenshots catch visual drift that static text checks miss. Use the existing
  visual regression harness when available; add one only when the requested
  behavior and regression risk justify it.
- **Monorepo:** trace affected consumers and shared contracts, then target checks
  to those packages plus required repository gates.
- **No test harness:** choose a direct reproducible check first. Add scaffolding
  only if meaningful verification requires it or the user requested it.
- **Migration:** establish compatibility, existing data, rollback limitations,
  and relevant deployment ordering before changing persistence.
- **AI behavior:** identify the deterministic contract, representative failure
  cases, and acceptance evidence. Use existing eval infrastructure when it
  addresses the behavior; a new framework or design document is not automatic.
- **Unfamiliar codebase:** use available source search and symbol navigation;
  delegate independent discovery only when it adds useful evidence. Index
  generation is optional and should not modify tracked source unexpectedly.
