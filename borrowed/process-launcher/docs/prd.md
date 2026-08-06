# Process Launcher PRD

## Problem

Local automation often needs a small trusted process to start commands, track their lifecycle, and expose status to scripts or AI agents. Shell scripts can start commands, but they do not provide a reusable API for process status, output lookup, delayed launch cancellation, or simple always-on service recovery.

On macOS, an additional constraint comes from TCC (Transparency Consent and Control) privacy controls. The system restricts access to Microphone, Camera, Screen Recording, Accessibility, Full Disk Access, and protected folders. These checks look at the responsible process and its GUI application ancestry. A child process only inherits TCC permissions if its parent chain leads back to a trusted GUI application that the user has granted permission to.

Process Launcher provides both the control surface and a TCC permission bridge. It is intentionally narrow: receive a command, start a child process, capture output, record lifecycle events, expose current process state, persist delayed jobs that must survive launcher restarts, and run YAML-declared recurring jobs. Started from an interactive terminal, every child it launches inherits that terminal's TCC grants.

## Goals

- Start one-off commands through `POST /run`.
- Track process status, exit code, timestamps, labels, and output file paths.
- Capture stdout and stderr into local log files.
- Record heartbeat events as JSONL for audit and troubleshooting.
- Support durable delayed launches that can be listed, cancelled while pending, and recovered after launcher or machine restarts.
- Support absolute `run_at` scheduling for cross-day jobs.
- Support a small set of configured always-on services with restart and circuit-breaker behavior.
- Support YAML-declared periodic jobs for daily, weekly, fixed-interval, and limited cron-compatible schedules.
- Expose periodic jobs and their run history through read-only API endpoints.
- Provide an OpenAPI schema for human scripts and AI agents.

## Non-Goals

- Process Launcher is not a distributed job queue.
- It does not recover arbitrary child process handles across restarts.
- It does not provide API-created or API-mutated recurring jobs. YAML remains the source of truth for recurring schedules.
- It does not replace YAML configuration with SQLite. YAML remains the bootstrap and declared-service source.
- It does not support API-created always-on services. Always-on services are declarative-only and must be defined in YAML.
- It is not a full cron replacement for every system-level daemon. It targets local user-session automation that benefits from the launcher's environment, TCC inheritance, logs, and API observability.
- It does not send notifications.
- It does not sandbox commands.
- It is not designed to be exposed to untrusted networks.

## Users

The primary users are local developers, automation scripts, and AI agents that need a predictable API for running local commands. The service assumes that callers on localhost are trusted.

## Configuration

Runtime configuration lives in `config/launcher.yaml`, which is ignored by git. The repository ships `config/launcher.example.yaml` with fake placeholders.

```yaml
server:
  host: 127.0.0.1
  port: 7997

logging:
  dir: logs
  heartbeat_retention_days: 30
  output_retention_days: 30

storage:
  sqlite_path: state/launcher.db

services:
  demo_service:
    label: demo_service
    command: ["python", "-m", "http.server", "8080"]
    cwd: /path/to/demo/project
    env:
      DEMO_MODE: development
    restart_delay: 10
    max_restarts: 3
    restart_window: 60

periodic_jobs:
  daily_job:
    label: daily_job
    command: ["python", "scripts/daily.py"]
    cwd: /path/to/project
    env_file: .env
    enabled: true
    schedule:
      type: daily
      time: "19:00"
      timezone: America/Los_Angeles
    overlap_policy: skip
    misfire_policy: skip
    timeout: 1800

  weekly_job:
    label: weekly_job
    command: ["python", "scripts/weekly.py"]
    cwd: /path/to/project
    enabled: true
    schedule:
      type: weekly
      days_of_week: [thu]
      time: "07:30"
      timezone: America/Los_Angeles
    overlap_policy: skip
    misfire_policy: skip

  poller:
    label: poller
    command: ["python", "scripts/poll.py"]
    cwd: /path/to/project
    enabled: false
    schedule:
      type: interval
      every_seconds: 600
    overlap_policy: skip
```

Private paths, real service names, secrets, and local job recipes belong in the ignored local config or in a separate private overlay.

## API Surface

