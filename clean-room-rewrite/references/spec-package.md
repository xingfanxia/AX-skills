# Spec package

The spec package is the only thing the builder receives from the old system.
Write it so a competent engineer who has never seen the old code could rebuild
the product and pass its oracle suite.

## Layout

```
spec/
  README.md            product purpose, users, reading order, non-goals
  architecture.md      target module map, data flow, contracts-first build order
  ledger/
    behavior.md        B-### entries, grouped by module
    pitfalls.md        P-### entries
  contracts/
    surfaces.md        every external surface that must not change
    data-model.md      tables, IDs, persisted payload formats, migrations
    config.md          env vars, flags, secrets (names only), schedules
  ops.md               deploy, jobs, alerts, backups, runbooks
  carry-over.md        data/assets moved verbatim, with source → target paths
  oracle/              black-box tests recorded against the old system
  decisions.md         builder deviations and intended changes (starts empty)
```

## Behavior ledger entry

```
B-042 · feed · Hot list ranking
Given: items with scores and timestamps in the last 24h
When:  a reader opens /hot
Then:  items are ordered by decayed score; ties break by newer first;
       at most 50 items; admin and anonymous readers see the same list
Evidence: <old path or live URL>          Oracle: oracle/hot-ranking.spec
```

One observable behavior per entry. "Evidence" points at where a distiller saw
it; the builder never follows it, auditors do.

## Pitfall ledger entry

Pitfalls are the "why" behind code that looks wrong — the fences you must not
remove without knowing why they were built.

```
P-017 · ingest · Source X returns HTTP 200 with an HTML error page when rate limited
Consequence if ignored: the page is parsed as an article and published
Required behavior: treat a missing <article> marker as a retryable failure
Evidence: <old path, incident, or commit>
```

Mine pitfalls from bug-fix commits, comments, special cases, retries, feature
flags, and incident notes — not only from the current code shape.

## Contract inventory

List every surface an outside party or stored data depends on: public URLs and
redirects, SEO metadata, API paths and response shapes, webhooks in and out,
cookies and local storage keys, analytics event names, email/SMS templates,
database tables and persisted JSON payloads, file/object storage layout,
scheduled jobs and their timing, and environment/flag names. Mark each as
**keep** (byte-compatible), **migrate** (with the migration), or **drop** (a
listed non-goal).

## Oracle suite

Record black-box checks against the old system so the builder can run them
without its source: HTTP request/response snapshots with volatile fields
masked, rendered-page assertions, job input → output fixtures, and golden
outputs for deterministic engines. Money, auth, entitlement, and private-data
behavior needs explicit cases, including denial, replay, and concurrency.

## Distiller prompt skeleton

> You are distilling `<system>` into a spec package for a clean-room rebuild.
> The builder will never see this source. Enumerate surfaces mechanically
> first (routes, tables, jobs, env, integrations), then write one ledger entry
> per observable behavior, a pitfall entry for every special case you find and
> its evidence, and the contract inventory marked keep/migrate/drop. Preserve
> all functionality and every easy-to-miss detail. Do not propose the new
> implementation beyond the module map. Output in the layout above.

Run at least two distillers independently; the reconciler diffs their output
before the builder starts.
