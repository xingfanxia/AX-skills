#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""pet-forge — text/photo → 10-state APNG desk pet, ready for clawd-on-desk.

Usage:
    generate.py --description "chubby gold tabby Munchkin with jade-green eyes" --pet-id munchkin
    generate.py --photo cat.jpg --breed Munchkin --pet-id xiaofei --display-name "小肥"
    generate.py --pet-id munchkin --only notification thinking   # retry just these states

Produces:
    output/<pet-id>/refs/                     # 7 character-anchor PNGs
    output/<pet-id>/animations/<state>/...    # 10 mp4s + 10 result.apngs
    {clawd-on-desk}/themes/<pet-id>/          # installed theme + 10 APNGs

Cost: ~$2.30/pet (7 gpt-image-2 + 10 Doubao). Wall: ~6-8 min.

Read SKILL.md for the full recipe and references/7-critical-lessons.md before
tweaking. The defaults here encode hard-won knowledge; resist the urge to
"simplify" them.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
TOOLS_DIR = SCRIPT_DIR / "tools"
PROMPTS_DIR = SCRIPT_DIR / "prompts"

ALL_STATES = [
    "idle-dozing", "sleeping", "working-typing", "thinking", "happy",
    "notification", "react-poke", "error", "collapse-sleep", "wake",
]

# States that need their own pose-ref (Lesson 1: state-pose refs are the liveliness unlock)
POSE_REF_STATES = ["idle-dozing", "happy", "thinking", "working-typing", "notification", "error"]

# Pose-ref prompts. Anchored on main-ref via gpt-image-2 --edit. Generic
# enough to work for any cartoon-cat character; the CHARACTER_PREFIX from
# template.js carries breed/coat/eye details.
POSE_REF_PROMPTS = {
    "idle-dozing": (
        "Same cat from reference image, now in DROWSY DOZING POSE: lying on belly, "
        "body relaxed and droopy, eyes half-closed/sleepy, head tilted forward as if "
        "about to nod off. Match character details exactly from reference. "
        "Solid bright green chroma key background #00B140."
    ),
    "happy": (
        "Same cat from reference image, now in PURE JOY CELEBRATION POSE: tail "
        "straight up, eyes squinted into HUGE happy crescent shapes (^^), little "
        "bounce in the body, sparkles ✨ and tiny hearts ♥ floating around. "
        "Solid bright green chroma key background #00B140."
    ),
    "thinking": (
        "Same cat from reference image, now in THOUGHTFUL PONDERING POSE: lying "
        "on belly tilted slightly, one front paw raised toward chin in a thoughtful "
        "gesture, head tilted curiously, with a yellow question mark '?' floating "
        "above. Match character details exactly. "
        "Solid bright green chroma key background #00B140."
    ),
    "working-typing": (
        "Same cat from reference image, now in HARDWORKING-AT-LAPTOP POSE: lying "
        "belly-down on a small wood surface with a chibi laptop in front, both "
        "front paws on the keyboard, focused intent expression. "
        "Solid bright green chroma key background #00B140."
    ),
    "notification": (
        "Same cat from reference image, now in ALERT NOTIFICATION POSE: sitting "
        "upright, eyes wide and surprised looking up at a bright red exclamation "
        "mark '!' floating in the upper right. Ears perked attentive. Match "
        "character details exactly INCLUDING ear shape — small triangular rounded "
        "tips, NOT tall pointy fox ears. "
        "Solid bright green chroma key background #00B140."
    ),
    "error": (
        "Same cat from reference image, now in DAZED FLAT-OUT POSE: lying flat on "
        "side, X-eyes (×_×), tongue lolling out, with a small puff cloud and "
        "yellow star particles floating around the head. "
        "Solid bright green chroma key background #00B140."
    ),
}

# Heuristics for detecting "green-eyed" pets from descriptions
GREEN_EYE_KEYWORDS = ["green eye", "green-eye", "jade", "翡翠", "绿眼", "olive eye", "emerald"]
FLUFFY_KEYWORDS = ["ragdoll", "persian", "maine coon", "norwegian forest", "siberian", "long-haired", "long coat", "fluffy", "布偶", "波斯", "缅因"]


# ─── Data classes ─────────────────────────────────────────────

