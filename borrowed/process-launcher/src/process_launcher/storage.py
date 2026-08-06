from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import MisfirePolicy, PeriodicRun, PeriodicRunStatus, ScheduledJob, ScheduledStatus


SCHEMA_VERSION = 2


class SQLiteStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self.migrate()

    def close(self) -> None:
        self._conn.close()

    def migrate(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        applied = {
            row["version"]
            for row in self._conn.execute("SELECT version FROM schema_migrations").fetchall()
        }
        if 1 not in applied:
            self._conn.execute(
                """
                CREATE TABLE scheduled_jobs (
                    id TEXT PRIMARY KEY,
                    label TEXT,
                    command_json TEXT NOT NULL,
                    cwd TEXT,
                    env_json TEXT NOT NULL,
                    timeout REAL,
                    scheduled_at TEXT NOT NULL,
                    run_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    misfire_policy TEXT NOT NULL,
                    result_pid INTEGER,
                    last_error TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    cancelled_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute("CREATE INDEX idx_scheduled_jobs_status_run_at ON scheduled_jobs(status, run_at)")
            self._conn.execute(
                "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
                (1, "create_scheduled_jobs", _serialize_datetime(datetime.now())),
            )
            self._conn.commit()
        if 2 not in applied:
            self._conn.execute(
                """
                CREATE TABLE periodic_runs (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    command_json TEXT NOT NULL,
                    cwd TEXT,
                    env_json TEXT NOT NULL,
                    timeout REAL,
                    scheduled_for TEXT NOT NULL,
                    status TEXT NOT NULL,
                    trigger TEXT NOT NULL,
                    result_pid INTEGER,
                    output_file TEXT,
                    last_error TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute("CREATE INDEX idx_periodic_runs_label_scheduled_for ON periodic_runs(label, scheduled_for)")
            self._conn.execute("CREATE INDEX idx_periodic_runs_status ON periodic_runs(status)")
            self._conn.execute(
                "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
                (2, "create_periodic_runs", _serialize_datetime(datetime.now())),
            )
            self._conn.commit()

    def upsert_scheduled_job(self, job: ScheduledJob) -> None:
        now = _serialize_datetime(datetime.now())
        self._conn.execute(
            """
            INSERT INTO scheduled_jobs(
                id, label, command_json, cwd, env_json, timeout, scheduled_at, run_at,
                status, misfire_policy, result_pid, last_error, started_at, completed_at,
                cancelled_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                label = excluded.label,
                command_json = excluded.command_json,
                cwd = excluded.cwd,
                env_json = excluded.env_json,
                timeout = excluded.timeout,
                scheduled_at = excluded.scheduled_at,
                run_at = excluded.run_at,
                status = excluded.status,
                misfire_policy = excluded.misfire_policy,
                result_pid = excluded.result_pid,
                last_error = excluded.last_error,
                started_at = excluded.started_at,
                completed_at = excluded.completed_at,
                cancelled_at = excluded.cancelled_at,
                updated_at = excluded.updated_at
            """,
            _job_values(job, created_at=now, updated_at=now),
        )
        self._conn.commit()

    def update_scheduled_job(self, job: ScheduledJob) -> None:
        self.upsert_scheduled_job(job)

    def list_scheduled_jobs(self) -> list[ScheduledJob]:
        rows = self._conn.execute("SELECT * FROM scheduled_jobs ORDER BY scheduled_at").fetchall()
        return [_row_to_job(row) for row in rows]

    def list_pending_scheduled_jobs(self) -> list[ScheduledJob]:
        rows = self._conn.execute(
            "SELECT * FROM scheduled_jobs WHERE status = ? ORDER BY run_at",
            (ScheduledStatus.PENDING.value,),
        ).fetchall()
        return [_row_to_job(row) for row in rows]

    def mark_stale_running_jobs_failed(self) -> None:
        now = _serialize_datetime(datetime.now())
        self._conn.execute(
            """
            UPDATE scheduled_jobs
            SET status = ?, last_error = ?, completed_at = ?, updated_at = ?
            WHERE status = ?
            """,
            (
                ScheduledStatus.FAILED.value,
                "launcher restarted while scheduled job was running",
                now,
                now,
                ScheduledStatus.RUNNING.value,
            ),
        )
        self._conn.commit()

    def upsert_periodic_run(self, run: PeriodicRun) -> None:
        now = _serialize_datetime(datetime.now())
        self._conn.execute(
            """
            INSERT INTO periodic_runs(
                id, label, command_json, cwd, env_json, timeout, scheduled_for, status,
                trigger, result_pid, output_file, last_error, started_at, completed_at,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                label = excluded.label,
                command_json = excluded.command_json,
                cwd = excluded.cwd,
                env_json = excluded.env_json,
                timeout = excluded.timeout,
                scheduled_for = excluded.scheduled_for,
                status = excluded.status,
                trigger = excluded.trigger,
                result_pid = excluded.result_pid,
                output_file = excluded.output_file,
                last_error = excluded.last_error,
                started_at = excluded.started_at,
                completed_at = excluded.completed_at,
                updated_at = excluded.updated_at
            """,
            _periodic_run_values(run, created_at=now, updated_at=now),
        )
        self._conn.commit()

    def list_periodic_runs(self, label: str | None = None) -> list[PeriodicRun]:
        if label is None:
            rows = self._conn.execute("SELECT * FROM periodic_runs ORDER BY scheduled_for").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM periodic_runs WHERE label = ? ORDER BY scheduled_for",
                (label,),
            ).fetchall()
        return [_row_to_periodic_run(row) for row in rows]

    def get_periodic_run(self, run_id: str) -> PeriodicRun | None:
        row = self._conn.execute("SELECT * FROM periodic_runs WHERE id = ?", (run_id,)).fetchone()
        return _row_to_periodic_run(row) if row else None

    def list_running_periodic_runs(self) -> list[PeriodicRun]:
        rows = self._conn.execute(
            "SELECT * FROM periodic_runs WHERE status = ? ORDER BY scheduled_for",
            (PeriodicRunStatus.RUNNING.value,),
        ).fetchall()
        return [_row_to_periodic_run(row) for row in rows]

    def mark_stale_periodic_runs_failed(self) -> None:
        now = _serialize_datetime(datetime.now())
        self._conn.execute(
            """
            UPDATE periodic_runs
            SET status = ?, last_error = ?, completed_at = ?, updated_at = ?
            WHERE status = ?
            """,
            (
                PeriodicRunStatus.FAILED.value,
                "launcher restarted while periodic run was running",
                now,
                now,
                PeriodicRunStatus.RUNNING.value,
            ),
        )
        self._conn.commit()


def _job_values(job: ScheduledJob, *, created_at: str, updated_at: str) -> tuple[Any, ...]:
    return (
        job.id,
        job.label,
        json.dumps(job.command),
        job.cwd,
        json.dumps(job.env),
        job.timeout,
        _serialize_datetime(job.scheduled_at),
        _serialize_datetime(job.run_at),
        job.status.value,
        job.misfire_policy.value,
        job.result_pid,
        job.last_error,
        _serialize_optional_datetime(job.started_at),
        _serialize_optional_datetime(job.completed_at),
        _serialize_optional_datetime(job.cancelled_at),
        created_at,
        updated_at,
    )


def _row_to_job(row: sqlite3.Row) -> ScheduledJob:
    return ScheduledJob(
        id=row["id"],
        label=row["label"],
        command=json.loads(row["command_json"]),
        cwd=row["cwd"],
        env=json.loads(row["env_json"]),
        timeout=row["timeout"],
        scheduled_at=_parse_datetime(row["scheduled_at"]),
        run_at=_parse_datetime(row["run_at"]),
        status=ScheduledStatus(row["status"]),
        misfire_policy=MisfirePolicy(row["misfire_policy"]),
        result_pid=row["result_pid"],
        last_error=row["last_error"],
        started_at=_parse_optional_datetime(row["started_at"]),
        completed_at=_parse_optional_datetime(row["completed_at"]),
        cancelled_at=_parse_optional_datetime(row["cancelled_at"]),
    )


def _periodic_run_values(run: PeriodicRun, *, created_at: str, updated_at: str) -> tuple[Any, ...]:
    return (
        run.id,
        run.label,
        json.dumps(run.command),
        run.cwd,
        json.dumps(run.env),
        run.timeout,
        _serialize_datetime(run.scheduled_for),
        run.status.value,
        run.trigger,
        run.result_pid,
        run.output_file,
        run.last_error,
        _serialize_optional_datetime(run.started_at),
        _serialize_optional_datetime(run.completed_at),
        created_at,
        updated_at,
    )


def _row_to_periodic_run(row: sqlite3.Row) -> PeriodicRun:
    return PeriodicRun(
        id=row["id"],
        label=row["label"],
        command=json.loads(row["command_json"]),
        cwd=row["cwd"],
        env=json.loads(row["env_json"]),
        timeout=row["timeout"],
        scheduled_for=_parse_datetime(row["scheduled_for"]),
        status=PeriodicRunStatus(row["status"]),
        trigger=row["trigger"],
        result_pid=row["result_pid"],
        output_file=row["output_file"],
        last_error=row["last_error"],
        started_at=_parse_optional_datetime(row["started_at"]),
        completed_at=_parse_optional_datetime(row["completed_at"]),
    )


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _serialize_optional_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _parse_optional_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
