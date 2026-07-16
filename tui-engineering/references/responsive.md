# Responsive narrow mode — stack, don't truncate

The phone floor is ≈45 columns (Moshi portrait). Phones have abundant *rows*
and starved *columns* — so the narrow strategy is **stack, don't truncate**:
a message wrapped onto an indented continuation line survives; a message
truncated at 10 chars is gone. On a monitoring tool the message IS the
product ("看不清全貌" is the user complaint this prevents).

## 1. The audit workflow (do this, don't guess)

Width-limit tests only assert lines *fit* — they cannot see information loss.
Render and READ:

1. Write a throwaway script: render every tab at 45×38 with fixture data,
   strip ANSI, print each frame in a bordered box.
2. Read each tab. Catalog every `…` where the truncated content matters —
   rank by information loss (alert messages > metadata > decorations).
3. Fix per the patterns below.
4. Re-render, re-read.
5. Pin each fix with an **information-survival test** (testing.md §2).

The axfleet audit found six loss sites this way; zero were visible to the
layout-contract tests.

## 2. Fix patterns

Pick ONE narrow breakpoint (`width < 60`) and pass `width` into every
renderer. Then, per element class:

### Non-selectable rows → stack

- **Message rows** (alerts, events, push logs): heading line (severity ·
  host · age · badges), then the FULL message word-wrapped on indented
  continuation lines (`wrapPlain(msg, width - indent)`).
- **Metadata rows** (per-agent stats): name+status line, then metadata packed
  on ` · ` boundaries (`packParts` — never a word wrapper, which leaves
  dangling `·` at line ends and splits units like `today 3.2M $1.80`).
- **Summary one-liners** (`docs · queue · fails · stuck`): split into two
  logical halves on their own lines.
- **Right-aligned metadata** (`as of 8m ago`): drop to its own line rather
  than colliding with the left text.

### Selectable rows → compress (NEVER two lines)

Hit-testing and follow-selection require one line per item (see input.md §5),
so selectable rows compress instead of stacking:

- status words → glyphs (`running` → `●`, `failed` → `✖`, warn → `▲`)
- units abbreviate (`3.94 Mbps` → `3.9M`)
- healthy-state details move to the detail box; only WARNINGS keep badges in
  the row (`cert 11d!` stays; `cert 67d` moves to the box)
- name column gets a tighter truncation before signal columns shrink

### Tables/bars → shrink decoration before data

A bar chart's bar gives up cells before the label does: a 5-cell bar next to
a readable `claude-opus-4-8` beats a 7-cell bar next to `claude-opus-4-8…`.
Compute label width from what remains after bar + numbers, with a floor.
Drop cosmetic suffixes (`(client)`) at narrow.

### Chrome

- Tab bar: measured degradation (full labels → 3-letter), never a hardcoded
  breakpoint — see architecture.md §4.
- Header KPIs: hide the nice-to-haves (`$X today`, agent counts) below a
  width; keep up/down + problem count always.
- Footer hints: a short narrow variant; discoverability > completeness.

## 3. What NOT to do

- ❌ Two-line selectable rows (breaks the hit-test/selection invariant).
- ❌ Horizontal scrolling — terminals do it badly; nobody finds content there.
- ❌ Hiding whole sections at narrow width. Stacking means you don't have to:
  vertical space is the abundant resource.
- ❌ Word-wrapping ` · `-joined metadata (dangling separators) — pack parts.
- ❌ Trusting "it fits at 80 cols" — the failure window can be narrow
  (axfleet's tab bar was truncated ONLY at 76–79 cols).

## 4. Pinning

For every audit finding fixed, add an assertion that the previously-truncated
content appears in the 45-col render (see testing.md §2). These are the tests
that stop a future "small layout tweak" from silently reintroducing loss.
