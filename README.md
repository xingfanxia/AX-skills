# AX-skills

A collection of production-grade Claude Code skills built by [@xingfanxia](https://github.com/xingfanxia) (AX). Each skill is self-contained, runs on Claude Code / OpenAI Codex / OpenClaw, and ships with examples + tests.

> **What's a Skill?** A reusable slash-command-style capability for AI coding agents — bundles a `SKILL.md` (how to use), Python entrypoints, prompt templates, and reference docs. The agent invokes it like `/jewelry-marketing` and the skill takes over.

## Skills in this repo

### Vertical / domain skills

| Skill | Purpose | Status |
|---|---|---|
| [`jewelry-marketing`](./jewelry-marketing/) | One photo in → full XHS marketing bundle out (12 images + 6 copy styles + analysis) for jewelry e-commerce merchants. Auto-routes finished products vs raw stones. | ✅ v1.0 |
| [`banxian-skill`](./banxian-skill/) | 三合一东方占卜（小六壬 / 梅花易数 / 六爻）+ 赛博半仙人设。py 算法引擎从 panpanmao 玄学平台 TS 移植，64 卦完整数据 + 守"一事一占""医不问卦"规矩。 | ✅ v1.0 |
| [`pet-forge`](./pet-forge/) | AI desk-pet asset generator — text or photo → 10 character-consistent APNG state animations + ready-to-install `theme.json` for clawd-on-desk (or any APNG-based pet runtime). Productionizes the 小肥 + 胖猫 build workflow. ~$2.30/pet, ~6-8 min. | ✅ v1.0 |
| [`learning-coach`](./learning-coach/) | 在 Claude Code 里**主动引导你学任何东西**的学习教练（语言/技术/技能）。轻校准→喂 i-1 可理解输入→零评判猜读→工程化撞见→"今天懂了"→主动给下一小步。全程零考试·零背诵·零纠错羞辱，降焦虑优先于进度。领域无关内核 + 可选 playbook（英语首个）。四方调研交叉验证支撑。 | 🚧 v0.2 MVP |

### Writing

| Skill | Purpose | Status |
|---|---|---|
| [`khazix-writer`](./khazix-writer/) | 卡兹克风格中文公众号长文 — 强口语化、叙事驱动、四层自检（L1 硬性规则 → L2 风格 → L3 内容 → L4 活人感）。Personal-experience / methodology long-form. | ✅ |
| [`wandian-writer`](./wandian-writer/) | 晚点 LatePost 风格中文深度长文 — 冷静判断、数据先行、判断式 header、段尾落点、对立面陈述。Industry analysis / company breakdown. Includes 6-范文 in-context reference. | ✅ |

### Research

| Skill | Purpose | Status |
|---|---|---|
| [`deep-research`](./deep-research/) | Verification-style research — multi-agent parallel investigation, Tier 1-4 source authority cross-validation, traceable decision memo output. **Use when judging claims to make a decision.** | ✅ |
| [`narrative-research`](./narrative-research/) | 横纵分析法（Horizontal-Vertical Analysis）by 卡兹克 — 双轴叙事型调研。纵轴追溯生命历程，横轴对比共时竞品，交叉出洞察 + PDF 报告。**Use for understanding a thing from zero.** Narrative counterpart to `deep-research`. | ✅ |
| [`serenity-bottleneck-research`](./serenity-bottleneck-research/) | Turn a secular tech/industry trend, supply chain, or public investment thesis into concrete constraints, an evidence ladder (L0–L4), disconfirmation tests, and a reflexivity / attention-risk filter. Distills the *research process*, not trades — output is hypotheses to verify, never buy/sell advice. | ✅ |

### Media generation

| Skill | Purpose | Status |
|---|---|---|
| [`gpt-image`](./gpt-image/) | OpenAI gpt-image-2 image generation — Azure-routed with auto fallback to OpenAI direct on rate-limit. Defaults to JPG. Best for photorealistic / editorial / product / UI mockups / images with rendered text. Sister to `gemini-image`. | ✅ |
| [`gemini-image`](./gemini-image/) | Google Gemini 3.1 Flash Image generation. Sister to `gpt-image` — same shape, different provider. Best for **multi-reference image input** (background swap, character consistency across scenes — gpt-image cannot do this) and softer / illustrated / Studio Ghibli / watercolor aesthetics. | ✅ |
| [`transcribe`](./transcribe/) | Audio / video transcription via Google Gemini 3 Flash. Speaker diarization, auto language detection, files up to 500MB / ~8.4 hours. ~\$0.50/M input tokens. | ✅ |

### Documents

| Skill | Purpose | Status |
|---|---|---|
| [`apple-pdf`](./apple-pdf/) | Markdown / notes / reports → professionally formatted PDFs with SF typography. Default PDF generator. | ✅ |

### DevOps / Infrastructure

| Skill | Purpose | Status |
|---|---|---|
| [`cloudflare-r2-setup`](./cloudflare-r2-setup/) | Wire a Vercel / Next.js app's object storage to **Cloudflare R2** (zero egress, China-reachable), or migrate off Vercel Blob — the de-risked way. Proven write-toggle + host-routed-reads architecture (no data migration, instant rollback) + the full pitfall list (wrangler can't mint S3 keys, Vercel CLI env corruption, `next/image`/CSP blocking R2 images, custom-domain CDN 404-caching, private-bucket PII reads). | ✅ |

### Workflow / quality

