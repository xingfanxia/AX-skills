# AI Workflow Spine

Design and audit AI-native workflows without turning them into prompt tangles or autonomous-loop theater.

The skill separates five concerns that are often mixed together:

1. deterministic collection, filtering, validation, retries, and persistence;
2. AI judgment such as selection, synthesis, ranking, and research;
3. a plain boundary artifact that can be inspected and replayed;
4. a control contract covering trigger, freshness, no-op, completion, cadence, and cost;
5. offline-first tests for the boundaries most likely to drift.

## Use it for

- LLM-backed products and pipelines
- coding-agent or skill architecture
- scheduled research, reporting, and triage workflows
- debugging stale, polluted, or unreplayable AI inputs
- deciding whether work belongs in a normal turn, persisted goal, or scheduled task

## Example

```text
Use ai-workflow-spine to audit this daily report generator. Identify the
deterministic layer, AI judgment layer, boundary artifact, replay path, trigger,
no-op and stop conditions, and the smallest tests needed before scheduling it.
```

## Output

Depending on the task, the skill returns a concise workflow audit, a PRD/RFC patch, a skill/config patch, or a boundary-focused test plan.

The complete operating contract lives in [`SKILL.md`](./SKILL.md).

## Further reading

- [Loop engineering: Getting started with loops](https://claude.com/blog/getting-started-with-loops)
- [Codex scheduled tasks](https://learn.chatgpt.com/docs/automations)
