#!/usr/bin/env python3
"""
transcribe_any.py

Audio transcription using Google Gemini 3 Flash.
Supports files up to 500MB / ~8.4 hours with speaker diarization.

Examples:
  # Basic transcription
  python transcribe_any.py meeting.mp3 --out_txt transcript.txt

  # With speaker diarization
  python transcribe_any.py interview.m4a --diarize --out_txt transcript.txt

  # Specify language for better accuracy
  python transcribe_any.py podcast.mp3 --language zh --diarize

Env:
  GEMINI_API_KEY - Required (also checks nanobanana/.env)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Load .env files from script directory and nanobanana (for shared Gemini key)
script_dir = Path(__file__).parent
for env_file in [script_dir / ".env", script_dir.parent / "nanobanana" / ".env"]:
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def _die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def _info(msg: str) -> None:
    print(f"INFO: {msg}", file=sys.stderr)


def _get_file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def _get_audio_duration(path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return 0.0
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except:
        return 0.0


def _fmt_duration(seconds: float) -> str:
    """Human readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def _gemini_upload_file(client, audio_path: Path) -> Any:
    """Upload file to Gemini Files API."""
    _info(f"Uploading {audio_path.name} to Gemini Files API...")
    uploaded = client.files.upload(file=str(audio_path))

    # Wait for processing
    while uploaded.state.name == "PROCESSING":
        _info("Waiting for file processing...")
        time.sleep(2)
        uploaded = client.files.get(name=uploaded.name)

    if uploaded.state.name == "FAILED":
        _die(f"Gemini file processing failed: {uploaded.state}")

    _info(f"File uploaded: {uploaded.name}")
    return uploaded


def transcribe_gemini(
    audio_path: Path,
    model: str,
    language: Optional[str],
    diarize: bool,
) -> Tuple[str, Dict[str, Any]]:
    """Transcribe using Gemini API."""
    try:
        from google import genai
    except ImportError:
        _die("google-genai package not installed. Run: pip install google-genai")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        _die("GEMINI_API_KEY not set. Add it to .env or environment.")

    client = genai.Client(api_key=api_key)

    # Upload file
    uploaded_file = _gemini_upload_file(client, audio_path)

    # Build prompt - optimized for natural sentence boundaries
    if diarize:
        prompt = """请将这段音频转录成文字，并标注说话人。

要求：
1. 识别不同的说话人，用 SPEAKER_0、SPEAKER_1 等标签区分
2. 每段对话用时间戳标注，格式：[HH:MM:SS - HH:MM:SS] SPEAKER_X: 内容
3. **重要**：保持自然的句子边界，不要在句子中间断开
4. 使用正确的标点符号（句号、逗号、问号等）
5. 每个说话人的一段完整发言作为一个段落，不要把一句话拆成多行
6. 逐字转录，保留口语特点但使用正确标点

示例输出格式：
[00:00:20 - 00:00:45] SPEAKER_0: 大家好，欢迎收听本期节目。今天我们请到了一位特别的嘉宾，请先跟大家打个招呼。
[00:00:45 - 00:01:05] SPEAKER_1: 哈喽大家好，我叫张三，很高兴能参与这个节目的录制。
"""
    else:
        prompt = """请将这段音频逐字转录成文字。

要求：
1. 保持自然的句子边界，不要在句子中间断开
2. 使用正确的标点符号（句号、逗号、问号等）
3. 分段落输出，每个自然段落之间空一行
4. 保留口语特点但确保可读性
"""

    if language:
        lang_names = {
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
        }
        lang_name = lang_names.get(language, language)
        prompt += f"\n\n音频语言是{lang_name}，请用原语言转录。"

    _info(f"Transcribing with {model}...")

    response = client.models.generate_content(
        model=model,
        contents=[uploaded_file, prompt],
    )

    text = response.text.strip()

    # Build response dict
    resp_dict = {
        "provider": "gemini",
        "model": model,
        "text": text,
        "file_name": uploaded_file.name,
    }

    # Clean up uploaded file
    try:
        client.files.delete(name=uploaded_file.name)
        _info("Cleaned up uploaded file")
    except:
        pass

    return text, resp_dict


def main() -> None:
    p = argparse.ArgumentParser(
        description="Audio transcription using Gemini 3 Flash (up to 500MB / 8.4 hours)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported formats: MP3, WAV, M4A, MP4, OGG, FLAC, WebM, AAC

Examples:
  %(prog)s meeting.mp3 --out_txt transcript.txt
  %(prog)s interview.m4a --diarize --language zh
  %(prog)s podcast.mp3 --diarize --out_txt out.txt --out_json out.json
""")

    p.add_argument("audio", type=str, help="Path to audio file")
    p.add_argument(
        "--model",
        default="gemini-3-flash-preview",
        help="Gemini model to use (default: gemini-3-flash-preview)",
    )
    p.add_argument(
        "--diarize",
        action="store_true",
        help="Enable speaker diarization (identify different speakers)",
    )
    p.add_argument(
        "--language",
        default=None,
        help="ISO-639-1 language code (e.g., zh, en, ja). Auto-detect if not specified.",
    )
    p.add_argument(
        "--out_txt",
        type=str,
        default=None,
        help="Save transcript to text file",
    )
    p.add_argument(
        "--out_json",
        type=str,
        default=None,
        help="Save full API response to JSON file",
    )

    args = p.parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        _die(f"Audio file not found: {audio_path}")

    file_size_mb = _get_file_size_mb(audio_path)
    duration = _get_audio_duration(audio_path)

    _info(f"File: {audio_path.name}")
    _info(f"Size: {file_size_mb:.1f}MB, Duration: {_fmt_duration(duration)}")

    if file_size_mb > 500:
        _die(f"File too large ({file_size_mb:.1f}MB). Gemini limit is 500MB.")

    # Transcribe
    start_time = time.time()

    text, resp = transcribe_gemini(
        audio_path=audio_path,
        model=args.model,
        language=args.language,
        diarize=args.diarize,
    )

    elapsed = time.time() - start_time
    _info(f"Transcription completed in {elapsed:.1f}s")

    # Output
    if args.out_json:
        out_json_path = Path(args.out_json).expanduser().resolve()
        out_json_path.write_text(json.dumps(resp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _info(f"Saved JSON to {out_json_path}")

    if args.out_txt:
        out_txt_path = Path(args.out_txt).expanduser().resolve()
        out_txt_path.write_text(text + "\n", encoding="utf-8")
        _info(f"Saved transcript to {out_txt_path}")

    # Print to stdout
    print(text)


if __name__ == "__main__":
    main()
