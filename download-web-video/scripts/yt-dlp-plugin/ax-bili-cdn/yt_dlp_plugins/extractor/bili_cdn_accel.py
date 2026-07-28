"""yt-dlp extractor override that swaps Bilibili VOD media onto a measured CDN."""

from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit

from yt_dlp.extractor.bilibili import BiliBiliIE


ALLOWED_HOSTS = {
    "upos-sz-mirrorcos.bilivideo.com",
    "upos-sz-mirrorali.bilivideo.com",
    "upos-sz-mirrorhw.bilivideo.com",
    "upos-tf-all-hw.bilivideo.com",
    "upos-tf-all-tx.bilivideo.com",
}


def _rewrite_media_url(value: str, target: str) -> str:
    parts = urlsplit(value)
    host = (parts.hostname or "").lower()
    path = parts.path.lower()
    is_bili = (
        host.endswith((".bilivideo.com", ".bilivideo.cn", ".bilivideo.net"))
        or host.endswith(".akamaized.net")
        or "mcdn.bilivideo." in host
    )
    is_vod = (
        path.endswith((".m4s", ".mp4", ".flv", ".m3u8"))
        or path.startswith(("/upgcxcode/", "/v1/resource/"))
    ) and "/live-bvc/" not in path
    if parts.scheme not in {"http", "https"} or not is_bili or not is_vod:
        return value
    return urlunsplit(("https", target, parts.path, parts.query, parts.fragment))


class _AxBiliCdnAcceleratorIE(BiliBiliIE, plugin_name="axcdn"):
    """Replace the built-in video extractor only when AX_BILI_CDN_HOST is set."""

    def extract_formats(self, play_info):
        formats = super().extract_formats(play_info)
        target = os.environ.get("AX_BILI_CDN_HOST", "").strip().lower()
        if not target:
            return formats
        if target not in ALLOWED_HOSTS:
            self.report_warning("AX Bilibili CDN target rejected: not in the allowlist")
            return formats

        changed = 0
        for item in formats:
            if item.get("url"):
                rewritten = _rewrite_media_url(item["url"], target)
                changed += rewritten != item["url"]
                item["url"] = rewritten
            for fragment in item.get("fragments") or []:
                if fragment.get("url"):
                    rewritten = _rewrite_media_url(fragment["url"], target)
                    changed += rewritten != fragment["url"]
                    fragment["url"] = rewritten
        if changed:
            self.to_screen(f"AX CDN accelerator rewrote {changed} VOD media URL(s) to {target}")
        return formats
