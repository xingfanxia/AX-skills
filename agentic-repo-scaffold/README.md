# agentic-repo-scaffold

Turns the agentic-repo-architecture framework into committed, executable artifacts in a target repo: an `AGENTS.md` architecture contract, a one-command verification harness with runnable boundary / giant-file / generated-clean checks, `.agent/` refactor ledgers, and optional Cursor rules + CI gate. Stack-aware (frontend / backend / general).

**Why a skill, not just docs:** instruction files are context, not enforcement. The architecture rules only hold if a deterministic check fails CI when they're broken. This skill installs those checks alongside the prose.

## Entry point
`SKILL.md` — the procedure. Invoked via the Skill tool or trigger phrases like "scaffold AGENTS.md", "add a verification harness", "make this repo agent-maintainable".

## Layout
- `SKILL.md` — stack detection → AGENTS.md → verify harness → `.agent/` ledgers → optional Cursor/CI → run-and-prove.
- `references/` — the full blueprint, bundled so the package is self-contained: `general.md` (framework-agnostic core), `frontend.md` (Next.js/React), `backend.md` (services). Each ships with source matrices + citations.
- `templates/` — droppable artifacts:
  - `AGENTS.template.md`, `CLAUDE.pointer.md`
  - `check-giant-files.mjs` / `check-giant-files.py` / `check-boundaries.mjs` / `check-generated-clean.sh` (dependency-free, runnable)
  - `Makefile.fragment`, `package.verify.json`, `ci-verify.yml`
  - `agent-ledgers/{PROGRESS,EVIDENCE,DECISIONS}.md`

## The one mental model
```
explicit public API + pure core + application/orchestration + ports + side-effect adapters
+ machine-readable contracts + generated-code isolation + executable architecture rules
+ one-command verification + separate verification context
= a repo coding agents can safely maintain
```

Cross-platform: Claude Code · OpenAI Codex · OpenClaw. Distinct from `/init` (codebase-doc file); this writes the architecture contract + executable gates.
