# Process Launcher RFC

## Status

Draft for the public package scaffold.

## Design Summary

Process Launcher is a localhost FastAPI server around `subprocess.Popen`. It starts child processes, captures combined stdout and stderr, stores current process handles in memory, persists scheduled jobs and periodic run history in SQLite, runs YAML-declared recurring jobs, and writes heartbeat events to JSONL files. It favors a small implementation over a broad job-management framework.

## Decisions

### D1: Localhost API

The service binds to `127.0.0.1` by default. `POST /run` accepts arbitrary commands, so network exposure would require authentication, authorization, and command policy work that is outside the current scope.

### D2: Process Handles Stay In Memory

Tracked process handles stay in memory. Restarting the launcher starts with an empty `/processes` table because a new process cannot safely inherit old `subprocess.Popen` handles. Durable run history can be added separately, but process control APIs only operate on children owned by the current launcher process.

### D3: SQLite-Backed Scheduled Jobs

Delayed and absolute-time scheduled jobs are stored in SQLite. YAML remains the bootstrap config for server, logging, storage, and declared always-on services. SQLite owns runtime lifecycle records for scheduled work: `pending`, `running`, `completed`, `failed`, `cancelled`, and `missed`.

Pending scheduled jobs can be updated through `PATCH /scheduled/{job_id}`. The update operation is intentionally narrow: it edits launch metadata such as `run_at`, `label`, `timeout`, or `misfire_policy` while preserving the job id, command, cwd, and env. The scheduler cancels the existing in-memory delay task, persists the edited row, and registers a new delay task. Running or terminal jobs return a conflict instead of mutating history.

Scheduled job completion follows the child process exit result. The scheduler marks a job `running` after it starts the child process, then waits for the process exit callback. Exit code `0` marks the job `completed`; non-zero exit, killed status, or start failure marks it `failed` with `last_error`. This keeps the scheduling API honest for commands that start successfully but fail immediately.

Dry-run validation stays at the caller layer. Many scheduled commands are tool-specific CLIs with their own `--dry-run`, `--check`, or preview modes. The launcher cannot infer those flags from an arbitrary command safely, so it records and executes the command it receives. Agents and scripts should run the target command's dry-run path before creating a durable schedule. When no dry-run exists, they should disclose that limitation before scheduling.

The database includes a `schema_migrations` table. Each migration runs once and leaves a permanent version record so future launcher versions can upgrade older database files predictably.

### D4: YAML-Declared Periodic Jobs

Recurring schedules are declared in YAML under `periodic_jobs:`. YAML is the only source of truth for periodic job creation, deletion, enablement, command changes, and schedule changes. This mirrors declared always-on services and avoids hidden long-term state created through HTTP.

The periodic HTTP API is mostly read-only:

- `GET /periodic`
- `GET /periodic/{label}`
- `GET /periodic/{label}/runs`
- `GET /periodic/{label}/runs/{run_id}`
- `POST /periodic/reload`

`POST /periodic/reload` is a reconcile operation, not a mutation API. It rereads `periodic_jobs` from the YAML config path already used at startup, validates the full config, replaces only the in-memory periodic declarations, and restarts scheduler loops for future runs. It does not reload declared services, server settings, logging settings, storage settings, or environment outside periodic jobs. Active periodic child processes are not stopped and keep the command, env, and timeout they started with.

There is intentionally no `POST /periodic`, `run-now`, `enable`, or `disable` endpoint. Manual validation should use `POST /run` with the same command and a test label.

Supported schedule types are `daily`, `weekly`, `interval`, and limited 5-field `cron`. The first three are the preferred forms because they encode the user's intent more clearly than cron text. `cron` exists as a migration escape hatch for expressions like multiple run times in one day.

Periodic job declarations stay in YAML. Periodic run instances stay in SQLite. This keeps durable run history queryable without making SQLite the source of long-term desired state.

### D5: Always-On Service Recovery

Always-on services use minimal restart logic because the launcher already owns the child process. Each service can set `restart_delay`, `max_restarts`, and `restart_window`. After repeated failures, the service enters `circuit_breaker` until a caller resets it.

