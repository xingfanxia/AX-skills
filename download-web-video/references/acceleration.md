# Bilibili acceleration notes

This skill adapts the safe, reusable part of
[realzza/bilibili-accelerator](https://github.com/realzza/bilibili-accelerator):
classify unreliable PCDN/MCDN delivery, measure several normal UPOS mirrors,
then keep the signed path and query while changing only the media host.

## What is reused

- Candidate UPOS hosts are probed with a small HTTP range request.
- Selection uses observed time-to-first-byte and throughput, not a fixed
  "fastest CDN" claim.
- Live video is excluded because Bilibili live delivery uses a different tier.
- The original URL remains the default unless it looks unhealthy or another
  host is materially faster.
- YouTube direct HTTP media can use aria2 split connections; DASH/HLS stays on
  yt-dlp's native fragment downloader.
- Bilibili `auto` uses the selected CDN with yt-dlp's native downloader. aria2
  splitting is reserved for explicit `force` mode because several UPOS mirrors
  have returned inconsistent ranges after a retry.

## What is intentionally different

The reference project modifies browser playback payloads and can react to a
stall. A command-line download has no browser player, so this skill performs a
bounded preflight probe and supplies a local yt-dlp extractor override only for
the selected Bilibili VOD host. It does not install a global plugin or mutate
the browser.

## Trust boundary

- Browser cookies remain inside yt-dlp. Never export, print, commit, or copy
  cookie values.
- A successful cookie extraction count does not prove site login. Confirm an
  authenticated site feature such as member-only formats or non-danmaku
  Bilibili subtitles.
- Signed media URLs are short-lived credentials. Do not put them in
  `manifest.json`, diagnostics, tests, or chat output.
- The plugin accepts only a small UPOS allowlist and rewrites only Bilibili VOD
  media paths. It ignores API, subtitle, thumbnail, and live URLs.

## Failure behavior

- If all CDN probes fail, retain the original URL and continue.
- If aria2 is absent, use yt-dlp's native downloader.
- Exit code is not treated as proof of a valid Bilibili download. The wrapper
  probes every required stream with ffprobe and compares its duration with the
  entry metadata; this catches containers whose video or audio track silently
  ends early.
- If a chosen CDN later fails or media validation rejects a track, use a clean
  output directory and rerun with `--accelerator off`. Do not resume the
  rejected `.part` file.
- If captions or premium formats are unexpectedly absent, select the exact
  browser profile, for example `chrome:Default`; yt-dlp otherwise chooses the
  most recently used profile, which may not be logged in to the target site.
