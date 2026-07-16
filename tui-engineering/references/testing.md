# Testing — layered headless strategy + deterministic fixtures

Everything runs without a TTY (`bun run verify` = `tsc --noEmit && bun test`).
Render tests initialize the theme in 256-color compat mode so escape codes are
deterministic.

## 1. Layout contract (the foundation — add with the FIRST tab)

For every tab × several sizes — minimum `[45,30]` (phone portrait), `[76,24]`
(phone landscape / small desktop), `[120,40]` (desktop):

```ts
for (const tab of TABS) for (const [cols, rows] of SIZES)
  test(`${tab} fits ${cols}x${rows}`, () => {
    const { lines } = renderFrame(setTab(loadedState(), tab), cols, rows);
    expect(lines).toHaveLength(rows);                       // exact height
    for (const l of lines) expect(visibleWidth(l)).toBeLessThanOrEqual(cols);
  });
```

This is the "terminal never soft-wraps" guarantee that keeps diff painting
correct. Every new tab inherits it by joining the `TABS` loop. Also test the
empty state (no data yet) renders a full frame.

## 2. Information-survival assertions (the narrow-mode pins)

Width tests can't see truncation loss. For each thing narrow mode must
preserve, assert its FULL text appears at 45 cols:

```ts
const textAt = (tab, cols = 45, rows = 40) =>
  renderFrame(setTab(loadedState(), tab), cols, rows).lines.map(stripAnsi).join('\n');

test('alerts: push messages and errors survive', () => {
  expect(textAt('alerts')).toContain('api-gateway failed');   // the whole message
  expect(textAt('alerts')).toContain('auth expired');         // the error detail
});
```

Add one per audit finding (responsive.md §1). Also assert the wide layout
still contains the same content — proves narrow paths are gated, not global.

## 3. Pure input tests

- **Key decode table**: plain chars, arrows in CSI + SS3 forms, ctrl-c/tab/
  shift-tab/enter, mixed bursts decode in order.
- **The F-key leak case**: `decodeKeys('\x1b[15~')` must be `[]` — digits from
  unknown CSI params must never surface as keys.
- **SGR mouse**: press/drag/release coords (0-based after conversion), wheel
  directions 64/65/66/67, motion-without-button ignored, mouse digits never
  leak as keys.
- **Reassembly property test** — split a mouse report at EVERY byte boundary:

  ```ts
  const whole = '\x1b[<32;12;7M';
  for (let cut = 1; cut < whole.length; cut++) {
    const head = whole.slice(0, cut);
    const start = incompleteEscapeStart(head);
    const events = [...decodeEvents(head.slice(0, start)),
                    ...decodeEvents(head.slice(start) + whole.slice(cut))];
    expect(events).toEqual([{ kind: 'mouse', mouse: { kind: 'drag', x: 11, y: 6 } }]);
  }
  ```

- Escape-fragment holdback: partial `\x1b[`, `\x1bO`, `\x1b[<32;12` held;
  complete sequences and plain text pass whole; over-long tails flushed.

## 4. Gesture tests (drive the state machine with event lists)

```ts
const run = (events: Mouse[]) => { /* fold gestureStep, collect actions */ };
```

- tap: press+release in place (and with 1-cell wobble)
- vertical drag: scrolls follow the finger; correct catch-up on lock
- **wobbly horizontal swipe**: crosses several rows → exactly
  `[{type:'swipe'}]`, zero scroll actions (this is the real-finger case the
  naive recognizer fails)
- fast flick (bare press+release, no drags) still swipes
- vertically-locked drag never swipes; drag with no press ignored
- sub-threshold wobble emits nothing

## 5. Hit-range tests

Ranges cover all tabs in order, non-overlapping, within `cols` at every size;
the midpoint of each label resolves to its tab; the leading margin resolves
to null.

## 6. Demo e2e

Boot the real event loop against shipped fixtures and walk every tab at
several sizes. Catches "fixture doesn't satisfy the contract" and "this tab
crashes on empty/edge data" — the classes unit tests miss.

## 7. Deterministic fixtures

Generate metrics as a **pure function of (key, time)** — layered
incommensurate sines seeded by a string hash:

```ts
/** Smooth deterministic metric: pure fn of (key, t). No mutable state. */
export function metric(key: string, t: number, base: number, amp: number,
                       opts: { min?: number; max?: number; period?: number } = {}): number {
  const phase = fnv1a(key);                       // per-key phase from a string hash
  const p = opts.period ?? 480_000;
  const v = base
    + amp * 0.6 * Math.sin((t / p) * 2 * Math.PI + phase)
    + amp * 0.3 * Math.sin((t / (p / 2.7)) * 2 * Math.PI + phase * 1.7)
    + amp * 0.1 * Math.sin((t / (p / 7.3)) * 2 * Math.PI + phase * 3.1);
  return clamp(v, opts.min, opts.max);
}
```

Properties that matter:

- **Live gauges and history sparklines agree** — same function, different `t`.
- The demo "stream" is a `setInterval` re-invoking the builders — the real
  event-loop code runs unmodified against fixtures.
- **Aliasing trap**: day-sampled series must use a period that does NOT divide
  a day evenly, or the series collapses into a short repeating pattern
  (use e.g. `37 * DAY`, not a divisor-friendly default).
- Type fixtures against the same `contracts/` the renderers consume — `tsc`
  then proves demo data is shape-complete. No `as any` in fixtures, ever.

## 8. The audit render script (keep it, don't ship it)

A ~30-line scratch script that renders all tabs at a given size with ANSI
stripped is the single highest-leverage debugging tool for this class of app —
run it after every renderer change and *read the frames*. It is how narrow-
mode information loss, alignment drift, and box-border breaks actually get
caught.