- `GET /health` reports server liveness.
- `POST /run` starts a command immediately or creates a durable scheduled launch with `delay_seconds` or `run_at`.
- `GET /scheduled` lists delayed jobs.
- `PATCH /scheduled/{job_id}` updates a pending delayed job's launch metadata, such as `run_at`.
- `POST /scheduled/{job_id}/cancel` cancels a pending delayed job.
- `GET /periodic` lists YAML-declared periodic jobs with runtime state.
- `GET /periodic/{label}` returns one periodic job.
- `GET /periodic/{label}/runs` lists run records for one periodic job.
- `GET /periodic/{label}/runs/{run_id}` returns one periodic run record.
- `GET /processes` lists tracked processes.
- `GET /processes/{pid}` returns one tracked process.
- `POST /processes/{pid}/stop` terminates a tracked process.
- `GET /processes/{pid}/output` reads captured output.
- `POST /declared-services/{label}/restart` restarts one YAML-declared always-on service.
- `GET /logs/heartbeat` reads heartbeat events.
- `GET /logs/output` lists output log files.
- `GET /logs/output/{filename}` reads one output log file.
- `GET /openapi.json` exposes the generated OpenAPI schema.

## Private Overlay Pattern

The public repository contains the generic tool, tests, docs, and skill. A private workspace can maintain overlays such as job aliases, real service recipes, local paths, private domains, notification policies, and operational runbooks. This keeps the package reusable while allowing a user-specific workflow to stay private.

## Durable Scheduling

Delayed jobs are stored in SQLite under `storage.sqlite_path`, relative to the config base directory when a relative path is used. On startup, Process Launcher reloads `pending` jobs and schedules them again. `completed`, `failed`, `cancelled`, and `missed` jobs remain queryable but are not reloaded.

Pending scheduled jobs can be updated through `PATCH /scheduled/{job_id}`. The launcher cancels the existing in-memory delay task, persists the edited job, and registers a new delay task for the updated `run_at`. Jobs that have already started or reached a terminal state cannot be updated.

A scheduled job is `completed` only after its child process exits with code `0`. If the child process exits non-zero, is killed, or cannot be started, the scheduled job becomes `failed` and records `last_error`. Starting the child process successfully is not enough to mark the scheduled job complete.

Callers should dry-run commands before scheduling whenever the target CLI supports it. Dry runs catch missing credentials, incompatible Python versions, invalid paths, and malformed arguments before the durable job is committed. If the target CLI has no dry-run mode, the caller should make that risk explicit and let the user decide whether to schedule anyway. Process Launcher does not enforce dry-run policy because it accepts arbitrary commands and cannot know the correct dry-run flag for each tool.

If a pending job's `run_at` time has already passed while the launcher was down, `misfire_policy` decides what happens:

- `run_immediately` starts the job during recovery.
- `skip` marks the job as `missed`.
- `fail` marks the job as `failed` with an explanatory error.

If the launcher restarts while a scheduled job is `running`, the next startup marks that job `failed` because the new launcher process no longer owns a reliable process handle.

## Declarative Always-On Services

Always-on services are a product-level declaration, not a runtime injection API. They must be defined in `config/launcher.yaml` under `services:`. This keeps long-lived local daemons visible in the bootstrap config, avoids hidden persistent service state, and keeps `/run` focused on one-off or scheduled command execution.

There is no `/services` list/create/reset API surface. Declared services are launched as ordinary tracked child processes, so callers inspect them through `/processes`, `/processes/{pid}/output`, `/logs/heartbeat`, and `/logs/output`.

The only service-specific API is `POST /declared-services/{label}/restart`. It exists for operational recovery of YAML-declared services whose device discovery or external connections need a fresh start. It cannot create services, cannot list services, and returns 404 for labels that are not present in YAML.

## Declarative Periodic Jobs

Periodic jobs are also YAML-declared. This keeps recurring automation auditable and avoids a second hidden source of truth. The HTTP API lets callers inspect declarations, next run time, active PID, last status, and run history. It cannot create, modify, enable, disable, or trigger periodic jobs through `/periodic`; those changes still happen in YAML.

`POST /periodic/reload` reloads only `periodic_jobs` from `config/launcher.yaml` into the running launcher. It does not reload or restart declared services, logging, storage, or server settings. Active periodic child processes keep the configuration they started with; the reloaded declarations affect only future runs. If the new YAML cannot be parsed or validated, the launcher returns an error and keeps the previous in-memory periodic declarations.

For manual validation, callers should submit the same command through `POST /run` with a test label. This preserves the split: YAML defines long-term recurring intent, while `POST /run` remains the one-off execution surface.

Supported schedule types are:

- `daily`: run every day at `time` in `timezone`.
- `weekly`: run on `days_of_week` at `time` in `timezone`.
- `interval`: run every `every_seconds`; this covers polling and every-N-hours jobs.
- `cron`: limited 5-field compatibility for migration cases where daily/weekly/interval are awkward.

`overlap_policy: skip` prevents a new run from starting while the prior run is active. `misfire_policy` is recorded in the declaration for recovery semantics; the initial implementation uses `skip` as the safe default for recurring jobs.
