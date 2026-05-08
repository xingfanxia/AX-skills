# gemini-image

> Google Gemini image generation (Gemini 3.1 Flash Image / Nano Banana 2). Sister to [`gpt-image`](../gpt-image/) — same shape, different provider. Multi-reference image editing, soft / illustrated aesthetic baseline.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## When to pick this over gpt-image

- **Multi-reference image input** (background swap, character consistency across scenes, style transfer) — gpt-image cannot accept reference images
- Aesthetic leans **soft / illustrated / hand-drawn / Studio Ghibli / Chiikawa / watercolor**
- A/B testing the same prompt across providers
- You want a **warmer / more painterly default**

For photorealistic / editorial / product / UI mockups / images with rendered text → use [`gpt-image`](../gpt-image/) instead. For ambiguous requests → default to `gpt-image` (smaller files, faster batching), regenerate with `gemini-image` if aesthetic feels wrong.

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/gemini-image ~/.claude/skills/gemini-image
ln -sf ~/AX-skills/gemini-image ~/.codex/skills/gemini-image

# API key (Google AI Studio → https://aistudio.google.com/apikey)
echo 'GEMINI_API_KEY=your_key_here' > ~/AX-skills/gemini-image/.env
```

`.env` is gitignored. Script uses `uv run --script` shebang — auto-installs deps on first run, no manual venv.

## Usage

```bash
# Single image
generate.py "a cyberpunk cat reading a book"

# Multi-reference edit
generate.py "swap to tropical beach background" --reference original.png

# Character consistency across scenes (up to 14 references)
generate.py "same character drinking coffee" --reference scene1.png --reference scene2.png

# 3 variations
generate.py "watercolor lighthouse" --n 3 --name lighthouse

# Custom resolution / aspect
generate.py "Ghibli landscape" --resolution 4K --aspect 16:9
```

See [SKILL.md](./SKILL.md) for full CLI options and routing details.

## Credit / Attribution

The original Gemini image-generation logic was adapted from **feedtailor Inc.**'s open-source [`feedtailor/ccskill-nanobanana`](https://github.com/feedtailor/ccskill-nanobanana) (MIT). The upstream LICENSE is preserved as [`LICENSE-UPSTREAM-NANOBANANA`](./LICENSE-UPSTREAM-NANOBANANA) per MIT terms.

This is a **modified version**: rewritten with `uv` shebang for zero-venv install, restructured CLI for parity with `gpt-image`, integrated into the AX-skills ecosystem with parallel-generation guidance, and renamed from `nanobanana` to `gemini-image` for clarity (the upstream "Nano Banana" naming refers to the underlying Gemini model nickname, not a separate product). Copyright on adapted portions remains with feedtailor Inc. per MIT.
