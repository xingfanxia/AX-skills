---
name: ai-workflow-spine
description: Use when designing, auditing, or improving an AI-native workflow, agentic project, coding-agent setup, skill, pipeline, scheduled automation, or LLM-backed product where deterministic code and AI judgment interact.
---

# AI Workflow Spine

Use this skill to turn a fuzzy AI workflow into a maintainable system with explicit boundaries, replayable artifacts, and tests that let future agents iterate safely.

## Goal

Produce or improve a workflow where deterministic engineering and AI judgment each do the jobs they are best suited for, with a clear artifact boundary between them.

## When To Use

Use for:

- New AI/agent projects.
- Codex, Claude Code, OpenCode, or agent workflow setup.
- LLM-backed pipelines, scheduled automations, report generators, image/content generators, or research systems.
- Refactors where model prompts, tools, sources, and code are tangled together.
- Postmortems where bad AI output may be caused by stale or polluted inputs.

Do not use for small deterministic code fixes unless the bug crosses an AI/tool boundary.

## Core Pattern

Default spine:

`PRD -> RFC -> deterministic boundary artifact -> AI judgment step -> replayable output -> tests`

Use the lightest version that fits the task. A one-day project may need a short README section instead of separate docs, but it still needs the boundary and verification.

## Instructions

1. Identify the deterministic layer.
   - Collection, filtering, parsing, auth, config, scheduling, idempotency, retries, validation, and persistence should usually be code.
   - Make source enablement config-driven when possible.

2. Identify the AI judgment layer.
   - Interpretation, selection, synthesis, summarization, prompt writing, ranking, or dynamic research may belong to an LLM or agent.
   - Prefer a single API call when the input/output contract is fixed.
   - Upgrade to an agent only when the workflow must fetch extra context while deciding.

3. Define the boundary artifact.
   - Choose a plain, inspectable artifact: markdown context, JSON bundle, prompt file, CSV, rendered report draft, transcript, or query result bundle.
   - The artifact should be understandable without re-running private tools.
   - Save enough metadata to debug freshness and filtering: source, timestamp/window, config mode, and fallback reason when relevant.

4. Make outputs replayable.
   - Save the AI-facing input and the AI-produced intermediate output when they affect user-visible results.
   - Retry generation from the same intermediate artifact before recollecting data.
   - When output quality is poor, inspect the artifact before tuning prompts or switching models.

5. Define the control contract.
   - Use the lightest runner that fits: an ordinary turn for short or exploratory work, a persisted goal for bounded multi-turn work with verifiable completion, and a scheduled task only when inputs recur or external state must be revisited later.
   - For schedules, continue the same task when prior context matters; use standalone runs when each input window should be independent.
   - Name the trigger, one run's work unit, freshness or delta check, no-op condition, completion condition, pause/escalation conditions, and retry or cost boundary. Match polling cadence to how often the source can meaningfully change.
   - Separate completion of one run from retirement of a recurring routine. An unchanged source should normally produce a cheap no-op, not repeated work.
   - Pilot the exact prompt, tools, model route, and permissions on a representative slice before unattended execution; review early runs before widening scope or cadence.

6. Document decisions.
   - PRD: product philosophy, success criteria, target user, non-goals.
   - RFC: architecture boundary, alternatives rejected, coupling choices, fallback behavior, known failure modes.
   - Working log: changelog and lessons learned from real failures.

7. Test the boundaries.
   - Prioritize tests for parsers, time/window filtering, source unavailable behavior, fallback signals, retries, output shape, privacy scans, and artifact replay.
   - Keep default tests offline. Put live APIs, credentials, hardware, and expensive model calls behind opt-in integration tests.

## Acceptance Criteria

A workflow shaped by this skill is done when:

- The deterministic layer and AI judgment layer are explicitly separated.
- There is a named boundary artifact with a stable schema or format.
- A future agent can inspect and replay the artifact without guessing hidden state.
- Long-running work has an explicit trigger, per-run work unit, no-op condition, completion/stop conditions, and a bounded retry, cadence, or cost policy where relevant.
- Unattended execution has been piloted manually with the same prompt, tools, model route, and permission boundary.
- Fallback and retry behavior is specified for empty inputs, stale sources, model failures, and downstream push/render failures.
- Tests cover the boundary and the failure modes most likely to break autonomous iteration.
- Docs record at least one rejected alternative when the architecture choice was non-obvious.

## Output

Return one of these, depending on the task:

- A concise workflow audit with gaps and proposed changes.
- A PRD/RFC/doc patch.
- A skill or config patch.
- A test plan focused on artifact boundaries and agent-safe iteration.

Keep recommendations scoped. Do not introduce a framework, graph engine, or multi-agent system unless the workflow needs dynamic context gathering or parallel independent work.
