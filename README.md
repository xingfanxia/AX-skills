# AX-skills

A collection of production-grade Claude Code skills built by [@xingfanxia](https://github.com/xingfanxia) (AX). Each skill is self-contained, runs on Claude Code / OpenAI Codex / OpenClaw, and ships with examples + tests.

> **What's a Skill?** A reusable slash-command-style capability for AI coding agents — bundles a `SKILL.md` (how to use), Python entrypoints, prompt templates, and reference docs. The agent invokes it like `/jewelry-marketing` and the skill takes over.

## Skills in this repo

| Skill | Purpose | Status |
|---|---|---|
| [`jewelry-marketing`](./jewelry-marketing/) | One photo in → full XHS marketing bundle out (12 images + 6 copy styles + analysis) for jewelry e-commerce merchants. Auto-routes finished products vs raw stones. | ✅ v1.0 |
| [`banxian-skill`](./banxian-skill/) | 三合一东方占卜（小六壬 / 梅花易数 / 六爻）+ 赛博半仙人设。py 算法引擎从 panpanmao 玄学平台 TS 移植，64 卦完整数据 + 守"一事一占""医不问卦"规矩。 | ✅ v1.0 |
| _more coming…_ | | |

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
├── examples/             # Test fixtures (small images, sample inputs)
└── 商业价值说明书.md     # 200-word value prop (for 繁星计划 submissions)
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

## Submission to 繁星计划·Fun Skills 全国大赛

- [`jewelry-marketing`](./jewelry-marketing/) — 赛道二 · 电商赛道。See [商业价值说明书](./jewelry-marketing/商业价值说明书.md).
- [`banxian-skill`](./banxian-skill/) — 赛道三 · 邪修脑洞。See [商业价值说明书](./banxian-skill/商业价值说明书.md).
