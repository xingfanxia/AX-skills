#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=1.50"]
# ///
"""GPT Image 2.5: quality-first Sunburst, Flare on rate limits.

Azure and NewAPI support both generation and edits. --variant flare selects
latency-first routing, with Sunburst as its 429 fallback.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import AzureOpenAI, OpenAI, RateLimitError

CONFIG_FILE = Path.home() / ".config" / "gpt-image" / "credentials"

# Conservative image size bounds inherited from the previous image model:
#   * dims must be multiples of 16
#   * long edge <= 3840
#   * total pixels <= 8,294,400 (exactly 3840x2160 UHD; the API rejects
#     2496x3328 = budget + 12k px with "exceeds the current pixel budget",
#     while 2160x3840 and 2880x2880 = exactly budget pass)
# clamp_size() shrinks any oversized request to the largest same-aspect size
# that satisfies all three rules, so "4K" asks degrade instead of erroring.
SIZE_MULTIPLE = 16
LONG_EDGE_MAX = 3840
PIXEL_BUDGET = 3840 * 2160  # 8,294,400


def clamp_size(size: str) -> str:
    """Clamp WxH to the conservative image size bounds, preserving aspect ratio."""
    try:
        w_s, h_s = size.lower().split("x")
        w, h = int(w_s), int(h_s)
    except ValueError:
        return size  # let the API produce its own error for junk input
    if w <= 0 or h <= 0:
        return size
    scale = min(1.0, LONG_EDGE_MAX / max(w, h), (PIXEL_BUDGET / (w * h)) ** 0.5)
    cw = int(w * scale) // SIZE_MULTIPLE * SIZE_MULTIPLE
    ch = int(h * scale) // SIZE_MULTIPLE * SIZE_MULTIPLE
    clamped = f"{cw}x{ch}"
    if clamped != size:
        print(f"size {size} exceeds image size bounds, clamped to {clamped}", file=sys.stderr)
    return clamped

VARIANTS = ("sunburst", "flare")
DEFAULT_AZURE_API_VERSION = "2025-04-01-preview"
CRED_KEYS = (
    "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_VERSION",
    "NEWAPI_API_KEY", "NEWAPI_BASE_URL", "GPT_IMAGE_VARIANT",
)


def load_credentials() -> dict[str, str]:
    creds: dict[str, str] = {}
    if CONFIG_FILE.exists():
        for raw in CONFIG_FILE.read_text().splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                creds[key.strip()] = value.strip().strip('"').strip("'")
    for key in CRED_KEYS:
        if os.environ.get(key):
            # Foundry's global v1 setting is not the classic image API version.
            if key == "AZURE_OPENAI_API_VERSION" and os.environ[key] == "v1":
                continue
            creds[key] = os.environ[key]
    return creds


def build_azure_client(creds: dict[str, str], variant: str):
    endpoint = creds.get("AZURE_OPENAI_ENDPOINT")
    api_key = creds.get("AZURE_OPENAI_API_KEY")
    if not (endpoint and api_key):
        return None, None
    base = endpoint.rstrip("/")
    for suffix in ("/openai/v1", "/openai"):
        if base.endswith(suffix):
            base = base[:-len(suffix)]
            break
    model = f"gpt-image-2.5-{variant}"
    version = creds.get("AZURE_OPENAI_API_VERSION", DEFAULT_AZURE_API_VERSION)
    if version == "v1":
        version = DEFAULT_AZURE_API_VERSION
    return AzureOpenAI(
        azure_endpoint=base, api_key=api_key, api_version=version,
        azure_deployment=model, max_retries=0, timeout=600,
    ), model


def build_newapi_client(creds: dict[str, str], variant: str):
    key, base = creds.get("NEWAPI_API_KEY"), creds.get("NEWAPI_BASE_URL")
    if not (key and base):
        return None, None
    return OpenAI(api_key=key, base_url=base.rstrip("/"), max_retries=0,
                  timeout=600), f"gpt-image-2.5-{variant}"


def is_retryable_rate_limit(error):
    """Quota exhaustion and image user errors need a fix, not another request."""
    body = getattr(error, "body", None) or {}
    if isinstance(body, dict):
        detail = body.get("error", body)
        if isinstance(detail, dict):
            codes = (str(detail.get("code", "")), str(detail.get("type", "")))
            if any(code in ("insufficient_quota", "image_generation_user_error", "billing_hard_limit_reached") for code in codes):
                return False
    return isinstance(error, RateLimitError)


def generate_with_fallback(primary, fallback, prompt, size, retries=0,
                           edit_images=None, output_format="jpeg", quality=None):
    """Retry only 429s on the other variant; preserve all edit inputs."""
    client, model = primary
    try:
        return generate_one(client, model, prompt, size, retries, model,
                            edit_images, output_format, quality)
    except RateLimitError as error:
        if not is_retryable_rate_limit(error):
            raise
        client, model = fallback
        print(f"[429] switching to {model}", file=sys.stderr)
        return generate_one(client, model, prompt, size, retries, model,
                            edit_images, output_format, quality)


def generate_one(
    client: OpenAI,
    model: str,
    prompt: str,
    size: str,
    retries: int,
    label: str,
    edit_images: list[Path] | None = None,
    output_format: str = "jpeg",
    quality: str | None = None,
):
    """Call images.generate (text→image) or images.edit (image+text→image).

    If edit_images is provided (non-empty), routes to images.edit with one or
    multiple input images. File handles are opened inside the retry loop so
    they're fresh for each attempt and closed even on failure.

    output_format is passed to the API — "jpeg" (default), "png", or "webp".
    JPEG is ~75% smaller than PNG for typical photographic / illustrative
    output. Use "png" only when transparency or pixel-exactness is required.
    """
    common = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "output_format": output_format,
    }
    if quality is not None:
        common["quality"] = quality
    backoff = 5
    for attempt in range(retries + 1):
        try:
            if edit_images:
                handles = [open(p, "rb") for p in edit_images]
                try:
                    image_arg = handles[0] if len(handles) == 1 else handles
                    return client.images.edit(image=image_arg, **common)
                finally:
                    for h in handles:
                        h.close()
            return client.images.generate(**common)
        except RateLimitError as error:
            if not is_retryable_rate_limit(error) or attempt == retries:
                raise
            print(
                f"[{label}] 429 rate-limited (attempt {attempt + 1}/"
                f"{retries + 1}), waiting {backoff}s...",
                file=sys.stderr,
            )
            time.sleep(backoff)
            backoff *= 2


def save_image(
    result, output_dir: Path, basename: str, index: int | None, ext: str = "jpg"
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not result.data:
        raise RuntimeError("no image data in API response")
    suffix = f"_{index}" if index is not None else ""
    path = output_dir / f"{basename}{suffix}.{ext}"
    img_bytes = base64.b64decode(result.data[0].b64_json)
    path.write_bytes(img_bytes)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate images via GPT Image 2.5 Sunburst / Flare"
    )
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument(
        "--size",
        default="1024x1024",
        help=(
            "WxH, any multiples of 16 up to long edge 3840 and 8,294,400 px "
            "total (auto-clamped). 4K presets: 3840x2160 landscape, 2160x3840 "
            "portrait, 2880x2880 square, 2480x3312 3:4 (default: 1024x1024)"
        ),
    )
    parser.add_argument(
        "--n", type=int, default=1, help="Number of images (default: 1)"
    )
    parser.add_argument(
        "--output",
        default=str(Path.home() / "Downloads" / "gpt-image"),
        help="Output directory (default: ~/Downloads/gpt-image)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Basename for output files (default: gpt-image-<timestamp>)",
    )
    parser.add_argument("--quality", choices=["low", "medium", "high", "xhigh", "max", "auto"],
                        help="Optional quality; omitted preserves API auto default")
    parser.add_argument("--provider", choices=["auto", "azure", "newapi"],
                        default="auto", help="auto prefers Azure, then NewAPI")
    parser.add_argument("--variant", choices=VARIANTS,
                        help="sunburst: quality (default); flare: speed; other variant on 429")
    parser.add_argument("--azure-retries", type=int, default=0,
                        help="429 retries per variant before switching (default: 0)")
    parser.add_argument(
        "--edit",
        action="append",
        default=[],
        metavar="PATH",
        help="Path to input image for edit mode. Repeat for multi-image input "
        "(e.g., --edit a.png --edit b.png). When provided, routes to "
        "images.edit (image+prompt → edited image) instead of images.generate.",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["jpg", "jpeg", "png", "webp"],
        default="jpg",
        help="Output format (default: jpg). ~75%% smaller than png for typical "
        "photo/illustration output. Use png when transparency is needed or "
        "when the image is an icon/logo/diagram with pixel-exact sharp edges.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Max concurrent API calls when --n > 1 (default: 5, capped by --n).",
    )
    args = parser.parse_args()
    args.size = clamp_size(args.size)

    # Normalize: jpg ↔ jpeg — API wants "jpeg", filename extension is "jpg"
    api_format = "jpeg" if args.fmt == "jpg" else args.fmt
    ext = "jpg" if args.fmt in ("jpg", "jpeg") else args.fmt

    # Validate edit image paths up front
    edit_paths: list[Path] = []
    for raw in args.edit:
        p = Path(raw).expanduser().resolve()
        if not p.is_file():
            print(f"error: --edit path not found: {p}", file=sys.stderr)
            return 2
        edit_paths.append(p)

    creds = load_credentials()
    variant = args.variant or creds.get("GPT_IMAGE_VARIANT", "sunburst")
    if variant not in VARIANTS or args.n < 1 or args.azure_retries < 0:
        parser.error("invalid variant, image count, or retries")
    other = "flare" if variant == "sunburst" else "sunburst"
    provider = args.provider
    if provider == "auto":
        provider = "azure" if creds.get("AZURE_OPENAI_API_KEY") and creds.get("AZURE_OPENAI_ENDPOINT") else "newapi"
    builder = build_azure_client if provider == "azure" else build_newapi_client
    primary, fallback = builder(creds, variant), builder(creds, other)
    if primary[0] is None:
        print(f"error: {provider} credentials missing; see {CONFIG_FILE}", file=sys.stderr)
        return 2
    output_dir = Path(args.output).expanduser()
    basename = args.name or f"gpt-image-{int(time.time())}"

    def _worker(i: int) -> Path:
        result = generate_with_fallback(
            primary, fallback, args.prompt, args.size, args.azure_retries,
            edit_paths or None, api_format, args.quality,
        )
        return save_image(result, output_dir, basename, i if args.n > 1 else None, ext=ext)

    # Dispatch: sync for n=1 (no thread overhead), pool for n>1.
    paths: list[Path | None] = [None] * args.n
    any_failed = False
    if args.n == 1:
        try:
            paths[0] = _worker(0)
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            any_failed = True
    else:
        workers = max(1, min(args.n, args.concurrency))
        print(
            f"[dispatch] generating {args.n} images with {workers} concurrent workers",
            file=sys.stderr,
        )
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_worker, i): i for i in range(args.n)}
            for fut in as_completed(futures):
                i = futures[fut]
                try:
                    paths[i] = fut.result()
                except Exception as e:
                    any_failed = True
                    print(f"[worker#{i}] failed: {e}", file=sys.stderr)

    # Print completed paths in original order; failed slots show a marker.
    for i, p in enumerate(paths):
        if p is not None:
            print(p)
        else:
            print(f"# failed: index {i}", file=sys.stderr)

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
