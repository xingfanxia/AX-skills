# Process Launcher Skill

## Purpose

Use Process Launcher when a local workflow needs to start a command through a trusted localhost API, inspect process status, read output logs, schedule durable one-shot jobs, run a small set of YAML-declared always-on services, or run YAML-declared periodic jobs.

## Trigger Words

Match this skill on phrases about launching or scheduling local commands: "run in background", "schedule", "set a reminder", "delay this", "run in N minutes/hours", "run tomorrow morning", "recurring job", "periodic job", "every day/week", or the tool name ("process launcher", "background job manager"). Chinese triggers in active use: 延时执行、定时执行、几分钟后执行、几小时后执行、明天早上、定时任务、延迟任务、周期任务、用 launcher 跑、background job manager、process launcher、schedule、set a reminder。

## Why Process Launcher Exists (macOS TCC)

Process Launcher started as a solution to a macOS-specific problem. Apple's TCC (Transparency Consent and Control) framework restricts access to Microphone, Camera, Screen Recording, Accessibility, Full Disk Access, and protected folders. The system checks the responsible process and its GUI application ancestry. A plain background process spawned by cron, launchd, or PM2 has no GUI ancestor and therefore inherits no TCC permissions.

Process Launcher acts as a bridge. Start it from an interactive terminal (Terminal.app, iTerm2), and every job it launches inherits that terminal's TCC grants. All TCC-sensitive work goes through this one process, so you do not need each automation script to reconnect to a GUI session.

**This only works if the launcher itself runs inside an interactive GUI terminal session.** Background supervisors break the chain. See the Start section below for details.

Keychain is a separate concern from TCC. Keychain has its own access control based on code identity and team ID, and interactive terminal context mainly helps the `/usr/bin/security` prompts appear in the right session. If a task needs Keychain access, test it independently of the TCC chain rather than assuming terminal context is enough.

## Setup

Install the package in editable mode:

```bash
uv venv
uv pip install -e '.[dev]'
```

Create local config from the public example:

```bash
cp config/launcher.example.yaml config/launcher.yaml
```

Put real paths, service labels, `.env` references, and local SQLite paths only in the ignored local config or in a private overlay. Always-on services are declarative-only; do not create them through HTTP. Inspect them through the regular process and log endpoints. Use `POST /declared-services/{label}/restart` only for a service already present in YAML.

Periodic jobs are also declarative-only. Define them under `periodic_jobs:` in YAML and inspect them through read-only `/periodic` endpoints. Do not create, modify, enable, disable, or trigger recurring jobs through HTTP; use `POST /run` with the same command when you need a one-off manual validation.

## Start The Launcher

**Important:** Start the launcher from an interactive terminal session. Terminal.app or iTerm2 works. tmux and zellij work only if the multiplexer server was itself started from one of those GUI terminals. If the server was started by launchd, SSH, or an automated script, TCC inheritance is broken.

```bash
# From an interactive terminal
process-launcher start --config config/launcher.yaml
```

The module entrypoint is equivalent:

```bash
python -m process_launcher start --config config/launcher.yaml
```

**Do not** start the launcher from cron, launchd, PM2, or any supervisor that lacks a GUI terminal ancestor. Jobs launched through those parents will not have TCC access, which is the main reason to use this tool on macOS.

## Common Calls

Before scheduling a durable job, run the target CLI's dry-run/check mode when it has one. This catches missing credentials, bad paths, bad Python versions, and malformed arguments before the job is persisted. If the target CLI has no dry-run mode, tell the user that the schedule will be created without preflight validation and that the underlying command may fail later.

Health check:

```bash
curl -sf http://127.0.0.1:7997/health
```

Run a command. A `command` string runs through a shell (`shell=True`, so pipes and redirection work); a `command` array execs directly, which is safer but has no shell features.

```bash
curl -sf -X POST http://127.0.0.1:7997/run \
  -H 'Content-Type: application/json' \
  -d '{"command": ["python", "-c", "print(\"hello\")"], "label": "demo"}'
```

