#!/usr/bin/env python3
"""Structural linter for the AX-skills repo (one skill dir per top-level folder).

Adapted from staruhub/ClaudeSkills (MIT) scripts/validate.py, reimplemented
for AX-skills conventions: skills live at the repo root, `docs/` is the Pages
showcase, `remotion/` is promo-video source, `scripts/` is repo tooling.

Checks per skill dir:
  FAIL (exit 1):
    - SKILL.md exists
    - YAML frontmatter present with non-empty `name` + `description`
    - frontmatter `name` matches the directory name exactly
    - SKILL.md > 500 lines, unless the skill is in OVERSIZE_ALLOWLIST
    - dangling refs: `references/<x>.md` or `scripts/<x>.<ext>` paths
      mentioned in SKILL.md that don't exist inside the skill dir
  WARN (exit 0, unless --strict):
    - SKILL.md > 300 lines
    - orphan files under references/ scripts/ assets/ whose basename is
      never mentioned in SKILL.md or any other text file of the skill
    - hardcoded machine paths (/Users/<name>/) outside allowlisted lines

File universe: when `git` is available, only files git can see (tracked +
untracked-but-not-ignored) are scanned, so gitignored local artifacts
(e.g. per-skill `test_results/`) don't produce machine-dependent noise.

Usage:
  python3 scripts/validate_skills.py             # validate every skill dir
  python3 scripts/validate_skills.py --skill X   # validate one skill
  python3 scripts/validate_skills.py --strict    # warnings become failures
  python3 scripts/validate_skills.py --root DIR  # lint a different checkout

Pure stdlib — no pyyaml; frontmatter is parsed with a naive `---` split,
which is sufficient for the flat `name:` / `description:` keys skills use.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Documented non-skill top-level dirs (see CLAUDE.md "Layout").
NON_SKILL_DIRS = {"docs", "remotion", "scripts", "tmp", "node_modules"}

# SKILL.md line-count gates.
WARN_LINES = 300
FAIL_LINES = 500

# Skills allowed past the 500-line hard cap. Every entry needs an honest
# reason string; the report prints it so the exemption stays visible.
# (Empty as of 2026-07: the largest SKILL.md is serenity-bottleneck-research
# at ~407 lines — over the warn line but under the cap.)
OVERSIZE_ALLOWLIST: dict[str, str] = {}

# Lines allowed to contain a hardcoded /Users/<name>/ path.
# skill name -> list of substrings; a warning line matching any substring
# for that skill is suppressed. Alternatively, put the inline marker
# `lint-allow-path` on the offending line itself.
PATH_ALLOWLIST: dict[str, list[str]] = {}
PATH_MARKER = "lint-allow-path"

HARDCODED_PATH_RE = re.compile(r"/Users/[A-Za-z0-9._\-]+/")

# Skill-relative asset paths mentioned in SKILL.md that must exist on disk.
# Lookbehind rejects matches embedded in longer paths ("~/.claude/references/",
# "Preferences/…") ; extension requirement skips prose like `scripts/<topic>/`
# or `references/04` section shorthand.
DANGLING_REF_RE = re.compile(
    r"(?<![A-Za-z0-9_/~.\-])"
    r"(references/[A-Za-z0-9_./\-]+\.md"
    r"|scripts/[A-Za-z0-9_./\-]+\.[A-Za-z0-9]{1,5})"
)

# Dirs whose files must be referenced somewhere in the skill (orphan check).
ASSET_DIRS = ("references", "scripts", "assets")
ORPHAN_IGNORE_RE = re.compile(r"^\.|\.pyc$|^__pycache__$")
# Self-describing entry files need no mention elsewhere.
ORPHAN_EXEMPT_BASENAMES = {"README.md"}
# Text files whose content counts as "mentions" for the orphan check.
HAYSTACK_SUFFIXES = {".md", ".json", ".py", ".sh", ".txt", ".yml", ".yaml"}


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Naive frontmatter parse: return {key: same-line value} or None."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not m:
        return None
    fields: dict[str, str] = {}
    block = m.group(1)
    lines = block.splitlines()
    for i, line in enumerate(lines):
        km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not km:
            continue
        key, value = km.group(1), km.group(2).strip().strip("\"'")
        if value in ("", ">", ">-", "|", "|-"):
            # Block scalar / empty: treat first indented continuation line
            # as evidence the value is non-empty.
            for cont in lines[i + 1 :]:
                if re.match(r"^\s+\S", cont):
                    value = cont.strip()
                    break
                if not cont.startswith((" ", "\t")):
                    break
        fields[key] = value
    return fields


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def git_visible_files(root: Path) -> set[Path] | None:
    """Absolute paths git can see (tracked + untracked-but-not-ignored),
    or None when git/repo is unavailable (then the filesystem walk rules)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others",
             "--exclude-standard"],
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return {
        (root / p.decode("utf-8", "ignore")).resolve()
        for p in out.split(b"\0")
        if p
    }


