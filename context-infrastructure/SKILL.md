---
name: context-infrastructure
description: Design, audit, or improve durable context and memory systems for AI agents using layered observations, reflection, conservative promotion, progressive disclosure, and replayable boundary artifacts. Use when building long-running agent memory, deciding what belongs in sessions versus rules or skills, preventing context bloat, or turning repeated corrections and workflows into durable assets. Do not use it to copy another person's private axioms or automatically promote one-off observations.
---

# Context Infrastructure

Treat context as a compounding system, not a giant prompt. Route, filter, test,
and promote experience so future agents receive the smallest useful context.

This AX adaptation is inspired by the public
[`grapeot/context-infrastructure`](https://github.com/grapeot/context-infrastructure)
reference implementation and the Observer/Reflector pattern described by
[Mastra Observational Memory](https://mastra.ai/research/observational-memory).
Reuse the architecture, not another person's accumulated axioms, preferences,
or private data.

## Define four layers

| Layer | Purpose | Typical contents |
|---|---|---|
| L0 Session | Execute the current task | Prompt, active diff, command output, current plan |
| L1 Observations | Preserve selected raw signals | User corrections, repeated friction, notable failures, explicit preferences |
| L2 Reflection | Distill and discard | Deduplicated patterns, contradictions, counterexamples, promotion proposals |
| L3 Durable assets | Change future behavior | Axioms, reusable skills, global methodology, technical knowledge, project memory |

Do not skip layers. Keep a new signal in L1 until reflection shows that it is
repeated, stable, useful outside the original task, and routed to the right
scope.

## Separate observation from promotion

Make the Observer append concise evidence. Make the Reflector merge, discard, or
propose promotion.

- Record only explicit corrections, preferences, retractions, and recurring
  workflow lessons worth reconsidering. Most tasks should produce no memory.
- Preserve source, date, scope, and counterexamples needed to evaluate a signal.
- Merge duplicates and flag contradictions during reflection.
- Generate a reviewable promotion proposal before changing durable rules,
  axioms, skills, or shared memory.
- Keep automatic promotion off by default unless the domain has deterministic
  validation, rollback, and an explicitly authorized policy.

This split prevents one intense session from rewriting long-term behavior.

## Route promotion by scope

| Repeated signal | Durable target |
|---|---|
| Stable personal preference | Personal axiom or preference profile |
| Repeated cross-project workflow | Reusable skill |
| Global operating methodology | Focused rule or policy |
| Reusable technical lesson | Knowledge entry |
| Project-specific decision or constraint | Project memory or source-of-truth documentation |
| One-off task fact | Keep ephemeral or discard |

Promote only claims that change future decisions. Preserve dissent and edge
conditions; a rule without boundaries is usually too broad.

## Design for progressive disclosure

- Keep the global entrypoint as a routing table, not the whole memory system.
- Use indexes to tell agents when to load focused rules, skills, or knowledge.
- Put triggering information in skill metadata and detailed procedure in the
  skill body or directly linked references.
- Retrieve project-specific context before global history when the task depends
  on current source truth.
- Prefer sparse, high-density context over broad dumps and repeated summaries.

Do not add another agent when a fixed-contract parser, index, or API call can
route the context deterministically.

## Make boundaries inspectable

For every context-producing workflow, define:

1. **Input boundary:** source records, time window, permissions, and freshness.
2. **Selection boundary:** inclusion, exclusion, deduplication, and privacy rules.
3. **Artifact boundary:** an inspectable observation or reflection record before
   AI judgment becomes durable.
4. **Promotion boundary:** owner, threshold, review, target, and rollback.
5. **Consumption boundary:** which task shape loads which durable asset.

Store AI-facing inputs and AI-produced intermediate outputs when they affect
visible or durable behavior. Debug bad output by inspecting freshness,
timestamps, filters, ordering, and fallbacks before changing the model or prompt.

## Protect integrity

Test the parts that future agents rely on:

- parser and schema shape;
- time-window and freshness filtering;
- deduplication and contradiction handling;
- fallback and retry signals;
- privacy, secret, and retention scans;
- deterministic replay from saved boundary artifacts;
- promotion thresholds and rollback behavior.

Minimize collection. Do not inspect private stores, upload records, or broaden
retention without authorization. Redact secrets before an observation becomes a
shared or durable artifact.

## Completion contract

Return a compact system design or audit containing:

- the L0–L3 stores and owners;
- Observer and Reflector contracts;
- the signal-to-target promotion table and review threshold;
- progressive-disclosure routing;
- privacy, freshness, replay, and rollback checks;
- remaining manual decisions.

Complete only when a new observation can be traced from source to consumption
without silent promotion or an uninspectable context jump.