RunRequest fields:

| Field | Type | Required | Notes |
|------|------|------|------|
| command | string or string[] | yes | Command to run. A string runs through a shell; an array execs directly. |
| cwd | string | | Working directory. |
| env | object | | Extra environment variables. |
| label | string | | Label used to identify the process (affects log file names). |
| timeout | float | | Seconds before the child is killed. |
| delay_seconds | float | | Delay before launch, persisted to SQLite and recovered after restart. |
| run_at | datetime | | Absolute launch time; mutually exclusive with `delay_seconds`. |
| misfire_policy | string | | Recovery when `run_at` passed while the launcher was down: `run_immediately` / `skip` / `fail`. |

List processes and read output:

```bash
curl -sf http://127.0.0.1:7997/processes
curl -sf 'http://127.0.0.1:7997/processes?running_only=true'
curl -sf http://127.0.0.1:7997/processes/{pid}
curl -sf -X POST http://127.0.0.1:7997/processes/{pid}/stop
curl -sf http://127.0.0.1:7997/processes/{pid}/output
curl -sf 'http://127.0.0.1:7997/processes/{pid}/output?tail=50'
```

Tracked process states:

| State | Meaning |
|------|------|
| running | Child process is still active. |
| exited | Child exited (zero or non-zero). |
| killed | Stopped manually or killed by timeout. |
| circuit_breaker | An always-on service tripped its breaker after repeated failures. |

Inspect YAML-declared periodic jobs and run history:

```bash
curl -sf http://127.0.0.1:7997/periodic
curl -sf http://127.0.0.1:7997/periodic/{label}
curl -sf http://127.0.0.1:7997/periodic/{label}/runs
curl -sf http://127.0.0.1:7997/periodic/{label}/runs/{run_id}
```

There are no periodic write endpoints. To test a periodic command before enabling it in YAML, submit a one-off `/run` request with a test label. `POST /periodic/reload` hot-reloads only the `periodic_jobs:` section of `config/launcher.yaml` into the running launcher; it does not touch declared services, logging, storage, or server settings, and a run already in flight keeps the configuration it started with.

Schedule and cancel a durable delayed launch:

```bash
curl -sf -X POST http://127.0.0.1:7997/run \
  -H 'Content-Type: application/json' \
  -d '{"command": ["python", "-c", "print(\"later\")"], "label": "later", "delay_seconds": 300}'

curl -sf -X POST http://127.0.0.1:7997/run \
  -H 'Content-Type: application/json' \
  -d '{"command": ["python", "daily.py"], "label": "absolute_time", "run_at": "2026-06-10T09:00:00-07:00", "misfire_policy": "run_immediately"}'

curl -sf http://127.0.0.1:7997/scheduled
curl -sf -X PATCH http://127.0.0.1:7997/scheduled/{job_id} \
  -H 'Content-Type: application/json' \
  -d '{"run_at": "2026-06-11T08:00:00-07:00"}'
curl -sf -X POST http://127.0.0.1:7997/scheduled/{job_id}/cancel
```

Scheduled jobs are persisted in SQLite and recovered on launcher restart. Pending jobs can be updated with `PATCH /scheduled/{job_id}`; the launcher replaces the old in-memory delay task and keeps the same job id. Running, completed, failed, cancelled, or missed jobs cannot be updated. If `run_at` passed while the launcher was down, `misfire_policy` controls recovery: `run_immediately`, `skip`, or `fail`. A scheduled job becomes `completed` only after its child process exits with code `0`; non-zero exits become `failed`. Note the recovery boundary across restarts: scheduled jobs are persisted and restored, regular process handles live only in memory (so `/processes` starts fresh after a restart), and always-on services restart from the YAML declaration.

When `POST /run` creates a delayed job, the immediate response may show `pid: 0` and `output_file: null` because no child process has started yet. Treat that as a scheduled handoff, not as a process launch. Call `GET /scheduled` and match by label, command, and `run_at` to get the durable job id for later cancellation or audit.

### OpenCode Same-Session Reminders

