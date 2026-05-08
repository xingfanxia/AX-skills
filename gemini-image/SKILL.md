---
name: gemini-image
description: |
  Generate images via Google Gemini (Gemini 3.1 Flash Image / Nano Banana 2).
  Sister skill to `gpt-image` — same shape, different provider. Pick by aesthetic
  preference: Gemini's baseline tends toward soft / illustrated / photographic-natural;
  GPT Image tends toward sharper / more graphic / better text rendering. Both can do
  every category — there is no "illustration vs realistic" hard divide.

  PREFER this skill when:
  - You need to edit / extend an existing image (multi-reference image input — supports up to 14 reference images)
    Use cases: background swap, character consistency across scenes, style transfer
  - The aesthetic you want leans soft / illustrated / hand-drawn / Studio Ghibli / Chiikawa-like
  - You want to A/B test the same prompt across providers (`gpt-image` for sharpness, `gemini-image` for warmth)

  PREFER `gpt-image` when:
  - The image must contain rendered text that has to be readable (titles, infographic labels, logos)
  - You need batches > 5 with the same prompt (gpt-image has built-in concurrency)
  - You want photorealistic editorial / product / brand-imagery default

  Triggers: generate image, create image, AI drawing, make an image, gemini image, nano banana, illustration, watercolor, anime style, multi-reference edit, character consistency, background swap.
---

# Gemini Image Generation

Image generation via Google's Gemini multimodal API.

## Setup (one-time)

```bash
# Install via the AX-skills repo
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/gemini-image ~/.claude/skills/gemini-image
ln -sf ~/AX-skills/gemini-image ~/.codex/skills/gemini-image

# Get API key from Google AI Studio: https://aistudio.google.com/apikey
# Either export GEMINI_API_KEY in your shell, or:
echo 'GEMINI_API_KEY=your_key_here' > ~/AX-skills/gemini-image/.env
```

`.env` is gitignored. The script auto-installs deps on first run via `uv` (no manual venv needed).

## Quick start

```bash
# Single image
~/.claude/skills/gemini-image/generate.py "a cyberpunk cat reading a book"

# Specific aspect / resolution
~/.claude/skills/gemini-image/generate.py "Studio Ghibli landscape" --aspect 16:9 --resolution 4K

# Multiple variations of the same prompt
~/.claude/skills/gemini-image/generate.py "watercolor lighthouse" --n 3 --name lighthouse

# Multi-reference edit (background swap)
~/.claude/skills/gemini-image/generate.py "swap the background to a tropical beach" \
  --reference original.png

# Character consistency across scenes
~/.claude/skills/gemini-image/generate.py "the same character now drinking coffee" \
  --reference scene1.png --reference scene2.png
```

## CLI

| Flag | Purpose | Default |
|---|---|---|
| `prompt` | Image prompt (positional, required) | — |
| `--resolution` | `1K` / `2K` / `4K` | `2K` |
| `--aspect` | Aspect ratio (`1:1`, `16:9`, `9:16`, etc.) | `16:9` |
| `--output` | Output directory | `~/Downloads/gemini-image/` |
| `--name` | Stable filename stem (default: timestamp). For `--n>1`, `_1.._N` suffix appended. | timestamp |
| `--n` | Number of variations to generate sequentially | `1` |
| `--reference` | Reference image path (repeatable, max 14) | none |

## Routing — gemini-image vs gpt-image

These are sister skills, not specialists. The most predictable distinguishers:

| Picks for `gemini-image` | Picks for `gpt-image` |
|---|---|
| Multi-reference image input (background swap, character across scenes, style transfer) — gpt-image cannot accept reference images at all | Image must contain rendered text that has to be readable |
| Soft / illustrated / hand-drawn / Studio Ghibli / Chiikawa / watercolor aesthetic | Photorealistic editorial, product shots, UI mockups, brand imagery (default) |
| You want a warmer / more painterly default | Batches > 5 same-prompt (gpt-image has built-in `--n` concurrency) |

When the request is ambiguous about aesthetic, default to `gpt-image` (it's the platform default — JPG output, smaller files, faster batching). If the result reads "wrong tone", regenerate with `gemini-image`.

## Parallel generation

For different prompts in parallel, use shell backgrounding:

```bash
~/.claude/skills/gemini-image/generate.py "prompt A" --name a &
~/.claude/skills/gemini-image/generate.py "prompt B" --name b &
~/.claude/skills/gemini-image/generate.py "prompt C" --name c &
wait
```

For same-prompt variations, use `--n N` (sequential within a single process).

## Output format

Defaults to PNG (Gemini API returns PNG). Convert to JPG to save space (~75% smaller) when transparency isn't needed:

```bash
sips -s format jpeg -s formatOptions 85 in.png --out out.jpg
```

## Cost note

Gemini 3.1 Flash Image is currently in preview (free tier available). Check current pricing at https://ai.google.dev/pricing.
