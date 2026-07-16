# AX-skills — repo conventions (read first)

Curated **public** collection of AX's Agent Skills + GitHub Pages demo pages and demo videos for selected skills.
Live: <https://xingfanxia.github.io/AX-skills/>

## Layout

- `<skill-name>/SKILL.md` — one dir per skill = the skill source (mirrors the canonical copy in `~/.claude/skills/`). E.g. `banxian-skill/`, `jewelry-marketing/`, `game-script-creation/`, `proxy-node-setup/`.
- `docs/` — the Pages site (**served from `main` branch `/docs`**, legacy branch-build, auto-deploys on push):
  - `docs/index.html` — showcase landing (card grid; each card has a JS-injected `▶ 影片` button → R2-streamed demo video in a lightbox).
  - `docs/<skill>/index.html` — that skill's interactive demo page (+ `assets/motion.min.js`, optional `images/`, optional PDF; carries the shared `#promo-link` snippet + a per-skill `#source-link` (`源码 ↗` → `tree/main/<skill-dir>`) after `#home-link`). Existing `*-roadshow.pdf` filenames are legacy compatibility names, not current product terminology.
  - `docs/.nojekyll`.
- `remotion/` — Remotion source for demo videos (committed; `node_modules/` + `out/` gitignored). `src/terminal/sessions.ts` = the per-skill scripted Claude-Code sessions (the demo content + source of truth), `src/terminal/TerminalPromo.tsx` = the terminal-sim composition engine, `scripts/render-all.mjs` + `scripts/upload-r2.mjs` = the pipeline. **Rendered `.mp4`s are NOT in the repo** — they live on R2 (`ax-blog-media` bucket, `ax-skills/` prefix) served at `https://media.ax0x.ai/ax-skills/<slug>.mp4`. Composition id === demo slug === R2 filename (one source of truth).
- `scripts/validate_skills.py` — structural skill linter (stdlib-only). Run `python3 scripts/validate_skills.py` after adding/editing any skill: enforces SKILL.md frontmatter `name` === dir name, 300/500 line caps (500+ needs an `OVERSIZE_ALLOWLIST` entry with a reason), dangling `references/*.md` / `scripts/*.<ext>` mentions, orphan asset files, and hardcoded `/Users/<name>/` paths. `--skill <name>` for one skill, `--strict` to make warnings fail.

## Demo page style — ONE family, do not diverge

Every interactive demo page is **guizang-ppt-skill Style A (电子杂志) · 🌙 沙丘 / Dune** — uniform:
- theme `--ink:#1f1a14` / `--paper:#f0e6d2`, dark-paper body
- fonts: Playfair Display + Source Serif 4 + Noto Serif SC (serif display/headings/numbers) + Noto Sans SC (body) + IBM Plex Mono (kicker/meta/code)
- shared scaffold: WebGL dual-bg, magazine chrome/foot, `#nav` pill pager, top-left chrome pills (`← AX Skills` home link + `▶ Demo` video + per-skill `源码 ↗` source link), ESC overview, `B` low-power, Motion One local-first (`assets/motion.min.js`) + CDN fallback.

> The README once described banxian=IKB / jewelry=柠檬黄 (Swiss) — that's **historical**; all demos were unified to Dune Style A. Match the current files, not old docs.

**When building a new demo page: read an existing demo (e.g. `docs/jewelry/index.html`) as the exact reference and produce a structural sibling.** Never introduce a different theme/style.

## Add a new skill demo (the flow)

1. Add `<skill>/SKILL.md` — the skill source (genericized; see rules).
2. Build `docs/<skill>/index.html` in Style A Dune, sibling of an existing demo page; copy `assets/motion.min.js` alongside.
3. Add an `<article class="card <skill>">` to `docs/index.html`: `num` / `role` / `h2`+`.id`(skill name) / one-line `p` / `.src`(`源自 <product>` or `配套 <blog>`) / `.cta` = `查看 →` (`<skill>/`) + `源码 ↗` (`github.com/xingfanxia/AX-skills/tree/main/<skill>`) [+ optional `PDF ↓`].
4. Add a demo video (optional): write a scripted terminal session for the skill in `remotion/src/terminal/sessions.ts` (`id` === demo slug) — **ground it in the skill's real `SKILL.md`** (actual invocation / workflow phases / output structure / persona, NOT the card blurb — blurb-scripted sessions misrepresent the skill and get rejected). Keep ≤16 visible lines, font-safe glyphs only (no hexagram chars/emoji → tofu), genericize infra. Add the id to the arrays in `remotion/scripts/*.mjs`, then `cd remotion && node scripts/render-all.mjs <slug> && node scripts/upload-r2.mjs <slug>`. The landing `▶ 影片` button + demo page `#promo-link` auto-resolve `media.ax0x.ai/ax-skills/<slug>.mp4` from the slug — no per-card HTML edit needed. Visually-verify a near-end still before declaring done.
5. `git push origin main` → Pages rebuilds from `/docs`.
6. **Visual-verify**: open the demo + screenshot key views; play the demo-video lightbox; confirm it's a Dune sibling and reads clean.

