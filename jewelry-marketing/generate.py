#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31"]
# ///
"""jewelry-marketing — one-photo-in, full-XHS-bundle-out.

Distilled from shichuan (识川) production system, narrowed for jewelry merchants.

Usage:
    generate.py PRODUCT.jpg [options]

Auto-routes:
    finished_product  → 12 marketing images + 6-style copy + analysis JSON
    raw_material      → 8 design images (sketch canonical, 7 dependents)
                        + analysis JSON

Options:
    --output DIR              output dir (default: ./jewelry_bundle/<timestamp>)
    --mode auto|marketing|design   (default: auto)
    --templates A,B,C         only generate these (default: full bundle)
    --jewelry-type ring|pendant|earring|brooch  (design mode subject)
    --copy-only               skip image gen, just write analysis.json + copy.md
    --analyze-only            skip everything, just write analysis.json
    --seller-description TEXT extra context for analyzer
    --concurrency N           parallel image gens (default 4)
    --image-format jpeg|png   output image format (default jpeg)

Credentials (env vars, or ~/.config/gpt-image/credentials):
    GEMINI_API_KEY            — required for analysis (Gemini Flash 3, free tier OK)
    OPENAI_API_KEY            — required for image gen (gpt-image-2 via OpenAI direct)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests

# Make sibling `prompts` package importable
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from prompts import (  # noqa: E402
    build_analysis_prompt,
    parse_analysis_json,
    MARKETING_BUILDERS,
    MARKETING_ORDER,
    PHOTO_TEMPLATES,
    OMIT_REFERENCE,
    UNIVERSAL_SUFFIX,
    REALISM_SUFFIX,
    DESIGN_BUILDERS,
    DESIGN_ORDER,
    DESIGN_DEPS,
    format_copy_md,
)
from prompts.helpers import detect_jewelry_type  # noqa: E402


# ─── Credential loading ─────────────────────────────────────────

CRED_FILE = Path.home() / ".config" / "gpt-image" / "credentials"


def _load_cred_file() -> dict[str, str]:
    """Load KEY=VALUE pairs from ~/.config/gpt-image/credentials."""
    if not CRED_FILE.exists():
        return {}
    out: dict[str, str] = {}
    for line in CRED_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _env_or_file(key: str, file_creds: dict[str, str]) -> Optional[str]:
    """Env var wins; fall back to credentials file."""
    return os.environ.get(key) or file_creds.get(key)


def load_credentials() -> dict[str, Optional[str]]:
    """Discover credentials from env + ~/.config/gpt-image/credentials."""
    file_creds = _load_cred_file()
    return {
        "gemini_key": _env_or_file("GEMINI_API_KEY", file_creds),
        "openai_key": _env_or_file("OPENAI_API_KEY", file_creds)
        or _env_or_file("OPENAI_API_KEY_GPT_IMAGE", file_creds),
    }


# ─── Gemini analysis ────────────────────────────────────────────

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_ANALYSIS_MODEL = "gemini-3-flash-preview"


def analyze_product(
    image_b64s: list[str],
    api_key: str,
    seller_description: Optional[str] = None,
) -> dict[str, Any]:
    """Call Gemini Flash 3 with the analysis prompt + product images."""
    prompt = build_analysis_prompt(len(image_b64s), seller_description)

    parts: list[dict[str, Any]] = []
    for b64 in image_b64s:
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": b64}})
    parts.append({"text": prompt})

    url = f"{GEMINI_API_BASE}/{GEMINI_ANALYSIS_MODEL}:generateContent"
    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["TEXT"]},
    }

    resp = requests.post(
        url,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        json=body,
        timeout=120,
    )
    if not resp.ok:
        raise RuntimeError(
            f"Gemini analysis failed: HTTP {resp.status_code}: {resp.text[:300]}"
        )

    data = resp.json()
    text = ""
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            t = part.get("text")
            if t:
                text += t

    if not text:
        raise RuntimeError(f"Gemini returned no text. Raw: {json.dumps(data)[:300]}")

    return parse_analysis_json(text)


# ─── GPT Image 2 generation (OpenAI direct) ────────────────────

OPENAI_RETRIES = 2
REQUEST_TIMEOUT = 240


class RateLimitError(Exception):
    pass


class ProviderError(Exception):
    pass


def _extract_b64(resp: requests.Response, op: str) -> str:
    if resp.status_code == 429:
        raise RateLimitError(f"openai {op} 429")
    if not resp.ok:
        raise ProviderError(f"openai {op} {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    items = data.get("data") or []
    if not items:
        raise ProviderError(f"openai {op}: empty data array")
    b64 = items[0].get("b64_json")
    if not b64:
        raise ProviderError(f"openai {op}: no b64_json (returned URL?)")
    return b64


def _openai_generate(prompt: str, key: str, size: str, output_format: str) -> str:
    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        json={
            "model": "gpt-image-2",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": "medium",
            "output_format": output_format,
            **({"output_compression": 85} if output_format != "png" else {}),
        },
        timeout=REQUEST_TIMEOUT,
    )
    return _extract_b64(resp, "generate")


def _openai_edit(
    prompt: str, image_bytes: bytes, key: str, size: str, output_format: str
) -> str:
    files = {"image": ("input.jpg", image_bytes, "image/jpeg")}
    data = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "n": "1",
        "size": size,
        "quality": "medium",
        "output_format": output_format,
    }
    if output_format != "png":
        data["output_compression"] = "85"
    resp = requests.post(
        "https://api.openai.com/v1/images/edits",
        headers={"Authorization": f"Bearer {key}"},
        files=files,
        data=data,
        timeout=REQUEST_TIMEOUT,
    )
    return _extract_b64(resp, "edit")


def _retry(fn, retries: int, label: str, base_backoff: float = 3.0):
    """Exp-backoff retry on rate limits (429)."""
    backoff = base_backoff
    for attempt in range(retries + 1):
        try:
            return fn()
        except RateLimitError:
            if attempt == retries:
                raise
            print(
                f"  [retry] {label} rate-limited, sleeping {backoff:.0f}s "
                f"({attempt + 1}/{retries + 1})",
                file=sys.stderr,
            )
            time.sleep(backoff)
            backoff *= 2


def generate_image(
    prompt: str,
    creds: dict[str, Optional[str]],
    image_bytes: Optional[bytes] = None,
    size: str = "1024x1536",
    output_format: str = "jpeg",
) -> tuple[bytes, str]:
    """Generate one image via OpenAI direct (gpt-image-2). Returns (bytes, "openai").

    If image_bytes is given, uses image-edit endpoint (img2img); else
    text-to-image generate.
    """
    openai_key = creds.get("openai_key")
    if not openai_key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Put it in env or ~/.config/gpt-image/credentials."
        )

    if image_bytes:
        b64 = _retry(
            lambda: _openai_edit(prompt, image_bytes, openai_key, size, output_format),
            OPENAI_RETRIES,
            "edit",
        )
    else:
        b64 = _retry(
            lambda: _openai_generate(prompt, openai_key, size, output_format),
            OPENAI_RETRIES,
            "generate",
        )
    return base64.b64decode(b64), "openai"


# ─── Marketing pipeline ─────────────────────────────────────────


def build_marketing_prompt(template: str, analysis: dict) -> tuple[str, bool]:
    """Returns (final_prompt, omit_reference)."""
    builder = MARKETING_BUILDERS.get(template)
    if not builder:
        raise ValueError(f"Unknown marketing template: {template}")

    raw = builder(analysis)
    needs_realism = template in PHOTO_TEMPLATES
    final = raw + (REALISM_SUFFIX if needs_realism else "") + UNIVERSAL_SUFFIX
    return final, template in OMIT_REFERENCE


def run_marketing_pipeline(
    analysis: dict,
    image_bytes: bytes,
    creds: dict[str, Optional[str]],
    output_dir: Path,
    templates: list[str],
    concurrency: int = 4,
    image_format: str = "jpeg",
) -> dict[str, Any]:
    """Generate marketing bundle in parallel. Returns summary dict."""
    marketing_dir = output_dir / "marketing"
    marketing_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {"success": [], "failed": []}
    started = time.time()

    print(f"\n[marketing] Generating {len(templates)} templates "
          f"with concurrency={concurrency}...")

    def task(idx_template: tuple[int, str]) -> tuple[str, str, str]:
        idx, template = idx_template
        try:
            prompt, omit_ref = build_marketing_prompt(template, analysis)
            ref = None if omit_ref else image_bytes
            t0 = time.time()
            img_bytes, provider = generate_image(
                prompt, creds, image_bytes=ref, output_format=image_format
            )
            ext = "png" if image_format == "png" else "jpg"
            out_path = marketing_dir / f"{idx:02d}_{template}.{ext}"
            out_path.write_bytes(img_bytes)
            dt = time.time() - t0
            print(f"  ✓ {template:<20} ({provider}, {dt:.0f}s, {len(img_bytes)//1024}KB)")
            return ("success", template, str(out_path))
        except Exception as e:
            print(f"  ✗ {template:<20} FAILED: {e}", file=sys.stderr)
            return ("failed", template, str(e))

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        # Use original index from MARKETING_ORDER for stable filename numbering
        indexed = [
            (MARKETING_ORDER.index(t) + 1, t)
            for t in templates
            if t in MARKETING_ORDER
        ]
        for status, template, info in pool.map(task, indexed):
            if status == "success":
                results["success"].append({"template": template, "path": info})
            else:
                results["failed"].append({"template": template, "error": info})

    results["elapsed_seconds"] = round(time.time() - started, 1)
    return results


# ─── Design pipeline ────────────────────────────────────────────


def run_design_pipeline(
    analysis: dict,
    image_bytes: bytes,
    creds: dict[str, Optional[str]],
    output_dir: Path,
    templates: list[str],
    jewelry_type: str,
    concurrency: int = 4,
    image_format: str = "jpeg",
) -> dict[str, Any]:
    """Two-phase generation: sketch first, then dependents in parallel."""
    design_dir = output_dir / "design"
    design_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {"success": [], "failed": []}
    started = time.time()

    # Ensure sketch is generated if any dependent is requested
    has_dependents = any(t in DESIGN_DEPS for t in templates)
    needs_sketch = "sketch" in templates or has_dependents

    sketch_bytes: Optional[bytes] = None
    ext = "png" if image_format == "png" else "jpg"

    # ─── Phase 1: sketch (canonical, blocking) ───────────────────
    if needs_sketch:
        print(f"\n[design phase 1] Generating canonical sketch "
              f"(jewelry_type={jewelry_type})...")
        try:
            sketch_prompt = DESIGN_BUILDERS["sketch"](analysis, jewelry_type)
            t0 = time.time()
            sketch_bytes, provider = generate_image(
                sketch_prompt,
                creds,
                image_bytes=image_bytes,
                output_format=image_format,
            )
            dt = time.time() - t0
            if "sketch" in templates:
                idx = DESIGN_ORDER.index("sketch") + 1
                out_path = design_dir / f"{idx:02d}_sketch.{ext}"
                out_path.write_bytes(sketch_bytes)
                print(f"  ✓ sketch                ({provider}, {dt:.0f}s, {len(sketch_bytes)//1024}KB)")
                results["success"].append({"template": "sketch", "path": str(out_path)})
            else:
                print(f"  ✓ sketch (hidden prerequisite, {dt:.0f}s)")
        except Exception as e:
            err = f"Sketch generation failed: {e}"
            print(f"  ✗ sketch FAILED — cannot generate dependents: {e}", file=sys.stderr)
            results["failed"].append({"template": "sketch", "error": err})
            results["elapsed_seconds"] = round(time.time() - started, 1)
            return results

    # ─── Phase 2: dependents (parallel, share sketch as ref) ─────
    dependents = [t for t in templates if t in DESIGN_DEPS]

    if dependents and sketch_bytes:
        print(f"\n[design phase 2] Generating {len(dependents)} dependents "
              f"with concurrency={concurrency}...")

        def task(template: str) -> tuple[str, str, str]:
            try:
                prompt = DESIGN_BUILDERS[template](analysis, jewelry_type)
                t0 = time.time()
                img_bytes, provider = generate_image(
                    prompt,
                    creds,
                    image_bytes=sketch_bytes,
                    output_format=image_format,
                )
                idx = DESIGN_ORDER.index(template) + 1
                out_path = design_dir / f"{idx:02d}_{template}.{ext}"
                out_path.write_bytes(img_bytes)
                dt = time.time() - t0
                print(f"  ✓ {template:<20} ({provider}, {dt:.0f}s, {len(img_bytes)//1024}KB)")
                return ("success", template, str(out_path))
            except Exception as e:
                print(f"  ✗ {template:<20} FAILED: {e}", file=sys.stderr)
                return ("failed", template, str(e))

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            for status, template, info in pool.map(task, dependents):
                if status == "success":
                    results["success"].append({"template": template, "path": info})
                else:
                    results["failed"].append({"template": template, "error": info})

    results["elapsed_seconds"] = round(time.time() - started, 1)
    return results


# ─── CLI ────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Jewelry e-commerce marketing material generator (XHS-ready bundle)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("image", help="Path to product photo (jpg/png)")
    p.add_argument("--output", help="Output directory (default: ./jewelry_bundle/<timestamp>)")
    p.add_argument(
        "--mode",
        choices=["auto", "marketing", "design"],
        default="auto",
        help="Pipeline (default auto: route by analysis.input_type)",
    )
    p.add_argument(
        "--templates",
        help="Comma-separated template IDs (default: all in chosen pipeline)",
    )
    p.add_argument(
        "--jewelry-type",
        choices=["ring", "pendant", "earring", "brooch"],
        help="Design mode subject (default: inferred from analysis)",
    )
    p.add_argument(
        "--copy-only",
        action="store_true",
        help="Skip image gen, just write analysis.json + copy.md",
    )
    p.add_argument(
        "--analyze-only",
        action="store_true",
        help="Skip everything, just write analysis.json",
    )
    p.add_argument(
        "--seller-description",
        help="Extra context for analyzer (e.g., '天然 GIA 钻 1ct')",
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Parallel image gens (default 4 — bump higher if your OpenAI tier allows)",
    )
    p.add_argument(
        "--image-format",
        choices=["jpeg", "png"],
        default="jpeg",
        help="Output image format (default jpeg)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: Input image not found: {image_path}", file=sys.stderr)
        return 1

    creds = load_credentials()
    if not creds["gemini_key"]:
        print("ERROR: GEMINI_API_KEY not set (required for analysis).", file=sys.stderr)
        return 2

    # ─── Output dir ──────────────────────────────────────────────
    if args.output:
        output_dir = Path(args.output)
    else:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = Path("./jewelry_bundle") / ts
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📦 Output: {output_dir.resolve()}")

    # ─── Phase 1: analyze ────────────────────────────────────────
    print(f"\n🔍 Analyzing {image_path.name} with Gemini Flash 3...")
    image_bytes = image_path.read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode()

    t0 = time.time()
    analysis = analyze_product(
        [image_b64], creds["gemini_key"], args.seller_description
    )
    print(f"  ✓ {time.time() - t0:.1f}s — input_type="
          f"{analysis.get('input_type', 'unknown')} "
          f"(conf={analysis.get('input_type_confidence', 'unknown')})")

    # Save analysis JSON
    (output_dir / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2)
    )
    print(f"  → analysis.json")

    if args.analyze_only:
        print("\n✅ analyze-only mode — done.")
        return 0

    # Always write copy.md (it's free — no extra API calls)
    copy_md = format_copy_md(analysis)
    (output_dir / "copy.md").write_text(copy_md)
    print(f"  → copy.md")

    if args.copy_only:
        print("\n✅ copy-only mode — done (no images generated).")
        return 0

    # ─── Phase 2: pick pipeline ──────────────────────────────────
    if args.mode == "auto":
        input_type = analysis.get("input_type", "finished_product")
        confidence = analysis.get("input_type_confidence", "high")
        if input_type == "raw_material":
            pipeline = "design"
        else:
            pipeline = "marketing"
        print(f"\n🚦 Auto-routed → {pipeline} pipeline (input_type={input_type}, conf={confidence})")
    else:
        pipeline = args.mode
        print(f"\n🚦 Forced → {pipeline} pipeline (--mode={pipeline})")

    # ─── Phase 3: image gen ──────────────────────────────────────
    if pipeline == "marketing":
        templates = (
            args.templates.split(",")
            if args.templates
            else MARKETING_ORDER
        )
        # Filter to known IDs only
        valid = [t for t in templates if t in MARKETING_BUILDERS]
        invalid = [t for t in templates if t not in MARKETING_BUILDERS]
        if invalid:
            print(f"  ⚠️  Skipping unknown marketing templates: {invalid}", file=sys.stderr)
        if not valid:
            print("ERROR: No valid templates to generate.", file=sys.stderr)
            return 3
        results = run_marketing_pipeline(
            analysis, image_bytes, creds, output_dir, valid,
            concurrency=args.concurrency,
            image_format=args.image_format,
        )
    else:  # design
        templates = (
            args.templates.split(",")
            if args.templates
            else DESIGN_ORDER
        )
        valid = [t for t in templates if t in DESIGN_BUILDERS]
        invalid = [t for t in templates if t not in DESIGN_BUILDERS]
        if invalid:
            print(f"  ⚠️  Skipping unknown design templates: {invalid}", file=sys.stderr)
        if not valid:
            print("ERROR: No valid templates to generate.", file=sys.stderr)
            return 3

        jt = args.jewelry_type or detect_jewelry_type(analysis)
        results = run_design_pipeline(
            analysis, image_bytes, creds, output_dir, valid,
            jewelry_type=jt,
            concurrency=args.concurrency,
            image_format=args.image_format,
        )

    # ─── Summary ─────────────────────────────────────────────────
    summary = {
        "input_image": str(image_path.resolve()),
        "input_type": analysis.get("input_type"),
        "category": analysis.get("category"),
        "subcategory": analysis.get("subcategory"),
        "pipeline": pipeline,
        "results": results,
        "generated_at": datetime.now().isoformat(),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)
    )

    succ = len(results["success"])
    fail = len(results["failed"])
    elapsed = results["elapsed_seconds"]
    print(f"\n{'─' * 60}")
    print(f"✅ Done: {succ} succeeded, {fail} failed in {elapsed}s")
    print(f"   Bundle: {output_dir.resolve()}")
    return 0 if fail == 0 else 4


if __name__ == "__main__":
    sys.exit(main())
