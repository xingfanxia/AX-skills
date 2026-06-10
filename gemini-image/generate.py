#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-genai>=1.52.0", "Pillow>=10.0.0", "python-dotenv>=1.0.0"]
# ///
"""Google Gemini image generation (Nano Banana 2 / Nano Banana Pro).

Successor of the retired nanobanana plugin — same CLI shape.

Usage:
    generate.py "prompt" [--model nb2|pro] [--resolution 2K] [--aspect 16:9]
                         [--output DIR] [--name NAME] [--n N] [--reference IMG]
                         [--ab-test]

Reads GEMINI_API_KEY from environment (preferred) or from a .env file
next to this script.  See SKILL.md for setup.

Sister skill to `gpt-image` — same shape, different provider.  Pick by
aesthetic preference: Gemini's baseline tends toward soft / illustrated /
photographic-natural; GPT Image tends toward sharper / more graphic /
better text rendering.  Both can do every category.

Multi-reference editing: pass --reference up to 14 times to seed the
generation with reference images (background swap, character consistency
across scenes, style transfer).  GPT Image cannot accept reference images.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# Load .env from script directory (allows the symlinked install to keep
# its key alongside the script without polluting the repo).
_script_dir = Path(__file__).parent
load_dotenv(_script_dir / ".env")

DEFAULT_RESOLUTION = "2K"
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_OUTPUT_DIR = str(Path.home() / "Downloads" / "gemini-image")
MODEL_MAP = {
    "nb2": "gemini-3.1-flash-image",  # Nano Banana 2 — Flash speed, default
    "pro": "gemini-3-pro-image",      # Nano Banana Pro — highest quality
}

MIME_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate images with Google Gemini")
    p.add_argument("prompt", type=str, help="Image prompt")
    p.add_argument(
        "--resolution",
        choices=["1K", "2K", "4K"],
        default=DEFAULT_RESOLUTION,
        help=f"Output resolution (default: {DEFAULT_RESOLUTION})",
    )
    p.add_argument(
        "--aspect",
        default=DEFAULT_ASPECT_RATIO,
        help=f"Aspect ratio, e.g. 1:1, 16:9, 9:16 (default: {DEFAULT_ASPECT_RATIO})",
    )
    p.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    p.add_argument(
        "--name",
        default=None,
        help="Stable filename stem (default: timestamp). For --n>1, suffix _1.._N is appended.",
    )
    p.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of images to generate sequentially (default: 1)",
    )
    p.add_argument(
        "--reference",
        action="append",
        default=[],
        help="Reference image path (repeatable, max 14)",
    )
    p.add_argument(
        "--model",
        choices=sorted(MODEL_MAP),
        default="nb2",
        help="Model tier: nb2 (Nano Banana 2, default) or pro (Nano Banana Pro)",
    )
    p.add_argument(
        "--ab-test",
        action="store_true",
        help="Generate with BOTH models for side-by-side comparison (filenames get _nb2/_pro suffix)",
    )
    return p.parse_args(argv)


def output_path_for(
    args: argparse.Namespace,
    mime_type: str,
    idx: int | None,
    tag: str | None = None,
) -> Path:
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = MIME_TO_EXT.get(mime_type, ".png")
    stem = args.name or datetime.now().strftime("%Y%m%d_%H%M%S")
    if tag:
        stem = f"{stem}_{tag}"
    suffix = "" if idx is None else f"_{idx}"
    return out_dir / f"{stem}{suffix}{ext}"


def build_contents(prompt: str, reference_images: list[str]) -> object:
    if not reference_images:
        return prompt
    parts: list = []
    for path in reference_images:
        if not Path(path).exists():
            raise FileNotFoundError(f"Reference image not found: {path}")
        parts.append(Image.open(path))
    parts.append(prompt)
    return parts


def generate_one(
    client: "genai.Client",
    args: argparse.Namespace,
    idx: int | None,
    model_id: str,
    tag: str | None = None,
) -> str | None:
    contents = build_contents(args.prompt, args.reference)
    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=args.aspect,
                image_size=args.resolution,
            ),
        ),
    )
    for part in response.parts:
        if part.text is not None:
            print(f"[Info] {part.text}")
        elif part.inline_data is not None:
            mime_type = part.inline_data.mime_type or "image/png"
            image = part.as_image()
            out = output_path_for(args, mime_type, idx, tag)
            image.save(str(out))
            print(f"[Success] Image saved: {out}")
            return str(out)
    print("[Warning] Response did not contain an image")
    return None


def main() -> int:
    args = parse_args()

    if args.reference and len(args.reference) > 14:
        print("[Error] Maximum 14 reference images allowed", file=sys.stderr)
        return 2

    if args.n < 1:
        print("[Error] --n must be >= 1", file=sys.stderr)
        return 2

    client = genai.Client()

    tiers = sorted(MODEL_MAP) if args.ab_test else [args.model]
    failures = 0
    for tier in tiers:
        model_id = MODEL_MAP[tier]
        tag = tier if args.ab_test else None
        if args.n == 1:
            if generate_one(client, args, None, model_id, tag) is None:
                failures += 1
        else:
            for i in range(1, args.n + 1):
                if generate_one(client, args, i, model_id, tag) is None:
                    failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
