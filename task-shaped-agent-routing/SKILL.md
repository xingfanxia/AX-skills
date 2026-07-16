---
name: task-shaped-agent-routing
description: Design or audit model capability, reasoning depth, agent roles, delegation boundaries, and review topology from the actual shape of work. Use when choosing between direct execution and delegation, defining a multi-agent workflow, assigning heterogeneous capability tiers, or correcting wasteful or shallow agent orchestration. Do not invoke it merely because agents are available or to protect the coordinator from reading important context.
---

# Task-Shaped Agent Routing

Route for answer quality first. Optimize latency and cost only among routes that
are reasonably expected to reach the same acceptance quality.

## Read the work shape

Classify the task before choosing a model or team:

- Is the operation exact or open-ended?
- Is the relevant source known or does it require exploration?
- Is the work sequential or genuinely independent?
- How much cross-file or cross-system integration is required?
- How observable is correctness?
- What is the blast radius and reversibility of a wrong answer?
- Does one named claim need independent confirmation?

Choose the lowest sufficient capability tier, not the lowest available tier.
Escalate before delegation when ambiguity, weak observability, or irreversible
impact makes a lower tier unlikely to succeed in one pass.

## Choose direct or delegated execution

Keep work with the coordinator when it is:

- a trivial lookup or exact local edit;
- sequential work on known files, even when deep or numerous;
- source the coordinator must understand to integrate the result;
- faster to verify directly than to specify and reconcile.

Delegate when it provides real value:

- independent investigations can run in parallel;
- a specialist capability is materially better for a bounded problem;
- output is high-volume and low-signal, such as raw logs or broad inventories;
- a long implementation has coherent, non-overlapping ownership boundaries;
- one high-impact claim needs a fresh independent review.

Do not delegate to hide context from the coordinator. Use parallel tool calls for
independent read-only lookups that do not need separate judgment.

## Use a capability ladder

Map platform-specific models and roles onto these portable tiers:

| Work tier | Required capability | Typical team shape |
|---|---|---|
| Exact lookup or one-line edit | Coordinator or fast deterministic tool | Direct |
| File/symbol inventory | Fast read-only retrieval with careful extraction | One bounded scout when output is bulky |
| Mechanical low-risk edit | Reliable instruction following and deterministic verification | Direct or one mechanical worker |
| Routine implementation | Strong bounded coding and test judgment | One worker with clear acceptance |
| Cross-file integration, debugging, or focused review | Strong synthesis and causal reasoning | Integrator, debugger, or focused reviewer |
| Wide research or long-horizon implementation | Strong orientation and evidence synthesis | Researcher or senior worker |
| Consequential architecture or deep research | Highest practical design judgment | Architect or deep researcher |
| One blocking decision after escalation | Maximum available reasoning on exactly one bottleneck | One specialist, then return control |

Treat model names and benchmark scores as runtime-specific evidence, not durable
methodology. Recalibrate the mapping when the platform, model family, or local
evaluation changes.

## Write a bounded child contract

Give every delegated task:

1. **Objective:** one concrete outcome or question.
2. **Scope:** owned files, data, systems, and mutation permissions.
3. **Inputs:** the minimum source artifacts needed to do the work.
4. **Evidence:** commands, citations, tests, or artifacts the child must return.
5. **Acceptance:** observable conditions for success.
6. **Stop condition:** when to return, retry, or escalate instead of expanding
   scope.

Ask for findings and evidence, not vague opinions. Use non-overlapping ownership
by default. Keep delegated writes disjoint or assign a single integrator.

## Coordinate and integrate

- Let the coordinator own the stable objective, dependency order, and final
  acceptance decision.
- Treat child output as evidence, not authority. Reject shallow, contradictory,
  or incomplete work instead of polishing it through repeated weak loops.
- Resume sequential integration as soon as the parallel value is exhausted.
- Retry once only when the failure is instruction-local and the correction is
  clear. Escalate or take over when the task shape was misrouted.
- Never let a worker silently broaden permissions or perform an external action
  not authorized by the user.

## Budget overlap and review

Routine low-risk work needs no independent reviewer. Add one overlapping pass
only for a named high-impact or materially uncertain claim. State the claim the
reviewer must validate and provide fresh source artifacts without leaking the
expected conclusion.

Do not create several generic reviewers to manufacture confidence. Prefer one
strong, targeted pass plus deterministic verification.

## Completion contract

Return:

- the task-shape assessment;
- the selected capability tier and direct/delegated topology;
- each child contract and ownership boundary, when delegation is justified;
- the integration and verification owner;
- escalation and stop conditions.

If direct execution is the best route, say so and do not spawn. Good routing is
often a decision to keep the team small.
