#!/usr/bin/env python3
"""
transcribe_any.py

Audio transcription using Google Gemini 3 Flash (default) or OpenAI
gpt-4o-transcribe-diarize. For long audio (>15min) the audio is split at
silence boundaries with ffmpeg silencedetect and each chunk is transcribed
in parallel — preserves coherence (no loops, no fabricated timestamps,
which Gemini 3 Flash exhibits on long single-call audio).

Examples:
  # Basic transcription
  python transcribe_any.py meeting.mp3 --out_txt transcript.txt

  # With speaker diarization
  python transcribe_any.py interview.m4a --diarize --out_txt transcript.txt

  # Specify language for better accuracy
  python transcribe_any.py podcast.mp3 --language zh --diarize

  # Use OpenAI (must have OPENAI_API_KEY; auto-uses diarize variant)
  python transcribe_any.py meeting.m4a --provider openai --out_txt out.txt

  # Tune chunking
  CHUNK_TARGET_SEC=600 CHUNK_PARALLELISM=4 python transcribe_any.py long.m4a --diarize

Env:
  GEMINI_API_KEY        Required for --provider gemini (also checks nanobanana/.env)
  OPENAI_API_KEY        Required for --provider openai
  CHUNK_THRESHOLD_SEC   Only chunk if audio > this many seconds (default 900 = 15min)
  CHUNK_TARGET_SEC      Aim for chunks this long (default 480 = 8min)
  CHUNK_MIN_SEC         Min chunk size (default 300 = 5min)
  CHUNK_MAX_SEC         Max chunk size (default 720 = 12min)
  CHUNK_PARALLELISM     Concurrent API calls per file (default 8)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Load .env files from script directory and nanobanana (for shared Gemini key)
script_dir = Path(__file__).parent
for env_file in [script_dir / ".env", script_dir.parent / "nanobanana" / ".env"]:
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


CHUNK_THRESHOLD_SEC = int(os.environ.get("CHUNK_THRESHOLD_SEC", "900"))
CHUNK_TARGET_SEC = int(os.environ.get("CHUNK_TARGET_SEC", "480"))
CHUNK_MIN_SEC = int(os.environ.get("CHUNK_MIN_SEC", "300"))
CHUNK_MAX_SEC = int(os.environ.get("CHUNK_MAX_SEC", "720"))
CHUNK_PARALLELISM = int(os.environ.get("CHUNK_PARALLELISM", "8"))


def _die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def _info(msg: str) -> None:
    print(f"INFO: {msg}", file=sys.stderr)


def _get_file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def _get_audio_duration(path: Path) -> float:
    """Get audio duration in seconds using ffprobe. Returns 0.0 if unavailable."""
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
    except Exception:
        return 0.0


def _fmt_duration(seconds: float) -> str:
    """Human readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def _fmt_ts(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def _parse_ts(ts: str) -> int:
    parts = ts.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


# Lenient enough to catch single-digit timestamp components (e.g., "00:1:04")
# that the model sometimes emits despite the prompt asking for HH:MM:SS.
_TIMESTAMP_RE = re.compile(r"\[(\d{1,2}:\d{1,2}:\d{1,2})\s*-\s*(\d{1,2}:\d{1,2}:\d{1,2})\]")


def _offset_timestamps(transcript: str, offset_sec: float) -> str:
    """Shift every `[HH:MM:SS - HH:MM:SS]` (or shorter variant) timestamp by offset_sec."""

    def replace(m):
        start = _parse_ts(m.group(1)) + offset_sec
        end = _parse_ts(m.group(2)) + offset_sec
        return f"[{_fmt_ts(start)} - {_fmt_ts(end)}]"

    return _TIMESTAMP_RE.sub(replace, transcript)


# ---------------------------------------------------------------------------
# Audio chunking (silence-aware) — shared by both providers
# ---------------------------------------------------------------------------

def _detect_silence(audio_path: Path, noise_db: int = -30, min_duration: float = 0.5) -> List[Tuple[float, float]]:
    """Run ffmpeg silencedetect; return list of (start_sec, end_sec)."""
    if not shutil.which("ffmpeg"):
        return []
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-i", str(audio_path),
                "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
                "-f", "null", "-",
            ],
            capture_output=True, text=True, timeout=180,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    intervals: List[Tuple[float, float]] = []
    pending_start: Optional[float] = None
    for line in result.stderr.splitlines():
        if "silence_start:" in line:
            try:
                pending_start = float(line.split("silence_start:")[1].strip())
            except (ValueError, IndexError):
                pending_start = None
        elif "silence_end:" in line and pending_start is not None:
            try:
                end_part = line.split("silence_end:")[1].split("|")[0].strip()
                intervals.append((pending_start, float(end_part)))
            except (ValueError, IndexError):
                pass
            pending_start = None
    return intervals