## Demo videos (Remotion)

Each showcased skill may have a ~13–18s 1920×1080 demo video, authored in `remotion/` and hosted on R2 (NOT committed). **The demo is a scripted Claude-Code terminal session showing the skill actually being used — not a replay of the interactive page.** Design: an inverted-Dune terminal window (ink `#17130c` body / paper `#f0e6d2` text, IBM Plex Mono + Noto Sans SC) floating on the paper dot-grid frame, with traffic-light chrome and the brand corners. The user types an invocation, the agent works (spinner → ✓ steps), output streams in, a gold `◆` result banner lands.

- **Authoring** is pure content: `src/terminal/sessions.ts` holds one `Session` per skill — an array of typed events (`in` prompt / `sys` dim line / `run` spinner-then-✓ / `out` streamed lines / `done` banner). The engine (`src/terminal/TerminalPromo.tsx` + `EventLine.tsx` + `types.ts`) derives ALL timing from the events and sets duration via the composition's computed `durationInFrames` — no per-event frames in the data. Keep a session ≲ 16 visible lines (the window height) so it doesn't need to scroll. Genericize per the rules (proxy uses `tw.example.com` / `<你的域名>` / `<token>`); avoid Unicode that isn't in the loaded fonts (e.g. Yijing hexagram glyphs render as tofu — use names).
- **Render:** `cd remotion && npm install && node scripts/render-all.mjs [slug…]` → `out/<slug>.mp4`. Preview: `npx remotion studio`. Sanity-check a frame: `npx remotion still src/index.ts <slug> out.png --frame=175`.
- **Host:** `node scripts/upload-r2.mjs [slug…]` → `wrangler r2 object put ax-blog-media/ax-skills/<slug>.mp4` (wrangler is already logged in for ax-blog). Served at `https://media.ax0x.ai/ax-skills/<slug>.mp4` (range-request enabled → seekable).
- **Embed:** landing JS injects `▶ 影片` per card (slug from the demo link); each demo page carries the shared `#promo-link` lightbox snippet (slug from `location.pathname`, robust to `/<slug>/` and `/<slug>/index.html`). Both stream from R2 — no big files in the repo. Re-rendering a skill replaces the mp4 at the same URL; no showcase edit needed.
- The Remotion skill itself (`remotion-best-practices`) is installed in `~/.claude/skills/` (from `remotion-dev/skills`), NOT vendored here — it's a third-party skill, not an AX skill.

## Rules (non-negotiable)

- **Public repo → no real infra secrets.** Genericize server/proxy **node IPs, real node domains, tokens, subscription URLs** to placeholders (`tw.example.com`, `<你的域名>`, `<token>`, role labels like "US 母机"/"TW 节点"). Real **product** domains in `源自`/`配套` links are fine (panpanmao.ai, shichuan.ax0x.ai, blog.ax0x.ai). Grep new decks/skills for known real identifiers → must be 0.
- **No "Roadshow" / "路演" / "Funskills" / "Funskills Roadshow" as current terminology.** Those are legacy naming bugs. These are **AX Skills demos**. Keep legacy filenames only when renaming would break an existing public URL.
- **Catalog priority:** feature and order AX-original skills and methods first, especially those distilled from shipped products or repeated internal use. Keep explicitly adapted/ported skills discoverable with attribution, but place them after original work in Featured lists, landing pages, and demo inventories unless the user deliberately overrides that order.
- **Visual-verify demos** — grep/validator alone misses layout bugs (invisible labels, footnote-vs-pager collisions). Open it.
- **Pages CDN (Fastly) caches hard.** After a push the new path can 404 / serve stale for ~1–2 min; `?cb=` does NOT bust it — just retry. Build status: `gh api repos/xingfanxia/AX-skills/pages/builds`.

## Style brief (image-set skills convention)

Skills that batch-generate image sets (gpt-image, gemini-image, and any skill built on them) define a **style brief** once — 风格名 + palette / typography / composition key params in a few sentences — and inject it verbatim into every prompt of the set; only content parameters vary per image. Cover-first: generate the cover to lock the style, verify one content image against it, then batch the rest. Details (incl. the 中文文字排版纪律 verbatim 禁止项 suffix): `gpt-image/SKILL.md` / `gemini-image/SKILL.md`.

## Current demos
`banxian-skill` · `jewelry-marketing` · `game-script-creation` · `proxy-node-setup` · `serenity-bottleneck-research` · `web-novel-writing` · `dr-sharp` · `trident` — all 沙丘 Dune Style A, each with an R2-hosted terminal demo (a scripted Claude-Code session grounded in the skill's real `SKILL.md`).

> `dr-sharp` + `trident` (added 2026-06-14) are improved ports of 秒秒Guo (mmguo.dev) prompts — credit the source in the demo/card (`改进自 秒秒Guo`), keep them after AX-original work in catalog ordering, and do not present them as flagship original methods.
