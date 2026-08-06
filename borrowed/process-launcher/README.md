# Process Launcher

Process Launcher is a small localhost service that starts and tracks child processes through an HTTP API. It is designed for workflows where another tool, script, or AI agent needs a stable control surface for launching commands, checking status, reading captured output, and managing a few always-on local services.

The server binds to `127.0.0.1` by default. It accepts arbitrary commands from local callers, so it should be treated as a trusted local automation tool rather than a network-facing service.

## Features

- `POST /run` starts one-off commands and returns a PID plus output log path.
- `GET /processes` and `GET /processes/{pid}` report tracked process state.
- `GET /processes/{pid}/output` reads captured stdout and stderr.
- `delay_seconds` schedules a durable delayed launch that can be listed, cancelled, and recovered after restart.
- Scheduled jobs complete only when their child process exits with code `0`; failed child processes mark the scheduled job failed.
- Dry-run the target command before scheduling when the CLI supports it. If no dry-run exists, make that risk explicit before creating a durable schedule.
- Always-on services can be declared in YAML with restart delay, restart window, and circuit breaker limits.
- Periodic jobs can be declared in YAML with daily, weekly, fixed-interval, or cron-compatible schedules; inspect them and their run history through read-only `/periodic` endpoints and hot-reload with `POST /periodic/reload`.
- Heartbeat and output logs are retained locally and ignored by git.

## Install

```bash
uv venv
uv pip install -e '.[dev]'
```

The package exposes both a console script and a module entrypoint:

```bash
process-launcher start --config config/launcher.yaml
python -m process_launcher start --config config/launcher.yaml
```

## Configure

Copy the public example and edit it for your machine:

```bash
cp config/launcher.example.yaml config/launcher.yaml
```

`config/launcher.yaml` is intentionally ignored by git. Keep real local paths, service names, tokens, and `.env` references there. The tracked repository only ships `config/launcher.example.yaml` with generic placeholder values.

Always-on services are declarative-only. Define them under `services:` in YAML; `/run` does not create always-on services dynamically, and there is no service list/create API. Inspect declared services through the regular process and log endpoints. Use `POST /declared-services/{label}/restart` only to restart a service already declared in YAML.

Periodic jobs are declarative-only too. Define them under `periodic_jobs:` in YAML (schedule types: `daily`, `weekly`, `interval`, or `cron`); there are no periodic write endpoints. Inspect declarations, next run time, and run history through the read-only `/periodic` endpoints, and reload the `periodic_jobs:` section into a running launcher with `POST /periodic/reload`. See `config/launcher.example.yaml` for the schedule shape.

## Run

```bash
process-launcher start --config config/launcher.yaml
```

Then call the API from another shell:

```bash
curl -sf http://127.0.0.1:7997/health
curl -sf -X POST http://127.0.0.1:7997/run \
  -H 'Content-Type: application/json' \
  -d '{"command": ["python", "-c", "print(\"hello\")"], "label": "hello"}'
```

## macOS TCC Permission Bridge

macOS privacy controls (TCC, Transparency Consent and Control) restrict access to Microphone, Camera, Screen Recording, Accessibility, Full Disk Access, and protected folders like Desktop, Documents, and Downloads. The system checks the responsible process and its GUI application ancestry. A child process only inherits TCC permissions if its parent chain leads back to a trusted GUI application (Terminal, iTerm2) that the user has granted permission to.

Process Launcher acts as a TCC permission bridge. You start it inside an interactive terminal session, and every child it launches runs in that same permission context. This lets automation scripts and AI agents run TCC-sensitive commands through the API without each child having to reconnect to a GUI session.

### When It Matters

- Local Network access (Bonjour, mDNS, local socket discovery).
- Microphone or Camera recording.
- Screen Recording or Accessibility permissions.
- Full Disk Access or access to protected folders.
- Keychain access where interactive prompts are needed. Keychain has its own access control system separate from TCC. But foreground terminal context helps auth tooling and prompt dialogs work correctly, because the prompts appear in the terminal session.

### When It Does Not Help

Running Process Launcher under a background supervisor like PM2, cron, or launchd defeats the TCC bridge. Those managers do not run inside an interactive GUI session, so their child processes inherit no TCC permissions.

tmux and zellij can work, but only if the multiplexer server was itself started from an interactive GUI terminal. If the server was started by launchd, an SSH session, or a background automation script, the TCC inheritance chain is broken.

launchd may work for signed application bundles with stable bundle IDs that have been granted TCC entitlements. But a plain script or binary launched by launchd is not the design target. It will almost certainly fail for TCC-sensitive jobs. Use a signed `.app` bundle if you need launchd scheduling with TCC access.

### Start From The Right Session

Start the launcher from a terminal you opened interactively:

```bash
# In Terminal.app or iTerm2:
process-launcher start --config config/launcher.yaml

# Or via tmux started from the same terminal:
tmux new-session -d -s launcher 'process-launcher start --config config/launcher.yaml'
```

Do not add it to crontab, launchd plists, PM2 ecosystem files, or any supervisor that would start it without a GUI terminal ancestor.

## Private Overlay Pattern

This repository is public-ready and generic. It ships a reusable skill in `skills/skill_process_launcher.md`, public docs, and fake configuration examples. A user workspace can keep a private overlay separately: aliases, real job recipes, private paths, domain-specific service labels, and operational runbooks. That overlay should point to this package but should not be committed here.

## Testing

```bash
python -m pytest -v
python -m pytest -v -m live_integration
python -m pytest -v --cov=process_launcher --cov-report=term-missing
```

The default tests use temporary configs and short-lived subprocesses. The `live_integration` marker starts a real launcher process on port `7976` using the existing pytest fixture.
