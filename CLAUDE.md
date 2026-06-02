# AX-skills — repo conventions (read first)

Curated **public** collection of AX's Agent Skills + a GitHub Pages **showcase** of one 路演 deck per skill.
Live: <https://xingfanxia.github.io/AX-skills/>

## Layout

- `<skill-name>/SKILL.md` — one dir per skill = the skill source (mirrors the canonical copy in `~/.claude/skills/`). E.g. `banxian-skill/`, `jewelry-marketing/`, `game-script-creation/`, `proxy-node-setup/`.
- `docs/` — the Pages site (**served from `main` branch `/docs`**, legacy branch-build, auto-deploys on push):
  - `docs/index.html` — showcase landing (card grid).
  - `docs/<skill>/index.html` — that skill's deck (+ `assets/motion.min.js`, optional `images/`, optional `<skill>-roadshow.pdf`).
  - `docs/.nojekyll`.

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
4. `git push origin main` → Pages rebuilds from `/docs`.
5. **Visual-verify**: open the deck + screenshot key slides; confirm it's a Dune sibling and reads clean.

## Rules (non-negotiable)

- **Public repo → no real infra secrets.** Genericize server/proxy **node IPs, real node domains, tokens, subscription URLs** to placeholders (`tw.example.com`, `<你的域名>`, `<token>`, role labels like "US 母机"/"TW 节点"). Real **product** domains in `源自`/`配套` links are fine (panpanmao.ai, shichuan.ax0x.ai, blog.ax0x.ai). Grep new decks/skills for known real identifiers → must be 0.
- **No "Funskills" / "Funskills Roadshow".** Legacy naming bug — these are **AX Skills**. (title / chrome / kicker.)
- **Visual-verify decks** — grep/validator alone misses layout bugs (invisible labels, footnote-vs-pager collisions). Open it.
- **Pages CDN (Fastly) caches hard.** After a push the new path can 404 / serve stale for ~1–2 min; `?cb=` does NOT bust it — just retry. Build status: `gh api repos/xingfanxia/AX-skills/pages/builds`.

## Current decks
`banxian-skill` · `jewelry-marketing` · `game-script-creation` · `proxy-node-setup` — all 沙丘 Dune Style A.
