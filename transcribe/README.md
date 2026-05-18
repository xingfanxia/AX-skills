# transcribe

> Audio / video transcription via Google Gemini 3 Flash (default) or OpenAI gpt-4o-transcribe-diarize. Speaker diarization, auto language detection, files up to 500MB / ~8.4 hours. **Silence-aware chunking + parallel transcription** for long audio.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Single-file CLI wrapper for transcription. Handles long-form audio (interviews, podcasts, meetings) by auto-chunking at silence boundaries with `ffmpeg` and transcribing chunks in parallel — sidesteps Gemini 3 Flash's loop-on-long-audio failure mode.

## When to use

- "Transcribe this audio"
- "Convert this meeting recording to text"
- "I have an interview MP3 — give me the transcript"

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/transcribe ~/.claude/skills/transcribe

# System dep — required for silence-aware chunking of long audio
brew install ffmpeg                   # macOS
# or: apt install ffmpeg              # Debian/Ubuntu

# Set up venv + API key
cd ~/AX-skills/transcribe
python3 -m venv venv
./venv/bin/pip install google-genai openai   # openai is optional, only for --provider openai
echo 'GEMINI_API_KEY=your_key_here' > .env   # get key at https://aistudio.google.com/apikey
# Optional for --provider openai:
# echo 'OPENAI_API_KEY=sk-...' >> .env
```

`.env` is gitignored — never committed.

## Usage

```bash
# Basic — Gemini, no speaker labels
~/AX-skills/transcribe/venv/bin/python ~/AX-skills/transcribe/transcribe_any.py audio.mp3 --out_txt transcript.txt

# With speaker labels
~/AX-skills/transcribe/venv/bin/python ~/AX-skills/transcribe/transcribe_any.py meeting.m4a --diarize --out_txt transcript.txt

# Use OpenAI (gpt-4o-transcribe-diarize — speaker labels always on)
~/AX-skills/transcribe/venv/bin/python ~/AX-skills/transcribe/transcribe_any.py meeting.m4a --provider openai --out_txt transcript.txt
```

Long files (>15 min) are auto-chunked at silence boundaries with `ffmpeg silencedetect` and transcribed in parallel (default 8 concurrent). 2-hour file → ~37 sec on Gemini.

See [SKILL.md](./SKILL.md) for full CLI options, env var tunables, and provider-choice rationale.
