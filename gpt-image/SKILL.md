---
name: gpt-image
description: Generate or edit product, editorial, photographic and typography images with GPT Image 2.5. Sunburst favors quality; Flare favors speed. Automatically use the other variant on rate limits.
---

# GPT Image 2.5

Use **Sunburst** by default for final artwork, product and jewelry marketing,
pet reference assets, covers, typography, and fidelity-sensitive edits. Use
**Flare** for quick previews, drafts and interactive iteration. The other 2.5
variant is the fallback on HTTP 429, in either direction. Other errors surface
without switching models. Generation and edits follow the same routing.

## Invocation

```bash
~/.claude/skills/gpt-image/generate.py "<prompt>" [options]
# Fast preview, with Sunburst fallback on rate limits:
~/.claude/skills/gpt-image/generate.py "<prompt>" --variant flare
# Final edit, with Flare fallback on rate limits:
~/.claude/skills/gpt-image/generate.py "<prompt>" --edit source.png --variant sunburst
```

The executable uses `uv` and its inline OpenAI dependency. Allow up to ten
minutes per image; Sunburst is slower than Flare. Do not reuse old image-model
latency or cost estimates as current measurements.

- `--quality low|medium|high|xhigh|max|auto`: optional; omitted means API auto.
  Keep the actual application setting when comparing models.
- `--variant sunburst|flare`: CLI wins over `GPT_IMAGE_VARIANT`; default Sunburst.
- `--provider auto|azure|newapi`: auto uses configured Azure, then NewAPI.
- `--azure-retries N`: optional 429 retries per variant, default zero so the
  alternate deployment is tried immediately. Both rate limited: fail visibly.
- `--edit PATH`: repeat for multiple references; inputs reopen on every retry.
- `--size WxH`: default 1024x1024. Conservatively clamps to multiples of 16,
  long edge 3840 and 8,294,400 pixels. These are inherited bounds, not a claim
  that the new model's maximum dimensions have been measured.
- `--n N`, `--concurrency N`: image count and parallel workers (default 1 / 5).
- `--format jpg|jpeg|png|webp`: default JPG; PNG for transparency or crisp assets.
- `--output DIR`, `--name NAME`: output location and basename. Each saved path
  is printed to stdout. Use project scratch for temporary review images.

## Credentials and routing

Credentials come from environment or `~/.config/gpt-image/credentials` (the
local compatibility path points into `~/creds/`). Never commit keys.

```dotenv
AZURE_OPENAI_ENDPOINT=https://<resource>.cognitiveservices.azure.com
AZURE_OPENAI_API_KEY=<key-for-that-resource>
AZURE_OPENAI_API_VERSION=2025-04-01-preview
# Optional NewAPI provider; base URL includes /v1:
NEWAPI_BASE_URL=https://<your-gateway>/v1
NEWAPI_API_KEY=<gateway-key>
GPT_IMAGE_VARIANT=sunburst
```

Azure needs deployments named `gpt-image-2.5-sunburst` and
`gpt-image-2.5-flare` on the same resource. Each deployment/model is selected
explicitly; obsolete `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_MODEL`, and
`OPENAI_IMAGE_MODEL` no longer override the routing. The generic Foundry `v1`
API version is ignored in favor of the classic image API version above.
NewAPI uses those same two model aliases. There is no silent fallback to an
older image model or an unrelated OpenAI direct account.

## Prompting tips

GPT Image is strongest when you give it:
- **Subject + context**: "a stoic robot barista in a futuristic cafe on Mars"
- **Camera/framing**: "low-angle shot, shallow depth of field (f/1.8)"
- **Lighting**: "golden hour backlight", "soft window light, 4500K"
- **Style**: "1990s product photography", "editorial, Magnum photos aesthetic"
- **Typography (when needed)**: spell the exact text in quotes, specify font style and placement — e.g., `text reading "URBAN EXPLORER" at the top, bold, white, sans-serif`

For typography/text integration, GPT Image is usually better than Gemini.
For reference-image editing, use nanobanana instead.

**Repaint over a draft, don't generate from text**: for infographics, charts,
and diagrams, text-prompt-only generation is unreliable. Build the structure
first (matplotlib / hand-SVG / a rough render), pass it via `--edit
draft.png`, and let GPT Image improve the presentation while preserving the
title and annotation text.

## 中文文字排版纪律 (CJK text discipline)

Any prompt that renders Chinese text MUST end with this suffix, appended
verbatim (`prompt + SUFFIX` — a hard invariant you concatenate every time,
never trust the model to remember it):

```
禁止：文字重叠、文字压在复杂图像上、伪汉字乱码、逐字竖排英文、
超过两种字体、页面四边贴字无留白、装饰元素盖过标题、每页超过 5 个信息块。
```

- **>30 字正文 → 留位策略**: image models cannot reliably render long CJK
  body text. Have the model draw only the layout and visuals, leave the text
  zone blank, and overlay real text in post (PPT / image editor). This is the
  only reliable approach for long Chinese copy.
- **成套图 cover-first**: generate the cover first (it locks the style), then
  1 content image to verify style match, then batch the rest — same style
  brief injected into every prompt, only content parameters vary. Re-check
  against the cover every ~5 images; on drift, regenerate reusing the cover
  prompt's style paragraph.
- 中文横排；标点不出现在行首；中英混排时英文占比 ≤ 20%。
- **Prompt 里的内部约束不要直接喂给模型**: any constraint in a prompt
  ("public data only", "no logo") is frequently rendered as visible text on
  the image. Separate rules from copy — phrase constraints as "Do not render
  any text about X" AND enumerate the exact visible strings the model is
  allowed to draw.

<!-- Adapted from staruhub/ClaudeSkills (MIT) -->

Migration evidence and application timings: [references/image25-migration.md](references/image25-migration.md).
