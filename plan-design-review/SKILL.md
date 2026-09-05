---
name: plan-design-review
description: Review the design completeness of an implementation plan when the user asks for a plan design review or design-completeness check. Assess seven dimensions, concrete interaction states, and generic design risks. Review-only requests produce findings; requested plan improvements apply clear fixes and batch consequential choices.
---

# Plan Design Review

Find missing user-facing design decisions before implementation. Review the
plan against its audience, existing product patterns, and accepted scope.

## Scope and inputs

Read the supplied plan and relevant project instructions, existing design
references, and components. Use version-control context only when it resolves
what changed; no PR or remote lookup is required for a local plan review.
A named design-system file is useful when present, but its absence is not
automatically a defect.

If the plan has no user-facing UI or interaction scope, explain that this
design review is not applicable. Do not start implementation or edit product
code. A review-only request remains read-only. If the user asks to improve the
plan, apply clear reversible improvements directly to that plan.

Preserve deliberate design choices. Avoid inventing a new aesthetic or
product requirement merely to make a review more opinionated.

## Design lens

Describe what the user sees, can do, and understands, including recovery from
failure. Prioritize hierarchy, interaction states, user journey, and alignment
with the product's existing vocabulary. Prefer removing a distracting element
over adding another. Empty states should explain the situation and offer an
appropriate next action; decorative warmth is not required in every context.

Simulate relevant constraints: first use, repeat use, poor connectivity,
long content, touch, keyboard, and assistive technology. Consider only cases
that apply to this product. Tie taste judgments to an observable design
problem and its effect on the user.

## Seven-dimension rubric

Use these dimensions together, not as seven approval gates. When scoring is
requested or useful for comparison, rate applicable dimensions from 0–10 with
a short reason and the concrete missing specification. Scores are diagnostic;
do not loop until every score reaches 10 or use an arbitrary average as proof
of readiness.

| Dimension | Review question |
|---|---|
| Information architecture | Is the primary, secondary, and tertiary content clear, with sensible navigation and grouping? |
| Interaction states | Are loading, empty, error, success, and partial states defined for relevant features? |
| User journey | Does the plan connect entry, action, feedback, recovery, and return use? |
| Design specificity | Are design choices concrete and suited to this product, rather than vague template language? |
| Design system alignment | Does the plan reuse appropriate components, tokens, and established conventions? |
| Responsive and accessibility | Are meaningful viewport changes, keyboard/focus behavior, semantics, contrast, and touch behavior specified? |
| Unresolved decisions | Which remaining choices would materially change implementation or the user's experience? |

Generic card grids or hero sections are not defects on their own. Flag a
pattern when it obscures hierarchy, invents unnecessary UI, or conflicts with
the product. Replace vague phrases such as “clean, modern” with a specific
decision supported by the reference or requested direction.

For interaction-heavy plans, build or repair a state table:

| Feature | Loading | Empty | Error | Success | Partial |
|---|---|---|---|---|---|
| Relevant feature | Visible feedback | Explanation and next action | Message and recovery | Confirmation and next state | What remains usable |

Mark states not applicable with a reason. Specify triggers, what persists,
focus changes, and retry/cancel behavior where they affect the interaction.

When a journey is unclear, a short storyboard can expose the gap:

| Step | User action | Expected feedback | Recovery or next action |
|---|---|---|---|
| Relevant step | What the user does | What they see and understand | What happens next |

## Apply findings and resolve choices

Separate clear fixes from consequential choices. For authorized plan edits,
resolve obvious gaps from existing patterns without asking about each issue.
For review-only work, present those same improvements as recommendations.

Batch unresolved consequential choices into one concise request, with a
recommendation, alternatives, and the user-visible tradeoff for each. Continue
independent review or authorized improvements while input is pending. Do not
pause to ask whether to perform the review the user already requested.
Do not treat silence as approval for an unresolved consequential choice.

Keep out-of-scope design ideas separate from required fixes. Add TODOs only
when requested or already part of the project's authorized planning workflow;
do not open a separate approval question for every potential TODO.

## Acceptance and output

Completion means the requested review covers applicable dimensions, findings
are concrete, and implementation-affecting unknowns are resolved or explicitly
identified. For plan improvement, the authorized changes are in the plan and
consistent with its acceptance criteria.

Deliver the plan path if edited, the most material findings or changes, useful
scores if used, existing patterns to reuse, and any unresolved decision with
its consequence. State remaining readiness gaps honestly. Do not substitute a
large review report for the requested plan improvements.
