---
name: gemini-image
description: Generate images or image edits with Google Gemini / Nano Banana. Use for Gemini image, nano banana, multi-reference image edits, background swaps, character consistency, style transfer, or soft illustrated / watercolor / anime aesthetics; prefer gpt-image for readable text, large same-prompt batches, and sharp product/editorial defaults.
---

# Gemini Image Generation

Image generation via Google's Gemini multimodal API.

## Setup (one-time)

```bash
# Install via the AX-skills repo
git clone https://github.com/xingfanxia/AX-skills.git ~/projects/devtools/AX-skills
ln -sf ~/projects/devtools/AX-skills/gemini-image ~/.claude/skills/gemini-image
ln -sf ~/projects/devtools/AX-skills/gemini-image ~/.codex/skills/gemini-image

# Get API key from Google AI Studio: https://aistudio.google.com/apikey
# Either export GEMINI_API_KEY in your shell, or:
echo 'GEMINI_API_KEY=your_key_here' > ~/projects/devtools/AX-skills/gemini-image/.env
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

# Highest quality (Nano Banana Pro), or compare both tiers side-by-side
~/.claude/skills/gemini-image/generate.py "editorial portrait" --model pro
~/.claude/skills/gemini-image/generate.py "editorial portrait" --ab-test --name compare
```

## CLI

| Flag | Purpose | Default |
|---|---|---|
| `prompt` | Image prompt (positional, required) | — |
| `--model` | `nb2` (Nano Banana 2, `gemini-3.1-flash-image`) or `pro` (Nano Banana Pro, `gemini-3-pro-image`) | `nb2` |
| `--ab-test` | Generate with BOTH model tiers; filenames get `_nb2` / `_pro` suffix | off |
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

## 中文文字排版纪律 (CJK text discipline)

Any prompt that renders Chinese text MUST end with this suffix, appended verbatim (`prompt + SUFFIX` — a hard invariant you concatenate every time, never trust the model to remember it):

```
禁止：文字重叠、文字压在复杂图像上、伪汉字乱码、逐字竖排英文、
超过两种字体、页面四边贴字无留白、装饰元素盖过标题、每页超过 5 个信息块。
```

- **>30 字正文 → 留位策略**: image models cannot reliably render long CJK body text. Have the model draw only layout + visuals, leave the text zone blank, overlay real text in post (PPT / image editor). This is the only reliable approach for long Chinese copy. (For text that must render readably, gpt-image is the stronger pick anyway — see routing above.)
- **成套图 cover-first**: generate the cover first (locks the style), then 1 content image to verify style match, then batch the rest — same style brief injected into every prompt, only content parameters vary. Re-check against the cover every ~5 images; on drift, regenerate reusing the cover prompt's style paragraph (`--reference cover.png` also helps here).
- 中文横排；标点不出现在行首；中英混排时英文占比 ≤ 20%。

<!-- Adapted from staruhub/ClaudeSkills (MIT) -->

## Cost note

Both models are GA (previews shut down 2026-06-25). nb2 (`gemini-3.1-flash-image`) output: $0.067/1K, $0.101/2K, $0.151/4K per image; pro (`gemini-3-pro-image`) costs roughly 2x nb2. Check current pricing at https://ai.google.dev/gemini-api/docs/pricing.
