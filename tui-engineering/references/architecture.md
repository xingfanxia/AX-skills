# Architecture — pure core, one adapter, ANSI math, painting

Reference implementation: [axfleet-ui-public](https://github.com/xingfanxia/axfleet-ui-public)
(`tui/` directory). File names below refer to it.

## 1. The layer rules

- **Everything except `term.ts` and `index.ts` is a pure function.** Layout
  bugs, input decoding, and gesture recognition become plain unit tests — no
  TTY, no PTY harness, no snapshot flakiness.
- **State transitions return new objects and preserve identity on no-op:**

  ```ts
  export function setTab(s: AppState, tab: Tab): AppState {
    if (tab === s.tab) return s;            // same reference → loop skips redraw
    return { ...s, tab, sel: 0, scroll: 0 };
  }
  ```

  The event loop redraws only when `next !== state`.
- **The data source hides behind fetch/stream functions** with
  failure-as-value results (`{ ok: true, data } | { ok: false, error }`), so
  a dead backend renders an error footer instead of throwing, and the whole
  API can be swapped for fixtures in one file (that's how the public demo
  works).
- **Lazily fetch per-tab data** (tokens, history, notifications) with a TTL
  stamp in state; stamp failures too so errors back off instead of refetching
  every keystroke.

## 2. ANSI width math (`ansi.ts`) — write this SECOND, before any renderer

`String.length` is wrong twice in a terminal: escape codes count as
characters, and CJK/emoji occupy two cells. One module owns cell math:

```ts
const ANSI_RE = /\x1b\[[0-9;]*m/g;
export const stripAnsi = (s: string) => s.replace(ANSI_RE, '');

/** Pragmatic wcwidth: CJK/kana/Hangul/fullwidth/emoji = 2, ZWJ/marks = 0. */
export function charWidth(cp: number): number {
  if (cp === 0x200b || cp === 0x200d || (cp >= 0x0300 && cp <= 0x036f) || cp === 0xfe0f) return 0;
  if ((cp >= 0x1100 && cp <= 0x115f) || (cp >= 0x2e80 && cp <= 0x303e) ||
      (cp >= 0x3041 && cp <= 0x33ff) || (cp >= 0x3400 && cp <= 0x4dbf) ||
      (cp >= 0x4e00 && cp <= 0x9fff) || (cp >= 0xac00 && cp <= 0xd7a3) ||
      (cp >= 0xf900 && cp <= 0xfaff) || (cp >= 0xfe30 && cp <= 0xfe4f) ||
      (cp >= 0xff00 && cp <= 0xff60) || (cp >= 0xffe0 && cp <= 0xffe6) ||
      (cp >= 0x1f300 && cp <= 0x1f9ff) || (cp >= 0x20000 && cp <= 0x3fffd)) return 2;
  return 1;
}

export function visibleWidth(s: string): number {
  let w = 0;
  for (const ch of stripAnsi(s)) w += charWidth(ch.codePointAt(0) ?? 0);
  return w;
}
```

The full toolkit:

| fn | contract | failure it prevents |
|---|---|---|
| `truncate(s, w)` | cut at cell boundary, keep escape codes, append `…` + `\x1b[0m` if any code seen | color bleeding into the next cell after a cut |
| `padEnd/padStart(s, w)` | pad by *visible* width; re-truncate if over | jagged columns when labels contain ANSI or CJK |
| `wrapPlain(text, w)` | word-wrap plain text; hard-break over-long words at the cell boundary | URLs blowing out the frame |
| `packParts(parts, w)` | greedy-pack ` · `-separated parts, break only BETWEEN parts | dangling `·` at line ends; units like `today 3.2M $1.80` split mid-unit |

Truncate must reserve one cell for the ellipsis and check `w + cw > width - 1`
per code point — a cut landing on a wide char at `width-1` otherwise overflows.

If labels can be bilingual, get `charWidth` right on day one: mixed-width rows
are the classic source of "the box borders are jagged".

## 3. Painting (`term.ts`)

```ts
const ENTER_ALT = '\x1b[?1049h';  // + HIDE_CURSOR '\x1b[?25l' on enter
const LEAVE_ALT = '\x1b[?1049l';  // SHOW_CURSOR + LEAVE on exit, reverse order
```

**Line-diffed paints** — keep the previous frame, rewrite only changed rows:

```ts
draw(lines: string[]): void {
  let out = '';
  if (this.prev.length === 0) {
    out = HOME + lines.map((l) => l + CLEAR_LINE_RIGHT).join('\r\n') + CLEAR_BELOW;
  } else {
    for (let i = 0; i < Math.max(lines.length, this.prev.length); i++) {
      const line = lines[i] ?? '';
      if (line === this.prev[i]) continue;
      out += `\x1b[${i + 1};1H` + line + CLEAR_LINE_RIGHT;  // cursor-addressed row rewrite
    }
  }
  if (out) process.stdout.write(out);
  this.prev = [...lines];
}
```

- A 1s clock tick ("`ago` freshness") costs a few bytes — matters over
  mosh/SSH, and mosh diffs again on top.
- On resize: clear `prev` (full repaint) and re-render.
- **Crash restore is mandatory**: a renderer throw must never strand the user
  in a raw-mode alt screen:

  ```ts
  const die = (err: unknown) => { term.exit(); console.error('crashed:', err); process.exit(1); };
  process.on('uncaughtException', die);
  process.on('unhandledRejection', die);
  ```

## 4. The frame contract (`render/frame.ts`)

- Fixed chrome: row 0 header · row 1 tab bar · row 2 rule · rows 3..N-2 body ·
  last row footer. **Export the row numbers as named constants**
  (`TAB_BAR_ROW`, `BODY_TOP_ROW`) — hit-testing uses them; magic numbers drift.
- The composer guarantees **exactly `rows` lines, each ≤ `cols` cells**
  (`lines.map(l => truncate(l, cols))` as the final safety net). If a line
  soft-wraps, the diff painter's row addressing corrupts the whole screen.
- **Scroll clips at the frame level**: tab renderers return FULL content;
  the composer slices `[scroll, scroll + bodyH)` and reports `bodyTotal` so
  the event loop clamps scrolling. Renderers never know about scroll.
- **Measure, don't assume**: build the tab bar with full labels, measure with
  `visibleWidth`, degrade to 3-letter labels only if it doesn't fit.
  (A hardcoded breakpoint left the last tab truncated in a 4-column window of
  terminal widths, 76–79 — measured degradation can't have that bug.)
- The tab-bar builder returns **hit ranges** (`{tab, start, end}` per label)
  computed from the same string it renders — click targets can't drift from
  pixels. See input.md §hit-testing.

## 5. The event loop (`index.ts`) — the only other impure file

Responsibilities, nothing more:

- `redraw()` — render frame, cache `bodyTotal` + `tabRanges`, `term.draw`.
- `update(next)` — identity-skip, assign, redraw, kick lazy per-tab fetches.
- Data plumbing: stream connect with quiet degradation to polling
  (stream drop ≠ error; only "polling fails too" escalates to the red footer).
- Input handlers (see input.md) funneling into pure transitions.
- `shutdown()` — abort stream, clear timers, `term.exit()`, `process.exit`.

Keep a `moveOrScroll(delta)` helper: j/k, wheel, and drag all funnel through
one place — "move the cursor where one exists, else scroll the pane".
