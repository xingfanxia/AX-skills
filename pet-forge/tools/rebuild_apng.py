"""Rebuild an APNG from PNG frames with a unified palette.

Usage:
  python rebuild_apng.py <input_frames_dir> <output_apng>
"""
import argparse
import glob
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

TARGET_HEIGHT = 200
TARGET_FPS = 8
MAX_COLORS = 192
PLAYS = 1


def parse_args():
    parser = argparse.ArgumentParser(description="Quantize PNG frames with a shared palette and assemble APNG.")
    parser.add_argument("input_frames_dir", help="directory containing PNG frames")
    parser.add_argument("output_apng", help="output APNG path")
    parser.add_argument("--pattern", default="*.png", help="frame filename glob, default *.png")
    parser.add_argument("--height", type=int, default=TARGET_HEIGHT, help="target frame height")
    parser.add_argument("--fps", type=int, default=TARGET_FPS, help="APNG frame rate")
    parser.add_argument("--max-colors", type=int, default=MAX_COLORS, help="global palette color count")
    parser.add_argument("--plays", type=int, default=PLAYS, help="APNG play count: 0 loops forever, 1 plays once")
    return parser.parse_args()


def resize_frame(path: str, height: int) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    ratio = height / img.height
    new_w = int(img.width * ratio)
    return img.resize((new_w, height), Image.LANCZOS)


def main():
    args = parse_args()
    frames = sorted(glob.glob(str(Path(args.input_frames_dir) / args.pattern)))
    if not frames:
        raise SystemExit(f"No frames matched {Path(args.input_frames_dir) / args.pattern}")

    output_apng = Path(args.output_apng)
    output_apng.parent.mkdir(parents=True, exist_ok=True)
    workdir = tempfile.mkdtemp(prefix="pet-forge-rebuild-")

    try:
        print("Building unified palette from all frames...")
        resized = [resize_frame(frame, args.height) for frame in frames]
        max_w = max(img.width for img in resized)
        atlas = Image.new("RGBA", (max_w * len(resized), args.height), (0, 0, 0, 0))
        for i, img in enumerate(resized):
            atlas.paste(img, (max_w * i, 0))

        palette_img = atlas.quantize(colors=args.max_colors, method=Image.Quantize.FASTOCTREE)

        print("Applying unified palette to each frame...")
        quantized_dir = Path(workdir) / "quantized"
        quantized_dir.mkdir(parents=True, exist_ok=True)
        for i, img in enumerate(resized):
            alpha = img.getchannel("A")
            quantized = img.convert("RGB").quantize(palette=palette_img, dither=Image.Dither.NONE).convert("RGBA")
            quantized.putalpha(alpha)
            quantized.save(quantized_dir / f"frame_{i + 1:03d}.png", optimize=True)

        print(f"Assembling APNG ({args.fps}fps, plays={args.plays})...")
        result = subprocess.run([
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-i", str(quantized_dir / "frame_%03d.png"),
            "-plays", str(args.plays), "-f", "apng", str(output_apng)
        ], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg APNG assembly failed")

        size_kb = os.path.getsize(output_apng) / 1024
        print(f"Done -> {output_apng} ({size_kb:.0f}KB)")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
