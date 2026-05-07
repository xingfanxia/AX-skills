#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=1.50"]
# ///
"""GPT Image generation with Azure-first, OpenAI-direct fallback.

Usage:
    generate.py "prompt" [--size 1024x1024] [--n 1] [--output DIR] [--name NAME]
                         [--provider auto|azure|openai] [--azure-retries 3]

Reads credentials from environment variables (preferred) or
~/.config/gpt-image/credentials. See this skill's SKILL.md for setup.

Rate-limit behaviour:
  * Azure GPT Image has a strict 10 RPM limit. In --n N mode we sleep 7s
    between Azure calls for safety.
  * On Azure 429: exponential backoff (5s, 10s, 20s) for --azure-retries
    attempts, then fall through to OpenAI direct if OPENAI_API_KEY is set.
  * OpenAI direct gets 2 retries on 429 before bailing.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import APIError, AzureOpenAI, OpenAI, RateLimitError

CONFIG_FILE = Path.home() / ".config" / "gpt-image" / "credentials"

CRED_KEYS = (
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_DEPLOYMENT",
    "AZURE_OPENAI_MODEL",
    "AZURE_OPENAI_API_VERSION",
    "OPENAI_API_KEY",
    "OPENAI_IMAGE_MODEL",
)

# Azure's quirk: the deployment name (URL path) and the underlying model name
# (request body) are different. For the user's setup:
#   deployment = "gpt-image-2-1"   # what the user named it in Azure
#   model      = "gpt-image-2"     # what Azure calls the actual model
# When calling images.edit on the classic deployment path, Azure requires the
# REAL model name in the request body — passing the deployment name there
# raises "The model 'X' does not exist." Set AZURE_OPENAI_MODEL explicitly to
# override the default.
DEFAULT_AZURE_MODEL = "gpt-image-2"

# Default Azure API version — 2025-04-01-preview is what the user's
# gpt-image-2-1 deployment accepts for both generations and edits (classic
# deployment path). The unified /openai/v1 endpoint supports generations
# but NOT edits as of 2026-04, so we use AzureOpenAI which routes to
# /openai/deployments/{deployment}/images/{op}?api-version=X natively.
DEFAULT_AZURE_API_VERSION = "2025-04-01-preview"


def load_credentials() -> dict[str, str]:
    creds: dict[str, str] = {}
    if CONFIG_FILE.exists():
        for raw in CONFIG_FILE.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip().strip('"').strip("'")
    for k in CRED_KEYS:
        v = os.environ.get(k)
        if v:
            creds[k] = v  # env wins over file
    return creds


def build_azure_client(creds: dict[str, str]) -> tuple[AzureOpenAI | None, str | None]:
    """Return (AzureOpenAI client, model_name) or (None, None).

    Two Azure concepts that confusingly share names:
      * Deployment name — e.g. `gpt-image-2-1`; used in the URL path
      * Model name       — e.g. `gpt-image-2`;   sent in the request body

    The AzureOpenAI client routes to
    /openai/deployments/{deployment}/images/{op}?api-version=X via
    `azure_deployment` kwarg, and the caller passes `model=<real model name>`
    at call time which ends up in the request body. This matters because
    the classic edit endpoint rejects requests where body `model` equals the
    deployment rather than the real model name ("The model 'X' does not exist").

    Accepts endpoints with or without /openai/v1 suffix — strips it.
    """
    endpoint = creds.get("AZURE_OPENAI_ENDPOINT")
    api_key = creds.get("AZURE_OPENAI_API_KEY")
    if not (endpoint and api_key):
        return None, None
    base = endpoint.rstrip("/")
    for suffix in ("/openai/v1", "/openai"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    deployment = creds.get("AZURE_OPENAI_DEPLOYMENT", "gpt-image-2-1")
    model = creds.get("AZURE_OPENAI_MODEL", DEFAULT_AZURE_MODEL)
    api_version = creds.get("AZURE_OPENAI_API_VERSION", DEFAULT_AZURE_API_VERSION)
    client = AzureOpenAI(
        azure_endpoint=base,
        api_key=api_key,
        api_version=api_version,
        azure_deployment=deployment,
    )
    return client, model


def build_openai_client(creds: dict[str, str]) -> tuple[OpenAI | None, str | None]:
    api_key = creds.get("OPENAI_API_KEY")
    if not api_key:
        return None, None
    model = creds.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
    return OpenAI(api_key=api_key), model


def generate_one(
    client: OpenAI,
    model: str,
    prompt: str,
    size: str,
    retries: int,
    label: str,
    edit_images: list[Path] | None = None,
    output_format: str = "jpeg",
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
        except RateLimitError:
            if attempt == retries:
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
        description="Generate images via Azure GPT Image, fallback to OpenAI direct"
    )
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument(
        "--size",
        default="1024x1024",
        help="Size: 1024x1024 | 1792x1024 | 1024x1792 (default: 1024x1024)",
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
    parser.add_argument(
        "--provider",
        choices=["auto", "azure", "openai"],
        default="auto",
        help="Provider: auto = Azure → OpenAI fallback; azure = Azure only; "
        "openai = OpenAI only (default: auto)",
    )
    parser.add_argument(
        "--azure-retries",
        type=int,
        default=3,
        help="Retries on Azure 429 before falling back (default: 3)",
    )
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
    azure_client, azure_model = build_azure_client(creds)
    openai_client, openai_model = build_openai_client(creds)

    if args.provider == "azure" and azure_client is None:
        print(
            "error: --provider azure but AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT missing. "
            f"Set env vars or create {CONFIG_FILE}",
            file=sys.stderr,
        )
        return 2
    if args.provider == "openai" and openai_client is None:
        print(
            "error: --provider openai but OPENAI_API_KEY missing. "
            f"Set env var or create {CONFIG_FILE}",
            file=sys.stderr,
        )
        return 2
    if azure_client is None and openai_client is None:
        print(
            "error: no credentials found.\n"
            "  set env vars: AZURE_OPENAI_API_KEY (+ AZURE_OPENAI_ENDPOINT) "
            "and/or OPENAI_API_KEY\n"
            f"  or create {CONFIG_FILE} — see ~/.codex/skills/gpt-image/SKILL.md",
            file=sys.stderr,
        )
        return 2

    output_dir = Path(args.output).expanduser()
    basename = args.name or f"gpt-image-{int(time.time())}"

    # Shared routing state across worker threads.
    # fallback_event: once ANY worker hits an exhausted Azure + we have an
    # OpenAI fallback configured, flip this so subsequent workers skip Azure
    # and go straight to OpenAI. Avoids N workers all retrying Azure in
    # parallel when Azure is obviously down/saturated.
    fallback_event = threading.Event()
    azure_allowed = args.provider in ("auto", "azure") and azure_client is not None
    openai_allowed = args.provider in ("auto", "openai") and openai_client is not None
    if args.provider == "openai":
        fallback_event.set()

    def _worker(i: int) -> Path:
        """Generate one image (index i). Thread-safe; clients are shared."""
        use_oai_now = fallback_event.is_set() or not azure_allowed
        result = None
        if not use_oai_now:
            try:
                result = generate_one(
                    azure_client,
                    azure_model,
                    args.prompt,
                    args.size,
                    args.azure_retries,
                    f"azure#{i}",
                    edit_images=edit_paths or None,
                    output_format=api_format,
                )
            except (RateLimitError, APIError) as e:
                if openai_allowed and args.provider != "azure":
                    if not fallback_event.is_set():
                        fallback_event.set()
                        print(
                            f"[azure#{i}] exhausted, switching batch to OpenAI direct: "
                            f"{type(e).__name__}",
                            file=sys.stderr,
                        )
                else:
                    raise RuntimeError(f"azure failed — {e}") from e
        if result is None:
            if not openai_allowed:
                raise RuntimeError(
                    "azure failed and no OpenAI fallback configured"
                )
            result = generate_one(
                openai_client,
                openai_model,
                args.prompt,
                args.size,
                2,
                f"openai#{i}",
                edit_images=edit_paths or None,
                output_format=api_format,
            )
        index = i if args.n > 1 else None
        return save_image(result, output_dir, basename, index, ext=ext)

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