def _pick_split_points(total_sec: float, silences: List[Tuple[float, float]]) -> List[float]:
    """Pick split timestamps near each CHUNK_TARGET_SEC boundary,
    preferring a silence midpoint within [CHUNK_MIN_SEC, CHUNK_MAX_SEC] of
    the previous split. Falls back to hard split if no silence in window.
    """
    splits = [0.0]
    current = 0.0
    while current + CHUNK_MAX_SEC < total_sec:
        target = current + CHUNK_TARGET_SEC
        best: Optional[float] = None
        for s, e in silences:
            mid = (s + e) / 2
            if current + CHUNK_MIN_SEC <= mid <= current + CHUNK_MAX_SEC:
                if best is None or abs(mid - target) < abs(best - target):
                    best = mid
        if best is None:
            best = target
        splits.append(best)
        current = best
    splits.append(total_sec)
    return splits


def _chunk_audio_at_silence(audio_path: Path) -> Tuple[List[Tuple[Path, float, float]], Any]:
    """Split audio into chunks at silence near each target boundary.

    Returns (chunks, cleanup_fn) where chunks = list of (chunk_path, start_offset, duration).
    Caller MUST invoke cleanup_fn() when done to remove temp files.
    """
    total = _get_audio_duration(audio_path)
    if total <= 0 or total <= CHUNK_THRESHOLD_SEC:
        return [(audio_path, 0.0, total)], lambda: None

    if not shutil.which("ffmpeg"):
        _info("ffmpeg not found — falling back to single-chunk transcription (may degrade on long audio)")
        return [(audio_path, 0.0, total)], lambda: None

    silences = _detect_silence(audio_path)
    splits = _pick_split_points(total, silences)

    tmp_dir = Path(tempfile.mkdtemp(prefix="transcribe_chunk_"))
    chunks: List[Tuple[Path, float, float]] = []
    for i in range(len(splits) - 1):
        start, end = splits[i], splits[i + 1]
        chunk_path = tmp_dir / f"chunk_{i:02d}{audio_path.suffix}"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", str(start), "-to", str(end),
                    "-i", str(audio_path),
                    "-c", "copy",
                    str(chunk_path),
                ],
                check=True, timeout=180,
            )
            chunks.append((chunk_path, start, end - start))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            _info(f"failed to extract chunk {i} ({start:.0f}-{end:.0f}s): {e}")

    def cleanup():
        for cp, _, _ in chunks:
            try:
                cp.unlink(missing_ok=True)
            except Exception:
                pass
        try:
            tmp_dir.rmdir()
        except Exception:
            pass

    return chunks, cleanup


# ---------------------------------------------------------------------------
# Provider: Gemini
# ---------------------------------------------------------------------------

def _gemini_upload(client, audio_path: Path):
    uploaded = client.files.upload(file=str(audio_path))
    while uploaded.state.name == "PROCESSING":
        time.sleep(2)
        uploaded = client.files.get(name=uploaded.name)
    if uploaded.state.name == "FAILED":
        _die(f"Gemini file processing failed: {uploaded.state}")
    return uploaded


def _gemini_transcribe_one(client, audio_path: Path, model: str, prompt: str) -> str:
    """Single Gemini call on one chunk. Returns plain text."""
    uploaded = _gemini_upload(client, audio_path)
    resp = client.models.generate_content(
        model=model,
        contents=[uploaded, prompt],
        config={
            # Gemini 3 thinking models share max_output_tokens between thinking
            # + actual output. For transcription (perceptual, not reasoning),
            # thinking_level=minimal lets the full budget go to the transcript.
            "thinking_config": {"thinking_level": "minimal"},
            "max_output_tokens": 65536,
        },
    )
    text = (resp.text or "").strip()
    try:
        finish = resp.candidates[0].finish_reason
        if finish and str(finish).upper().endswith("MAX_TOKENS"):
            _info(f"chunk may be truncated (finish_reason={finish})")
    except (AttributeError, IndexError, TypeError):
        pass
    try:
        client.files.delete(name=uploaded.name)
    except Exception:
        pass
    return text


