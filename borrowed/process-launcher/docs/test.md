# Test Plan

## Test Layers

The default test suite uses pytest, temporary config directories, and short-lived local subprocesses. It validates the package without requiring a pre-existing launcher process.

The `live_integration` marker is reserved for tests that start a real launcher server on port `7976` through the existing pytest fixture. These tests remain opt-in.

## Commands

```bash
python -m pytest -v
python -m pytest -v --cov=process_launcher --cov-report=term-missing
python -m pytest -v -m live_integration
```

## Coverage Areas

- Config parsing and `.env` loading.
- Process start, stop, timeout, cwd, env, output capture, and zombie reaping.
- Service monitor restart behavior and circuit breaker behavior.
- Heartbeat and output log writing, filtering, and retention cleanup.
- FastAPI endpoints for health, process control, scheduled jobs, logs, and OpenAPI.
- SQLite schema migration and durable scheduled job recovery.
- Pending scheduled job updates: rescheduling updates SQLite state, replaces the in-memory delay task, rejects non-pending jobs, and returns 404 for unknown job ids.
- YAML-declared periodic job parsing, next-run calculation, read-only API endpoints, run records, and stale-running recovery.
- Misfire policies for jobs whose `run_at` passes while the launcher is down.
- Scheduled job status follows child process exit code: `0` completes, non-zero fails.
- Periodic run status follows child process exit code and records output log paths.
- Periodic write endpoints remain unavailable; YAML is the only source of truth.
- Live HTTP behavior through the `live_integration` fixture.

## Marker Semantics

`live_integration` tests may launch a real server process and submit commands through HTTP. The fixture checks whether port `7976` is free and skips if it is already occupied. The default test command should continue to avoid depending on a running external service.

## TCC Testing Note

TCC permissions cannot be tested in automated CI or unit tests. The permission model depends on the process ancestry chain, which is absent in non-interactive test runners. Manual verification from a terminal session is required to confirm that a launched child process inherits the expected TCC grants. The `live_integration` marker can be used for this manual check on a development machine.
