# Decision gate — rewrite, refactor, or strangle

Measure before judging. "It feels like a mess" is not evidence; neither is the
file count. Separate three kinds of code first, because they have different
remedies:

| Kind | Examples | Remedy when it hurts |
|---|---|---|
| Logic | routes, services, components, domain engines | refactor or rewrite |
| Data | knowledge bases, copy, translations, prompts, fixtures, generated types | carry over verbatim |
| Meta | verification scripts, manifests, baselines, evidence, plans, CI glue | collapse or delete — never rewrite the product for it |

## Signals

Run the equivalent commands for the stack; record numbers, not adjectives.

| Signal | How to measure | Points toward rewrite when |
|---|---|---|
| Logic size | LOC of logic only (exclude tests, data, generated, meta) | small enough to rebuild in days of agent time |
| Type/lint escape hatches | count of `@ts-nocheck`, `any`, `# type: ignore`, lint disables | pervasive, not a few dozen |
| God files | logic files > 500 LOC, and whether they mix domain/UI/IO/state | many, and mixed-responsibility |
| Duplication | copy-paste detector (e.g. `jscpd`) or diffing same-named files across features | the same logic forked across many features with divergent fixes |
| Change coupling | median files touched per feature commit; how often an unrelated area breaks | a small change regularly breaks distant features |
| Defect churn | share of `fix` commits; files that recur in fixes | fixes cluster everywhere, not in a few hotspots |
| Boundary health | forbidden imports, cycles, pure layers doing IO | no stable boundary exists to refactor toward |
| Meta tax | share of recent commits that had to touch manifests/baselines/evidence | high — but this points to collapsing meta, not a rewrite |
| Oracle availability | live system, replayable data, recorded responses | a black-box oracle exists |
| State risk | money, entitlements, auth, personal data, persisted payload formats | low or cleanly migratable |

A useful change-coupling probe with Git:

```bash
git log --since=<window> --no-merges --format='%H %s' | grep -viE ' (docs|test|chore)' |
  while read h _; do git show --name-only --format= "$h" | grep -cE '\.(ts|tsx|py|go)$'; done |
  sort -n | awk '{a[NR]=$1} END{print "median files/commit:", a[int(NR/2)+1]}'
```

## Reading the result

- **Refactor** — types are sound, boundaries mostly hold, debt clusters in a
  few hotspots. Fix the hotspots in place; each gets characterization tests
  first.
- **Collapse meta** — product code is fine but most change cost is spent
  updating verification, manifests, or ceremony. Delete or merge gates that do
  not protect a real boundary; keep money, auth, and private-data checks.
- **Strangler (Variant B)** — structure is the problem in some bounded contexts
  but the whole system is too large, too stateful, or too money-bearing to
  rebuild at once.
- **Full clean-room rewrite** — structure dominates change cost everywhere,
  the logic fits the budget, an oracle exists, and state migrates reversibly.

A system can land in more than one row; name the ranked actions, not a single
label.

## Cost estimate

Before committing to a rewrite, estimate spec size: count behavior surfaces
(user-visible features, routes, APIs, jobs, integrations) and persisted
contracts (tables, payload formats, cookies, URLs). If the builder's context
cannot hold the architecture plus one module's spec at a time, split the
system first.
