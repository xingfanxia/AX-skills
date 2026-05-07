---
name: transcribe
description: This skill should be used when the user wants to "transcribe audio", "transcribe video", "speech to text", "convert audio to text", "transcription", or needs to extract text from audio/video files. Supports files up to 500MB / ~8.4 hours with speaker diarization.
---

# Audio Transcription Skill (Gemini)

## Overview

Transcribe audio and video files using Gemini 3 Flash. Supports speaker diarization, auto language detection, and files up to 500MB (~8.4 hours).

## Capabilities

- **File size**: Up to 500MB
- **Audio length**: Up to ~8.4 hours
- **Speaker diarization**: Identifies different speakers
- **Auto language detection**: Works with any language
- **Formats**: MP3, WAV, M4A, MP4, OGG, FLAC, WebM, AAC

## Setup (one-time)

```bash
# Install in a venv next to the script
cd <skill-dir>           # e.g. ~/.claude/skills/transcribe (a symlink to AX-skills/transcribe)
python3 -m venv venv
./venv/bin/pip install google-genai

# Set API key (Google AI Studio → https://aistudio.google.com/apikey)
echo 'GEMINI_API_KEY=your_key_here' > .env
```

## Quick Start

```bash
# Basic transcription (always save to file)
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py audio.mp3 --out_txt transcript.txt

# With speaker diarization (recommended for interviews/podcasts)
<skill-dir>/venv/bin/python <skill-dir>/transcribe_any.py meeting.m4a --diarize --out_txt transcript.txt
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
| `--model` | Gemini model | gemini-3-flash-preview |
| `--diarize` | Enable speaker identification | False |
| `--language` | ISO-639-1 code (zh, en, ja, es) | Auto-detect |
| `--out_txt` | Save transcript to text file | None |
| `--out_json` | Save full response to JSON | None |

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

## Troubleshooting

**Unicode filename error:**
```bash
cp "中文文件名.m4a" /tmp/audio.m4a
# Then transcribe /tmp/audio.m4a
```

**Missing API key:**
Set `GEMINI_API_KEY` in the skill's `.env` file (see Setup above).

## Notes

- API cost: ~$0.50/M input tokens
- Long files (>2 hours) may take 5-10 minutes to process
