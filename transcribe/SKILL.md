---
name: transcribe
description: This skill should be used when the user wants to "transcribe audio", "transcribe video", "speech to text", "convert audio to text", "transcription", or needs to extract text from audio/video files. Default engine is 妙记 (Volcano Lark Minutes ASR) for best speaker diarization; Gemini/OpenAI available as fallbacks. Supports files up to ~8.4 hours with speaker diarization.
---

# Audio Transcription Skill (妙记 / Gemini / OpenAI)

## Overview

Transcribe audio and video files. Three providers, default **妙记 (Volcano Lark Minutes ASR, `volc.lark.minutes`)**:

| Provider | When | Diarization |
|---|---|---|
| **`lark`** (默认 妙记) | Default — best speaker accuracy, single call | Server-side, most accurate |
| `gemini` | Fallback — no Volcano creds, or non-diarized notes | Chunk-stitched + Senko/pyannote |
| `openai` | Fallback — granular turn detection | gpt-4o-transcribe-diarize |

**Why 妙记 is the default:** verified across 5 real recordings (2026-06-17), 妙记 returned the exact speaker count on every 2-person conversation (2/2/2/2) while Gemini-chunk-stitch, OpenAI, and the raw Doubao auc models all over-counted (3–5 speakers). 妙记 does server-side diarization in a **single call** (no chunking, no cross-chunk speaker reconcile) and handled a 3.45-hour file in one pass.

## ⚠️ Ask the user how many speakers (for `lark`)

Before transcribing with 妙记, **ask the user how many speakers are in the audio** if it isn't obvious. Pass it via `--speakers N`. Use `--speakers 0` (auto-detect) only when the count is unknown — auto is good but a known count improves accuracy. Example prompt: *"How many people are speaking in this recording? (I'll auto-detect if you're not sure.)"*

## Capabilities

- **Speaker diarization**: `SPEAKER_1`, `SPEAKER_2`, … (妙记 server-side; best accuracy)
- **Audio length**: single-call up to several hours (妙记 handled 3.45h); Gemini/OpenAI auto-chunk
- **Auto language detection** + **code-switching**: Chinese + English mixed handled cleanly
- **Formats**: MP3, WAV, M4A, MP4, OGG, FLAC, WebM, AAC (auto-converted to 16kHz mono mp3 before upload)

## Setup (one-time)

```bash
cd <skill-dir>           # e.g. ~/.claude/plugins/transcribe
python3 -m venv venv
./venv/bin/pip install tos requests          # 妙记 (default): TOS hosting + API
./venv/bin/pip install google-genai openai   # optional, for --provider gemini/openai
brew install ffmpeg                           # required (audio conversion + chunking)

# Credentials in the skill's .env (gitignored):
#   妙记 (default):
echo 'VOLC_API_KEY=...'           >> .env     # 妙记 x-api-key
echo 'VOLC_TOS_ACCESS_KEY=...'    >> .env     # Volcano TOS (hosts audio for 妙记 to fetch)
echo 'VOLC_TOS_SECRET_KEY=...'    >> .env
echo 'VOLC_TOS_BUCKET=...'        >> .env
echo 'VOLC_TOS_REGION=...'        >> .env     # e.g. cn-shanghai
echo 'VOLC_TOS_ENDPOINT=...'      >> .env     # e.g. tos-cn-shanghai.volces.com
#   fallbacks (optional):
echo 'GEMINI_API_KEY=...'         >> .env
echo 'OPENAI_API_KEY=...'         >> .env
```

How 妙记 hosting works: the skill converts the audio to a small 16kHz-mono mp3, uploads it to Volcano TOS, hands 妙记 a presigned URL, then deletes the object after transcription. 妙记 fetches from TOS intra-China (fast); the only cross-border leg is the upload, minimized by compression + parallel multipart.

## Quick Start

