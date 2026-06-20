# gpt-image

> OpenAI gpt-image-2 image generation — handles both Azure-routed and direct OpenAI API calls, with auto rate-limit fallback.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The default image generator in AX's workflow. Used for: photorealistic images, editorial illustrations, product shots, UI mockups, brand imagery, anything with embedded text, and batches > 10. Defaults to JPG (~75% smaller than PNG).

## When to use

- "Generate an image of X"
- "Make a cover image for this post"
- "I need a hero image"
- Any image generation that's NOT illustration / anime / watercolor / hand-drawn (those go to a Gemini-based skill better at illustrations)

## Routing

- **gpt-image (this)** ← photorealistic, editorial, product, UI mockup, brand imagery, images with text, batches > 10, ambiguous style requests
- **Gemini Nano Banana** ← illustration / anime / watercolor / Chiikawa / 吉卜力 / hand-drawn / cartoon style, OR multi-reference-image editing (background swap, character consistency across scenes)

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills

# This is a Codex-side skill (also runs on Claude Code)
ln -sf ~/AX-skills/gpt-image ~/.codex/skills/gpt-image
ln -sf ~/AX-skills/gpt-image ~/.claude/skills/gpt-image
```

## API key setup

Set one or both of:
- `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` (preferred for higher rate limits)
- `OPENAI_API_KEY` (fallback)

The skill auto-detects which is available and falls back to OpenAI direct on Azure rate-limit hits.

## Parallel generation

Single-request latency is ~100s/image. Built-in `--n` flag with `--concurrency` for same-prompt batches:

```bash
python generate.py "a cyberpunk cat" --n 5 --concurrency 5
```

For different prompts, shell-level backgrounding:

```bash
python generate.py "prompt A" --name a &
python generate.py "prompt B" --name b &
wait
```

See [SKILL.md](./SKILL.md) for full CLI options.
