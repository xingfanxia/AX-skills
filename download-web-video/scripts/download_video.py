#!/usr/bin/env python3
"""Download one Bilibili or YouTube video into a reproducible artifact bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit, urlunsplit


BILI_CDN_CANDIDATES = (
    "upos-sz-mirrorcos.bilivideo.com",
    "upos-sz-mirrorali.bilivideo.com",
    "upos-sz-mirrorhw.bilivideo.com",
    "upos-tf-all-hw.bilivideo.com",
    "upos-tf-all-tx.bilivideo.com",
)
MEDIA_SUFFIXES = {
    ".3gp", ".aac", ".flac", ".flv", ".m4a", ".m4s", ".mkv",
    ".mov", ".mp3", ".mp4", ".ogg", ".opus", ".ts", ".wav", ".webm",
}
P2P_SUFFIXES = (
    ".szbdyd.com",
    ".mountaintoys.cn",
    ".nexusedgeio.com",
    ".ahdohpiechei.com",
)


@dataclass(frozen=True)
class ProbeResult:
    host: str
    ok: bool
    status: int | None
    bytes_read: int
    ttfb_ms: float | None
    elapsed_ms: float | None
    throughput_mbps: float | None
    error: str | None = None


class DownloadError(RuntimeError):
    """A command or prerequisite failed without exposing credential material."""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Bilibili or YouTube video URL.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Bundle directory for media, captions, metadata, and manifest.json.",
    )
    auth = parser.add_mutually_exclusive_group()
    auth.add_argument(
        "--cookies-from-browser",
        metavar="SPEC",
        help="yt-dlp browser spec, for example chrome:Default, firefox, or safari.",
    )
    auth.add_argument(
        "--cookies",
        metavar="FILE",
        help="Netscape cookie file. The file is read by yt-dlp and never copied.",
    )
    parser.add_argument(
        "--format",
        default="bestvideo*+bestaudio/best",
        help="yt-dlp format selector.",
    )
    parser.add_argument(
        "--sub-langs",
        default="zh.*,ai-zh,en.*",
        help="yt-dlp subtitle language selector.",
    )
    parser.add_argument(
        "--no-subtitles",
        action="store_true",
        help="Do not request human or automatic captions.",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Write metadata/captions/thumbnail without downloading media.",
    )
    parser.add_argument(
        "--playlist",
        action="store_true",
        help="Allow playlist or Bilibili anthology download; default is one entry.",
    )
    parser.add_argument(
        "--accelerator",
        choices=("auto", "off", "force"),
        default="auto",
        help="Use aria2 and, for Bilibili VOD, measured CDN host selection.",
    )
    parser.add_argument(
        "--concurrent-fragments",
        type=int,
        default=8,
        help="Parallel DASH/HLS fragments for yt-dlp's native downloader.",
    )
    parser.add_argument(
        "--connections",
        type=int,
        default=8,
        help="aria2 split connections for direct HTTP media.",
    )
    parser.add_argument(
        "--probe-bytes",
        type=int,
        default=256 * 1024,
        help="Maximum bytes read from each Bilibili CDN candidate.",
    )
    parser.add_argument(
        "--probe-timeout",
        type=float,
        default=4.0,
        help="Seconds allowed for each Bilibili CDN range probe.",
    )
    parser.add_argument(
        "--output-template",
        default="%(id)s.%(ext)s",
        help="yt-dlp output template relative to --output-dir.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print a credential-redacted execution plan without network access.",
    )
    args = parser.parse_args(argv)
    if args.concurrent_fragments < 1 or args.connections < 1:
        parser.error("parallelism values must be positive")
    if args.probe_bytes < 1024 or args.probe_timeout <= 0:
        parser.error("probe limits must be positive")
    return args


def site_kind(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    if host == "b23.tv" or host.endswith(".bilibili.com"):
        return "bilibili"
    if host == "youtu.be" or host.endswith(".youtube.com"):
        return "youtube"
    return "other"


def swap_url_host(url: str, host: str) -> str:
    """Swap only the authority while preserving a signed media path/query."""
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("expected an HTTP(S) URL")
    clean_host = host.strip().lower()
    if clean_host not in BILI_CDN_CANDIDATES:
        raise ValueError(f"unapproved Bilibili CDN host: {host}")
    return urlunsplit(("https", clean_host, parts.path, parts.query, parts.fragment))


def looks_like_bili_media_url(value: str) -> bool:
    parts = urlsplit(value)
    host = (parts.hostname or "").lower()
    path = parts.path.lower()
    return (
        parts.scheme in {"http", "https"}
        and (
            host.endswith((".bilivideo.com", ".bilivideo.cn", ".bilivideo.net"))
            or host.endswith(".akamaized.net")
            or any(host.endswith(suffix) for suffix in P2P_SUFFIXES)
        )
        and (
            path.endswith((".m4s", ".mp4", ".flv", ".m3u8"))
            or path.startswith(("/upgcxcode/", "/v1/resource/"))
        )
        and "/live-bvc/" not in path
    )


def looks_like_bad_bili_host(url: str) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    query = parts.query.lower()
    return (
        host.endswith(P2P_SUFFIXES)
        or ".mcdn.bilivideo." in host
        or "os=mcdn" in query
        or bool(parts.port and parts.port not in {80, 443})
        or bool(re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", host))
        or any(marker in host for marker in ("mirroraliov", "mirrorcosov", "mirrorhwov"))
        or (host.startswith("upos-") and "302" in host.split(".", 1)[0])
    )


def cookie_args(args: argparse.Namespace) -> list[str]:
    if args.cookies_from_browser:
        return ["--cookies-from-browser", args.cookies_from_browser]
    if args.cookies:
        cookie_path = Path(args.cookies).expanduser()
        if not cookie_path.is_file():
            raise DownloadError(f"cookie file not found: {cookie_path}")
        return ["--cookies", str(cookie_path.resolve())]
    return []


def cookie_summary(args: argparse.Namespace) -> dict[str, str]:
    if args.cookies_from_browser:
        return {
            "mode": "browser",
            "browser": args.cookies_from_browser.split(":", 1)[0].split("+", 1)[0],
            "profile": "explicit" if ":" in args.cookies_from_browser else "most-recent",
        }
    if args.cookies:
        return {"mode": "file", "browser": "n/a", "profile": "n/a"}
    return {"mode": "none", "browser": "n/a", "profile": "n/a"}


def require_executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise DownloadError(f"required executable not found: {name}")
    return path


def run_checked(command: list[str], *, env: dict[str, str] | None = None) -> None:
    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        raise DownloadError(f"{Path(command[0]).name} exited with status {exc.returncode}") from exc


def discover_info(
    yt_dlp: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    command = [
        yt_dlp,
        "--ignore-config",
        "--dump-single-json",
        "--skip-download",
        "--no-warnings",
        "--format",
        args.format,
        *cookie_args(args),
        "--yes-playlist" if args.playlist else "--no-playlist",
        args.url,
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode:
        detail = completed.stderr.strip().splitlines()
        tail = detail[-1] if detail else f"status {completed.returncode}"
        raise DownloadError(f"yt-dlp metadata discovery failed: {tail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise DownloadError("yt-dlp did not return valid discovery JSON") from exc


def iter_entries(info: dict[str, Any]) -> list[dict[str, Any]]:
    entries = info.get("entries")
    if isinstance(entries, list):
        return [entry for entry in entries if isinstance(entry, dict)]
    return [info]


def find_probe_url(info: dict[str, Any]) -> tuple[str | None, dict[str, str]]:
    candidates: list[dict[str, Any]] = []
    for entry in iter_entries(info):
        for item in entry.get("formats") or []:
            if isinstance(item, dict) and looks_like_bili_media_url(str(item.get("url") or "")):
                candidates.append(item)
    if not candidates:
        return None, {}
    selected = max(
        candidates,
        key=lambda item: (
            int(item.get("height") or 0),
            float(item.get("tbr") or 0),
            int(item.get("filesize") or item.get("filesize_approx") or 0),
        ),
    )
    headers = {
        str(key): str(value)
        for key, value in (selected.get("http_headers") or info.get("http_headers") or {}).items()
        if str(key).lower() in {"user-agent", "referer", "origin", "accept"}
    }
    headers.setdefault("Referer", "https://www.bilibili.com/")
    headers.setdefault("User-Agent", "Mozilla/5.0")
    return str(selected["url"]), headers


def probe_host(
    original_url: str,
    host: str,
    headers: dict[str, str],
    *,
    byte_limit: int,
    timeout: float,
) -> ProbeResult:
    original_host = (urlsplit(original_url).hostname or "").lower()
    try:
        probe_url = original_url if host == original_host else swap_url_host(original_url, host)
        request_headers = {
            **headers,
            "Range": f"bytes=0-{byte_limit - 1}",
            "Accept-Encoding": "identity",
        }
        request = urllib.request.Request(probe_url, headers=request_headers)
        started = time.perf_counter()
        with urllib.request.urlopen(request, timeout=timeout) as response:
            ttfb = time.perf_counter() - started
            payload = response.read(byte_limit)
            elapsed = time.perf_counter() - started
            status = getattr(response, "status", None)
        throughput = (len(payload) * 8 / 1_000_000) / max(elapsed, 0.001)
        return ProbeResult(
            host=host,
            ok=bool(payload) and status in {200, 206},
            status=status,
            bytes_read=len(payload),
            ttfb_ms=round(ttfb * 1000, 1),
            elapsed_ms=round(elapsed * 1000, 1),
            throughput_mbps=round(throughput, 2),
        )
    except (OSError, ValueError, urllib.error.URLError) as exc:
        return ProbeResult(
            host=host,
            ok=False,
            status=getattr(exc, "code", None),
            bytes_read=0,
            ttfb_ms=None,
            elapsed_ms=None,
            throughput_mbps=None,
            error=type(exc).__name__,
        )


def choose_cdn_host(
    original_url: str,
    results: Sequence[ProbeResult],
    mode: str,
) -> str | None:
    if mode == "off":
        return None
    original_host = (urlsplit(original_url).hostname or "").lower()
    usable = [result for result in results if result.ok and result.throughput_mbps]
    candidates = [result for result in usable if result.host in BILI_CDN_CANDIDATES]
    if not candidates:
        return None
    best = max(candidates, key=lambda result: result.throughput_mbps or 0)
    original = next((result for result in usable if result.host == original_host), None)
    if mode == "force" or original is None:
        return best.host
    original_speed = original.throughput_mbps or 0
    if looks_like_bad_bili_host(original_url):
        # A host label is a risk hint, not stronger evidence than a healthy
        # measured connection. Switch only when the candidate is comparable;
        # otherwise retain an unusually fast original mirror.
        return best.host if (best.throughput_mbps or 0) >= original_speed * 0.8 else None
    return best.host if (best.throughput_mbps or 0) >= original_speed * 1.25 else None


def probe_bilibili_cdn(
    info: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[str | None, list[ProbeResult]]:
    original_url, headers = find_probe_url(info)
    if not original_url:
        return None, []
    original_host = (urlsplit(original_url).hostname or "").lower()
    hosts = list(dict.fromkeys((original_host, *BILI_CDN_CANDIDATES)))
    results = [
        probe_host(
            original_url,
            host,
            headers,
            byte_limit=args.probe_bytes,
            timeout=args.probe_timeout,
        )
        for host in hosts
    ]
    return choose_cdn_host(original_url, results, args.accelerator), results


def plugin_root() -> Path:
    return Path(__file__).resolve().parent / "yt-dlp-plugin"


def build_download_command(
    yt_dlp: str,
    output_dir: Path,
    args: argparse.Namespace,
    *,
    use_aria2: bool,
    use_bili_plugin: bool,
) -> list[str]:
    command = [
        yt_dlp,
        "--ignore-config",
        "--newline",
        "--continue",
        "--retries",
        "10",
        "--fragment-retries",
        "10",
        "--retry-sleep",
        "fragment:exp=1:10",
        "--socket-timeout",
        "20",
        "--concurrent-fragments",
        str(args.concurrent_fragments),
        "--format",
        args.format,
        "--merge-output-format",
        "mp4",
        "--write-info-json",
        "--write-thumbnail",
        "--paths",
        str(output_dir),
        "--paths",
        f"temp:{output_dir / '.tmp'}",
        "--output",
        args.output_template,
        *cookie_args(args),
        "--yes-playlist" if args.playlist else "--no-playlist",
    ]
    if not args.no_subtitles:
        command.extend([
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            args.sub_langs,
            "--sub-format",
            "srt/best",
        ])
    if args.metadata_only:
        command.append("--skip-download")
    if use_aria2:
        command.extend([
            "--downloader",
            "aria2c",
            "--downloader",
            "dash,m3u8:native",
            "--downloader-args",
            (
                f"aria2c:-x {args.connections} -s {args.connections} "
                "-k 1M --file-allocation=none --summary-interval=0"
            ),
        ])
    if use_bili_plugin:
        command.extend(["--plugin-dirs", str(plugin_root())])
    command.append(args.url)
    return command


def sanitize_metadata(info: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "id", "title", "description", "duration", "uploader", "uploader_id",
        "upload_date", "timestamp", "webpage_url", "original_url", "format_id",
        "format", "ext", "width", "height", "fps", "vcodec", "acodec",
    )
    summary = {key: info.get(key) for key in allowed if info.get(key) is not None}
    summary["subtitle_languages"] = sorted((info.get("subtitles") or {}).keys())
    summary["automatic_caption_languages"] = sorted((info.get("automatic_captions") or {}).keys())
    chapters = info.get("chapters")
    if isinstance(chapters, list):
        summary["chapters"] = [
            {
                key: chapter.get(key)
                for key in ("title", "start_time", "end_time")
                if chapter.get(key) is not None
            }
            for chapter in chapters
            if isinstance(chapter, dict)
        ]
    return summary


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_bundle_files(output_dir: Path) -> list[dict[str, Any]]:
    files = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or ".tmp" in path.parts or path.name == "manifest.json":
            continue
        files.append({
            "path": str(path.relative_to(output_dir)),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "kind": "media" if path.suffix.lower() in MEDIA_SUFFIXES else "sidecar",
        })
    return files


def load_written_metadata(output_dir: Path) -> list[dict[str, Any]]:
    summaries = []
    for path in sorted(output_dir.rglob("*.info.json")):
        try:
            summaries.append(sanitize_metadata(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return summaries


def write_manifest(
    output_dir: Path,
    args: argparse.Namespace,
    *,
    selected_cdn: str | None,
    probes: Sequence[ProbeResult],
    use_aria2: bool,
) -> Path:
    metadata = load_written_metadata(output_dir)
    subtitle_languages = sorted({
        language
        for item in metadata
        for language in item.get("subtitle_languages", [])
        if language != "danmaku"
    })
    auth_state = (
        "site-feature-confirmed"
        if subtitle_languages
        else ("requested-not-confirmed" if cookie_summary(args)["mode"] != "none" else "not-requested")
    )
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": args.url,
        "site": site_kind(args.url),
        "authentication": {
            **cookie_summary(args),
            "state": auth_state,
            "evidence": (
                f"non-danmaku subtitle languages: {', '.join(subtitle_languages)}"
                if subtitle_languages
                else "no site-specific authenticated feature was confirmed"
            ),
        },
        "acceleration": {
            "mode": args.accelerator,
            "direct_downloader": "aria2c" if use_aria2 else "yt-dlp-native",
            "selected_bilibili_cdn": selected_cdn,
            "probe_results": [asdict(result) for result in probes],
        },
        "metadata_only": args.metadata_only,
        "entries": metadata,
        "files": collect_bundle_files(output_dir),
    }
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def redacted_plan(command: Sequence[str], args: argparse.Namespace) -> dict[str, Any]:
    redacted = list(command)
    if "--cookies" in redacted:
        redacted[redacted.index("--cookies") + 1] = "<COOKIE_FILE>"
    return {
        "site": site_kind(args.url),
        "authentication": cookie_summary(args),
        "command": redacted,
        "note": (
            "Browser cookie values and signed media URLs are not printed or copied "
            "into manifest.json. A yt-dlp info JSON may contain short-lived format "
            "URLs and must remain a local artifact."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir).expanduser().resolve()
    yt_dlp = require_executable("yt-dlp")
    use_aria2 = args.accelerator != "off" and shutil.which("aria2c") is not None
    is_bilibili = site_kind(args.url) == "bilibili"
    use_bili_plugin = False

    if args.dry_run:
        command = build_download_command(
            yt_dlp, output_dir, args, use_aria2=use_aria2, use_bili_plugin=is_bilibili,
        )
        print(json.dumps(redacted_plan(command, args), ensure_ascii=False, indent=2))
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.metadata_only:
        ffmpeg = require_executable("ffmpeg")
        probe = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True)
        if probe.returncode:
            raise DownloadError("ffmpeg exists but cannot start; repair it before downloading merged media")

    selected_cdn = None
    probes: list[ProbeResult] = []
    if is_bilibili and args.accelerator != "off":
        info = discover_info(yt_dlp, args)
        selected_cdn, probes = probe_bilibili_cdn(info, args)
        use_bili_plugin = selected_cdn is not None
        readable = [
            {
                "host": result.host,
                "ok": result.ok,
                "ttfb_ms": result.ttfb_ms,
                "throughput_mbps": result.throughput_mbps,
                "error": result.error,
            }
            for result in probes
        ]
        print(json.dumps({
            "bilibili_cdn_probe": readable,
            "selected_host": selected_cdn or "original",
        }, ensure_ascii=False, indent=2), flush=True)

    command = build_download_command(
        yt_dlp,
        output_dir,
        args,
        use_aria2=use_aria2,
        use_bili_plugin=use_bili_plugin,
    )
    env = os.environ.copy()
    if selected_cdn:
        env["AX_BILI_CDN_HOST"] = selected_cdn
    run_checked(command, env=env)
    manifest = write_manifest(
        output_dir,
        args,
        selected_cdn=selected_cdn,
        probes=probes,
        use_aria2=use_aria2,
    )
    print(json.dumps({
        "result": "ok",
        "output_dir": str(output_dir),
        "manifest": str(manifest),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DownloadError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
