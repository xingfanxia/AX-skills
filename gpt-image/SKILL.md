---
name: gpt-image
description: |
  Generate images via OpenAI's GPT Image family (Azure deployment
  gpt-image-2-1, OpenAI direct fallback on rate-limit). PREFER this skill
  for: photorealistic scenes, product shots, editorial/brand imagery, UI
  mockups, and any image where embedded text MUST render correctly
  (posters with titles, infographics with labels, logos with wordmark).
  AVOID for: illustration, anime, watercolor, Chiikawa / 吉卜力 / hand-drawn
  aesthetics, reference-image editing, or character-consistency across
  scenes — use the separate nanobanana skill (Google Gemini) for those.
  When genuinely ambiguous (no style signal), ask once: "realistic /
  editorial (gpt-image) or illustration / anime (nanobanana)?" — do NOT
  silently default.
---

# /gpt-image — Azure-first, OpenAI-fallback image generation

Generate images using GPT Image via Azure (preferred — user has contracted
compute at 10 RPM on deployment `gpt-image-2-1`), with automatic fallback
to OpenAI direct if Azure rate-limits.

## When to use this skill vs nanobanana

| User intent | Skill |
|---|---|
| Photorealistic, editorial, UI mock, typographic, product shot | **gpt-image** |
| Logo with embedded text | **gpt-image** |
| Illustration, anime, reference-image editing, style transfer | **nanobanana** |
| Character consistency across scenes using reference images | **nanobanana** |
| Batch > 10 images per minute | **gpt-image** (it falls back to OpenAI direct, no throttle) |

If the user doesn't specify a style and no clear signal points either way,
ask once; otherwise default to gpt-image for text-heavy / photorealistic
requests and nanobanana for illustrative requests.

## Invocation

```bash
~/.codex/skills/gpt-image/generate.py "<prompt>" [options]
```

The script is a PEP 723 uv script with inline dependencies — no venv setup
needed. uv caches `openai` after first run.

### Options

- `--size` — `1024x1024` (default), `1792x1024` (landscape), `1024x1792` (portrait)
- `--n` — number of images (default 1; batch throttled to 10 RPM on Azure)
- `--output` — output directory (default `~/Downloads/gpt-image/`)
- `--name` — basename for output files (default `gpt-image-<timestamp>`)
- `--provider` — `auto` (default, Azure → OpenAI fallback) | `azure` (Azure only) | `openai` (OpenAI direct only)
- `--azure-retries` — 429 retries on Azure before fallback (default 3)
- `--edit PATH` — **image-to-image edit mode**. When provided, routes to `images.edit` (input image + prompt → edited image) instead of `images.generate`. Repeatable for multi-image input: `--edit a.png --edit b.png`.

### Examples (text → image)

```bash
# Single image, default landscape
~/.codex/skills/gpt-image/generate.py "editorial product shot of a matte-black espresso machine, soft window light, shallow depth of field" --size 1792x1024

# Batch of 4 (auto-throttled on Azure)
~/.codex/skills/gpt-image/generate.py "minimalist poster for a jazz club, 1960s swiss style, bold typography reading 'BLUE NOTE'" --n 4 --output ./assets

# Force OpenAI direct (skip Azure for known-large batches)
~/.codex/skills/gpt-image/generate.py "cover art variations for Mio AI" --n 8 --provider openai

# Force Azure (use contracted compute, no fallback)
~/.codex/skills/gpt-image/generate.py "retry this one on Azure only" --provider azure
```

### Examples (image + text → edited image)

```bash
# Edit: change background while preserving subject + pose
~/.codex/skills/gpt-image/generate.py "replace the background with a cozy library, keep the cat and pose unchanged" --edit ./cat.png --size 1024x1792

# Hybrid/style transfer: use source image as structural reference
~/.codex/skills/gpt-image/generate.py "transform into a Golden British Shorthair × Munchkin hybrid — plush golden fur, short legs kept" --edit ./munchkin.png --name hybrid

# Multi-image (pose + style)
~/.codex/skills/gpt-image/generate.py "draw this person in this pose" --edit ./person.png --edit ./pose.png
```

