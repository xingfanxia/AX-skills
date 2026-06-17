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


CHUNK_THRESHOLD_SEC = int(os.environ.get("CHUNK_THRESHOLD_SEC", "1080"))  # only chunk if audio > 18 min
CHUNK_TARGET_SEC = int(os.environ.get("CHUNK_TARGET_SEC", "720"))          # aim for ~12 min chunks
CHUNK_MIN_SEC = int(os.environ.get("CHUNK_MIN_SEC", "480"))                # but at least 8 min
CHUNK_MAX_SEC = int(os.environ.get("CHUNK_MAX_SEC", "900"))                # at most 15 min (Gemini coherence edge)
CHUNK_PARALLELISM = int(os.environ.get("CHUNK_PARALLELISM", "8"))          # concurrent chunk API calls
# Overlap between adjacent chunks. The overlap region is transcribed in BOTH
# chunks; we use it to reconcile per-chunk SPEAKER_0/SPEAKER_1 labels so they
# stay consistent across the whole transcript. Set 0 to disable reconciliation.
CHUNK_OVERLAP_SEC = int(os.environ.get("CHUNK_OVERLAP_SEC", "60"))


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
    """Parse `HH:MM:SS` (3-component) or `MM:SS` (2-component) — Gemini drops
    the hour on short chunks. Returns seconds."""
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    raise ValueError(f"unrecognized timestamp: {ts!r}")


# Accept 2- or 3-component timestamps (Gemini sometimes emits MM:SS) AND an
# optional trailing `:` artifact like `[06:41: - 06:42]` (truncated HH:MM:SS
# emission that left the separator). Lenient digit counts.
_TIMESTAMP_RE = re.compile(
    r"\[(\d{1,2}:\d{1,2}(?::\d{1,2})?):?\s*-\s*(\d{1,2}:\d{1,2}(?::\d{1,2})?):?\]"
)
_TURN_RE = re.compile(
    r"^\[(\d{1,2}:\d{1,2}(?::\d{1,2})?):?\s*-\s*(\d{1,2}:\d{1,2}(?::\d{1,2})?):?\]\s+(SPEAKER_\d+|[A-Z]):\s*(.*)$"
)
# Lines Gemini sometimes emits that aren't part of the transcript itself:
# compliance preambles ("好的，以下是…"), meta-commentary ("（注：...）"),
# refusal phrases. Drop them.
_META_LINE_RE = re.compile(
    r"^\s*(好的|以下是|这是.{0,15}(转录|音频)|（注[：:]|\(Note[：:]|Here.{0,5}(is|'s).{0,20}(transcription|transcript)|\[?.*?as an? AI)",
    re.IGNORECASE,
)


def _offset_timestamps(transcript: str, offset_sec: float) -> str:
    """Shift every `[HH:MM:SS - HH:MM:SS]` (or shorter variant) timestamp by offset_sec."""

    def replace(m):
        start = _parse_ts(m.group(1)) + offset_sec
        end = _parse_ts(m.group(2)) + offset_sec
        return f"[{_fmt_ts(start)} - {_fmt_ts(end)}]"

    return _TIMESTAMP_RE.sub(replace, transcript)


