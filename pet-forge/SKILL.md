---
name: pet-forge
description: Use when generating a custom desk-pet character for clawd-on-desk (or any APNG-based pet runtime) from either a text description or a real-pet photo + breed. Produces 10 lively, character-consistent state animations (idle / sleeping / working-typing / thinking / happy / notification / react-poke / error / collapse-sleep / wake), green-screen chroma-keyed APNGs, and a ready-to-install theme.json. Trigger phrases: 自定义桌面宠物, custom desk pet, generate pet animations, clawd theme, 给我做一只猫, pet-forge, 桌宠生成, custom cat sprites, AI pet animation pipeline.
---

# /pet-forge — AI desk-pet asset generator (clawd-on-desk-ready)

> Source: <https://github.com/xingfanxia/AX-skills/tree/main/pet-forge>
> License: MIT — fork & adapt freely
> Dogfood lineage: this skill produced the 小肥 (Munchkin, jade-green eyes) and 胖猫 (Ragdoll, sky-blue eyes) custom pets shipping in clawd-on-desk.

One prompt (or one photo + breed) → 10 character-consistent APNG states + theme.json, ready to drop into `clawd-on-desk/themes/<pet>/`.

## What it produces

For each pet:

| Output | Count | Format | Where |
|---|---|---|---|
| State animation APNG | 10 | APNG (200px height, 8fps, plays=0 infinite loop) | `clawd-on-desk/themes/<pet>/assets/<pet>-<state>.apng` |
| theme.json | 1 | JSON (schema v1) | `clawd-on-desk/themes/<pet>/theme.json` |
| Character refs (saved for re-runs) | 7 | PNG | `output/refs/<pet>/` |

**10 states**: `idle-dozing`, `sleeping`, `working-typing`, `thinking`, `happy`, `notification`, `react-poke`, `error`, `collapse-sleep`, `wake`.

## The pipeline (3 stages)

```
   ┌────────────────────────┐    ┌──────────────────────────┐    ┌────────────────────────┐
   │  Stage 1: Refs         │───▶│  Stage 2: Animation      │───▶│  Stage 3: Install      │
   │  gpt-image-2 ×7        │    │  Doubao Seedance ×10     │    │  chroma + theme.json   │
   │  ~$0.30 (7 × $0.04)    │    │  ~$2.00 (10 × $0.20)     │    │  $0 (local)            │
   └────────────────────────┘    └──────────────────────────┘    └────────────────────────┘
        Character anchor              State-pose-refs drive            APNG + theme.json
        (main + sleep + 5 poses)      Doubao image+lastFrame anchor     drop into theme dir
```

Total spend: ~**$2.30 / pet**, ~**5–8 min wall-clock** (parallelizable).

## Invocation

```bash
~/.claude/skills/pet-forge/generate.py [PROMPT_OR_OPTIONS]
```

PEP 723 uv script — no venv setup needed. `uv` handles deps on first run.

### Common forms

```bash
# 1. From text prompt
generate.py --description "chubby gold tabby British Shorthair Munchkin with jade-green eyes" --pet-id munchkin

# 2. From photo of a real cat + breed override
generate.py --photo ~/cats/xiao-fei.jpg --breed "Munchkin" --pet-id xiaofei

# 3. From an existing main-ref (skip stage 1, jump to stage 2/3)
generate.py --main-ref output/refs/munchkin/main-ref.png --pet-id munchkin

# 4. Re-run only specific states (fix a bad one)
generate.py --pet-id munchkin --only notification thinking

# 5. Dry-run (analyze + plan only, no API spend)
generate.py --description "..." --dry-run
```

### Options

```
  --pet-id <id>         filesystem-safe slug; becomes theme dir name + APNG prefix
  --description TEXT    text describing the pet (breed, color, eye color, build, vibe)
  --photo PATH          photo of the real pet (gpt-image-2 will edit-mode anchor on it)
  --breed TEXT          breed override (used to refine character prefix)
  --display-name TEXT   what shows in clawd-on-desk theme picker (Unicode OK: 小肥, 胖猫)

  --main-ref PATH       skip ref generation; use this image as character anchor
  --only STATES         comma-separated subset of the 10 states to (re)generate
  --skip-install        write to ./output/<pet>/ but don't copy to clawd-on-desk

  --green-eye           pass --sat-min 85 --despill-sat-min 70 to chroma_key.py
                        (REQUIRED for any pet with green eyes; auto-detected from
                         description if --description contains green/jade/翡翠/绿)

  --clawd-on-desk PATH  override clawd-on-desk repo path (default ~/projects/products/clawd-on-desk)
  --dry-run             print plan without API spend
```

