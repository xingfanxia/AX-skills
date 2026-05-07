"""Check extracted PNG frames for unexpected dark pixels.

Usage:
  python check_dark.py <frames_dir> [more_frames_dirs...]
"""
import argparse
import glob
from pathlib import Path

from PIL import Image


def parse_args():
    parser = argparse.ArgumentParser(description="Find frames with too many visible dark pixels in a region.")
    parser.add_argument("frames_dir", nargs="+", help="one or more directories containing PNG frames")
    parser.add_argument("--pattern", default="frame_*.png", help="frame filename glob")
    parser.add_argument("--dark-max", type=int, default=40, help="RGB max value counted as dark")
    parser.add_argument("--alpha-min", type=int, default=128, help="minimum alpha counted as visible")
    parser.add_argument("--ratio", type=float, default=0.03, help="problem threshold: dark pixels / visible pixels")
    return parser.parse_args()


def check_dir(frames_dir: Path, pattern: str, dark_max: int, alpha_min: int, ratio_limit: float):
    frames = sorted(glob.glob(str(frames_dir / pattern)))
    print(f"Checking {len(frames)} frames in {frames_dir}...")
    problem = []

    for i, frame_path in enumerate(frames):
        img = Image.open(frame_path).convert("RGBA")
        w, h = img.size
        region = img.crop((int(w * 0.6), int(h * 0.2), w, int(h * 0.8)))
        px = list(region.getdata())
        dark = sum(1 for r, g, b, a in px if a > alpha_min and r < dark_max and g < dark_max and b < dark_max)
        visible = sum(1 for _, _, _, a in px if a > alpha_min)
        if visible > 0 and dark / visible > ratio_limit:
            ratio = dark / visible * 100
            problem.append((i + 1, ratio))
            print(f"  PROBLEM frame_{i + 1:03d}: {ratio:.1f}% dark pixels")

    if not problem:
        print("  No dark frames found")
    return problem


def main():
    args = parse_args()
    total = 0
    for frames_dir in args.frames_dir:
        total += len(check_dir(Path(frames_dir), args.pattern, args.dark_max, args.alpha_min, args.ratio))
    print(f"\nDone: {total} problem frame(s)")


if __name__ == "__main__":
    main()
