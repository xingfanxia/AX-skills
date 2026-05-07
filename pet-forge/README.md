# pet-forge

> AI desk-pet asset generator — text or photo → 10 character-consistent APNG state animations + ready-to-install `theme.json` for [clawd-on-desk](https://github.com/anthropics/clawd-on-desk) (or any APNG-based pet runtime).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

This skill is part of [AX-skills](https://github.com/xingfanxia/AX-skills) — a personal collection of Claude Code / Codex skills.

## What it does

Feed it a description ("chubby gold tabby Munchkin with jade-green eyes") OR a real-pet photo + breed, get back **10 lively cartoon-style APNG animations** of that pet performing every state in a desk-pet's lifecycle:

`idle-dozing` · `sleeping` · `working-typing` · `thinking` · `happy` · `notification` · `react-poke` · `error` · `collapse-sleep` · `wake`

Plus a `theme.json` that drops straight into clawd-on-desk's themes directory.

## Why does this exist

Generating a character-consistent desk pet is harder than it looks:

- **AI video models won't morph far from the first frame in 4s.** If every state is anchored on a single "main reference image," all 10 states look like the same sitting cat with minor face wiggles.
- **Green-screen chroma-key removes green eye colors.** Default chroma settings (HSV hue 80-160 + saturation ≥40) catch jade-green eye colors and gray them out, leaving the pet with hollow eye sockets.
- **Doubao's image+lastFrame anchoring is the seam-free-loop secret.** Without both anchors, animations drift between iterations.
- **Long-coat breeds need different fileScales than short-coat ones** — the silhouette takes more visual space.

This skill bakes in those gotchas (and 4 more — see `references/7-critical-lessons.md`) so the next custom pet generation is `generate.py "..."` instead of a 12-hour debugging session.

## Quick start

```bash
# Install (after cloning AX-skills)
ln -sf ~/projects/AX-skills/pet-forge ~/.claude/skills/pet-forge

# Set credentials
mkdir -p ~/.config/gpt-image
cat > ~/.config/gpt-image/credentials <<EOF
OPENAI_API_KEY=sk-...
DOUBAO_API_KEY=...
EOF

# Generate a pet
~/.claude/skills/pet-forge/generate.py \
  --description "chubby gold tabby British Shorthair Munchkin with jade-green eyes" \
  --pet-id munchkin \
  --display-name "小肥"
```

After ~6-8 minutes and ~$2.30 of API spend, you'll have a complete `clawd-on-desk/themes/munchkin/` ready to use.

## How it works

```
   text or photo
        │
        ▼
┌────────────────────┐
│ STAGE 1: Refs      │   gpt-image-2 (Azure preferred, OpenAI direct fallback)
│  · main-ref        │   character anchor — defines breed, coat, eye color
│  · sleep-final-ref │   curled-up sleeping pose
│  · 5 pose-refs     │   one per "active" state (idle-dozing, working-typing, etc.)
└────────────────────┘
        │
        ▼
┌────────────────────┐
│ STAGE 2: Animation │   Doubao Seedance — image+lastFrame anchored 4s clips
│  10 mp4s × 4s      │   one per state, motion prompts wrap CHARACTER_PREFIX
└────────────────────┘
        │
        ▼
┌────────────────────┐
│ STAGE 3: Install   │   chroma_key.py (patched) → APNG, plays=0 infinite loop
│  10 APNGs          │   theme.json templated from breed-specific config
│  theme.json        │   copied into clawd-on-desk/themes/<pet>/
└────────────────────┘
```

## Lineage

This skill productionizes the workflow that produced the **小肥 (Munchkin)** and **胖猫 (Ragdoll)** custom pets shipping in [clawd-on-desk](https://github.com/anthropics/clawd-on-desk). All 7 lessons in `references/7-critical-lessons.md` are scars from that build.

## Vendored tools

The `tools/` directory contains a vendored snapshot of [pet-forge](https://github.com/) with a patched `chroma_key.py` (adds `--sat-min` and `--despill-sat-min` flags for green-feature-preserving chroma — required for jade-eyed pets). MIT-licensed, originally by pet-forge contributors.

## Reference

- `SKILL.md` — Claude Code skill manifest (full options, recipe)
- `references/7-critical-lessons.md` — gotchas and how to avoid them
- `references/chroma-tuning-guide.md` — when to tune chroma flags
- `references/theme-json-anatomy.md` — clawd-on-desk theme schema
- `examples/munchkin/` — `theme.json` + `animations.json` for 小肥
- `examples/ragdoll/` — same for 胖猫 (notes Ragdoll-specific fileScale bumps)

## License

MIT. Fork it, ship custom pets, share back if you find new gotchas.