## Credentials

Reads from env vars OR `~/.config/gpt-image/credentials`:

```
# Required for stage 1 (refs)
OPENAI_API_KEY=sk-...                # OpenAI direct (gpt-image-2)
# OR Azure-contracted (preferred, 10 RPM):
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_DEPLOYMENT=gpt-image-2-1
AZURE_OPENAI_API_VERSION=2025-04-01-preview

# Required for stage 2 (videos)
DOUBAO_API_KEY=...                   # ByteDance Volcengine doubao-seedance
```

## Critical lessons (read before tweaking)

These come from the dogfood production of 小肥 / 胖猫 — see `references/7-critical-lessons.md` for the full discussion.

1. **State-pose refs are the liveliness unlock.** If every state's ref is the SAME `main-ref.png`, Doubao won't morph far from it in 4s — outputs become "sitting cat with face wiggle." Ref each state in its action pose (paw to chin for thinking, alert sit for notification) and Doubao will produce real motion.
2. **No blush.** gpt-image-2 loves to add pink cheek blush; it kills photorealism for tabby/calico cats. Negative-prompt blush explicitly.
3. **Sleep-ref is two-wave.** Generate `sleep-final-ref.png` chained on main-ref FIRST, then chain `collapse-sleep` (main → sleep) and `wake` (sleep → main) state refs on it.
4. **Doubao image+lastFrame anchoring**. Pass the ref as BOTH `image` (first frame) and `lastFrame` (last frame) — this is how you get a seamless loop. For transition states (collapse-sleep, wake) use main as image, sleep as lastFrame (or vice versa).
5. **Green-eyed pets need chroma tuning.** Default `chroma_key.py` settings catch jade-green eyes (hue 80-160 + sat ≥40) and gray them out. Pass `--sat-min 85 --despill-sat-min 70` to preserve jade greens. Blue-eyed pets are unaffected.
6. **Chinese theme display names work** — `theme.json` `name` field is Electron Unicode-safe. Directory IDs stay ASCII (filesystem-safe).
7. **Fluffy pets need fileScales bumped ~5%**. Long-coat breeds (Ragdoll, Persian) take more visual space than short-coat. Bump `objectScale.fileScales` entries by 0.05 over a short-coat reference.

## When NOT to use this skill

- Pet runtime that's NOT APNG-based (e.g., the runtime expects sprite sheets, GIF, or live SVG) — output won't be compatible.
- Photorealistic pets (the prompt template targets chibi/kawaii cartoon style; bypass the template if you want realism).
- States outside the 10 fixed ones — skill is opinionated about the lifecycle. Add new states by editing `tools/animations.template.json` + `prompts/template.example.js` motion prompts.

## Cost & wall-clock

| Stage | API | Per-pet cost | Wall-clock (parallel) |
|---|---|---|---|
| 1: refs | gpt-image-2 (Azure or OpenAI) | $0.28 (7 × $0.04) | ~3 min (10 RPM Azure cap) |
| 2: animations | Doubao Seedance | $2.00 (10 × ~$0.20) | ~3-4 min (configurable parallel) |
| 3: chroma + install | local Python + ffmpeg | $0 | ~30 s |
| **Total** | | **~$2.30 / pet** | **~6–8 min** |

Retries (re-running 1-3 states) cost ~$0.30 / state.

## Customizing the character prefix

The `prompts/template.example.js` ships a generic chibi-cat CHARACTER_PREFIX. To swap in your own pet:

1. Copy `prompts/template.example.js` to `prompts/template.<your-pet>.js`
2. Edit `CHARACTER_PREFIX` to describe your specific cat (breed, coat color, eye color, body shape, distinctive markings)
3. Run `generate.py --pet-id <your-pet> --template prompts/template.<your-pet>.js`

Two reference templates ship: `template.munchkin.example.js` (jade-eyed gold tabby Munchkin) and `template.ragdoll.example.js` (blue-eyed seal-point bicolor Ragdoll). Fork either.

## See also

- `examples/munchkin/` — full theme.json + animations.json snapshot for 小肥
- `examples/ragdoll/` — same for 胖猫 (Ragdoll-specific notes about fileScale bumps)
- `references/7-critical-lessons.md` — production gotchas distilled
- `references/chroma-tuning-guide.md` — when to tune `--sat-min` / `--despill-sat-min`
- `references/theme-json-anatomy.md` — clawd-on-desk theme schema reference
- Pet-forge upstream (the underlying Node + Python tools we vendored): provides batch-gen, image/video gen, and the chroma pipeline. We've included a patched `chroma_key.py` with `--sat-min` + `--despill-sat-min` flags.
