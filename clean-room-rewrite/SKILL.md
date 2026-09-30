---
name: clean-room-rewrite
description: Decide whether a legacy codebase should be rewritten or refactored, and when a rewrite wins, rebuild it clean-room — distill the old system into an executable behavior spec, have a builder that never reads the old source implement it, audit parity against the old code with independent models, then shadow-run on real data and cut over with rollback. Use when asked to rewrite, rebuild, or 回炉重造 a system, or to judge whether a codebase is too tangled to refactor.
metadata:
  version: "1.0.0"
---

# Clean-Room Rewrite

Classic rewrites fail because implicit behavior gets lost. AI refactors of a
tangled codebase fail differently: once the agent reads the old code it
anchors on the old structure, and the "rewrite" becomes a reshuffle of the same
mess. A clean-room rewrite separates the two failure modes with an
**information barrier**:

- **Distillers and auditors** read the old code, the live system, and the data.
- **The builder** reads only the spec package and the old system as a black box
  (its UI, public responses, and sample data) — never the old source.
- **The spec package is the only channel** from old to new. Every gap an auditor
  finds goes back into the spec first, then into the code.
- **Parity is proven by execution** — oracle tests and a shadow run on real
  data — not by review prose.

Method inspired by the AIHOT 2.0 rewrite by 卡兹克
([KKKKhazix/AIHOT](https://github.com/KKKKhazix/AIHOT)). This skill adds a
decision gate before any rewrite, an executable spec with traceable IDs,
deterministic stop rules, a strangler variant for large systems, and a
cutover/rollback contract.

## Step 0 — decide first; most codebases should not be rewritten

Run the gate in [references/decision-gate.md](references/decision-gate.md) and
write the verdict with its evidence before producing any spec. A rewrite wins
only when all of these hold:

0. **The target is the existing product.** Parity against old behavior is
   wasted when the roadmap will change much of it. If the wanted product
   differs substantially, write a target spec instead and lock parity only on
   the subset being kept.
1. **Structure is the dominant cost of change.** Measured change coupling,
   duplication, and god files — not domain difficulty, not missing tests, and
   not a process or verification layer that happens to be heavy.
2. **Behavior is observable.** A black-box oracle exists: a live site, API
   responses, job outputs, and production data you can replay.
3. **The spec fits the builder's context.** The architecture plus one module's
   spec must fit in a builder's working context at a time; otherwise split into
   bounded contexts that each fit (Variant B). Agent hours are rarely the
   binding constraint; context and verification are.
4. **State migration is tractable and reversible.** Persisted formats, IDs,
   money and entitlement state, and user records can be carried over and
   rolled back.
5. **A shadow run is possible** before users depend on the new system.

The numbers in the gate are signals, not thresholds. Compare the full cost of
the rewrite — distillation, build, migration, acceptance — with targeted
repair. If any condition fails, the answer is a targeted refactor or Variant B.
A verdict of "do not rewrite" is a complete result.

The verdict is a recommendation. Committing to a rewrite is an irreversible
architecture decision that belongs to the product owner: deliver it as a
≤10-line verdict with the measurements, the cost estimate, and the ranked
alternatives.

## Roles

| Role | Reads | Produces |
|---|---|---|
| Distillers (≥2, independent) | old source, live system, data, ops config | independent spec drafts |
| Reconciler | both drafts + old source | the single reconciled spec package |
| Builder | spec package + black-box oracle only | the new system |
| Auditors (independent of the builder) | old source + new source + spec | parity findings mapped to ledger IDs |

Diversity catches omissions: use different model families for the two
distillers and for auditors versus the builder when available. Scale the roles
to the slice: a small Variant B context can use one distiller plus a strong
oracle suite. With a single model, use fresh sessions with isolated context and
lean harder on executable oracles.

**Enforce the barrier by construction.** A worktree is not a barrier — it shares
Git history, and earlier sessions still hold the old source in context. The
builder gets a fresh directory with no old Git history containing only the
spec package and the carried-over data, a fresh session, and no read access
to the old repository. The old schema reaches the builder only through
`contracts/data-model.md`; production snapshots enter the builder's
environment at the shadow phase, not before. "Please do not look" is not a
barrier.

**Carry data, not structure.** Knowledge bases, copy, prompts, translations,
fixtures, and static assets are data: move them verbatim and list them in the
spec's carry-over manifest. Rewriting curated domain data from prose loses it.
Generated artifacts such as database types are not data; regenerate them from
the target schema.

## Phases

1. **Inventory and gate** (Step 0). Enumerate routes, APIs, tables, jobs,
   webhooks, environment config, external integrations, and persisted formats
   mechanically — scripts and listings, not recollection.
2. **Distill** in parallel into the package format of
   [references/spec-package.md](references/spec-package.md): behavior ledger,
   contract inventory, pitfall ledger, data and migration notes, operations,
   carry-over manifest, non-goals, and black-box oracle tests recorded against
   the old system.
3. **Reconcile.** Diff the drafts; resolve every disagreement against the old
   source; check that every enumerated surface maps to a ledger ID. Design the
   target architecture for parallel agents: contracts and data model first,
   modules with narrow context.
4. **Build clean-room.** Contracts, schema, and migrations first; then modules
   in parallel. The oracle suite is the builder's acceptance. Deviations go in a
   decisions log, not silently into code; dropping or changing behavior needs
   the owner's authorization, not only a decisions entry.
5. **Parity audit.** Independent auditors compare old and new by module and
   report gaps against ledger IDs. Each gap amends the spec, then the builder
   fixes it. Finish with a fresh-context pass per feature module that ignores
   implementation and compares function and logic only.
6. **Bug and security audit, then improvements.** Keep redesign out of the
   parity phase: lock parity, then change UI or behavior as recorded decisions.
   Mixing them makes a regression indistinguishable from an intended change.
7. **Rehearse and shadow.** Import a production snapshot, run the new system
   beside the old one on real traffic and scheduled jobs, and diff outputs.
   Classify every difference as bug, intended change, or noise.
8. **Independent end-to-end acceptance** by an agent other than the builder.
9. **Cutover with rollback** per
   [references/parity-and-cutover.md](references/parity-and-cutover.md).
10. **Tune on real data** — caching, payload size, queries — and monitor.

## Stop rules

Audit loops need deterministic exits or they never end:

- **Spec complete:** every enumerated surface maps to at least one ledger ID,
  and every disagreement between the distillations is resolved.
- **Build complete:** the oracle suite passes, and each ledger ID is
  implemented or is an owner-authorized non-goal.
- **Parity complete:** zero open blocking findings; every difference classified
  as a bug is fixed and the oracle suite re-run green after the fix; the shadow
  diff has no unclassified difference over a window in which every scheduled
  job ran at least once. Two consecutive clean audit rounds are supporting
  evidence, not a substitute.
- **Cutover ready:** rollback was rehearsed, including the path for
  transactions created after the switch, and its timing measured.

And one exit for failure:

- **Abort:** if two consecutive parity rounds do not reduce the count of
  unledgered findings, distillation has failed. Stop, then fall back to Variant
  B on a smaller context or to targeted refactoring. Set a budget up front and
  stop when it is spent without convergence.

## Variant B — strangler rewrite for large systems

When the whole system fails condition 3, apply the same loop per bounded
context behind its existing contract: distill one context, rebuild it
clean-room, shadow it behind a flag or route split, cut over, and delete the
old path after the hold period before starting the next. Each context passes
the gate on its own; a missing oracle or rollback is not waived because the
slice is small. Start with the context whose change cost is highest and whose
state is simplest. Never run two contexts half-migrated at once.

Variant B requires the old and new sides to serve the same contract. A
redesigned surface that changes the product shape (different navigation,
features, or information model) is a new product, not a strangler slice:
condition 0 applies, and retiring the old surface is a product decision.

## Failure modes

- **Prose-only spec.** Implicit behavior — URLs, field order, cache headers,
  cookie names, timezones, retry semantics — survives only as contracts and
  oracle tests (Hyrum's law).
- **Leaky barrier.** A builder that reads the old code "just to check"
  reproduces its structure.
- **Rewriting the wrong problem.** When the pain is a heavy process layer,
  flaky tests, or missing knowledge, a rewrite rebuilds the same pain.
- **Money, auth, and private-data boundaries rebuilt from prose.** These need
  explicit contract tests and replay/concurrency checks carried over or
  re-recorded before cutover. Keep a single writer for money state; see the
  cutover reference.
- **Deleting protection by directory.** When collapsing a verification layer,
  classify each check by the contract it protects, not by its folder or era;
  an aggregate gate often hides a money or auth check inside.
- **Data migration as an afterthought.** Schema, IDs, and persisted payloads
  are part of the contract inventory from phase 1.
- **Cutover without a rehearsed rollback.**

## Deliverables

- the gate verdict with its measurements;
- the reconciled spec package and oracle suite;
- the new system, with a decisions log and a carry-over manifest;
- audit reports whose findings are mapped to ledger IDs and closed;
- the shadow-run diff classification, cutover record, and rollback evidence.
