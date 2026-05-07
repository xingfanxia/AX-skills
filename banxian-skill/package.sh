#!/usr/bin/env bash
# Package banxian-skill for 繁星计划·Fun Skills 全国大赛 submission.
# Produces ZIP at ./banxian-skill-submission.zip per spec:
#   1. skill.md (lowercase, per spec)
#   2. py scripts / data
#   3. (you fill in: video link in submission form)
#   4. 商业价值说明书
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
STAGE_DIR="$(mktemp -d)/banxian-skill"
ZIP_PATH="${SKILL_DIR}/banxian-skill-submission.zip"

mkdir -p "$STAGE_DIR"

# 1. skill.md (REQUIRED — spec uses lowercase). Source has SKILL.md
# (uppercase, Claude Code convention); macOS APFS is case-insensitive so
# we materialize it as skill.md in the stage dir via cp.
cp "${SKILL_DIR}/SKILL.md" "$STAGE_DIR/skill.md"

# 2. py scripts (algorithm engines + common utilities + lookup data)
mkdir -p "$STAGE_DIR/scripts/_lookup"
cp "${SKILL_DIR}/scripts/_common.py" "$STAGE_DIR/scripts/_common.py"
cp "${SKILL_DIR}/scripts/liuren.py" "$STAGE_DIR/scripts/liuren.py"
cp "${SKILL_DIR}/scripts/meihua.py" "$STAGE_DIR/scripts/meihua.py"
cp "${SKILL_DIR}/scripts/liuyao.py" "$STAGE_DIR/scripts/liuyao.py"
for f in "${SKILL_DIR}/scripts/_lookup/"*.json; do
  cp "$f" "$STAGE_DIR/scripts/_lookup/"
done

# 3. data/ knowledge markdown
cp -r "${SKILL_DIR}/data" "$STAGE_DIR/data"

# 4. 商业价值说明书 (REQUIRED ~200 words)
cp "${SKILL_DIR}/商业价值说明书.md" "$STAGE_DIR/商业价值说明书.md"

# 5. demo script (so reviewer can repro the video)
cp "${SKILL_DIR}/demo_script.md" "$STAGE_DIR/demo_script.md"

# 6. examples (3 real divination conversations)
cp -r "${SKILL_DIR}/examples" "$STAGE_DIR/examples"

# 7. tests (so reviewer can verify algorithm correctness)
mkdir -p "$STAGE_DIR/tests"
for f in "${SKILL_DIR}/tests/"*.py; do
  cp "$f" "$STAGE_DIR/tests/"
done

# 8. requirements + README
cp "${SKILL_DIR}/requirements.txt" "$STAGE_DIR/requirements.txt"
cp "${SKILL_DIR}/README.md" "$STAGE_DIR/README.md"

# 9. Build ZIP
rm -f "$ZIP_PATH"
cd "$(dirname "$STAGE_DIR")"
zip -rq "$ZIP_PATH" "banxian-skill" -x '*__pycache__*' '*.pyc' '*.pytest_cache*'

# 10. Cleanup
rm -rf "$(dirname "$STAGE_DIR")"

# 11. Report
SIZE=$(ls -lh "$ZIP_PATH" | awk '{print $5}')
COUNT=$(unzip -l "$ZIP_PATH" | tail -1 | awk '{print $2}')
echo "✓ Packaged: $ZIP_PATH"
echo "  Size:  $SIZE (limit 10MB)"
echo "  Files: $COUNT"