@dataclass
class PetSpec:
    pet_id: str
    description: Optional[str] = None
    photo: Optional[Path] = None
    breed: Optional[str] = None
    display_name: Optional[str] = None
    main_ref: Optional[Path] = None
    only_states: list[str] = field(default_factory=list)
    skip_install: bool = False
    clawd_path: Optional[Path] = None
    dry_run: bool = False
    green_eye: bool = False
    fluffy: bool = False
    template_path: Optional[Path] = None

    def __post_init__(self):
        # Auto-detect green eyes from description
        if not self.green_eye and self.description:
            text = self.description.lower()
            self.green_eye = any(kw in text for kw in GREEN_EYE_KEYWORDS)
        # Auto-detect fluffy
        if not self.fluffy:
            for src in (self.description or "", self.breed or ""):
                if any(kw in src.lower() for kw in FLUFFY_KEYWORDS):
                    self.fluffy = True
                    break
        # Default display name = pet_id
        if not self.display_name:
            self.display_name = self.pet_id.title()


# ─── Stage 1: refs ─────────────────────────────────────────────

def find_gpt_image_script() -> Path:
    """Locate the gpt-image generate.py — used for all ref generation."""
    candidates = [
        Path.home() / ".codex/skills/gpt-image/generate.py",
        Path.home() / ".claude/skills/gpt-image/generate.py",
        SCRIPT_DIR.parent / "gpt-image/generate.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "gpt-image skill not found. Install from "
        "https://github.com/xingfanxia/AX-skills/tree/main/gpt-image "
        "or set GPT_IMAGE_SCRIPT env var."
    )


def gen_main_ref(spec: PetSpec, output_dir: Path, gpt_image: Path) -> Path:
    """Generate or copy main-ref.png — the character anchor."""
    refs_dir = output_dir / "refs" / spec.pet_id
    refs_dir.mkdir(parents=True, exist_ok=True)
    target = refs_dir / "main-ref.png"

    if spec.main_ref and spec.main_ref.exists():
        shutil.copy(spec.main_ref, target)
        print(f"  ✓ main-ref copied from {spec.main_ref}")
        return target

    desc = spec.description or "cute chibi cartoon cat"
    prompt = (
        f"A cute chibi/kawaii style {desc} in 3/4 sitting view. "
        f"Centered on a solid bright green chroma key background #00B140. "
        f"Clean cartoon line art with bold outlines. NO pink cheek blush, NO red cheek "
        f"circles. Clear distinctive eye color. Character must be recognizable from "
        f"this single image — this is the anchor reference for animation."
    )

    cmd = [
        str(gpt_image), prompt,
        "--output", str(refs_dir),
        "--name", "main-ref",
        "--size", "1024x1024",
        "--format", "png",
    ]
    if spec.photo:
        cmd += ["--edit", str(spec.photo)]

    if spec.dry_run:
        print(f"  [dry-run] {' '.join(cmd)}")
        return target

    print(f"  · gen main-ref ({'photo-edit' if spec.photo else 'text-to-image'})...")
    subprocess.run(cmd, check=True)
    if not target.exists():
        raise RuntimeError(f"main-ref not generated at {target}")
    return target


def gen_sleep_ref(spec: PetSpec, output_dir: Path, main_ref: Path, gpt_image: Path) -> Path:
    """Sleep-final-ref chained on main-ref (Lesson 3)."""
    refs_dir = main_ref.parent
    target = refs_dir / "sleep-final-ref.png"
    if target.exists() and not spec.only_states:
        print(f"  · sleep-final-ref already exists, skipping")
        return target
    prompt = (
        "Same cat from reference image, now CURLED UP SLEEPING with eyes fully "
        "closed (peaceful flat-line eyes), body relaxed and rounded into a sleeping "
        "ball, paws tucked under chin or close to body. Match character details "
        "exactly from reference (coat color, markings, body shape). "
        "Solid bright green chroma key background #00B140."
    )
    cmd = [
        str(gpt_image), prompt,
        "--edit", str(main_ref),
        "--output", str(refs_dir),
        "--name", "sleep-final-ref",
        "--size", "1024x1024",
        "--format", "png",
    ]
    if spec.dry_run:
        print(f"  [dry-run] {' '.join(cmd)}")
        return target
    print(f"  · gen sleep-final-ref (chained on main-ref)...")
    subprocess.run(cmd, check=True)
    return target


