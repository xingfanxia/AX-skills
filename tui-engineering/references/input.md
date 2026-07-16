# Input — decoding, mouse/touch, gestures, hit-testing, phone terminals

Reference implementation: `tui/term.ts`, `tui/gesture.ts`, `tui/index.ts` in
[axfleet-ui-public](https://github.com/xingfanxia/axfleet-ui-public).

## 1. Key decoding — a pure function over stdin chunks

Raw mode delivers bytes. Decode with `decodeEvents(chunk) → (key | mouse)[]`
so every rule below is a unit test.

```ts
export function decodeEvents(chunk: string): TermEvent[] { /* loop over chunk */ }
```

Decode table (order matters — check specific before generic):

| bytes | event |
|---|---|
| `\x03` | ctrl-c |
| `\x1b[<c;x;y(M\|m)` | SGR mouse (see §2) — match BEFORE generic CSI |
| `\x1b[A`/`\x1bOA` (B/C/D) | arrows — both CSI and SS3 forms |
| `\x1b[Z` | shift-tab |
| `\x1b[` or `\x1bO` + anything else | **unknown CSI/SS3: consume THROUGH the final byte (0x40–0x7E)** |
| chunk-final lone `\x1b` | the ESC key (see escape timeout below) |
| `\t`, `\r`/`\n` | tab, enter |
| printable ≥ `' '` | itself |

**Why "consume through final byte" is critical**: F5 is `\x1b[15~`. Skipping
just `\x1b[` leaks `1` and `5` as number-key presses — in a TUI where digits
switch tabs, pressing F5 visibly jumps tabs. CSI final bytes are `0x40–0x7E`
(ECMA-48).

## 2. SGR mouse

Enable on enter, disable on exit **in reverse order**:

```
on:  \x1b[?1000h \x1b[?1002h \x1b[?1006h   (buttons + drags + SGR encoding)
off: \x1b[?1006l \x1b[?1002l \x1b[?1000l
```

Terminals without mouse support ignore these harmlessly — always safe to emit.

Reports look like `\x1b[<code;col;row(M|m)`. Decode:

```ts
function sgrMouse(code: number, col: number, row: number, final: string): Mouse | null {
  const pos = { x: col - 1, y: row - 1 };            // SGR is 1-based; convert ONCE here
  if (code & 64) {
    const kind = (['wheel-up','wheel-down','wheel-left','wheel-right'] as const)[code & 3]!;
    return { kind, ...pos };
  }
  if ((code & 3) === 3) return null;                  // motion w/o button (mode 1003) — ignore
  if (final === 'm') return { kind: 'release', ...pos };
  return { kind: code & 32 ? 'drag' : 'press', ...pos };
}
```

Masking with `& 3` / `& 32` / `& 64` means shift/alt/ctrl modifier bits
(4/8/16) don't break decoding.

## 3. Split-chunk carry-over + escape timeout (the subtle part)

Fast drags flood dozens of SGR reports; mosh/SSH can split one across read
chunks. Without carry-over, `\x1b[<32;12` + `;5M` decodes as garbage AND leaks
the digit `5` as a tab switch. Worse: a chunk split right after the ESC byte
reads as the ESC key — **if ESC quits your app, a drag flood randomly quits it**.

```ts
/** Index where a trailing possibly-incomplete escape begins, or s.length. */
export function incompleteEscapeStart(s: string): number {
  const i = s.lastIndexOf('\x1b');
  if (i === -1 || s.length - i > 24) return s.length;   // >24 cells isn't a sequence — flush
  const tail = s.slice(i);
  if (tail === '\x1b' || /^\x1b(\[[<0-9;]*|O)$/.test(tail)) return i;  // hold fragment back
  return s.length;
}
```

In the adapter:

```ts
process.stdin.on('data', (chunk) => {
  if (escTimer) { clearTimeout(escTimer); escTimer = null; }
  const data = pending + chunk.toString();
  const cut = incompleteEscapeStart(data);
  pending = data.slice(cut);
  dispatch(decodeEvents(data.slice(0, cut)));
  if (pending) {
    // Escape timeout: a fragment whose continuation never comes is real input
    // (a lone ESC = the ESC key), not a split sequence — flush-decode it.
    escTimer = setTimeout(() => { const held = pending; pending = ''; dispatch(decodeEvents(held)); }, 40);
  }
});
```

ESC-key latency becomes 40ms (imperceptible); split sequences reassemble
correctly. Clear the timer in `exit()`.

**Property test**: split a mouse report at EVERY byte boundary; assert
carry-over + decode yields exactly one mouse event and zero key leaks.

## 4. Gesture recognition — direction-locked state machine (`gesture.ts`)

Pure: `gestureStep(g, mouse) → { g, action }` where action ∈
`tap | scroll | swipe | null`. Wheel events bypass it.

```
press   → g = { x0, y0, lastY: y, axis: null }
drag    → axis 'h'?  do nothing (no scroll jitter mid-swipe)
          axis null? if max(|dxT|,|dyT|) < 2 cells: wobble zone, do nothing
                     else lock: axis = |dxT| ≥ 2·|dyT| ? 'h' : 'v'
                     ('v' emits the catch-up scroll from the press row)
          axis 'v'?  emit scroll (lastY - y): content follows the finger
release → axis ≠ 'v' and |dx| ≥ 5 and |dx| ≥ 2·|dyT|  → swipe (left = next)
          axis null and |dx| ≤ 1 and |dyT| ≤ 1          → tap at press coords
          else nothing; always reset g
```

Why the lock: the naive version (emit scroll on every dy, veto swipe if
"scrolled too much") **fails on real fingers** — a horizontal swipe always
wobbles across a few rows, so it scroll-jitters the pane and then vetoes
itself. Cell aspect is ~1:2 (w:h), so `|dx| ≥ 2·|dy|` in cells ≈ a 45°
physical threshold.

Also:
- Handle a **fast flick reported as bare press+release** (no drags): the
  release rule above covers it because `axis` is still null.
- Drag with no press seen → ignore (`g === null`).
- **Wheel-left/right → tab switch, debounced ~250ms** — some terminals report
  one tilt/swipe as a burst; without debounce one swipe jumps four tabs.

## 5. Hit-testing without a widget tree

Two rules, no retained-mode widgets:

```ts
const onTap = (x: number, y: number): void => {
  if (y === TAB_BAR_ROW) { const t = hitTab(tabRanges, x); if (t) update(setTab(state, t)); return; }
  const paneY = y - BODY_TOP_ROW + state.scroll;
  if (y >= BODY_TOP_ROW && y < term.rows - 1 && paneY >= 0 && paneY < selectableCount(state)) {
    update(followSel({ ...state, sel: paneY }, term.rows - 4));
  }
};
```

- `tabRanges` come from the tab-bar builder (same string it renders →
  targets can't drift). `hitTab` is a range lookup.
- The body rule works because of a **layout invariant: selectable lists render
  one line per item at the top of the pane** (item k is pane line k) — the
  same invariant keyboard follow-selection uses. Narrow-mode work may
  compress selectable rows but must NEVER make them two lines.

## 6. Phone terminals — what actually arrives (Moshi, measured 2026-07)

| Phone action | What the TUI receives |
|---|---|
| tap | SGR press + release at the cell |
| vertical pan | a burst of wheel-up/down events |
| horizontal swipe | **nothing** — hardwired to Moshi's multiplexer integration: live detection of tmux/Zellij/Herdr (remote CLI probes like `herdr session list --json`), then Moshi sends that multiplexer's tab chord. Other TUIs get "no active window". NOT bindable to custom keys — only tap/long-press/D-pad slots accept the custom shortcut builder. |
| Mouse-Mode drag | press/drag/release forwarded to the TUI (gesture recognizer applies) |

Design consequences (bake these in from the start):

1. **Never make swipe the only path to anything.** Tap-the-tab-label is the
   PRIMARY phone navigation; digit keys `1-9` direct-select as backup.
2. **Map arrow keys to next/prev** — phone terminals ship a D-pad; `←`/`→`
   works with zero configuration.
3. **Expose single-key next/prev aliases** (`n`/`p`) for custom D-pad/tap
   shortcut slots (a prefix chord can't be a slot binding; a single letter can)
   and for terminals whose gestures CAN send arbitrary keys.
4. Keep the drag-swipe recognizer anyway — it works in Moshi's Mouse Mode and
   on desktop terminals that forward drags.
5. Quit on `esc` as well as `q` — but only with the escape timeout from §3,
   or drag floods will fake it.
