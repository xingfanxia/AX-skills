#!/usr/bin/env python3
"""Prepare timestamped captions, frames, contact sheet, and evidence manifest."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


TIMING_RE = re.compile(
    r"(?P<start>(?:\d{1,2}:)?\d{2}:\d{2}[,.]\d{3})\s+-->\s+"
    r"(?P<end>(?:\d{1,2}:)?\d{2}:\d{2}[,.]\d{3})(?:\s+.*)?"
)
TAG_RE = re.compile(r"<[^>]+>|\{\\[^}]+\}")


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class FrameEvidence:
    index: int
    kind: str
    timestamp: float
    timestamp_label: str
    path: str
    nearby_caption: str | None


class EvidenceError(RuntimeError):
    """A media prerequisite or extraction command failed."""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", help="Local video file.")
    parser.add_argument("--output-dir", required=True, help="Evidence bundle directory.")
    parser.add_argument(
        "--subtitles",
        help="SRT or VTT path. If omitted, prefer a nearby human caption, then auto-caption.",
    )
    parser.add_argument("--info-json", help="Optional yt-dlp .info.json sidecar.")
    parser.add_argument(
        "--frame-count",
        type=int,
        default=24,
        help="Uniform frames across the full duration.",
    )
    parser.add_argument(
        "--timestamp",
        action="append",
        default=[],
        help="Additional HH:MM:SS or seconds; repeat or comma-separate values.",
    )
    parser.add_argument("--frame-width", type=int, default=960)
    parser.add_argument("--no-contact-sheet", action="store_true")
    parser.add_argument("--skip-sha256", action="store_true")
    args = parser.parse_args(argv)
    if args.frame_count < 0 or args.frame_width < 160:
        parser.error("frame count must be non-negative and width must be at least 160")
    return args


def require_executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise EvidenceError(f"required executable not found: {name}")
    return path


def timestamp_seconds(value: str) -> float:
    normalized = value.strip().replace(",", ".")
    if re.fullmatch(r"\d+(?:\.\d+)?", normalized):
        return float(normalized)
    parts = normalized.split(":")
    if len(parts) not in {2, 3}:
        raise ValueError(f"invalid timestamp: {value}")
    try:
        numbers = [float(part) for part in parts]
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value}") from exc
    if len(numbers) == 2:
        minutes, seconds = numbers
        return minutes * 60 + seconds
    hours, minutes, seconds = numbers
    return hours * 3600 + minutes * 60 + seconds


def format_timestamp(seconds: float, *, filename: bool = False) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    separator = "-" if filename else ":"
    suffix = "-" if filename else "."
    return (
        f"{hours:02d}{separator}{minutes:02d}{separator}{secs:02d}"
        f"{suffix}{millis:03d}"
    )


def clean_caption_text(value: str) -> str:
    value = TAG_RE.sub("", value)
    return " ".join(html.unescape(value).split())


def parse_subtitles(text: str) -> list[Cue]:
    cues: list[Cue] = []
    lines = text.replace("\ufeff", "").splitlines()
    index = 0
    while index < len(lines):
        match = TIMING_RE.match(lines[index].strip())
        if not match:
            index += 1
            continue
        start = timestamp_seconds(match.group("start"))
        end = timestamp_seconds(match.group("end"))
        index += 1
        body = []
        while index < len(lines) and lines[index].strip():
            line = lines[index].strip()
            if not line.startswith(("NOTE", "STYLE", "REGION")):
                body.append(line)
            index += 1
        caption = clean_caption_text(" ".join(body))
        if caption and end >= start:
            cue = Cue(start=start, end=end, text=caption)
            if cues and cue.text == cues[-1].text and cue.start <= cues[-1].end + 0.25:
                cues[-1] = Cue(cues[-1].start, max(cues[-1].end, cue.end), cue.text)
            else:
                cues.append(cue)
    return cues


def subtitle_priority(path: Path) -> tuple[int, str]:
    name = path.name.lower()
    if re.search(r"(?:^|[._-])zh(?:[._-]|$)", name) and "ai-zh" not in name:
        return (0, name)
    if "ai-zh" in name or "auto" in name:
        return (1, name)
    if re.search(r"(?:^|[._-])en(?:[._-]|$)", name):
        return (2, name)
    return (3, name)


def find_subtitles(media: Path, explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise EvidenceError(f"subtitle file not found: {path}")
        return path
    candidates = [
        path
        for extension in ("srt", "vtt")
        for path in media.parent.glob(f"{media.stem}*.{extension}")
        if path.is_file()
    ]
    return min(candidates, key=subtitle_priority) if candidates else None


def write_transcript(output_dir: Path, cues: Sequence[Cue]) -> tuple[Path, Path]:
    json_path = output_dir / "transcript.json"
    markdown_path = output_dir / "transcript.md"
    json_path.write_text(
        json.dumps([asdict(cue) for cue in cues], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if cues:
        body = "\n".join(
            f"[{format_timestamp(cue.start)} → {format_timestamp(cue.end)}] {cue.text}"
            for cue in cues
        )
    else:
        body = "_No captions were available. Use ASR before making speech-dependent claims._"
    markdown_path.write_text(f"# Timestamped transcript\n\n{body}\n", encoding="utf-8")
    return json_path, markdown_path


def ffprobe_metadata(ffprobe: str, media: Path) -> dict[str, Any]:
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(media),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode:
        raise EvidenceError(f"ffprobe failed: {completed.stderr.strip().splitlines()[-1]}")
    data = json.loads(completed.stdout)
    streams = data.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
    format_data = data.get("format") or {}
    duration = float(format_data.get("duration") or video.get("duration") or 0)
    if duration <= 0:
        raise EvidenceError("ffprobe did not report a positive media duration")
    return {
        "duration": duration,
        "bytes": int(format_data.get("size") or media.stat().st_size),
        "format_name": format_data.get("format_name"),
        "video": {
            key: video.get(key)
            for key in ("codec_name", "codec_long_name", "width", "height", "pix_fmt", "r_frame_rate")
            if video.get(key) is not None
        },
        "audio": {
            key: audio.get(key)
            for key in ("codec_name", "codec_long_name", "sample_rate", "channels")
            if audio.get(key) is not None
        },
    }


def uniform_timestamps(duration: float, count: int) -> list[float]:
    if count <= 0:
        return []
    return [duration * (index + 0.5) / count for index in range(count)]


def requested_timestamps(values: Sequence[str], duration: float) -> list[float]:
    results = []
    for item in values:
        for raw in item.split(","):
            if not raw.strip():
                continue
            seconds = timestamp_seconds(raw)
            if seconds < 0 or seconds > duration:
                raise EvidenceError(
                    f"requested timestamp {raw!r} lies outside 0–{format_timestamp(duration)}"
                )
            results.append(seconds)
    return results


def nearest_caption(cues: Sequence[Cue], timestamp: float) -> str | None:
    containing = [cue.text for cue in cues if cue.start <= timestamp <= cue.end]
    if containing:
        return " / ".join(dict.fromkeys(containing))[:320]
    if not cues:
        return None
    nearest = min(cues, key=lambda cue: abs(((cue.start + cue.end) / 2) - timestamp))
    distance = min(abs(nearest.start - timestamp), abs(nearest.end - timestamp))
    return nearest.text[:320] if distance <= 12 else None


def extract_frame(
    ffmpeg: str,
    media: Path,
    output_path: Path,
    timestamp: float,
    width: int,
) -> None:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{timestamp:.3f}",
        "-i",
        str(media),
        "-frames:v",
        "1",
        "-vf",
        f"scale=min({width}\\,iw):-2",
        "-q:v",
        "2",
        "-y",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode or not output_path.is_file():
        detail = completed.stderr.strip().splitlines()
        raise EvidenceError(
            f"ffmpeg frame extraction failed at {format_timestamp(timestamp)}"
            + (f": {detail[-1]}" if detail else "")
        )


def create_contact_sheet(
    ffmpeg: str,
    frame_paths: Sequence[Path],
    output_path: Path,
) -> None:
    if not frame_paths:
        return
    columns = min(4, max(1, math.ceil(math.sqrt(len(frame_paths)))))
    cell_width, cell_height = 480, 300
    inputs: list[str] = []
    filters = []
    labels = []
    layout = []
    for index, frame in enumerate(frame_paths):
        inputs.extend(["-i", str(frame)])
        label = f"v{index}"
        filters.append(
            f"[{index}:v]scale={cell_width}:{cell_height - 20}:"
            "force_original_aspect_ratio=decrease,"
            f"pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:color=0x17130c"
            f"[{label}]"
        )
        labels.append(f"[{label}]")
        layout.append(
            f"{(index % columns) * cell_width}_{(index // columns) * cell_height}"
        )
    filters.append(
        "".join(labels)
        + f"xstack=inputs={len(frame_paths)}:layout={'|'.join(layout)}:fill=0x17130c[out]"
    )
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        *inputs,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[out]",
        "-frames:v",
        "1",
        "-q:v",
        "3",
        "-y",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode or not output_path.is_file():
        detail = completed.stderr.strip().splitlines()
        raise EvidenceError(
            "ffmpeg contact-sheet generation failed"
            + (f": {detail[-1]}" if detail else "")
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_info_json(media: Path, explicit: str | None) -> tuple[Path | None, dict[str, Any]]:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise EvidenceError(f"info JSON not found: {path}")
    else:
        candidates = sorted(media.parent.glob(f"{media.stem}*.info.json"))
        path = candidates[0] if candidates else None
    if not path:
        return None, {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid info JSON: {path}") from exc
    allowed = (
        "id", "title", "description", "duration", "uploader", "uploader_id",
        "upload_date", "timestamp", "webpage_url", "original_url",
    )
    sanitized = {key: data.get(key) for key in allowed if data.get(key) is not None}
    sanitized["subtitle_languages"] = sorted((data.get("subtitles") or {}).keys())
    if isinstance(data.get("chapters"), list):
        sanitized["chapters"] = [
            {
                key: chapter.get(key)
                for key in ("title", "start_time", "end_time")
                if chapter.get(key) is not None
            }
            for chapter in data["chapters"]
            if isinstance(chapter, dict)
        ]
    return path, sanitized


def markdown_escape(value: str | None) -> str:
    return (value or "—").replace("|", "\\|").replace("\n", " ")


def write_index(
    output_dir: Path,
    media: Path,
    subtitle: Path | None,
    frames: Sequence[FrameEvidence],
    contact_sheet: Path | None,
) -> Path:
    lines = [
        "# Video evidence index",
        "",
        f"- Media: `{media.name}`",
        f"- Captions: `{subtitle.name}`" if subtitle else "- Captions: unavailable",
        (
            f"- Contact sheet: `{contact_sheet.relative_to(output_dir)}`"
            if contact_sheet
            else "- Contact sheet: not generated"
        ),
        "",
        "| # | Kind | Time | Frame | Nearby caption |",
        "|---:|---|---:|---|---|",
    ]
    lines.extend(
        (
            f"| {frame.index} | {frame.kind} | {frame.timestamp_label} | "
            f"`{frame.path}` | {markdown_escape(frame.nearby_caption)} |"
        )
        for frame in frames
    )
    path = output_dir / "evidence-index.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    media = Path(args.media).expanduser().resolve()
    if not media.is_file():
        raise EvidenceError(f"media file not found: {media}")
    output_dir = Path(args.output_dir).expanduser().resolve()
    frames_dir = output_dir / "frames"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg = require_executable("ffmpeg")
    ffprobe = require_executable("ffprobe")
    metadata = ffprobe_metadata(ffprobe, media)
    duration = float(metadata["duration"])
    subtitle = find_subtitles(media, args.subtitles)
    cues = (
        parse_subtitles(subtitle.read_text(encoding="utf-8", errors="replace"))
        if subtitle
        else []
    )
    transcript_json, transcript_markdown = write_transcript(output_dir, cues)
    info_path, source_metadata = load_info_json(media, args.info_json)

    schedule: list[tuple[str, float]] = [
        ("uniform", value)
        for value in uniform_timestamps(duration, args.frame_count)
    ]
    schedule.extend(
        ("targeted", value)
        for value in requested_timestamps(args.timestamp, duration)
    )
    seen: set[int] = set()
    deduplicated = []
    for kind, value in schedule:
        key = round(value * 10)
        if key not in seen:
            seen.add(key)
            deduplicated.append((kind, value))

    frames: list[FrameEvidence] = []
    frame_paths = []
    for index, (kind, timestamp) in enumerate(deduplicated, start=1):
        filename = (
            f"{kind}_{index:03d}_{format_timestamp(timestamp, filename=True)}.jpg"
        )
        path = frames_dir / filename
        extract_frame(ffmpeg, media, path, timestamp, args.frame_width)
        frame_paths.append(path)
        frames.append(FrameEvidence(
            index=index,
            kind=kind,
            timestamp=round(timestamp, 3),
            timestamp_label=format_timestamp(timestamp),
            path=str(path.relative_to(output_dir)),
            nearby_caption=nearest_caption(cues, timestamp),
        ))

    contact_sheet = None
    if frame_paths and not args.no_contact_sheet:
        contact_sheet = output_dir / "contact-sheet.jpg"
        create_contact_sheet(ffmpeg, frame_paths, contact_sheet)
    index_path = write_index(output_dir, media, subtitle, frames, contact_sheet)

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "media": {
            "name": media.name,
            "path": str(media),
            "sha256": None if args.skip_sha256 else sha256_file(media),
            **metadata,
        },
        "source_metadata": source_metadata,
        "info_json": str(info_path) if info_path else None,
        "captions": {
            "path": str(subtitle) if subtitle else None,
            "sha256": sha256_file(subtitle) if subtitle else None,
            "cue_count": len(cues),
            "transcript_json": str(transcript_json.relative_to(output_dir)),
            "transcript_markdown": str(transcript_markdown.relative_to(output_dir)),
        },
        "frames": [asdict(frame) for frame in frames],
        "contact_sheet": (
            str(contact_sheet.relative_to(output_dir)) if contact_sheet else None
        ),
        "index": str(index_path.relative_to(output_dir)),
    }
    manifest_path = output_dir / "evidence.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "result": "ok",
        "output_dir": str(output_dir),
        "duration": duration,
        "caption_cues": len(cues),
        "frames": len(frames),
        "manifest": str(manifest_path),
        "contact_sheet": str(contact_sheet) if contact_sheet else None,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EvidenceError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