def gen_pose_refs(spec: PetSpec, output_dir: Path, main_ref: Path, gpt_image: Path) -> dict[str, Path]:
    """Generate the 5 state-pose refs (Lesson 1)."""
    refs_dir = main_ref.parent
    refs: dict[str, Path] = {}
    states = spec.only_states or POSE_REF_STATES
    pose_states = [s for s in states if s in POSE_REF_STATES]

    for state in pose_states:
        target = refs_dir / f"{state}-ref.png"
        if target.exists() and state not in (spec.only_states or []):
            print(f"  · {state}-ref already exists, skipping")
            refs[state] = target
            continue
        prompt = POSE_REF_PROMPTS[state]
        cmd = [
            str(gpt_image), prompt,
            "--edit", str(main_ref),
            "--output", str(refs_dir),
            "--name", f"{state}-ref",
            "--size", "1024x1024",
            "--format", "png",
        ]
        if spec.dry_run:
            print(f"  [dry-run] {state}-ref")
            refs[state] = target
            continue
        print(f"  · gen {state}-ref (chained on main-ref)...")
        subprocess.run(cmd, check=True)
        refs[state] = target

    return refs


# ─── Stage 2: animations via Doubao ─────────────────────────────

def write_template_js(spec: PetSpec, animation_dir: Path) -> Path:
    """Write template.js with breed-aware CHARACTER_PREFIX."""
    template_src = spec.template_path or PROMPTS_DIR / "template.example.js"
    if not template_src.exists():
        raise FileNotFoundError(f"template not found: {template_src}")
    target = animation_dir / "template.js"
    target.write_bytes(template_src.read_bytes())
    return target


def write_animations_json(spec: PetSpec, animation_dir: Path) -> Path:
    """Build animations.json — pet-forge batch-gen config."""
    refs_rel = f"refs/{spec.pet_id}"
    states = spec.only_states or ALL_STATES
    jobs = []
    for s in states:
        if s == "react-poke":
            img = f"{refs_rel}/main-ref.png"
            last = f"{refs_rel}/main-ref.png"
        elif s == "collapse-sleep":
            img = f"{refs_rel}/main-ref.png"
            last = f"{refs_rel}/sleep-final-ref.png"
        elif s == "wake":
            img = f"{refs_rel}/sleep-final-ref.png"
            last = f"{refs_rel}/main-ref.png"
        elif s == "sleeping":
            img = f"{refs_rel}/sleep-final-ref.png"
            last = f"{refs_rel}/sleep-final-ref.png"
        else:
            img = f"{refs_rel}/{s}-ref.png"
            last = f"{refs_rel}/{s}-ref.png"
        jobs.append({"key": s, "image": img, "lastFrame": last, "api": "doubao"})

    config = {"delayMs": 60000, "stopOnError": False, "jobs": jobs}
    target = animation_dir / "animations.json"
    target.write_text(json.dumps(config, indent=2))
    return target


def run_doubao_batch(spec: PetSpec, animation_dir: Path) -> None:
    """Shell out to batch-gen.js inside the vendored tools/ dir."""
    if spec.dry_run:
        print("  [dry-run] doubao batch (10 jobs, ~$2.00, ~6 min)")
        return
    print("  · running Doubao batch (this takes ~6 min, 10 RPM API limit)...")
    cmd = ["node", str(TOOLS_DIR / "batch-gen.js"),
           "--config", str(animation_dir / "animations.json")]
    subprocess.run(cmd, check=True, cwd=animation_dir)


# ─── Stage 3: chroma + install ─────────────────────────────────

def chroma_keys(spec: PetSpec, animation_dir: Path) -> None:
    """Run chroma_key.py on each mp4. Use green-eye-protective flags if needed."""
    states = spec.only_states or ALL_STATES
    flags = ["--plays", "0"]
    if spec.green_eye:
        flags += ["--sat-min", "85", "--despill-sat-min", "70"]
        print("  · using green-eye-safe chroma flags (--sat-min 85 --despill-sat-min 70)")

    for s in states:
        mp4 = animation_dir / "output" / s / "doubao-video.mp4"
        apng = animation_dir / "output" / s / "result.apng"
        if not mp4.exists():
            print(f"    [warn] {s}: no mp4 — Doubao failed for this state?")
            continue
        if spec.dry_run:
            print(f"  [dry-run] chroma {s}")
            continue
        cmd = ["python3", str(TOOLS_DIR / "chroma_key.py"), str(mp4), str(apng), *flags]
        subprocess.run(cmd, check=True)


