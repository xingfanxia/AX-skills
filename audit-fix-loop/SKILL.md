---
name: audit-fix-loop
description: Iteratively audit and fix a specified diff, feature, or code area when the user explicitly requests an audit-and-fix loop or asks to keep fixing until clean. Validate reproducible defects and recheck affected behavior until the requested acceptance criteria are met. Review-only requests remain read-only.
metadata:
  version: "2.0.0"
---

# Audit-Fix Loop

Converge on verified fixes for defects within the requested scope.

## Contract

Identify the target diff, feature, paths, or whole-project scope from the
request and repository instructions. Preserve existing authorization and
user-owned changes. Audit/review alone produces findings; apply fixes only
when requested. Continue already authorized fixes without a new permission
question for each round.

Inspect source, callers, tests, and build configuration before choosing audit
slices or verification commands. Do not add cleanup, commits, PRs, remote
messages, memory updates, or documentation projects to the user's request.
Update documentation directly invalidated by a fix as part of that fix.

## Audit and triage

Audit the full requested scope first. Report concrete defects with location,
trigger or reproduction, expected versus actual behavior, impact, and evidence.
Trace cross-file contracts far enough to establish the failure. Distinguish
reproducible bugs from stylistic preferences, uncertain hypotheses, and
unrelated existing debt; do not turn coverage percentages into bug findings.

Deduplicate findings that share a root cause. Prioritize by impact and
confidence grounded in evidence, without a numeric confidence cutoff. An
in-scope supported defect remains work even when its severity is low; a nit
or speculative redesign does not become required merely because a reviewer
mentioned it.

If parallel work is useful and permitted, delegate independent audit slices or
fix clusters with explicit boundaries. Give writers disjoint ownership and
keep dependent fixes sequential. Choose available capabilities for the actual
difficulty; no prescribed agent roster, model, or compressed return limit.
Require enough evidence to integrate and verify each result.

## Fix, verify, recheck

Implement the smallest change that resolves the root cause and preserves
contracts. Test the demonstrated failure mode using the repository's existing
tools and fixtures. Add a regression test when it meaningfully protects that
behavior; choose unit, integration, or UI coverage from where the defect lives.

Examples of useful verification:

| Defect | Evidence that can establish the fix |
|---|---|
| Pure logic error | A deterministic example that failed before and now passes. |
| Query or transaction behavior | A database-backed check of the relevant constraint or interleaving. |
| Permission failure | Allowed and denied cases at the actual enforcement boundary. |
| UI state or interaction | Rendered state and the affected user interaction. |
| Configuration or build failure | The actual startup, build, or configuration consumer. |

Do not require both unit and E2E tests for every fix. Reversible wording or
format changes usually need inspection or the relevant linter. Required
project checks and project coverage contracts still apply.

After a fix, run the focused check and required project verification.
Investigate failures; distinguish failures caused by this diff from existing
or environmental failures. Do not delete a valid failing test to claim green.
Reuse passing evidence until new changes or unresolved concerns justify
repeating it.

Re-audit the changed files, their callers, affected contracts, and new tests.
Expand only when evidence shows wider impact. The initial requested scope does
not need a fresh whole-codebase audit after each local fix.

## Convergence and output

Finish when supported in-scope defects are resolved, affected rechecks find no
remaining defects, and required verification supports the acceptance criteria.
Report the checked scope and limitations rather than claiming an entire
codebase is defect-free.

If the same failure recurs without new evidence, change the hypothesis,
reproduce it more directly, or identify the missing dependency. Follow any
user-set round or time budget; an exhausted budget or external blocker is an
incomplete outcome, not convergence. Ask only for missing authority or a
material decision that cannot be inferred, after completing independent work.

Keep progress updates brief: supported findings, fixes verified, and the next
uncertainty. Deliver a concise result with changed files, evidence, and any
unresolved finding with its blocker. Store a report only when requested or the
project's workflow calls for one.