```bash
# Default 妙记 — ask the user for speaker count first
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py meeting.m4a --speakers 2 --out_txt transcript.txt

# 妙记 auto speaker detection (count unknown)
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py interview.m4a --out_txt transcript.txt

# Fallback providers
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py audio.mp3 --provider gemini --diarize --out_txt transcript.txt
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py audio.mp3 --provider openai --out_txt transcript.txt
```

> Replace `<skill-dir>` with the absolute path where the skill is installed.

## Workflow

### 1. Ask about speaker count (for default 妙记)
If the speaker count isn't obvious, ask the user. Pass `--speakers N` (or omit / `0` for auto).

### 2. Determine output file path
**ALWAYS save the transcript to a file.** Replace the audio extension with `_transcript.txt`:
- `/path/to/meeting.m4a` → `/path/to/meeting_transcript.txt`

### 3. Run transcription
```bash
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py "/path/audio.m4a" --speakers N --out_txt "/path/audio_transcript.txt"
```

## CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--provider` | `lark` (妙记), `gemini`, or `openai` | `lark` |
| `--speakers` | Expected speaker count for `lark` (0 = auto) | `0` |
| `--model` | Gemini model (ignored for `lark`/`openai`) | `gemini-3.5-flash` |
| `--diarize` | Speaker ID for `gemini` (implied for `lark`/`openai`) | False |
| `--language` | ISO-639-1 code (zh, en, ja) for gemini/openai | Auto-detect |
| `--out_txt` | Save transcript to text file | None |
| `--out_json` | Save full response to JSON | None |

## Tunable Env Vars

| Env Var | Description | Default |
|---|---|---|
| `VOLC_API_KEY`, `VOLC_TOS_*` | 妙记 + TOS credentials (required for `lark`) | — |
| `LARK_MP3_BITRATE` | mp3 bitrate for upload (lower = faster upload) | `32k` |
| `LARK_SOURCE_LANG` | 妙记 source language | `zh_cn` |
| `LARK_UPLOAD_TASKS` | Parallel multipart upload connections | `8` |
| `CHUNK_*`, `CHUNK_PARALLELISM` | Gemini/OpenAI chunking knobs | see code |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | Fallback providers | — |

## Output Example

```
[00:00:20 - 00:00:45] SPEAKER_1: 欢迎收听本期节目。
[00:00:45 - 00:01:05] SPEAKER_2: Thanks for having me.
```

## Fallback Providers (gemini / openai)

Both auto-split long audio at silence boundaries (ffmpeg `silencedetect`) and transcribe chunks in parallel, then reconcile speaker labels across chunks. This was the original engine before 妙记; use it when Volcano creds aren't available.

- **gemini** (default fallback): Gemini 3 Flash loops/fabricates timestamps on single-call audio > ~15 min, so chunking is what makes it usable. Good punctuation + code-switching; diarization is chunk-stitched (less accurate than 妙记).
- **openai** `gpt-4o-transcribe-diarize`: always diarized, granular turn detection; sometimes runs sentences together and mis-handles Chinese fillers.

## Troubleshooting

- **`妙记 provider unavailable` / missing creds:** ensure `tos requests` are installed in the venv and `VOLC_API_KEY` + `VOLC_TOS_*` are in `.env`. Fall back with `--provider gemini`.
- **Slow upload:** cross-border upload to a China TOS region can throttle; the skill compresses + uses parallel multipart. Lower `LARK_MP3_BITRATE` (e.g. `16k`) to shrink the upload further.
- **Unicode filename error:** `cp "中文名.m4a" /tmp/audio.m4a` then transcribe the copy.
- **ffmpeg not found:** required for audio conversion. `brew install ffmpeg`.

## Notes

- 妙记 wall time: ~100–150s for a 30–60 min file (single call); the 3.45h test ran in one pass.
- Gemini API cost: ~$0.20 for a 2-hour file. OpenAI: ~$0.90 for a 2-hour file.