def write_theme_json(spec: PetSpec, theme_dir: Path) -> Path:
    """Generate theme.json from breed-aware template."""
    fluffy_bump = 0.05 if spec.fluffy else 0.0
    s = lambda base: round(base + fluffy_bump, 2)  # noqa: E731
    pid = spec.pet_id

    theme = {
        "schemaVersion": 1,
        "name": spec.display_name,
        "author": "user (custom from pet-forge)",
        "version": "1.0.0",
        "description": spec.description or f"Custom pet — {pid}",
        "viewBox": {"x": 0, "y": 0, "width": 266, "height": 200},
        "layout": {
            "contentBox": {"x": 36, "y": 10, "width": 194, "height": 160},
            "centerX": 133, "baselineY": 170,
            "visibleHeightRatio": 0.35, "baselineBottomRatio": 0.05,
        },
        "eyeTracking": {"enabled": False},
        "states": {
            "idle":         [f"{pid}-idle-dozing.apng"],
            "yawning":      [f"{pid}-idle-dozing.apng"],
            "dozing":       [f"{pid}-idle-dozing.apng"],
            "collapsing":   [f"{pid}-collapse-sleep.apng"],
            "thinking":     [f"{pid}-thinking.apng"],
            "working":      [f"{pid}-working-typing.apng"],
            "error":        [f"{pid}-error.apng"],
            "attention":    [f"{pid}-happy.apng"],
            "notification": [f"{pid}-notification.apng"],
            "sleeping":     [f"{pid}-sleeping.apng"],
            "waking":       [f"{pid}-wake.apng"],
        },
        "workingTiers": [{"minSessions": 1, "file": f"{pid}-working-typing.apng"}],
        "idleAnimations": [{"file": f"{pid}-idle-dozing.apng", "duration": 5000}],
        "timings": {
            "minDisplay": {"attention": 5000, "error": 5000, "notification": 5200,
                           "working": 1000, "thinking": 1000},
            "autoReturn": {"attention": 5000, "error": 5000, "notification": 5200},
            "dndSkipYawn": True,
            "collapseDuration": 800, "wakeDuration": 1500,
            "deepSleepTimeout": 600000,
            "mouseIdleTimeout": 20000, "mouseSleepTimeout": 60000,
        },
        "hitBoxes": {
            "default":  {"x": 80, "y": 30, "w": 106, "h": 140},
            "sleeping": {"x": 60, "y": 60, "w": 146, "h": 100},
        },
        "sleepingHitboxFiles": [
            f"{pid}-sleeping.apng", f"{pid}-collapse-sleep.apng",
        ],
        "reactions": {
            "clickLeft":  {"file": f"{pid}-react-poke.apng", "duration": 2500},
            "clickRight": {"file": f"{pid}-react-poke.apng", "duration": 2500},
        },
        "miniMode": {"supported": False},
        "transitions": {},
        "objectScale": {
            "widthRatio": 0.58, "heightRatio": 0.44, "imgWidthRatio": 0.6,
            "objBottom": 0.05, "imgBottom": 0.05,
            "offsetX": 0.21, "offsetY": 0.28,
            "fileScales": {
                f"{pid}-idle-dozing.apng":    s(1.05),
                f"{pid}-thinking.apng":       s(1.20),
                f"{pid}-working-typing.apng": s(1.20),
                f"{pid}-notification.apng":   s(1.02),
                f"{pid}-error.apng":          s(1.25),
                f"{pid}-happy.apng":          s(1.20),
                f"{pid}-collapse-sleep.apng": s(1.05),
                f"{pid}-sleeping.apng":       s(1.05),
                f"{pid}-wake.apng":           s(1.05),
                f"{pid}-react-poke.apng":     s(1.05),
            },
        },
    }

    target = theme_dir / "theme.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(theme, ensure_ascii=False, indent=2) + "\n")
    return target