def skill_files(skill_dir: Path, visible: set[Path] | None) -> list[Path]:
    """All lint-relevant files in the skill dir, honoring git visibility."""
    return sorted(
        f
        for f in skill_dir.rglob("*")
        if f.is_file() and (visible is None or f.resolve() in visible)
    )


def lint_skill(
    skill_dir: Path,
    visible: set[Path] | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"{name}: SKILL.md missing")
        return
    text = read_text(skill_md)

    # 1. frontmatter: name + description; name must equal the dir name.
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append(f"{name}: no YAML frontmatter in SKILL.md")
    else:
        fm_name = fm.get("name", "")
        if not fm_name:
            errors.append(f"{name}: frontmatter missing `name`")
        elif fm_name != name:
            errors.append(
                f"{name}: frontmatter name '{fm_name}' != dir name '{name}'"
            )
        if not fm.get("description"):
            errors.append(f"{name}: frontmatter missing `description`")

    # 2. line-count gates.
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    if lines > FAIL_LINES:
        if name in OVERSIZE_ALLOWLIST:
            warnings.append(
                f"{name}: SKILL.md {lines} lines > {FAIL_LINES} "
                f"(allowlisted: {OVERSIZE_ALLOWLIST[name]})"
            )
        else:
            errors.append(
                f"{name}: SKILL.md {lines} lines > {FAIL_LINES} hard cap "
                f"(add to OVERSIZE_ALLOWLIST with a reason, or split)"
            )
    elif lines > WARN_LINES:
        warnings.append(f"{name}: SKILL.md {lines} lines > {WARN_LINES} soft cap")

    # 4. dangling refs: skill-relative paths mentioned in SKILL.md must exist.
    for ref in sorted(set(DANGLING_REF_RE.findall(text))):
        if not (skill_dir / ref).is_file():
            errors.append(f"{name}: SKILL.md mentions missing file {ref}")

    # 3. orphan files under references/ scripts/ assets/.
    files = skill_files(skill_dir, visible)
    haystack = "\n".join(
        read_text(f) for f in files if f.suffix in HAYSTACK_SUFFIXES
    )
    for f in files:
        rel = f.relative_to(skill_dir)
        if rel.parts[0] not in ASSET_DIRS:
            continue
        if f.name in ORPHAN_EXEMPT_BASENAMES:
            continue
        if any(ORPHAN_IGNORE_RE.search(part) for part in rel.parts):
            continue
        if f.name not in haystack:
            warnings.append(
                f"{name}: orphan file {rel} "
                f"(basename never mentioned in the skill's text files)"
            )

    # 5. hardcoded machine paths.
    allowed_substrings = PATH_ALLOWLIST.get(name, [])
    for f in files:
        if f.suffix not in HAYSTACK_SUFFIXES:
            continue
        if any(ORPHAN_IGNORE_RE.search(part) for part in f.relative_to(skill_dir).parts):
            continue
        for lineno, line in enumerate(read_text(f).splitlines(), 1):
            if not HARDCODED_PATH_RE.search(line):
                continue
            if PATH_MARKER in line:
                continue
            if any(sub in line for sub in allowed_substrings):
                continue
            warnings.append(
                f"{name}: hardcoded machine path in "
                f"{f.relative_to(skill_dir)}:{lineno}: {line.strip()[:100]}"
            )


def discover_skill_dirs(root: Path) -> list[Path]:
    return sorted(
        d
        for d in root.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name not in NON_SKILL_DIRS
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="AX-skills structural linter")
    parser.add_argument("--skill", help="validate a single skill dir by name")
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as failures"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repo root to lint (default: this script's repo)",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR repo root not found: {root}")
        return 2

    if args.skill:
        skill_dir = root / args.skill
        if not skill_dir.is_dir():
            print(f"ERROR no such skill dir: {skill_dir}")
            return 2
        skill_dirs = [skill_dir]
    else:
        skill_dirs = discover_skill_dirs(root)

    visible = git_visible_files(root)
    errors: list[str] = []
    warnings: list[str] = []
    for skill_dir in skill_dirs:
        lint_skill(skill_dir, visible, errors, warnings)

    print(f"validated {len(skill_dirs)} skill dir(s) under {root}")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"FAIL  {e}")

    failed = bool(errors) or (args.strict and bool(warnings))
    verdict = "FAIL" if failed else "PASS"
    print(
        f"{verdict} ({len(errors)} failure(s), {len(warnings)} warning(s)"
        f"{', strict' if args.strict else ''})"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