def _offset_and_filter_timestamps(
    transcript: str,
    offset_sec: float,
    max_internal_sec: float,
    audio_duration_sec: float = 0.0,
) -> str:
    """Shift timestamps by offset; clean up Gemini chunk-output anomalies.

    Handles:
      - Turn line with start past chunk end → drop (hallucinated).
      - Turn line with end past chunk end / end before start / huge utterance → clamp.
      - Turn line with absolute start/end past audio_duration_sec (if set) →
        drop or clamp. Filters out trailing-silence hallucinations.
      - Lines that OPEN with `[<time>` but never close `]` → drop (malformed turn).
      - Gemini compliance preamble / `（注：...）` meta lines → drop.
    """
    out_lines: List[str] = []
    tolerance = 30.0
    max_utterance_sec = 120.0
    for line in transcript.splitlines():
        m = _TURN_RE.match(line)
        if m:
            internal_start = _parse_ts(m.group(1))
            if internal_start > max_internal_sec + tolerance:
                continue
            internal_end = _parse_ts(m.group(2))
            # Clamp in priority order.
            if internal_end - internal_start > max_utterance_sec:
                internal_end = internal_start + max_utterance_sec
            if internal_end > max_internal_sec + tolerance:
                internal_end = max_internal_sec
            if internal_end < internal_start:
                internal_end = internal_start + 5
            new_start = internal_start + offset_sec
            new_end = internal_end + offset_sec
            if audio_duration_sec > 0:
                if new_start >= audio_duration_sec:
                    continue
                if new_end > audio_duration_sec:
                    new_end = audio_duration_sec
                if new_end < new_start:
                    new_end = min(new_start + 5, audio_duration_sec)
                    if new_end <= new_start:
                        continue
            new_line = _TIMESTAMP_RE.sub(
                f"[{_fmt_ts(new_start)} - {_fmt_ts(new_end)}]", line, count=1,
            )
            out_lines.append(new_line)
        elif line.startswith("[") and "]" not in line[:80]:
            # Opens like a turn but never closes `]` — Gemini garbage.
            continue
        elif _META_LINE_RE.match(line):
            # Gemini compliance preamble or `（注：...）` meta — not transcript.
            continue
        else:
            shifted = _offset_timestamps(line, offset_sec) if _TIMESTAMP_RE.search(line) else line
            out_lines.append(shifted)
    return "\n".join(out_lines)


def _parse_diarized_lines(transcript: str):
    """Return list of dicts per line; turn lines have is_turn=True + start/end/speaker/raw."""
    out = []
    for line in transcript.splitlines():
        m = _TURN_RE.match(line)
        if m:
            out.append({
                "is_turn": True,
                "start": _parse_ts(m.group(1)),
                "speaker": m.group(3),
                "raw": line,
            })
        else:
            out.append({"is_turn": False, "raw": line})
    return out


def _reconcile_speakers_across_chunks(chunk_records):
    """Align speaker labels across chunks via overlap-region voting.

    Each chunk after the first starts CHUNK_OVERLAP_SEC before the previous
    chunk ends, so the same audio is transcribed twice. For each chunk k>0,
    we vote: chunk_k's SPEAKER_X in the overlap → matches which chunk_{k-1}
    SPEAKER_Y by closest timestamp? Most-voted mapping wins, applied to all
    chunk_k's turns. Mapping flows cumulatively; chunk 0 is canonical.

    Handles swap collisions (chunk_k uses both SPEAKER_0 and SPEAKER_1 with
    inverted assignment) via atomic temp-prefix two-pass renaming.
    """
    if len(chunk_records) <= 1:
        return
    for rec in chunk_records:
        rec["parsed"] = _parse_diarized_lines(rec["text"])
    for k in range(1, len(chunk_records)):
        prev, cur = chunk_records[k - 1], chunk_records[k]
        overlap_start = cur["offset"]
        overlap_end = prev["end_abs"]
        if overlap_end <= overlap_start:
            continue
        prev_turns = [t for t in prev["parsed"]
                      if t["is_turn"] and overlap_start <= t["start"] < overlap_end]
        cur_turns = [t for t in cur["parsed"]
                     if t["is_turn"] and overlap_start <= t["start"] < overlap_end]
        if not prev_turns or not cur_turns:
            continue
        votes = {}
        for ct in cur_turns:
            closest = min(prev_turns, key=lambda pt: abs(pt["start"] - ct["start"]))
            if abs(closest["start"] - ct["start"]) > 5.0:
                continue
            votes.setdefault(ct["speaker"], {}).setdefault(closest["speaker"], 0)
            votes[ct["speaker"]][closest["speaker"]] += 1
        mapping = {}
        for cur_sp, prev_votes in votes.items():
            best_prev, _ = max(prev_votes.items(), key=lambda x: x[1])
            if cur_sp != best_prev:
                mapping[cur_sp] = best_prev
        if not mapping:
            continue
        # Detect swap collisions: extend mapping with inverse so we don't merge speakers.
        cur_speakers = {t["speaker"] for t in cur["parsed"] if t["is_turn"]}
        for src, dst in list(mapping.items()):
            if dst in cur_speakers and dst not in mapping:
                mapping[dst] = src
        # Atomic two-pass rename via temp prefix (avoids chain collisions).
        TMP = "__RECONCILE_TMP_"
        for t in cur["parsed"]:
            if t["is_turn"] and t["speaker"] in mapping:
                old = t["speaker"]
                tmp = TMP + mapping[old]
                t["raw"] = t["raw"].replace(f"] {old}:", f"] {tmp}:", 1)
                t["speaker"] = tmp
        for t in cur["parsed"]:
            if t["is_turn"] and t["speaker"].startswith(TMP):
                final = t["speaker"][len(TMP):]
                t["raw"] = t["raw"].replace(f"] {t['speaker']}:", f"] {final}:", 1)
                t["speaker"] = final


