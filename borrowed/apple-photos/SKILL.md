---
name: apple-photos
description: >-
  Apple Photos 结构化 CLI —— 只读元数据检索/过滤/备份（osxphotos）可用。
  ⚠️ 上游自标 live-unverified ALPHA：PhotoKit mutation（导入、像素验证去重删除）
  未经真实照片库验证，严禁对生产照片库执行任何 mutation 命令。
---

# apple-photos（borrowed: grapeot/apple-photos-skill, MIT）

权威契约（硬边界、删除授权协议、acceptance criteria）在 `skills/apple_photos.md`
—— **任何操作前先读它**，本文件只是入口。

## 速查

```bash
cd ~/.claude/skills/apple-photos
uv venv && uv pip install -e '.[dev]'   # 一次性 setup（osxphotos 依赖较重）
.venv/bin/apple-photos doctor --capability read   # 只读能力自检
.venv/bin/apple-photos --help
```

- **只用只读面**（search/filter/export/metadata backup）。mutation 面（import/delete）
  是 alpha：需要 `swift build` 原生 helper + 人工 TTY 确认短语 + 单次 HMAC token，
  且上游明言不要碰生产库 —— 在 AX 明确要求并指定测试库之前一律不碰。
- 删除授权协议（pixel-evidence + manifest + 人工确认）本身是"不可逆批量操作如何设计
  安全门"的范本，值得在别的 skill 里复用。
- Upstream: <https://github.com/grapeot/apple-photos-skill>（git clone，`git pull` 可更新）。
