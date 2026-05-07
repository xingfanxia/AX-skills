#!/usr/bin/env bash
# Package skill for 繁星计划·Fun Skills 全国大赛 submission.
# Produces ZIP at ./jewelry-marketing-submission.zip per spec:
#   1. skill.md (lowercase, per spec)
#   2. py scripts / data
#   3. (you fill in: video link in submission form)
#   4. 商业价值说明书
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
STAGE_DIR="$(mktemp -d)/jewelry-marketing"
ZIP_PATH="${SKILL_DIR}/jewelry-marketing-submission.zip"

mkdir -p "$STAGE_DIR"

# 1. skill.md (REQUIRED — spec uses lowercase). The source has SKILL.md
# (uppercase, Claude Code convention); macOS APFS is case-insensitive so
# we can't keep both files in the source dir. cp into a fresh stage dir
# materializes the file as the destination name (skill.md, lowercase).
cp "${SKILL_DIR}/SKILL.md" "$STAGE_DIR/skill.md"

# 2. py scripts + prompts package — exclude __pycache__ at copy time so we
# don't have to rely on zip's exclusion (which keeps empty dirs).
cp "${SKILL_DIR}/generate.py" "$STAGE_DIR/generate.py"
mkdir -p "$STAGE_DIR/prompts"
for f in "${SKILL_DIR}/prompts/"*.py; do
  cp "$f" "$STAGE_DIR/prompts/"
done

# 3. references docs
cp -r "${SKILL_DIR}/references" "$STAGE_DIR/references"

# 4. 商业价值说明书 (REQUIRED ~200 words)
cp "${SKILL_DIR}/商业价值说明书.md" "$STAGE_DIR/商业价值说明书.md"

# 5. demo script (so reviewer can repro the video)
cp "${SKILL_DIR}/demo_script.md" "$STAGE_DIR/demo_script.md"

# 6. example fixture
cp -r "${SKILL_DIR}/examples" "$STAGE_DIR/examples"

# 7. README at root for reviewer convenience
cat > "$STAGE_DIR/README.md" <<'EOF'
# jewelry-marketing — 繁星计划·Fun Skills 全国大赛 提交包

赛道：电商赛道（赛道二）
对应参考方向：电商营销文案生成 Skill（向上扩展为：分析 + 图 + 文 全链路）

## 提交内容

| # | 文件 | 说明 |
|---|---|---|
| 1 | `skill.md` | Skill 核心配置文件（YAML frontmatter + 调用说明） |
| 2 | `generate.py` + `prompts/` | Python 主入口 + 20 个 prompt 模板（12 营销 + 8 设计） |
| 3 | (见提交表单) | 效果演示视频链接 |
| 4 | `商业价值说明书.md` | 200 字商业价值说明 |

## 辅助资源

- `references/JEWELRY_TEMPLATES.md` — 20 个模板的视觉/适用场景对照表
- `references/COPY_STYLES.md` — 6 种 XHS 文案风格 tone 规则与配图策略
- `references/OUTPUT_BUNDLE.md` — 输出目录结构 + JSON schema + 成本估算
- `examples/sample.jpg` — 测试用珠宝商品图
- `demo_script.md` — 3 分钟演示视频脚本

## 快速试用

```bash
export GEMINI_API_KEY="<你的-gemini-key>"
export OPENAI_API_KEY="<你的-openai-key>"
./generate.py ./examples/sample.jpg --copy-only   # 最便宜的验证（不生图）
./generate.py ./examples/sample.jpg               # 完整 12 张营销 bundle
```

PEP 723 uv script — 第一次运行 uv 自动装 `requests` 依赖。
EOF

# Create ZIP
(cd "$(dirname "$STAGE_DIR")" && zip -r "$ZIP_PATH" "$(basename "$STAGE_DIR")" -x "*.pyc" -x "__pycache__/*")

echo ""
echo "✅ Submission ZIP packaged:"
echo "   $ZIP_PATH"
echo ""
ls -lh "$ZIP_PATH"
echo ""
echo "ZIP contents:"
unzip -l "$ZIP_PATH" | head -40
