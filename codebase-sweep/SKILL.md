---
name: codebase-sweep
description: Inspect the whole repository when the user explicitly requests a full codebase audit, health check, cleanup, or architecture documentation. Audit-only requests produce findings; fixes, documentation, and cleanup follow the requested scope. Whole-project review is not triggered by an ordinary feature or refactor.
metadata:
  version: "2.0.0"
---

# Codebase Sweep

Build an evidence-backed view of the whole requested codebase and complete the
specific audit, fixes, documentation, or cleanup the user asked for.

## Select the requested output

A full audit is read-only unless fixes were requested. A documentation request
calls for source-backed docs, not an automatic fix loop. A cleanup request
allows cleanup within its stated scope, not arbitrary deletion or a new
architecture. Carry previously authorized phases through without asking again.

Inspect applicable instructions and source-of-truth locations. Enumerate the
repository's services, packages, entry points, persistence, interfaces, build
tools, tests, and operational configuration. Use available search tools such
as `rg --files`, symbol navigation, or a maintained index. Exclude generated,
vendor, and archived material unless it belongs to the requested review.

## Full audit first

Cover all relevant layers in the first audit, including their integration
boundaries. Keep a coverage map of what was inspected and what remains
unverified; do not label a sample of files a full audit.

For instruction/workflow audits, follow registrations and callers as well as
filenames. Top-level `agents/` and `commands/`, runtime-profile templates,
scheduled prompts, editor rules, and agent CI may control behavior outside
`.claude/` or `.agents/`. Distinguish full reads, exact base-plus-delta review,
and justified ownership exclusions; index or pattern scans alone are not full
semantic coverage. Respect archived-capability consent while inventorying.

Use bounded parallel read-only agents for independent areas when useful and
permitted. Provide each area the same scope, finding criteria, and boundary
context; the owner reconciles cross-area findings. Fixed model names and
reviewer counts are unnecessary.

Support each defect with a source location, trigger or reproduction, impact,
and expected behavior. Deduplicate common causes. Style preferences, missing
coverage percentages, and speculative redesigns are not correctness findings.

## Fixes when requested

Use the audit/fix engine in [audit-fix-loop](../audit-fix-loop/SKILL.md), with
the whole repository as its initial scope and this audit as the completed
first pass. Read that skill when entering the fix phase; do not repeat the
initial audit. Later rechecks cover fixes, affected callers and contracts,
and regressions, expanding only when new evidence warrants it.

When using this skill independently of that companion, the same contract
applies: fix supported in-scope defects, verify their failure modes with
appropriate project checks, then recheck affected behavior until no supported
in-scope defects remain. Do not impose universal test suites or coverage
percentages.

## Documentation when requested

Read the source before describing behavior. Reuse the existing documentation
structure and create only the documents needed for the requested audience.
Useful content includes system ownership, data flow, entity constraints,
feature entry points, development setup, and actual verification commands.
Use diagrams where relationships are otherwise difficult to follow.

Distinguish confirmed behavior from rationale inferred from code. Link claims
to stable source paths and check commands and references. A missing
architecture file does not itself require creating an entire docs tree.

## Cleanup when requested

Resolve candidates with source and caller evidence before moving or removing
them. A filename such as `debug-*.py` or an old modification date is not proof
that a script is disposable. Check dynamic loading, configuration, automation,
documentation links, and external/public consumers.

Follow the repository's layout. Preserve uncertain material while establishing
its ownership; moving it to an archive can also break callers. Keep all
authorized moves reviewable, update affected references, and prefer
recoverable removal when practical. Respect explicit destructive-action
boundaries and ask only when target or authority remains unclear.

Do not move or rename the repository, create memory entries, open PRs, or
publish anything as an implied final cleanup phase.

## Completion

Run verification relevant to actual changes and required project contracts.
Read-only audits may report safe diagnostic results without modifying files.
Reuse passing results until subsequent changes affect them.

Deliver the requested artifact: an audit with coverage and reproducible
findings, verified fixes, source-backed docs, or a cleanup inventory. State
uninspected areas, unresolved defects, and environmental limits. For material
moves or deletions, list exact targets and recoverability. Complete all
authorized phases; do not claim convergence when required evidence is missing.
