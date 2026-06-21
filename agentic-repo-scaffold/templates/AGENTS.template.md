# AGENTS.md — Repository Contract for AI Coding Agents

This repo is maintained by humans and AI coding agents. Treat this file as the architecture contract. Keep it a routing map, not a knowledge dump — link to deeper docs.

> Fill every `<…>`. Delete stack sections that don't apply. Use the repo's REAL directory names — map the roles (pure core, orchestration, ports, adapters, isolated generated, thin transport) onto existing paths; don't impose new names on a legible repo.

## First steps (every task)
1. Read this file and any local `AGENTS.md` in the target subtree.
2. Read the build/test scripts (`<package.json scripts | Makefile | …>`).
3. Identify the smallest module/feature/service that owns the change.
4. Read the relevant contracts before implementing.
5. Plan before touching multiple layers.
6. Run `<verify command>` before claiming done.

## Architecture map
- `<path>` — `<role: route entries / pure core / application orchestration / ports / adapters / generated / tests>`
- … (one line per top-level landmark; a path must imply allowed imports + likely tests)

## Import rules
- Consumers import only a module's public API (`<public/ | index.* | api/>`); deep imports into internals are forbidden (enforced by `tools/verify/check-boundaries`).
- Pure core/domain imports no IO, framework, env, clock, random, or adapters.
- Application depends on ports, not concrete adapters.
- Adapters own all side effects; transport handlers stay thin (parse → auth → validate → one use case → map response).
- `generated/` is never hand-edited.
- Shared utilities must not import feature/module internals.

## Contract rules
Contractize every cross-boundary value and import it from the contract file — never duplicate the string:
- routes/params · API request/response · storage keys + payloads · events/messages · errors · config/env · domain entities · DOM test IDs · design tokens · telemetry names
- **Backend also:** OpenAPI/proto/AsyncAPI specs · RFC 9457 error envelope · DB constraints in migrations (append-only) · idempotency contracts for retried mutations · versioned async payloads · observability span/metric/log field names.
- Runtime-validate all external/persisted/untrusted input at the boundary (schema, e.g. Zod/JSON Schema); pass validated domain types inward. Don't change a public contract without compatibility checks + tests.

## File limits (split or allowlist with owner/reason/expiry)
- route page `<80>` · layout/route handler `<100>` · transport handler `<100>` · component `<200>` · core/application/adapter `<250>` · general source `<300>` · test `<400>` · non-generated hard cap `<500>`.

## Verification
```bash
<verify command>   # static + contracts + unit + integration + architecture + security + generated-clean + giant-file
```
CI runs the same command. **Done = it passes, or exact blockers are documented with command output.** Never mark done from inspection alone.

## Long-running work
Maintain `.agent/PROGRESS.md` (checkpoint state), `.agent/EVIDENCE.md` (command output per item), `.agent/DECISIONS.md` (architecture choices). Keep the repo buildable between checkpoints.

## Done definition
Change is in the owning module · contracts updated · core stays pure · side effects adapterized · file limits respected · generated files regenerated not hand-edited · relevant tests pass · architecture checks pass · verification evidence available.
