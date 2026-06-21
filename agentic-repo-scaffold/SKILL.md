---
name: agentic-repo-scaffold
description: >
  Scaffold a repository's agent-maintainability contract: an AGENTS.md architecture
  contract, an executable verification harness (boundary / giant-file / generated-clean
  checks), a single `make verify` / `pnpm verify` command, `.agent/` refactor ledgers,
  and optional Cursor rules. Stack-aware (frontend / backend / general). Use when the
  user says "scaffold AGENTS.md", "set up the agent contract", "add a verification
  harness", "make this repo agent-maintainable", "add architecture boundary checks",
  "wire up make verify", or starts/hardens a repo for long-horizon AI-agent maintenance.
  Implements the bundled agentic-repo-architecture blueprint (references/). Distinct from
  /init (which writes a codebase-documentation file): this writes the architecture
  CONTRACT + executable gates.
---

# agentic-repo-scaffold

Turns the agentic-repo-architecture framework into committed, executable artifacts in a target repo.

**Core principle:** instruction files are context, not enforcement. Every architecture rule this skill writes into `AGENTS.md` must have a matching deterministic check in `tools/verify/` and CI, or it will be violated under context pressure.

## When to use / not use

- **Use** for: a new repo, or hardening an existing one toward agent-safe boundaries; adding the verify harness; wiring `make verify`; standing up `.agent/` ledgers for a long refactor.
- **Don't use** for: writing a codebase-walkthrough doc (that's `/init`), or a one-file change. This is repo-infrastructure scaffolding.

## Procedure

Create a todo per step.

### 1. Detect stack and existing surface
- Read `package.json` / `go.mod` / `pyproject.toml` / `Cargo.toml`, the build scripts, and the top-level tree.
- Classify: **frontend/full-stack** (Next.js/React), **backend/service** (API/worker/RPC/events), or **general** (CLI/SDK/lib/monorepo/infra). Monorepo → classify per package.
- Inventory what already exists: `AGENTS.md`, `CLAUDE.md`, any `tools/verify` or check scripts, `.agent/`, `.cursor/rules`, a `verify` command, CI workflow. **Never clobber a richer existing file** — extend it, or write a `.proposed` sibling and diff.
- Load the matching stack reference (bundled in this skill) for the authoritative layer rules / contract tables / acceptance matrix:
  - frontend → `references/frontend.md`
  - backend → `references/backend.md`
  - general → `references/general.md`

### 2. Write `AGENTS.md` (the architecture contract)
- Start from `templates/AGENTS.template.md`. Fill in: real architecture map (use the ACTUAL directory names in this repo — don't impose `core/application/ports/adapters` names if the repo already has a working, legible convention; map the *roles* onto its real paths), import rules, contract rules, file limits, the verify command, and the done-definition.
- Enrich the stack-specific sections (layer table, boundary rules, backend contract list) from the matching reference file's §6/§8. Keep it a routing map, not a knowledge dump — link to deeper docs rather than inlining them.
- If `CLAUDE.md` is absent, drop the thin pointer from `templates/CLAUDE.pointer.md`. If it exists and is substantive, leave it; just ensure it references `AGENTS.md`.

### 3. Install the verification harness
- Copy from `templates/`, adapting globs/paths to the repo:
  - `check-giant-files.mjs` (language-agnostic LOC gate; or `check-giant-files.py` for non-JS repos)
  - `check-boundaries.mjs` (forbidden-import / purity check — set the layer regexes to the repo's real paths)
  - `check-generated-clean.sh` (regenerate + `git diff --quiet`; skip if the repo has no generated code)
- Wire ONE canonical command running the full gate set. Match the repo's runner:
  - JS/TS → a `verify` script in `package.json` (typecheck → lint → unit → contract → e2e/visual where present → architecture checks).
  - Go → a `make verify` target (`go vet` → `golangci-lint` → `go test ./...` → arch/giant-file checks).
  - Python → `make verify` (`ruff`/`mypy` → `pytest` → checks).
- Use `templates/Makefile.fragment` or `templates/package.verify.json` as the starting shape.

### 4. Stand up `.agent/` ledgers (only for genuine long-horizon work)
- Create `.agent/PROGRESS.md`, `.agent/EVIDENCE.md`, `.agent/DECISIONS.md` from `templates/agent-ledgers/`.
- These are repo-committed ledgers for *multi-session refactors* — not session-handoff scratch files. Name them PROGRESS/EVIDENCE/DECISIONS, commit them, and skip this step for a fresh repo with no active long refactor.

### 5. Optional: Cursor rules
- If the repo uses Cursor, drop the scoped `.cursor/rules/*.mdc` from the matching reference §8 (boundaries rule + verification rule). Skip otherwise.

### 6. Optional: CI gate
- If a CI workflow exists, add a job that runs the canonical verify command. If not, offer `templates/ci-verify.yml` (GitHub Actions). A check that isn't in CI is advisory only.

### 7. Verify the harness actually runs
- Run each new check script and the verify command. They must execute (even if they report pre-existing violations — that's signal, surface it). A scaffold that doesn't run is not done.
- Report: what was created/extended, which checks pass vs. flag existing debt, and the exact `verify` command. Do **not** mark done from inspection — show command output.

## Notes
- Templates and the `references/` blueprint ship inside this skill, so the package is self-contained.
- Be surgical: in an existing repo, adapt to its conventions rather than imposing the reference's directory names. The *roles* (pure core, orchestration, ports, adapters, isolated generated, thin transport) are the invariant; the *names* are the repo's.