Azure latency: edit ~42s, generate ~100-125s (as of 2026-04, eastus2). Edit is actually faster because much of the composition comes from the input image.

## Rate-limit behaviour

- **Azure**: 10 RPM. Batch mode sleeps 7s between requests for headroom.
- **On 429**: exponential backoff (5s → 10s → 20s) for `--azure-retries`
  attempts, then falls through to OpenAI direct if `OPENAI_API_KEY` is set.
- **OpenAI direct**: 2 retries on 429 before bailing.
- **Sticky fallback**: once the Azure batch has fallen over to OpenAI for
  one image, the remaining batch stays on OpenAI.

## Credentials setup (one-time per machine)

The script reads credentials from environment variables first, then from
`~/.config/gpt-image/credentials`. Env vars win.

### Option 1 — shell environment (preferred for scripting)

Add to `~/.zshrc`:

```bash
export AZURE_OPENAI_API_KEY="<azure-key>"
export AZURE_OPENAI_ENDPOINT="https://xingf-mnqrf4mc-eastus2.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="gpt-image-2-1"    # deployment name (URL path)
export AZURE_OPENAI_MODEL="gpt-image-2"           # underlying model (body)
export OPENAI_API_KEY="<openai-direct-key>"       # for fallback
```

### Option 2 — credentials file (preferred for one-off machines)

```bash
mkdir -p ~/.config/gpt-image
cat > ~/.config/gpt-image/credentials <<'EOF'
AZURE_OPENAI_ENDPOINT=https://xingf-mnqrf4mc-eastus2.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-image-2-1
AZURE_OPENAI_MODEL=gpt-image-2
AZURE_OPENAI_API_KEY=<azure-key>
OPENAI_API_KEY=<openai-direct-key>
EOF
chmod 600 ~/.config/gpt-image/credentials
```

**Azure deployment vs model name** — two names that Azure distinguishes:
- **Deployment name** (`AZURE_OPENAI_DEPLOYMENT`) is what YOU named the deployment in
  Azure portal. It goes in the URL path.
- **Model name** (`AZURE_OPENAI_MODEL`) is what Azure internally calls the underlying
  model. It goes in the request body. For the `gpt-image-2` family, Azure typically
  names the model `gpt-image-2` regardless of what you named the deployment.

If you pass the deployment name where the model name is expected, Azure's edit
endpoint returns `"The model 'X' does not exist"` — even though the deployment
does exist. Get the real model name via:
```bash
az cognitiveservices account deployment show \
  --name <resource> --resource-group <rg> \
  --deployment-name <deployment> \
  --query "properties.model.name" -o tsv
```

If only `AZURE_OPENAI_API_KEY` is set, fallback is disabled — rate-limit
errors surface directly. If only `OPENAI_API_KEY` is set, Azure is skipped
entirely.

## Output

The script prints the path of each saved PNG to stdout (one per line),
which makes it easy to pipe into subsequent tools:

```bash
~/.codex/skills/gpt-image/generate.py "prompt" --n 3 | xargs open
```

## Prompting tips

GPT Image is strongest when you give it:
- **Subject + context**: "a stoic robot barista in a futuristic cafe on Mars"
- **Camera/framing**: "low-angle shot, shallow depth of field (f/1.8)"
- **Lighting**: "golden hour backlight", "soft window light, 4500K"
- **Style**: "1990s product photography", "editorial, Magnum photos aesthetic"
- **Typography (when needed)**: spell the exact text in quotes, specify font style and placement — e.g., `text reading "URBAN EXPLORER" at the top, bold, white, sans-serif`

For typography/text integration, GPT Image is usually better than Gemini.
For reference-image editing, use nanobanana instead.