def transcribe_gemini(
    audio_path: Path,
    model: str,
    language: Optional[str],
    diarize: bool,
) -> Tuple[str, Dict[str, Any]]:
    """Transcribe via Gemini, chunking long audio at silence boundaries.

    Chunks run in parallel up to CHUNK_PARALLELISM workers; output is
    reassembled in chunk order with per-chunk timestamps offset to absolute time.
    """
    try:
        from google import genai
    except ImportError:
        _die("google-genai not installed. Run: pip install google-genai")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        _die("GEMINI_API_KEY not set. Add it to .env or environment.")

    client = genai.Client(api_key=api_key)

    # Build prompt
    if diarize:
        prompt = """请将这段音频转录成文字，并标注说话人。

要求：
1. 识别不同的说话人，用 SPEAKER_0、SPEAKER_1 等标签区分
2. 每段对话用时间戳标注，格式：[HH:MM:SS - HH:MM:SS] SPEAKER_X: 内容
3. **重要**：保持自然的句子边界，不要在句子中间断开
4. 使用正确的标点符号（句号、逗号、问号等）
5. 每个说话人的一段完整发言作为一个段落，不要把一句话拆成多行
6. 逐字转录，保留口语特点但使用正确标点
7. **保持源语言**：中文部分用中文，英文部分用英文，不要翻译

示例输出格式：
[00:00:20 - 00:00:45] SPEAKER_0: 大家好，欢迎收听本期节目。
[00:00:45 - 00:01:05] SPEAKER_1: Hello, my name is Zhang San.
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
            "zh": "中文", "en": "English", "ja": "日本語", "ko": "한국어",
            "es": "Español", "fr": "Français", "de": "Deutsch",
        }
        prompt += f"\n\n音频语言是{lang_names.get(language, language)}，请用原语言转录。"

    chunks, cleanup = _chunk_audio_at_silence(audio_path)
    try:
        if len(chunks) == 1:
            _info(f"Transcribing with {model} (single call, {_fmt_duration(chunks[0][2])})")
            text = _gemini_transcribe_one(client, chunks[0][0], model, prompt)
        else:
            n = len(chunks)
            workers = min(CHUNK_PARALLELISM, n)
            _info(f"Transcribing with {model} in {n} chunks (silence-aware, {workers} parallel)")

            def run(idx_chunk):
                i, (chunk_path, offset, chunk_dur) = idx_chunk
                _info(f"chunk {i+1}/{n} START: {_fmt_ts(offset)} → {_fmt_ts(offset + chunk_dur)} ({chunk_dur:.0f}s)")
                t0 = time.time()
                chunk_text = _gemini_transcribe_one(client, chunk_path, model, prompt)
                _info(f"chunk {i+1}/{n} DONE  ({time.time()-t0:.0f}s, {len(chunk_text)} chars)")
                return i, (_offset_timestamps(chunk_text, offset) if diarize else chunk_text)

            results: List[Optional[str]] = [None] * n
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for i, t in pool.map(run, enumerate(chunks)):
                    results[i] = t
            text = "\n\n".join(t for t in results if t)
    finally:
        cleanup()

    return text, {
        "provider": "gemini",
        "model": model,
        "chunks": len(chunks),
        "text": text,
    }


# ---------------------------------------------------------------------------
# Provider: OpenAI gpt-4o-transcribe-diarize
# ---------------------------------------------------------------------------

def transcribe_openai(
    audio_path: Path,
    language: Optional[str],
    diarize: bool,
) -> Tuple[str, Dict[str, Any]]:
    """Transcribe via OpenAI's gpt-4o-transcribe-diarize.

    NOTE: gpt-4o-transcribe-diarize ALWAYS produces diarized segments; the
    --diarize flag is implied. For non-diarized text, post-strip the speaker
    labels yourself.

    Side-by-side testing on a 2-hour Chinese conversation showed Gemini
    produces more faithful output (proper punctuation, correct code-switching
    for terms like "ROI", no English hallucinations from Chinese fillers).
    Gemini is the recommended default.
    """
    try:
        from openai import OpenAI
    except ImportError:
        _die("openai package not installed. Run: pip install openai")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        _die("OPENAI_API_KEY not set.")

    client = OpenAI(api_key=api_key)

    # OpenAI per-request limits are 25MB / 1500s — chunk long audio.
    chunks, cleanup = _chunk_audio_at_silence(audio_path)
    try:
        n = len(chunks)
        workers = min(CHUNK_PARALLELISM, n)
        if n == 1:
            _info("Transcribing with gpt-4o-transcribe-diarize (single chunk)")
        else:
            _info(f"Transcribing with gpt-4o-transcribe-diarize in {n} chunks ({workers} parallel)")

        def run(idx_chunk):
            i, (chunk_path, offset, chunk_dur) = idx_chunk
            _info(f"chunk {i+1}/{n} START: {_fmt_ts(offset)} → {_fmt_ts(offset + chunk_dur)} ({chunk_dur:.0f}s)")
            t0 = time.time()
            kwargs = {
                "model": "gpt-4o-transcribe-diarize",
                "file": open(chunk_path, "rb"),
                "response_format": "diarized_json",
                "chunking_strategy": "auto",
            }
            if language:
                kwargs["language"] = language
            try:
                resp = client.audio.transcriptions.create(**kwargs)
            finally:
                kwargs["file"].close()
            lines = []
            for seg in getattr(resp, "segments", []) or []:
                start = float(getattr(seg, "start", 0.0)) + offset
                end = float(getattr(seg, "end", 0.0)) + offset
                speaker = getattr(seg, "speaker", None) or "SPEAKER"
                text = (getattr(seg, "text", "") or "").strip()
                if not text:
                    continue
                if diarize:
                    lines.append(f"[{_fmt_ts(start)} - {_fmt_ts(end)}] {speaker}: {text}")
                else:
                    lines.append(text)
            _info(f"chunk {i+1}/{n} DONE  ({time.time()-t0:.0f}s, {len(lines)} segments)")
            return i, "\n".join(lines)

        results: List[Optional[str]] = [None] * n
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for i, t in pool.map(run, enumerate(chunks)):
                results[i] = t
        text = "\n".join(t for t in results if t)
    finally:
        cleanup()

    return text, {
        "provider": "openai",
        "model": "gpt-4o-transcribe-diarize",
        "chunks": len(chunks),
        "text": text,
    }


# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description="Audio transcription with Gemini 3 Flash or OpenAI gpt-4o-transcribe-diarize. Auto-chunks long audio at silence boundaries; chunks run in parallel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported formats: MP3, WAV, M4A, MP4, OGG, FLAC, WebM, AAC

Examples:
  %(prog)s meeting.mp3 --out_txt transcript.txt
  %(prog)s interview.m4a --diarize --language zh
  %(prog)s podcast.mp3 --diarize --provider openai
  CHUNK_TARGET_SEC=600 %(prog)s long.m4a --diarize     # tune chunking
""")

    p.add_argument("audio", type=str, help="Path to audio file")
    p.add_argument(
        "--provider",
        choices=["gemini", "openai"],
        default="gemini",
        help="STT provider (default: gemini — recommended for quality + cost)",
    )
    p.add_argument(
        "--model",
        default="gemini-3-flash-preview",
        help="Gemini model (ignored for --provider openai)",
    )
    p.add_argument(
        "--diarize",
        action="store_true",
        help="Enable speaker diarization (implied for --provider openai)",
    )
    p.add_argument(
        "--language",
        default=None,
        help="ISO-639-1 language code (zh, en, ja…). Auto-detect if omitted.",
    )
    p.add_argument("--out_txt", type=str, default=None, help="Save transcript to text file")
    p.add_argument("--out_json", type=str, default=None, help="Save full API response to JSON")

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

    start_time = time.time()

    if args.provider == "openai":
        text, resp = transcribe_openai(audio_path, args.language, args.diarize)
    else:
        text, resp = transcribe_gemini(audio_path, args.model, args.language, args.diarize)

    elapsed = time.time() - start_time
    _info(f"Transcription completed in {elapsed:.1f}s ({resp.get('chunks', 1)} chunk(s))")

    if args.out_json:
        out_json_path = Path(args.out_json).expanduser().resolve()
        out_json_path.write_text(json.dumps(resp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _info(f"Saved JSON to {out_json_path}")

    if args.out_txt:
        out_txt_path = Path(args.out_txt).expanduser().resolve()
        out_txt_path.write_text(text + "\n", encoding="utf-8")
        _info(f"Saved transcript to {out_txt_path}")

    print(text)


if __name__ == "__main__":
    main()
