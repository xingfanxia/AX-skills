# transcribe

> Audio / video transcription. Default engine **妙记 (Volcano Lark Minutes ASR)** for best speaker diarization (single-call, server-side); **Gemini 3.5 Flash** / **OpenAI gpt-4o-transcribe-diarize** as fallbacks. Auto language detection, code-switching, files up to ~8.4 hours.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Single-file CLI wrapper for transcription. The default 妙记 provider does server-side diarization in one call — verified across 5 real recordings (2026-06-17) to return the exact speaker count on every 2-person conversation, where chunk-stitched Gemini/OpenAI and the raw Doubao auc models all over-counted. Gemini/OpenAI fallbacks auto-chunk long audio at silence boundaries and transcribe in parallel.

## When to use

- "Transcribe this audio"
- "Convert this meeting recording to text"
- "I have an interview MP3 — give me the transcript"

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/transcribe ~/.claude/skills/transcribe

# System dep — required for audio conversion + chunking
brew install ffmpeg                   # macOS  (or: apt install ffmpeg)

# venv + deps
cd ~/AX-skills/transcribe
python3 -m venv venv
./venv/bin/pip install tos requests          # 妙记 (default)
./venv/bin/pip install google-genai openai   # optional — Gemini/OpenAI fallbacks

# Credentials in .env (gitignored, never committed):
#   妙记 (default): VOLC_API_KEY + VOLC_TOS_ACCESS_KEY/SECRET_KEY/BUCKET/REGION/ENDPOINT
#   fallbacks:      GEMINI_API_KEY, OPENAI_API_KEY
```

`.env` is gitignored — never committed. 妙记 hosts the audio in Volcano TOS (a small 16kHz-mono mp3, deleted after) so the API can fetch it via a presigned URL.

## Usage

```bash
# Default 妙记 — pass the speaker count if known (0 = auto-detect)
~/AX-skills/transcribe/venv/bin/python ~/AX-skills/transcribe/transcribe_any.py meeting.m4a --speakers 2 --out_txt transcript.txt

# 妙记 auto speaker detection
~/AX-skills/transcribe/venv/bin/python ~/AX-skills/transcribe/transcribe_any.py interview.m4a --out_txt transcript.txt

# Fallbacks
... transcribe_any.py audio.mp3 --provider gemini --diarize --out_txt transcript.txt
... transcribe_any.py audio.mp3 --provider openai --out_txt transcript.txt
```

妙记 transcribes in one call (~100–150s for a 30–60 min file; handled a 3.45h file in one pass). Gemini/OpenAI fallbacks auto-chunk files >15 min at silence boundaries and run chunks in parallel.

See [SKILL.md](./SKILL.md) for full CLI options, env var tunables, and provider-choice rationale.
