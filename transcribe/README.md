# transcribe

> Audio / video transcription via Google Gemini 3 Flash. Speaker diarization, auto language detection, files up to 500MB / ~8.4 hours.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Single-file CLI wrapper around the Gemini API for transcription. Cheap (~$0.50/M input tokens), supports any language Gemini supports, and handles long-form audio (interviews, podcasts, meetings).

## When to use

- "Transcribe this audio"
- "Convert this meeting recording to text"
- "I have an interview MP3 — give me the transcript"

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/transcribe ~/.claude/skills/transcribe

# Set up venv + API key
cd ~/AX-skills/transcribe
python3 -m venv venv
./venv/bin/pip install google-genai
echo 'GEMINI_API_KEY=your_key_here' > .env  # get key at https://aistudio.google.com/apikey
```

`.env` is gitignored — never committed.

## Usage

```bash
~/AX-skills/transcribe/venv/bin/python ~/AX-skills/transcribe/transcribe_any.py audio.mp3 --out_txt transcript.txt

# With speaker labels
~/AX-skills/transcribe/venv/bin/python ~/AX-skills/transcribe/transcribe_any.py meeting.m4a --diarize --out_txt transcript.txt
```

See [SKILL.md](./SKILL.md) for full CLI options and output format.
