# CLAUDE.md

Primary repository instructions live in `AGENTS.md`. Read it before editing.

Claude-specific:
- Use plan mode for changes touching multiple modules, contracts, or architecture boundaries.
- For long-running work, maintain `.agent/PROGRESS.md`, `.agent/EVIDENCE.md`, `.agent/DECISIONS.md`.
- If context is compacted/resumed, reread `AGENTS.md`, the `.agent/` ledgers, and the recent git diff.
- Don't rely on memory for architecture rules. Don't mark done from inspection — run the verify command or document exact blockers.