| Skill | Purpose | Status |
|---|---|---|
| [`mtc`](./mtc/) | **More Than Coding** — full product workflow from concept to code. Iterates design / story first → aligned data → build → polish. For games, demos, prototypes, interactive experiences. The signature AX workflow. | ✅ |
| [`plan-design-review`](./plan-design-review/) | Design-completeness review for `PLAN.md` / spec docs. Rates 7 dimensions 0-10, detects AI-slop patterns, builds interaction state tables. Catches gaps before code goes in. | ✅ |
| [`codebase-sweep`](./codebase-sweep/) | Full-codebase audit + cleanup loop (parallel reviewers + iterative fix + docs cleanup + architecture documentation + orphan-script archiving). One-shot comprehensive review of the whole project. | ✅ |
| [`audit-fix-loop`](./audit-fix-loop/) | Multi-round code-quality pass scoped to recent changes. Loops until no high-confidence issues remain (max 5 rounds). Each round adds tests for fixed code + incremental doc updates. | ✅ |
| [`pr-fix-loop`](./pr-fix-loop/) | Autonomously respond to GitHub PR review feedback until all comments resolved + CI green. Polls **all four** comment surfaces — `@claude` posts to issue thread, not formal reviews, so single-surface polls miss it. Max 5 rounds. | ✅ |
| [`agentic-repo-scaffold`](./agentic-repo-scaffold/) | Make a repo agent-maintainable: drops an `AGENTS.md` architecture contract + a one-command verification harness (runnable boundary / giant-file / generated-clean checks) + `.agent/` refactor ledgers + optional Cursor/CI gates. Stack-aware (frontend / backend / general). Ships the full blueprint + dependency-free check scripts bundled. | ✅ v1.0 |

### Meta / knowledge

| Skill | Purpose | Status |
|---|---|---|
| [`neat-freak`](./neat-freak/) | 洁癖 — End-of-session knowledge sync. Reconciles agent memory + project root markdown + `docs/` + README against actual code so nothing rots. Three-audience editorial pass (agent / project-AI / external readers). Cross-platform (Claude Code · Codex · OpenCode · OpenClaw). Idempotent — safe to run every phase. | ✅ |

## Install (Claude Code)

```bash
# Clone the repo
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills

# Symlink the skill into Claude Code's skill dir
mkdir -p ~/.claude/skills
ln -sf ~/AX-skills/jewelry-marketing ~/.claude/skills/jewelry-marketing

# Reload Claude Code — the skill should now show up via /<skill-name> or auto-trigger
```

For OpenAI Codex / OpenClaw, follow your platform's skill installation convention (usually a similar symlink pattern).

## Skill structure (convention)

```
<skill-name>/
├── SKILL.md              # Required — frontmatter (name + description) + usage doc
├── README.md             # GitHub-facing overview (optional, can mirror SKILL.md)
├── generate.py           # Main CLI entry point (PEP 723 uv script preferred)
├── prompts/              # Prompt builders, helpers, output formatters
├── references/           # Domain-specific reference docs
└── examples/             # Test fixtures (small images, sample inputs)
```

## Why these skills

- **Distilled from real production**: Each skill is extracted from a working product, not a toy demo. `jewelry-marketing` comes from [shichuan (识川)](https://github.com/xingfanxia/shichuan) — research-backed by 千瓜 / 数英 case studies on 周大福 / HEFANG / 樱桃珠宝 / 翡翠平安环 etc.
- **Niche depth over generic breadth**: Better to nail one merchant vertical than be average at everything.
- **Tool-grade, not toy-grade**: Single command, sensible defaults, real output bundle, error recovery.

## License

MIT — see [LICENSE](./LICENSE).

## Contributing

These are personal skills, but PRs welcome if you want to:
- Add a new skill (open issue first to discuss scope)
- Improve prompt quality on an existing skill
- Add tests / examples

Open an issue with the skill name in the title.

## Acknowledgments

- [Anthropic Claude Code](https://docs.claude.com/en/docs/claude-code) — the runtime
- [OpenAI gpt-image-2](https://platform.openai.com/docs/guides/images) — image generation
- [Google Gemini](https://ai.google.dev/) — multimodal analysis
- 千瓜 · 数英 · 我是产品经理 · fxbaogao — XHS merchant research foundation

## Routing cheatsheet

When the agent has multiple candidate skills, route by intent:

**Content / media**
- **Image gen** — default to `gpt-image` (photorealistic / editorial / product / UI / text-in-image / batches > 5). Switch to `gemini-image` for multi-reference image input (background swap, character consistency) OR softer / illustrated / Studio Ghibli / watercolor aesthetics. Both can do every category — pick by the differentiators above
- **PDF** generation from markdown → `apple-pdf`
- **Audio → text** → `transcribe`

**Writing**
- **ZH long-form**, personal experience / methodology / 活人感 → `khazix-writer`
- **ZH long-form**, industry analysis / company breakdown / cold judgment → `wandian-writer`

**Research**
- "Should I pick A or B" / verify a claim / decide → `deep-research`
- "Tell me the full story of X" / understand from zero → `narrative-research`

**Learning / coaching**
- 想在 Claude Code 里被**主动带着**学点东西(英语/某技术/任意技能),要零考试·零背诵·不挫败的引导式学习 → `learning-coach`

**Workflow / quality**
- Build a game / demo / interactive prototype → `mtc`
- Reviewing a `PLAN.md` / spec → `plan-design-review`
- "Audit the whole codebase" / "clean up everything" → `codebase-sweep`
- "Audit and fix" / iterative fix on recent changes → `audit-fix-loop`
- Autonomously close out PR review feedback + CI → `pr-fix-loop`
- End-of-session knowledge sync (memory + docs + README) → `neat-freak`
