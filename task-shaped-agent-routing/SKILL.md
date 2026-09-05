---
name: task-shaped-agent-routing
description: Design or audit agent responsibilities, delegation boundaries, and review topology from the actual work. Preserve the user's configured model and reasoning policy; do not invoke merely because agents are available.
---

# Task-Shaped Agent Routing

Choose responsibilities and parallel work that improve the requested outcome.
Model and reasoning settings come from the user's current routing policy, not
from an assumed cost or capability ladder.

## Respect the runtime contract

Honor an explicit model and reasoning preference for every role. In AX's Codex
configuration the uniform route is `gpt-6-astra` with `xhigh` reasoning.
Do not down-route scouts or workers, raise reviewer effort, or choose a
different model merely because a role sounds cheaper or harder.

For other environments, inherit the caller's supported settings unless the
user requests a different route. Do not silently translate model names into
unsupported provider-specific fields. Distinguish requested configuration
from observed runtime metadata, and disclose unavailable metadata.

## Decide whether delegation helps

Keep work direct when it is tightly sequential, needs the coordinator's own
source understanding, or is faster to perform and verify than to dispatch.

Delegate independent investigations, well-separated implementation areas, or
one consequential claim needing independent evidence when parallel agents can
save time or improve quality. Use parallel tool calls for independent lookups
that do not need separate judgment.

Before splitting, consider source ownership, integration cost, observability,
and the consequence of a wrong result. A large file count is not itself a
reason to create agents. A small change may still benefit from an independent
review of a concrete permission or persistence boundary.

## Bound the task

Give each child the outcome, relevant sources, owned files, allowed mutations,
expected evidence, and condition for returning. Add a retry limit when the
operation can loop. Keep writers disjoint and coupled changes sequential.

Roles describe the work: retrieval, implementation, integration, diagnosis,
research, architectural judgment, or focused review. They do not require
separate model tiers or a fixed roster.

Never let a worker broaden permissions or perform an external action that
the user has not authorized. Use actual tool capabilities rather than names
copied from another harness.

## Integrate and finish

The coordinator owns the stable objective, dependency order, and final
acceptance decision. Read child evidence and check consequential claims.
Incomplete or contradictory output calls for a better observation, a clarified
contract, or direct takeover; it does not automatically justify another
reviewer or a more expensive model.

Keep useful progress and uncertainty visible while continuing authorized work.
Do not create a new task graph or ledger for work that fits one coherent pass.

## Result

For a routing design, return the chosen direct/delegated structure, ownership,
runtime settings, and verification owner. For implementation, apply that
structure and deliver the requested result. Add independent review only for
a named material claim; do not use agent count as a quality metric.
