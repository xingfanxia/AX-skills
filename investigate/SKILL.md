---
name: investigate
description: Diagnose unclear, intermittent, cross-component, or high-impact bugs with evidence and falsifiable hypotheses. Use when the cause is not evident, a previous fix attempt failed, behavior differs across environments, or the failure crosses data or control-flow boundaries. If the cause is already local and obvious, use the fast path instead of turning the bug into an investigation ceremony.
---

# Focused Investigation

Build enough evidence to identify the root cause, then make the smallest coherent
fix allowed by the user's request.

Diagnosis-only requests stay read-only on every path below: establish the cause
and propose the correction without applying it. Existing authority for a fix
does not need another approval question.

## Choose the path

Use the fast path for a local, reproducible failure with an evident cause:

1. Read the failing code and exact error.
2. Reproduce with the smallest useful command or test.
3. Correct the producer or invariant when a fix is authorized; otherwise explain
   the evidenced cause and proposed change.
4. Verify the authorized correction with a focused regression check.

Use the investigation path when the cause is unclear, intermittent,
cross-component, environment-sensitive, high impact, or already survived one
plausible fix.

## Establish the symptom

1. Capture the exact observed behavior, expected behavior, and first known bad
   boundary.
2. Find the smallest reliable reproduction. If the failure is intermittent,
   record the conditions and frequency instead of calling a single pass success.
3. Separate observed facts from assumptions. Keep the evidence ledger in working
   context unless a durable artifact is necessary.

Do not edit before the symptom is specific enough to falsify a hypothesis.

## Trace the flow

Follow the relevant value, state transition, or control path back to its origin:

- inspect the caller and callee contracts at each boundary;
- locate the first point where actual state diverges from expected state;
- compare one nearby working path when it can isolate the difference;
- inspect timestamps, filtering, caching, retries, fallbacks, and environment
  inputs when freshness or orchestration may be involved.

Add temporary instrumentation only at boundaries that distinguish competing
hypotheses. Remove diagnostic noise after the cause is confirmed.

## Test one hypothesis at a time

State one falsifiable hypothesis in this form:

> Because **cause**, we observe **symptom**; changing or measuring **variable**
> should produce **distinguishing result**.

Run the smallest check that can disprove it. Change one meaningful variable at a
time. Do not accumulate speculative patches and call the combined result proof.

- If attempts fail or evidence conflicts, stop speculative editing and seek a
  discriminating observation. Re-map the flow or reconsider the abstraction when
  coupling is implicated; an attempt count alone does not decide the next step.
- Ask only for a consequential missing decision or authority the user has not
  supplied. Inspect accepted context first and continue independent useful work.

Search official documentation or primary sources when behavior depends on an
unfamiliar or version-sensitive dependency. Read only the relevant contract; do
not browse merely because a debugging checklist reached a certain step.

## Fix the root cause

Prefer fixing the producer or violated invariant. Add a boundary guard when
invalid external input is part of the real contract. Avoid duplicating validation
at every layer unless each layer owns a distinct invariant.

Keep nearby cleanup out of scope unless it is necessary for the requested fix.

## Verify proportionally

Run the cheapest regression check that observes the corrected behavior. Add a
test when it is practical and protects the failure mode. Run a broad suite only
when the impact is broad, the boundary is high risk, or the user asks for release
readiness.

Do not automatically freeze a directory, spawn reviewers, write a report, or
run every test. Use each only to answer a concrete uncertainty.

## Completion contract

Complete the investigation only when:

- the root-cause claim is supported by observed evidence;
- competing plausible explanations have been ruled out enough for the impact;
- the requested fix, if authorized, passes a regression check that sees the
  original symptom;
- residual uncertainty and untested environments are named honestly.

Return the diagnosis, the decisive evidence, the fix or proposed fix, the check
run, and any remaining risk. Keep the explanation shorter than the evidence
requires, not longer.
