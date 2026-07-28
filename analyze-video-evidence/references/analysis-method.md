# Evidence-first video analysis

The workflow keeps the useful routing from
[imlewc/video-to-subtitle-summary-skill](https://github.com/imlewc/video-to-subtitle-summary-skill):
prefer platform captions, avoid unnecessary ASR, and fall back to local or
private transcription when captions are absent. It extends that approach from
"subtitle plus summary" to an auditable multimodal analysis.

## Source priority

1. Human captions from the platform.
2. Platform automatic captions.
3. ASR transcript produced from the downloaded audio.
4. Visual evidence from exact frames.
5. Description, chapters, and uploader metadata as context, never as a
   substitute for the video's content.

Record which layer supports each material claim. Do not silently merge human
and automatic captions. If they disagree on a consequential term, inspect the
audio or nearby frame and mark remaining uncertainty.

## Two-pass frames

First run a uniform contact sheet across the complete duration. This prevents
an analyst from seeing only the sections suggested by the transcript.

Then identify timestamps where the transcript changes topic, enumerates items,
shows a table, or contradicts the draft conclusion. Rerun
`scripts/prepare_evidence.py` with repeated `--timestamp` arguments. Inspect
those individual images at full resolution, not only the contact sheet.

For visual-first videos with little speech, increase `--frame-count`. For a
static talking-head video, reduce it and focus on slide or chapter transitions.

## Claim-evidence ledger

Build a compact ledger before writing the final artifact:

| Claim | Speech evidence | Visual evidence | Confidence | Caveat |
|---|---|---|---|---|
| Exact conclusion | timestamp + short paraphrase | frame path if relevant | high/medium/low | unresolved ambiguity |

Use paraphrases by default. Keep any direct quote short and attach its timestamp.
Every ranking, recommendation, number, or named item in the final answer must
map to at least one ledger row.

## Analysis quality gates

- Cover the full video, including counterexamples and late revisions.
- Distinguish what the creator explicitly says from the analyst's inference.
- Preserve context-dependent recommendations instead of flattening them into a
  false universal tier list.
- Mark captions, OCR, or visual identifications that remain uncertain.
- Include the source URL, video title/uploader, analysis date, caption type,
  and evidence bundle path.
- Make the final HTML or table usable without the raw transcript, while keeping
  timestamps and frame references for verification.

## Privacy and copyright

Keep downloaded media and transcripts local unless the user authorizes
publication. A report may summarize and quote brief excerpts, but should not
redistribute the video, full transcript, or a large collection of source frames.