def install_to_clawd_on_desk(spec: PetSpec, animation_dir: Path) -> None:
    """Copy APNGs + theme.json into clawd-on-desk/themes/<pet-id>/."""
    if spec.skip_install:
        print(f"  · --skip-install set; output remains at {animation_dir / 'output'}")
        return
    clawd = spec.clawd_path or Path.home() / "projects/products/clawd-on-desk"
    if not clawd.exists():
        print(f"  · [warn] clawd-on-desk not found at {clawd} — skipping install")
        return

    theme_dir = clawd / "themes" / spec.pet_id
    assets_dir = theme_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    states = spec.only_states or ALL_STATES
    for s in states:
        src = animation_dir / "output" / s / "result.apng"
        dst = assets_dir / f"{spec.pet_id}-{s}.apng"
        if not src.exists():
            print(f"    [warn] {s}: no result.apng to install")
            continue
        if spec.dry_run:
            print(f"    [dry-run] {dst}")
            continue
        shutil.copy(src, dst)

    if not spec.only_states:
        # Full run — write fresh theme.json
        if spec.dry_run:
            print(f"    [dry-run] theme.json")
        else:
            write_theme_json(spec, theme_dir)
            print(f"  ✓ installed to {theme_dir}")


# ─── CLI ──────────────────────────────────────────────────────

def parse_args() -> PetSpec:
    p = argparse.ArgumentParser(
        description="pet-forge — generate clawd-on-desk-ready custom pet themes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--pet-id", required=True,
                   help="Filesystem-safe slug; becomes theme dir name + APNG prefix")
    p.add_argument("--description",
                   help="Text describing the pet (breed, color, eye color, build)")
    p.add_argument("--photo", type=Path,
                   help="Photo of the real pet (gpt-image-2 will edit-anchor on it)")
    p.add_argument("--breed",
                   help="Breed override (refines character prefix)")
    p.add_argument("--display-name",
                   help="What shows in clawd-on-desk theme picker (Unicode OK)")
    p.add_argument("--main-ref", type=Path,
                   help="Skip ref generation; use this image as character anchor")
    p.add_argument("--only", nargs="+", choices=ALL_STATES, default=[],
                   help="Subset of states to (re)generate")
    p.add_argument("--skip-install", action="store_true",
                   help="Don't copy to clawd-on-desk; keep output in ./output/<pet>/")
    p.add_argument("--green-eye", action="store_true",
                   help="Force green-eye chroma flags (auto-detected from --description)")
    p.add_argument("--fluffy", action="store_true",
                   help="Force fluffy-breed fileScale bumps (auto-detected)")
    p.add_argument("--clawd-on-desk", type=Path, dest="clawd_path",
                   help="Override clawd-on-desk repo path")
    p.add_argument("--template", type=Path, dest="template_path",
                   help="Custom template.js (overrides prompts/template.example.js)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print plan without API spend")
    args = p.parse_args()

    if not args.description and not args.photo and not args.main_ref:
        p.error("must provide one of: --description, --photo, --main-ref")
    return PetSpec(
        pet_id=args.pet_id, description=args.description,
        photo=args.photo, breed=args.breed,
        display_name=args.display_name, main_ref=args.main_ref,
        only_states=args.only, skip_install=args.skip_install,
        clawd_path=args.clawd_path, dry_run=args.dry_run,
        green_eye=args.green_eye, fluffy=args.fluffy,
        template_path=args.template_path,
    )


def main() -> int:
    spec = parse_args()

    print(f"\n🐾 pet-forge — {spec.display_name} ({spec.pet_id})")
    print(f"   green-eye chroma: {spec.green_eye} · fluffy scales: {spec.fluffy}")
    if spec.dry_run:
        print("   [DRY RUN — no API spend]")

    output_dir = Path.cwd() / "output" / spec.pet_id
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Stage 1] Refs (gpt-image-2)")
    gpt_image = find_gpt_image_script()
    main_ref = gen_main_ref(spec, output_dir, gpt_image)
    if not spec.only_states:
        gen_sleep_ref(spec, output_dir, main_ref, gpt_image)
        gen_pose_refs(spec, output_dir, main_ref, gpt_image)

    print("\n[Stage 2] Animations (Doubao)")
    write_template_js(spec, output_dir)
    write_animations_json(spec, output_dir)
    run_doubao_batch(spec, output_dir)

    print("\n[Stage 3] Chroma + install")
    chroma_keys(spec, output_dir)
    install_to_clawd_on_desk(spec, output_dir)

    print(f"\n✓ done. Test with: cd {spec.clawd_path or '~/projects/products/clawd-on-desk'} && npm start")
    print(f"  Then Settings → Theme → {spec.display_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
