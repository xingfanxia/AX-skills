---
name: transcribe
description: This skill should be used when the user wants to "transcribe audio", "transcribe video", "speech to text", "convert audio to text", "transcription", or needs to extract text from audio/video files. Supports files up to 500MB / ~8.4 hours with speaker diarization. Auto-chunks long audio at silence boundaries and runs chunks in parallel.
---

# Audio Transcription Skill (Gemini + OpenAI)

## Overview

Transcribe audio and video files using **Gemini 3 Flash** (default — better quality + cost) or **OpenAI `gpt-4o-transcribe-diarize`** (alternative).

**Why it's robust on long audio:** Gemini 3 Flash in a single call loops and fabricates timestamps on audio longer than ~15 minutes. This skill auto-splits long audio at silence boundaries (ffmpeg `silencedetect`) and transcribes chunks in parallel — each chunk stays in the model's coherent range and won't cut mid-sentence.

## Capabilities

- **File size**: Up to 500MB (Gemini); OpenAI is 25MB per request — auto-chunks under that
- **Audio length**: Up to ~8.4 hours
- **Speaker diarization**: Identifies different speakers (`SPEAKER_0`, `SPEAKER_1`, …)
- **Auto language detection**: Works with any language
- **Code-switching**: Preserves Chinese + English mixed audio correctly
- **Long-audio coherence**: Silence-aware chunking + parallel transcription (default 8 concurrent)
- **Formats**: MP3, WAV, M4A, MP4, OGG, FLAC, WebM, AAC

## Setup (one-time)

```bash
# Install in a venv next to the script
cd <skill-dir>           # e.g. ~/.claude/skills/transcribe (a symlink to AX-skills/transcribe)
python3 -m venv venv
./venv/bin/pip install google-genai openai   # openai is optional, only needed for --provider openai

# Install ffmpeg for silence-aware chunking (required for audio > 15 min)
brew install ffmpeg      # macOS
# or: apt install ffmpeg

# Set API keys (Google AI Studio → https://aistudio.google.com/apikey)
echo 'GEMINI_API_KEY=your_key_here' > .env
# Optional:
echo 'OPENAI_API_KEY=your_openai_key' >> .env
```

## Quick Start

```bash
# Basic transcription (always save to file)
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py audio.mp3 --out_txt transcript.txt

# With speaker diarization (recommended for interviews/podcasts)
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py meeting.m4a --diarize --out_txt transcript.txt

# Use OpenAI (auto-uses gpt-4o-transcribe-diarize — speaker labels always on)
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py meeting.m4a --provider openai --out_txt transcript.txt
```

> Replace `<skill-dir>` with the absolute path where you installed the skill.

## Workflow

### 1. Determine Output File Path

**ALWAYS save the transcript to a file.** Generate the output path by replacing the audio file extension with `_transcript.txt`:
- Input: `/path/to/audio.mp3` → Output: `/path/to/audio_transcript.txt`
- Input: `/path/to/meeting.m4a` → Output: `/path/to/meeting_transcript.txt`

### 2. Run Transcription

```bash
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py "/path/to/audio.mp3" --out_txt "/path/to/audio_transcript.txt"
```

### 3. Optional: Ask About Diarization

For interviews or multi-speaker content, consider asking if the user wants speaker identification (`--diarize`).

## CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--provider` | `gemini` or `openai` | `gemini` |
| `--model` | Gemini model (ignored for `--provider openai`) | `gemini-3.5-flash` |
| `--diarize` | Enable speaker identification (implied for OpenAI) | False |
| `--language` | ISO-639-1 code (zh, en, ja, es) | Auto-detect |
| `--out_txt` | Save transcript to text file | None |
| `--out_json` | Save full response to JSON | None |

## Tunable Env Vars

| Env Var | Description | Default |
|---|---|---|
| `CHUNK_THRESHOLD_SEC` | Only chunk if audio > this many sec | `900` (15 min) |
| `CHUNK_TARGET_SEC` | Aim for chunks of this length | `480` (8 min) |
| `CHUNK_MIN_SEC` | Min chunk size when picking silence boundary | `300` (5 min) |
| `CHUNK_MAX_SEC` | Max chunk size when picking silence boundary | `720` (12 min) |
| `CHUNK_PARALLELISM` | Concurrent API calls per file | `8` |
| `GEMINI_API_KEY` | Required for `--provider gemini` | — |
| `OPENAI_API_KEY` | Required for `--provider openai` | — |

## Output Examples

**With diarization:**
```
[00:00:20 - 00:00:45] SPEAKER_0: Welcome to today's episode...
[00:00:45 - 00:01:05] SPEAKER_1: Thanks for having me...
```

**Without diarization:**
```
Welcome to today's episode. We have a special guest...
Thanks for having me. I'm excited to be here...
```

## Provider Choice

**Default to `gemini`.** Side-by-side testing on a 2-hour Chinese+English conversation showed Gemini produces:
- Proper punctuation (OpenAI runs sentences together)
- Correct code-switching (`ROI` stays as `ROI`; OpenAI mis-transcribed it as `RY`)
- Cleaner diarization (OpenAI sometimes attributes both sides of a Q&A to the same speaker)
- No hallucinated English from Chinese filler particles (OpenAI emitted `"She is she."` from a Chinese 嗯/是)

OpenAI's main advantage: more granular turn detection (catches every interjection). Useful for podcast-style transcripts where every "yeah/嗯" matters; less useful for note-taking.

## Troubleshooting

**Unicode filename error:**
```bash
cp "中文文件名.m4a" /tmp/audio.m4a
# Then transcribe /tmp/audio.m4a
```

**Missing API key:**
Set `GEMINI_API_KEY` in the skill's `.env` file (or `OPENAI_API_KEY` for `--provider openai`).

**ffmpeg not found:**
Long-audio chunking requires `ffmpeg`. Install via `brew install ffmpeg`. Without it, the skill falls back to a single transcription call — which may loop on Gemini for audio > 15 min.

## Notes

- Gemini API cost: ~$0.50/M input tokens (~$0.20 for a 2-hour file)
- OpenAI gpt-4o-transcribe-diarize: $0.0075/min (~$0.90 for a 2-hour file)
- Wall time on a 2-hour file: ~37 sec with Gemini (8 parallel chunks) vs ~3 min with OpenAI
