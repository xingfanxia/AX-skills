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

1. Restore a recent production snapshot into an isolated store for the new
   system, through the real migration path. Control access to the snapshot,
   minimize or redact personal data where the check allows it, and keep
   production credentials and outbound channels out of the shadow environment.
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

- Decide the write strategy: freeze writes during switch, or one-way sync with
  a replay log. Money and entitlement state keeps a **single authoritative
  writer** at every moment; idempotency keys and reconciliation do not stop two
  independent stores from each recording the same charge. In the shadow run the
  new side writes only to its isolated store.
- Before cutover, replay the same input sequence of money writes — charges,
  refunds, reversals, out-of-order and duplicate webhook events — against both
  systems and compare balances and ledgers at the same watermark.
- Rehearse rollback end to end and record its duration. Rollback must carry
  back every transaction created on the new system after the switch; restoring
  the old snapshot alone loses them. The old system stays warm until the
  agreed hold period ends.
- Switch by DNS, route, or flag in the smallest reversible step available.
- Watch the same signals as the shadow run for the first full job cycle.
- Remove the old path only after the hold period and a final reconciliation.
