---
name: analyze-video-evidence
description: Analyze a local or downloaded video through timestamped human/automatic captions, ASR fallback, uniform and targeted ffmpeg frames, contact sheets, sanitized metadata, and a claim-evidence ledger. Use when Codex must summarize, compare, fact-check, extract rankings or recommendations, interpret slides/gameplay/demos, or create a Markdown/HTML report from Bilibili, YouTube, or local video while keeping conclusions traceable to exact speech and visual evidence.
---

# Analyze Video Evidence

Turn a video into a reviewable evidence bundle, then answer the user's actual
question from that bundle. Prefer source-backed findings over an untraceable
generic summary.

## Inputs

Accept either:

- a local video plus optional SRT/VTT and yt-dlp `.info.json`; or
- a Bilibili/YouTube URL downloaded first with `$download-web-video`.

Require `ffmpeg` and `ffprobe`. Keep downloaded media, full transcripts, and
frames local unless the user authorizes publication.

## Prepare the first-pass evidence

Run:

```bash
python3 <skill-dir>/scripts/prepare_evidence.py \
  "./video-source/BV....mp4" \
  --output-dir "./video-evidence" \
  --subtitles "./video-source/BV....zh.srt" \
  --info-json "./video-source/BV....info.json" \
  --frame-count 24
```

If captions are omitted, the script prefers a nearby human Chinese caption,
then automatic Chinese, English, and other SRT/VTT files. Do not claim that
speech was analyzed when no captions exist.

When captions are absent:

1. Extract/transcribe audio with an available local or user-approved ASR route,
   such as the AX `$transcribe` skill.
2. Save SRT or VTT beside the video.
3. Rerun the evidence preparation command with `--subtitles`.

## Inspect before concluding

Read `transcript.md`, `evidence-index.md`, and `evidence.json`. View
`contact-sheet.jpg`, then open ambiguous individual frames at full resolution.
The first pass samples the complete timeline rather than only transcript-picked
moments.

Identify topic transitions, enumerated items, tables, slides, on-screen labels,
and places where the creator revises or qualifies an earlier point. Add exact
frames for those moments:

```bash
python3 <skill-dir>/scripts/prepare_evidence.py VIDEO \
  --output-dir "./video-evidence" \
  --subtitles CAPTIONS \
  --timestamp 00:08:42 \
  --timestamp 00:19:15
```

Read [references/analysis-method.md](references/analysis-method.md) when the
task involves rankings, recommendations, factual verification, conflicting
captions, or a publishable report.

## Build the claim-evidence ledger

Before writing, map each material finding to:

- a transcript time range and short paraphrase;
- a frame path when the claim depends on visible content;
- confidence (`high`, `medium`, or `low`);
- a caveat when the source is context-dependent or ambiguous.

Distinguish the creator's explicit statement from your inference. Never invent
card names, slide text, numbers, or tiers to fill a gap.

## Produce the requested artifact

Match the user's requested format. For a table or HTML guide:

- lead with the decision-useful result;
- make tiers or priorities scannable;
- preserve conditions such as act, archetype, existing synergies, or upgrade
  state instead of forcing a universal order;
- attach compact timestamps to every important recommendation;
- include a methodology/source note and uncertainty labels;
- do not embed the full transcript or redistribute a large frame collection.

Use the frontend design workflow for a polished HTML artifact and visually
verify responsive layout with browser screenshots.

## Acceptance criteria

Require all applicable conditions:

- `evidence.json`, `evidence-index.md`, `transcript.json`, and `transcript.md`
  exist.
- The evidence manifest records media metadata, source SHA-256, caption hash,
  cue count, frame timestamps, and nearby caption context.
- A full-timeline contact sheet exists when frames were requested.
- Consequential claims have timestamped speech or visual evidence.
- Inference and source statements are labeled separately.
- The final artifact answers the requested question, opens locally, remains
  readable on desktop and mobile, and contains no cookies or signed media URLs.

## Output bundle

```text
<evidence-dir>/
├── evidence.json
├── evidence-index.md
├── transcript.json
├── transcript.md
├── contact-sheet.jpg
└── frames/
    ├── uniform_...
    └── targeted_...
```