Declared services come from YAML. API-created always-on services and broad service management endpoints are intentionally unsupported. This avoids hidden long-lived daemons created through `/run` and keeps the launcher split clear: YAML owns service desired state; SQLite owns scheduled job lifecycle state. Once launched, declared services are ordinary tracked child processes for API purposes.

The exception is `POST /declared-services/{label}/restart`, which restarts a service that already exists in YAML. It is a recovery operation for stale device discovery, dropped local-network connections, or manual flushes. It does not list, create, persist, or reset services through HTTP.

### D6: Logs Are Local Files

Heartbeat events are JSONL files named by date. Output logs are one file per process start. Retention is controlled by simple day-count settings. The launcher does not upload, archive, or analyze logs.

### D7: OpenAPI Is the Integration Contract

FastAPI generates the OpenAPI schema. Agents and scripts can inspect `/openapi.json` instead of relying on a separate hand-maintained API schema.

### D8: TCC Foreground Process Constraint

The launcher must run inside an interactive terminal session to inherit macOS TCC permissions. This is not a software limitation. It is a consequence of how macOS privacy controls audit the responsible process. The launcher is designed as a TCC bridge: start it once from a GUI terminal, then route all TCC-sensitive jobs through its API.

Background supervisors (cron, launchd, PM2) cannot provide the required GUI ancestry. Multiplexers (tmux, zellij) work only if their server was started from an interactive GUI terminal. This constraint is a deployment requirement, not a feature gap.

## Data Flow

```text
caller -> POST /run -> ProcessManager -> subprocess.Popen
                                      -> output log file
                                      -> heartbeat JSONL

caller -> POST /run with delay_seconds/run_at -> SQLite scheduled_jobs
                                             -> recovery scheduler
                                             -> ProcessManager at run_at

caller -> GET /processes/{pid} -> in-memory process table
caller -> GET /scheduled -> SQLite scheduled_jobs
caller -> PATCH /scheduled/{id} -> cancel old delay task -> update SQLite row -> new delay task
caller -> GET /periodic -> YAML periodic_jobs + SQLite periodic_runs
caller -> GET /logs/output/{file} -> local output log
```

## Startup Recovery

On startup, the launcher opens SQLite, applies pending migrations, marks stale `running` scheduled jobs as `failed`, then reloads `pending` scheduled jobs.

For each pending job:

- `run_at > now`: register an asyncio task for the remaining delay.
- `run_at <= now` and `misfire_policy = run_immediately`: run as soon as recovery completes.
- `run_at <= now` and `misfire_policy = skip`: mark `missed`.
- `run_at <= now` and `misfire_policy = fail`: mark `failed`.

Completed, failed, cancelled, and missed jobs stay in SQLite for inspection and are not rescheduled.

Periodic startup is separate from one-shot startup. The launcher reads YAML declarations, marks any previously `running` periodic runs as `failed` because the new process does not own their child process handles, then starts one scheduler loop per enabled periodic job. Disabled periodic jobs remain visible through `GET /periodic` but do not run.

Periodic reload follows the same declaration parsing path as startup but skips stale-run recovery. Already running child processes still have live process handles, so reload preserves active run tracking and only replaces future scheduler loops. If parsing or validation fails, the existing periodic manager remains unchanged.

Each periodic run starts as a normal tracked process and writes to the same output log and heartbeat paths as a one-off `/run` command. The periodic run record stores `scheduled_for`, `started_at`, `completed_at`, `status`, `result_pid`, `output_file`, and `last_error`.

If a prior run is still active and `overlap_policy = skip`, the launcher records a skipped run instead of starting another process. `run_concurrently` permits overlapping process starts.

## Security Model

The service is a trusted-local tool. A caller that can reach the API can run commands as the launcher user. Public deployments or shared machines need an additional security layer before exposing the API beyond localhost.

macOS TCC adds a deployment-level security constraint. The launcher must be started from an interactive GUI terminal to grant its children access to TCC-protected capabilities. Background startup methods (cron, launchd, PM2) bypass the GUI ancestry chain and will cause TCC-sensitive jobs to fail silently or with denied-permission errors.

## Public And Private Layers

The public package owns generic code and docs. Private overlays own real job recipes, local service aliases, personal paths, and secrets. This separation is part of the project design rather than an afterthought.