def _join_chunks_dropping_overlap(chunk_records) -> str:
    """Collect all turn lines across chunks, drop overlap-region duplicates,
    sort chronologically.

    For each chunk k: keep turns whose start >= chunk_{k-1}.end_abs (k=0 → keep
    all). Per-turn filter is robust to Gemini emitting chunk-internal turns out
    of chronological order, which slice-from-first-past-overlap mis-handled.

    Non-turn lines dropped — upstream _offset_and_filter_timestamps already
    stripped the legitimate Gemini-meta lines.
    """
    all_turns = []
    for k, rec in enumerate(chunk_records):
        if "parsed" not in rec:
            rec["parsed"] = _parse_diarized_lines(rec["text"])
        prev_end = chunk_records[k - 1]["end_abs"] if k > 0 else 0.0
        for t in rec["parsed"]:
            if t["is_turn"] and t["start"] >= prev_end:
                all_turns.append(t)
    all_turns.sort(key=lambda t: t["start"])
    return "\n".join(t["raw"] for t in all_turns)


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
        # Chunks 1..N start CHUNK_OVERLAP_SEC before splits[i] so the overlap
        # region is transcribed in BOTH adjacent chunks — enabling speaker
        # label reconciliation across chunk boundaries.
        nominal_start = splits[i]
        actual_start = nominal_start if i == 0 else max(0.0, nominal_start - CHUNK_OVERLAP_SEC)
        end = splits[i + 1]
        chunk_path = tmp_dir / f"chunk_{i:02d}{audio_path.suffix}"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", str(actual_start), "-to", str(end),
                    "-i", str(audio_path),
                    "-c", "copy",
                    str(chunk_path),
                ],
                check=True, timeout=180,
            )
            chunks.append((chunk_path, actual_start, end - actual_start))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            _info(f"failed to extract chunk {i} ({actual_start:.0f}-{end:.0f}s): {e}")

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
    """Single Gemini call on one chunk. Returns plain text.

    Retries `generate_content` on transient errors (503 UNAVAILABLE, 429
    RESOURCE_EXHAUSTED, 5xx) with exponential backoff — Gemini hits demand
    spikes occasionally and one chunk failing would otherwise abort the
    entire multi-chunk pipeline.
    """
    uploaded = _gemini_upload(client, audio_path)
    max_attempts = 4
    transient_codes = {429, 500, 502, 503, 504}
    transient_status = {"UNAVAILABLE", "RESOURCE_EXHAUSTED", "INTERNAL", "DEADLINE_EXCEEDED"}
    resp = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=[uploaded, prompt],
                config={
                    # Gemini 3 thinking models share max_output_tokens between
                    # thinking + actual output. For transcription (perceptual,
                    # not reasoning), thinking_level=minimal lets the full
                    # budget go to the transcript.
                    "thinking_config": {"thinking_level": "minimal"},
                    "max_output_tokens": 65536,
                },
            )
            break
        except Exception as e:
            msg = str(e)
            code = getattr(e, "code", None) or getattr(e, "status_code", None)
            status_match = any(s in msg.upper() for s in transient_status)
            code_match = code in transient_codes if code else False
            generic_5xx = " 5" in msg and ("503" in msg or "502" in msg or "504" in msg or "500" in msg)
            is_transient = status_match or code_match or generic_5xx
            if is_transient and attempt < max_attempts:
                backoff = 2 ** attempt
                _info(f"[retry] transient Gemini error (attempt {attempt}/{max_attempts-1}): {msg[:120]} — backing off {backoff}s")
                time.sleep(backoff)
                continue
            raise

    text = (resp.text or "").strip() if resp else ""
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


