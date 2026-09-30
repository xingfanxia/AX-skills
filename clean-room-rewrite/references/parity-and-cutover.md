# Parity audit, shadow run, and cutover

## Parity audit

Split the audit by module so each auditor holds one module of old code, new
code, and spec. Ask for gaps, not style:

> Compare old `<module>` with new `<module>` against the spec ledger. Ignore
> implementation choices. Report every user-visible behavior, edge case, error
> path, persisted-data effect, or pitfall that the new system misses or changes
> and the spec does not record as intended. Cite the ledger ID, or say
> "unledgered" and propose the entry.

Route every finding the same way: amend the spec (new or corrected ledger
entry, plus an oracle case when possible), then have the builder fix it. An
"unledgered" finding means distillation missed something; check neighboring
surfaces for the same class of miss.

Use at least one auditor from a different model family than the builder. After
the fix round, run a final fresh-context pass per feature module that compares
function and logic only.

## Shadow run

1. Restore a recent production snapshot into the new system's store, through
   the real migration path.
2. Mirror read traffic (or replay recorded requests) and run scheduled jobs on
   both systems. Keep external side effects — payments, messages, outbound
   webhooks, paid model calls — disabled or sandboxed on the new side.
3. Diff responses and job outputs with volatile fields masked. Classify each
   difference as bug, intended change (with a decisions entry), or noise (with
   the mask that removes it).
4. Continue until the window covers every scheduled job at least once and no
   difference is unclassified. Watch error rate, latency, and cost alongside
   the diff.

## Cutover runbook

- Decide the write strategy: freeze writes during switch, dual-write, or
  one-way sync with a replay log. Money and entitlement state must never have
  two writers without an idempotency key and a reconciliation check.
- Rehearse rollback end to end and record its duration; the old system stays
  warm, with a path back for its data, until the agreed hold period ends.
- Switch by DNS, route, or flag in the smallest reversible step available.
- Watch the same signals as the shadow run for the first full job cycle.
- Remove the old path only after the hold period and a final reconciliation.