For "remind me in N minutes in this same OpenCode session" workflows, Process Launcher should schedule an `opencode_skill append` command rather than a raw `sleep` or a new OpenCode submission. The OpenCode skill owns session inference, dry-run checks, and prompt storage; Process Launcher owns durable time-based execution.

Use a command array with absolute paths and a stable prompt file:

```bash
curl -sf -X POST http://127.0.0.1:7997/run \
  -H 'Content-Type: application/json' \
  -d '{
    "command": ["/absolute/path/to/opencode_skill/.venv/bin/python", "-m", "opencode_skill", "append", "--session-id", "ses_example", "--prompt-file", "/absolute/path/to/opencode_skill/prompts/reminder.md", "--send-timeout", "5", "--json"],
    "cwd": "/absolute/path/to/opencode_skill",
    "label": "opencode_append_reminder",
    "delay_seconds": 600,
    "timeout": 300
  }'
```

Prefer non-blocking append handoff for reminders. Avoid adding `--wait` unless the user explicitly wants the scheduled child process to block until OpenCode completes. A timed-out HTTP request can make the child process exit non-zero, so the scheduled job becomes `failed`, even though OpenCode may already have appended the message and produced a visible response in the session. In that case, inspect `/processes/{pid}/output` for the timeout and inspect the OpenCode session timeline separately before retrying.

Verification has two layers:

1. Process Launcher layer: `/scheduled/{job}` or `/scheduled` shows whether the delayed child process started and whether it exited with code `0`. After start, `/processes/{pid}` gives the output file, and `/processes/{pid}/output` is the best way to read failures.
2. OpenCode layer: the target session timeline is the source of truth for whether the reminder prompt was appended and answered. Do not infer model success from Launcher status alone.

Do not rely on `/logs/output?label=...` for targeted debugging unless the server version is known to support that filter. The reliable path is `/processes/{pid}` followed by `/processes/{pid}/output`.

ScheduledJob fields:

| Field | Type | Notes |
|------|------|------|
| id | string | Job ID (12-hex). |
| label | string? | Label. |
| command | string or string[] | Command. |
| cwd | string? | Working directory. |
| env | object | Environment variables. |
| timeout | float? | Execution timeout. |
| scheduled_at | datetime | Submission time. |
| run_at | datetime | Planned launch time. |
| status | string | pending / running / completed / failed / cancelled / missed. |
| misfire_policy | string | Recovery policy after a missed run_at. |
| result_pid | int? | Actual PID once executed. |
| last_error | string? | Failure or missed-run reason. |

Inspect logs. The bare `/logs` path is **not** a valid endpoint and returns 404; always use `/logs/heartbeat` or `/logs/output`.

```bash
curl -sf http://127.0.0.1:7997/logs/heartbeat
curl -sf 'http://127.0.0.1:7997/logs/heartbeat?event=PROCESS_EXITED'
curl -sf 'http://127.0.0.1:7997/logs/heartbeat?label=newsletter&limit=10'
curl -sf http://127.0.0.1:7997/logs/output
curl -sf http://127.0.0.1:7997/logs/output/{filename}
curl -sf 'http://127.0.0.1:7997/logs/output/{filename}?tail=50'
```

On-disk log layout (auto-cleaned after 30 days):

- Heartbeat: `logs/heartbeat_{YYYY-MM-DD}.jsonl`
- Output: `logs/output/{label}_{YYYYMMDD_HHMMSS}.log`

Restart a YAML-declared service:

```bash
curl -sf -X POST http://127.0.0.1:7997/declared-services/{label}/restart
```

There is no service list/create/reset API. Use `/processes` and logs to inspect declared services after startup or restart.

## Private Overlay Pattern

This skill is intentionally generic. Keep user-specific aliases, real job recipes, private domains, personal paths, and notification policies in a separate private skill or workspace file. The private overlay can call the public API examples here without modifying this repository.

## Safety Notes

`POST /run` executes commands as the launcher user. Use this service only on trusted localhost interfaces unless you add an authentication and authorization layer.
