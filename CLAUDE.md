# AX-skills — repo conventions (read first)

Curated **public** collection of AX's Agent Skills + a GitHub Pages **showcase** of one 路演 deck per skill.
Live: <https://xingfanxia.github.io/AX-skills/>

## Layout

- `<skill-name>/SKILL.md` — one dir per skill = the skill source (mirrors the canonical copy in `~/.claude/skills/`). E.g. `banxian-skill/`, `jewelry-marketing/`, `game-script-creation/`, `proxy-node-setup/`.
- `docs/` — the Pages site (**served from `main` branch `/docs`**, legacy branch-build, auto-deploys on push):
  - `docs/index.html` — showcase landing (card grid; each card has a JS-injected `▶ 影片` button → R2-streamed promo in a lightbox).
  - `docs/<skill>/index.html` — that skill's deck (+ `assets/motion.min.js`, optional `images/`, optional `<skill>-roadshow.pdf`; carries the shared `#promo-link` snippet after `#home-link`).
  - `docs/.nojekyll`.
- `remotion/` — Remotion source for the promo videos (committed; `node_modules/` + `out/` gitignored). `src/skills.ts` = copy registry (mirrors landing-card copy), `src/SkillPromo.tsx` = the Dune Style A composition, `scripts/render-all.mjs` + `scripts/upload-r2.mjs` = the pipeline. **Rendered `.mp4`s are NOT in the repo** — they live on R2 (`ax-blog-media` bucket, `ax-skills/` prefix) served at `https://media.ax0x.ai/ax-skills/<slug>.mp4`. Composition id === deck slug === R2 filename (one source of truth).

## Deck style — ONE family, do not diverge

Every deck is **guizang-ppt-skill Style A (电子杂志) · 🌙 沙丘 / Dune** — uniform:
- theme `--ink:#1f1a14` / `--paper:#f0e6d2`, dark-paper body
- fonts: Playfair Display + Source Serif 4 + Noto Serif SC (serif display/headings/numbers) + Noto Sans SC (body) + IBM Plex Mono (kicker/meta/code)
- shared scaffold: WebGL dual-bg, magazine chrome/foot, `#nav` pill pager, `← AX Skills` home link, ESC overview, `B` low-power, Motion One local-first (`assets/motion.min.js`) + CDN fallback.

> The README once described banxian=IKB / jewelry=柠檬黄 (Swiss) — that's **historical**; all decks were unified to Dune Style A. Match the current files, not old docs.

**When building a new deck: read an existing deck (e.g. `docs/jewelry/index.html`) as the exact reference and produce a structural sibling.** Never introduce a different theme/style.

## Add a new skill deck (the flow)

1. Add `<skill>/SKILL.md` — the skill source (genericized; see rules).
2. Build `docs/<skill>/index.html` in Style A Dune, sibling of an existing deck; copy `assets/motion.min.js` alongside.
3. Add an `<article class="card <skill>">` to `docs/index.html`: `num` / `role` / `h2`+`.id`(skill name) / one-line `p` / `.src`(`源自 <product>` or `配套 <blog>`) / `.cta` = `查看 →` (`<skill>/`) + `源码 ↗` (`github.com/xingfanxia/AX-skills/tree/main/<skill>`) [+ optional `PDF ↓`].
4. Add a promo video (optional but default): append the skill to `remotion/src/skills.ts` (`id` === deck slug) + the id arrays in `remotion/scripts/*.mjs`, then `cd remotion && node scripts/render-all.mjs <slug> && node scripts/upload-r2.mjs <slug>`. The landing `▶ 影片` button + deck `#promo-link` auto-resolve `media.ax0x.ai/ax-skills/<slug>.mp4` from the slug — no per-card HTML edit needed.
5. `git push origin main` → Pages rebuilds from `/docs`.
6. **Visual-verify**: open the deck + screenshot key slides; play the promo lightbox; confirm it's a Dune sibling and reads clean.

## Promo videos (Remotion) — the motion layer above the decks

Each deck'd skill gets a ~20s 1920×1080 promo, authored in `remotion/` and hosted on R2 (NOT committed). The composition (`SkillPromo`) is a **strict Dune Style A sibling** of the decks — same `--ink`/`--paper`, same fonts (Playfair / Source Serif 4 / Noto Serif SC / Noto Sans SC / IBM Plex Mono via `@remotion/google-fonts`), magazine chrome + dot-grid + drifting glow. Three scenes: Title → Capabilities (3 points) → Outro (source + CTA). Copy lives ONCE in `src/skills.ts`, mirroring the landing-card copy.

- **Render:** `cd remotion && npm install && node scripts/render-all.mjs [slug…]` → `out/<slug>.mp4`. Preview: `npx remotion studio`. Sanity-check a frame: `npx remotion still src/index.ts <slug> out.png --frame=95`.
- **Host:** `node scripts/upload-r2.mjs [slug…]` → `wrangler r2 object put ax-blog-media/ax-skills/<slug>.mp4` (wrangler is already logged in for ax-blog). Served at `https://media.ax0x.ai/ax-skills/<slug>.mp4` (range-request enabled → seekable).
- **Embed:** landing JS injects `▶ 影片` per card (slug from the deck link); each deck carries the shared `#promo-link` lightbox snippet (slug from `location.pathname`, robust to `/<slug>/` and `/<slug>/index.html`). Both stream from R2 — no big files in the repo.
- The Remotion skill itself (`remotion-best-practices`) is installed in `~/.claude/skills/` (from `remotion-dev/skills`), NOT vendored here — it's a third-party skill, not an AX skill.

## Rules (non-negotiable)

- **Public repo → no real infra secrets.** Genericize server/proxy **node IPs, real node domains, tokens, subscription URLs** to placeholders (`tw.example.com`, `<你的域名>`, `<token>`, role labels like "US 母机"/"TW 节点"). Real **product** domains in `源自`/`配套` links are fine (panpanmao.ai, shichuan.ax0x.ai, blog.ax0x.ai). Grep new decks/skills for known real identifiers → must be 0.
- **No "Funskills" / "Funskills Roadshow".** Legacy naming bug — these are **AX Skills**. (title / chrome / kicker.)
- **Visual-verify decks** — grep/validator alone misses layout bugs (invisible labels, footnote-vs-pager collisions). Open it.
- **Pages CDN (Fastly) caches hard.** After a push the new path can 404 / serve stale for ~1–2 min; `?cb=` does NOT bust it — just retry. Build status: `gh api repos/xingfanxia/AX-skills/pages/builds`.

## Current decks
`banxian-skill` · `jewelry-marketing` · `game-script-creation` · `proxy-node-setup` · `dr-sharp` · `trident` · `serenity-bottleneck-research` · `web-novel-writing` — all 沙丘 Dune Style A, each with an R2-hosted promo video.

> `dr-sharp` + `trident` (added 2026-06-14) are improved ports of 秒秒Guo (mmguo.dev) prompts — credit the source in the deck/card (`改进自 秒秒Guo`), not a real product link. They are content/persona skills (no infra), so the genericize rule is trivially satisfied.
