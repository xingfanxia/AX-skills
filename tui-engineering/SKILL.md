---
name: tui-engineering
description: >
  Build production-grade, phone-friendly terminal UIs (full-screen TUI
  dashboards) with zero terminal libraries — pure-core architecture, ANSI-safe
  layout math, line-diffed painting, SGR mouse + touch gestures, hit-testing,
  narrow-width responsive layouts, and a headless test harness. Distilled from
  the axfleet fleet-monitoring TUI. MUST trigger when the user says: "build a
  TUI", "terminal dashboard", "terminal UI", "full-screen CLI", "ncurses-style",
  "做个 TUI", "终端面板", "终端界面", "命令行 dashboard", "TUI 适配手机/Moshi",
  "mouse support in terminal", or asks to add tabs/mouse/touch/responsive
  behavior to an existing terminal program. Cross-platform: works on Claude
  Code, OpenAI Codex, OpenCode, and OpenClaw.
---

# TUI Engineering — phone-friendly terminal dashboards from scratch

> **Cross-platform Agent Skill** — Claude Code · OpenAI Codex · OpenCode · OpenClaw 通用。

Build a full-screen terminal UI the way axfleet is built: **no ncurses, no
blessed, no ink** — the terminal layer is ~500 lines you own and can test.
Every rule in this skill states the failure it prevents; every mechanism has a
runnable reference implementation at
**[xingfanxia/axfleet-ui-public](https://github.com/xingfanxia/axfleet-ui-public)**
(fixture-driven demo — `bun install && bun run tui`). The reference stack is
Bun + TypeScript; the architecture is stack-agnostic.

## When to use / not use

- ✅ Full-screen dashboards, monitors, pickers, multi-tab tools; anything that
  must stay readable at phone width (Moshi ≈45 cols) over mosh/SSH.
- ✅ Retrofitting mouse/touch/narrow-mode onto an existing raw-ANSI TUI.
- ❌ Line-oriented CLI output (just print), one-shot prompts (use readline),
  or apps already committed to a TUI framework (follow that framework).

## Architecture (non-negotiable shape)

```
contracts/  typed data model — the single shape everything renders from
state.ts    pure transitions: (state, event) → new state (never mutate)
render/     pure renderers: (state, cols, rows) → string[]  (one per tab)
term.ts     THE ONLY module touching stdin/stdout
api.ts      data source behind fetch/stream fns returning {ok,data}|{ok,error}
index.ts    impure event loop wiring term → state → render → paint
```

Everything except `term.ts`/`index.ts` is a pure function — that's what makes
layout, input decoding, and gestures unit-testable without a TTY. Transitions
return the **same reference** when nothing changed; the loop skips redraws on
identity. Detail: [references/architecture.md](references/architecture.md).

## Build order (follow this sequence)

1. **`contracts/`** — the typed data model. Fixtures and renderers both
   compile against it, so `tsc` proves demo data is shape-complete.
2. **`ansi.ts` + tests** — `visibleWidth` / `truncate` / `padEnd` / `wrapPlain`.
   All layout math flows through here. CJK/emoji = 2 cells. Never
   `String.length`. → [architecture.md §2](references/architecture.md)
3. **`term.ts`** — alt screen, raw mode, line-diffed paints, crash restore,
   pure `decodeEvents` with split-chunk carry-over + escape timeout.
   → [architecture.md §3](references/architecture.md), [input.md](references/input.md)
4. **`state.ts` + tests** — tabs, selection, scroll, data application.
5. **`render/frame.ts`** — chrome + first tab; add the layout-contract test
   NOW (every tab × sizes: exactly `rows` lines, each ≤ `cols`). Future tabs
   inherit the guarantee by joining the loop. → [testing.md](references/testing.md)
6. **Remaining tabs** — one pure renderer each.
7. **Fixtures + demo api** — deterministic noise, pure fn of (key, time). The
   TUI now runs headless; every later change is eyeball-verifiable.
   → [testing.md §fixtures](references/testing.md)
8. **Mouse/touch** — SGR decode → direction-locked gesture machine → hit
   ranges. Tests before wiring. → [input.md](references/input.md)
9. **Narrow-mode pass** — render every tab at ~45 cols with fixtures, catalog
   information loss, fix by stacking/compressing, pin with survival tests.
   → [responsive.md](references/responsive.md)
10. **Footer hints + README** — document keys; keep single-key next/prev
    aliases bindable from phone-terminal shortcut slots.

## Invariants checklist (verify before calling it done)

- [ ] Frame is exactly `rows` lines, every line `visibleWidth ≤ cols`, at ALL
      sizes (45×30 / 76×24 / 120×40 minimum) — soft-wrap corrupts diff paints
- [ ] Crash path restores the terminal (`uncaughtException` → `term.exit()`)
- [ ] Unknown CSI consumed through final byte (F5 must not leak "1","5")
- [ ] Trailing escape fragments carried across chunks + escape timeout
      (~40ms); NEVER eagerly treat chunk-final ESC as the ESC key if ESC quits
- [ ] Mouse modes disabled on exit in reverse order of enable
- [ ] Selectable list rows are ONE line each, list at top of pane
      (pane line == item index — hit-testing and follow-selection depend on it)
- [ ] Narrow mode stacks/wraps instead of truncating; survival tests assert
      full message text present at 45 cols
- [ ] Fixtures typed against `contracts/`; day-spaced noise periods don't
      divide a day evenly (aliasing)
- [ ] One command runs typecheck + all tests headless (`bun run verify`)

## Phone terminals — what actually arrives (hard-won facts)

| Phone action | What the TUI receives (Moshi, measured 2026-07) |
|---|---|
| tap | SGR press + release |
| vertical pan | wheel-up/down burst |
| horizontal swipe | **nothing by default** — armed only by moshi-hook's live env read of `$TMUX_PANE`/`$ZELLIJ`/`$HERDR_ENV` (that precedence); on detection swipe sends the mux's prefix chord (`Ctrl-B n`/`p`). Two verified recipes: tmux conditional binding forwards the chord into a pane titled via OSC 2 (input.md §6.5 — the default-setup path), or bare-shell `HERDR_ENV=1` impersonation + speak the chord (§6.6) |
| Mouse-Mode drag | press/drag/release forwarded (gesture recognizer applies) |

Consequences: tap-the-tab-label is primary phone navigation, never make swipe
the only path, map D-pad `←`/`→` to next/prev, keep single-key aliases
(`n`/`p`) for custom shortcut slots. Full table + gesture state machine:
[references/input.md](references/input.md).

## References

- [references/architecture.md](references/architecture.md) — layers, ANSI width math, diffed painting, frame contract
- [references/input.md](references/input.md) — key/mouse decoding (with code), gestures, hit-testing, phone-terminal channels
- [references/responsive.md](references/responsive.md) — narrow-mode methodology (stack-don't-truncate) + audit workflow
- [references/testing.md](references/testing.md) — layered test strategy, deterministic fixtures, verify harness
- Runnable reference: https://github.com/xingfanxia/axfleet-ui-public (code + `docs/tui-methodology.md`)