def _detect_speech_end(audio_path: Path) -> float:
    """Return the timestamp at which actual speech ends (start of trailing
    silence). Voice Memos / m4a files often pad recordings with trailing silence
    past the last spoken word; Gemini "transcribes" that silence into fabricated
    dialogue with bogus timestamps. Treating speech_end (not file end) as the
    effective audio bound drops those hallucinations. Falls back to file
    duration when no trailing silence is detected.
    """
    file_dur = _get_audio_duration(audio_path)
    silences = _detect_silence(audio_path, noise_db=-30, min_duration=2.0)
    if not silences:
        return file_dur
    trailing = [(s, e) for s, e in silences if e >= file_dur - 2.0]
    if not trailing:
        return file_dur
    return min(s for s, _ in trailing)


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

    speech_end = _detect_speech_end(audio_path)
    chunks, cleanup = _chunk_audio_at_silence(audio_path)
    try:
        if len(chunks) == 1:
            _info(f"Transcribing with {model} (single call, {_fmt_duration(chunks[0][2])})")
            text = _gemini_transcribe_one(client, chunks[0][0], model, prompt)
        else:
            n = len(chunks)
            workers = min(CHUNK_PARALLELISM, n)
            _info(f"Transcribing with {model} in {n} chunks (silence-aware, {workers} parallel, {CHUNK_OVERLAP_SEC}s overlap)")

            def run(idx_chunk):
                i, (chunk_path, offset, chunk_dur) = idx_chunk
                _info(f"chunk {i+1}/{n} START: {_fmt_ts(offset)} → {_fmt_ts(offset + chunk_dur)} ({chunk_dur:.0f}s)")
                t0 = time.time()
                chunk_text = _gemini_transcribe_one(client, chunk_path, model, prompt)
                _info(f"chunk {i+1}/{n} DONE  ({time.time()-t0:.0f}s, {len(chunk_text)} chars)")
                if diarize:
                    # Filter out timestamps Gemini hallucinated beyond chunk bounds,
                    # offset to absolute time, clamp post-EOF hallucinations.
                    chunk_text = _offset_and_filter_timestamps(
                        chunk_text, offset, chunk_dur, audio_duration_sec=speech_end,
                    )
                return i, chunk_text

            results: List[Optional[str]] = [None] * n
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for i, t in pool.map(run, enumerate(chunks)):
                    results[i] = t

            if diarize:
                # Reconcile speaker labels across chunks using the overlap region.
                chunk_records = [
                    {
                        "offset": chunks[i][1],
                        "end_abs": chunks[i][1] + chunks[i][2],
                        "text": results[i] or "",
                    }
                    for i in range(n)
                ]
                _reconcile_speakers_across_chunks(chunk_records)
                text = _join_chunks_dropping_overlap(chunk_records)
            else:
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

        if n == 1:
            text = results[0] or ""
        elif diarize:
            chunk_records = [
                {
                    "offset": chunks[i][1],
                    "end_abs": chunks[i][1] + chunks[i][2],
                    "text": results[i] or "",
                }
                for i in range(n)
            ]
            _reconcile_speakers_across_chunks(chunk_records)
            text = _join_chunks_dropping_overlap(chunk_records)
        else:
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
# Provider: 妙记 (Volcano Lark Minutes ASR) — best diarization, single call
# ---------------------------------------------------------------------------

