---
name: download-web-video
description: Download Bilibili and YouTube videos with yt-dlp, optional browser-profile or Netscape-file authentication, human/automatic captions, metadata, thumbnails, resumable transfers, and Bilibili CDN probing plus aria2 acceleration. Use when Codex must save an online video or captions locally, access formats/subtitles that require an existing browser login, prepare source media for transcription or visual analysis, or produce a reproducible download bundle without exposing cookies or signed media URLs.
---

# Download Web Video

Produce a local evidence bundle with the media, captions, metadata, hashes, and
a credential-safe manifest. Support single Bilibili and YouTube URLs by default;
enable playlists only when the user asks.

## Prerequisites

Require `yt-dlp` and `ffmpeg`; use `aria2c` when available. On macOS:

```bash
brew install yt-dlp ffmpeg aria2
```

Treat browser cookies and signed media URLs as credentials. Pass cookies
directly to yt-dlp, never export or print their values, and never commit them.
The yt-dlp `*.info.json` artifact can contain short-lived signed format URLs;
keep it local even though `manifest.json` intentionally excludes those URLs.

## Download

Run the bundled wrapper:

```bash
python3 <skill-dir>/scripts/download_video.py \
  "https://www.bilibili.com/video/BV..." \
  --output-dir "./video-source" \
  --cookies-from-browser "chrome:Default"
```

For YouTube, use the same command and URL shape. Authentication is optional:

```bash
python3 <skill-dir>/scripts/download_video.py \
  "https://www.youtube.com/watch?v=..." \
  --output-dir "./video-source"
```

Use a Netscape cookie file only when the user supplies one:

```bash
python3 <skill-dir>/scripts/download_video.py URL \
  --output-dir "./video-source" \
  --cookies "/path/to/cookies.txt"
```

Do not assume that `--cookies-from-browser chrome` means the target site is
logged in. yt-dlp chooses the most recently accessed Chrome profile. If
captions or member formats are unexpectedly absent, identify the intended local
profile and pass it explicitly, such as `chrome:Default`.

## Choose the lightest mode

- Need only captions/metadata: add `--metadata-only`.
- Need no private browser state: omit both cookie options.
- Need a single entry from an anthology or playlist: keep the default
  `--no-playlist` behavior.
- Need the full playlist: add `--playlist` only with user intent.
- Need predictable native transfer behavior: add `--accelerator off`.
- Need to test the plan without network access: add `--dry-run`; cookie-file
  paths are redacted.

For Bilibili VOD, `auto` probes a bounded UPOS candidate set and rewrites only
signed media hosts when the original is unhealthy or a candidate is materially
faster. Read [references/acceleration.md](references/acceleration.md) before
changing the host policy, credential boundary, or the local
`bili_cdn_accel.py` yt-dlp plugin.

## Verify the bundle

Require all applicable conditions:

- `manifest.json` exists and identifies the original page URL, site, selected
  downloader, CDN probe results, output files, sizes, and SHA-256 hashes.
- At least one media file exists unless `--metadata-only` was requested.
- A `.info.json` sidecar exists.
- Requested captions exist when the site advertises them; otherwise report that
  captions were unavailable rather than inventing a transcript.
- `manifest.json` contains neither cookie values nor signed media URLs.
- The media opens with `ffprobe` and has the expected duration.

## Output

Write all results beneath `--output-dir`:

```text
<output-dir>/
├── <video-id>.mp4              # unless metadata-only
├── <video-id>.<lang>.srt       # when available
├── <video-id>.info.json
├── <video-id>.<thumbnail-ext>
└── manifest.json
```

Keep the bundle project-local or in a user-approved destination. Do not place
downloaded media, cookies, or short-lived URLs inside this public skill source.
