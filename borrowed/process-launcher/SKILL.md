---
name: process-launcher
description: >-
  Localhost 进程启动/调度服务，核心价值是 macOS TCC 权限桥接——从 GUI 终端启动后，
  它 spawn 的后台任务继承麦克风/摄像头/屏幕录制/Accessibility 权限（cron/launchd
  起的进程拿不到）。另有 SQLite 持久化的延时/定时任务和 YAML 声明式常驻服务
  （带熔断）。用于：后台任务因 TCC 报权限错、延时执行、定时任务、录音/录屏类自动化。
---

# process-launcher（borrowed: grapeot/process-launcher, MIT）

完整契约（含 trigger words、API endpoints、YAML 声明规则、安全边界）在
`skills/skill_process_launcher.md` —— 用之前先读它。架构与开发规范见 `AGENTS.md`。

## 速查

```bash
cd ~/.claude/skills/process-launcher
# 一次性 setup
uv venv && uv pip install -e '.[dev]'
cp config/launcher.example.yaml config/launcher.yaml   # 真实路径只写进本地 config

# 启动 —— 必须从交互式 GUI 终端（Terminal.app/iTerm2）启动，launchd/cron/SSH 会断掉 TCC 链
.venv/bin/process-launcher start --config config/launcher.yaml
```

- 一次性任务 / 延时任务走 `POST /run`、`/scheduled`；常驻服务和周期任务只能 YAML 声明，HTTP 只读。
- AX 场景锚点：watch-transcriber 等录音类自动化、mac-audio-guard —— 凡是后台跑要碰
  mic/screen 的 job，用这个而不是裸 cron。
- Upstream: <https://github.com/grapeot/process-launcher>（本目录是 git clone，`git pull` 可更新）。