def transcribe_lark(audio_path: Path, num_speakers: int) -> Tuple[str, Dict[str, Any]]:
    """Transcribe via 妙记 (volc.lark.minutes). Server-side diarization in a
    single call — no chunking / cross-chunk speaker reconcile. Best speaker
    accuracy of all providers (verified across 5 real recordings 2026-06-17).

    Hosts the audio in Volcano TOS so 妙记 can fetch it via FileURL. Needs
    VOLC_API_KEY + VOLC_TOS_* in the skill's .env. See volc_lark.py.

    num_speakers: 0 = auto-detect; N = hint the expected speaker count.
    """
    try:
        import volc_lark
    except ImportError as e:
        _die(f"妙记 provider unavailable: {e}. Run `pip install tos requests` in the skill venv, or use --provider gemini.")
    try:
        text = volc_lark.lark_transcribe(audio_path, num_speakers)
    except volc_lark.LarkError as e:
        _die(f"妙记 transcription failed: {e}\n"
             f"Check VOLC_API_KEY + VOLC_TOS_* in the skill .env, or fall back with --provider gemini.")
    return text, {
        "provider": "lark",
        "model": "volc.lark.minutes",
        "num_speakers": num_speakers or "auto",
        "text": text,
    }


# ---------------------------------------------------------------------------

def to_markdown(text: str, audio_path: Path, resp: Dict[str, Any]) -> str:
    """Render the transcript as a markdown document: a header with metadata and
    the diarized transcript inside a fenced code block (so each
    `[ts] SPEAKER:` line keeps its own line when rendered as markdown)."""
    speakers = sorted(set(re.findall(r"\bSPEAKER_\d+\b", text)))
    meta = [f"provider: {resp.get('provider', '?')}"]
    if resp.get("model"):
        meta.append(f"model: {resp['model']}")
    if speakers:
        meta.append(f"speakers: {len(speakers)}")
    header = f"# {audio_path.stem}\n\n> " + " · ".join(meta) + "\n"
    return f"{header}\n## Transcript\n\n```\n{text.strip()}\n```\n"


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
        choices=["lark", "gemini", "openai"],
        default="lark",
        help="STT provider (default: lark — 妙记, best diarization, single call)",
    )
    p.add_argument(
        "--model",
        default="gemini-3.5-flash",
        help="Gemini model (ignored for --provider lark/openai)",
    )
    p.add_argument(
        "--diarize",
        action="store_true",
        help="Enable speaker diarization (implied for --provider lark/openai)",
    )
    p.add_argument(
        "--speakers",
        type=int,
        default=0,
        help="Expected speaker count for --provider lark (0 = auto-detect). "
             "Ask the user how many speakers when known — improves accuracy.",
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

    if args.provider == "lark":
        text, resp = transcribe_lark(audio_path, args.speakers)
    elif args.provider == "openai":
        text, resp = transcribe_openai(audio_path, args.language, args.diarize)
    else:
        text, resp = transcribe_gemini(audio_path, args.model, args.language, args.diarize)

    elapsed = time.time() - start_time
    _info(f"Transcription completed in {elapsed:.1f}s ({resp.get('chunks', 1)} chunk(s))")

    if args.out_json:
        out_json_path = Path(args.out_json).expanduser().resolve()
        out_json_path.write_text(json.dumps(resp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _info(f"Saved JSON to {out_json_path}")

    markdown = to_markdown(text, audio_path, resp)

    if args.out_txt:
        out_txt_path = Path(args.out_txt).expanduser().resolve()
        out_txt_path.write_text(markdown, encoding="utf-8")
        _info(f"Saved markdown transcript to {out_txt_path}")

    print(markdown)


if __name__ == "__main__":
    main()
