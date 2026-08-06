from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from process_launcher.models import MisfirePolicy, PeriodicRun, PeriodicRunStatus, ScheduledJob, ScheduledStatus
from process_launcher.storage import SQLiteStore


def test_storage_creates_schema_and_migration_record(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "state" / "launcher.db")
    try:
        rows = store._conn.execute("SELECT version, name FROM schema_migrations").fetchall()
        assert [(row["version"], row["name"]) for row in rows] == [
            (1, "create_scheduled_jobs"),
            (2, "create_periodic_runs"),
        ]
    finally:
        store.close()


def test_storage_round_trips_scheduled_job(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "launcher.db")
    run_at = datetime.now() + timedelta(hours=1)
    job = ScheduledJob(
        label="demo",
        command=["python", "demo.py"],
        cwd="/tmp/demo",
        env={"A": "B"},
        timeout=30,
        scheduled_at=datetime.now(),
        run_at=run_at,
        misfire_policy=MisfirePolicy.SKIP,
    )
    try:
        store.upsert_scheduled_job(job)
        jobs = store.list_scheduled_jobs()
        assert len(jobs) == 1
        assert jobs[0].label == "demo"
        assert jobs[0].command == ["python", "demo.py"]
        assert jobs[0].env == {"A": "B"}
        assert jobs[0].misfire_policy == MisfirePolicy.SKIP
    finally:
        store.close()


def test_storage_marks_stale_running_jobs_failed(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "launcher.db")
    job = ScheduledJob(
        label="running",
        command="python demo.py",
        scheduled_at=datetime.now(),
        run_at=datetime.now(),
        status=ScheduledStatus.RUNNING,
    )
    try:
        store.upsert_scheduled_job(job)
        store.mark_stale_running_jobs_failed()
        stored = store.list_scheduled_jobs()[0]
        assert stored.status == ScheduledStatus.FAILED
        assert stored.last_error == "launcher restarted while scheduled job was running"
    finally:
        store.close()


def test_storage_round_trips_periodic_run(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "launcher.db")
    run = PeriodicRun(
        label="daily",
        command=["python", "daily.py"],
        cwd="/tmp/demo",
        env={"A": "B"},
        timeout=30,
        scheduled_for=datetime.now() + timedelta(hours=1),
        status=PeriodicRunStatus.RUNNING,
        result_pid=123,
        output_file="daily.log",
    )
    try:
        store.upsert_periodic_run(run)
        runs = store.list_periodic_runs("daily")
        assert len(runs) == 1
        assert runs[0].label == "daily"
        assert runs[0].command == ["python", "daily.py"]
        assert runs[0].env == {"A": "B"}
        assert runs[0].status == PeriodicRunStatus.RUNNING
        assert store.get_periodic_run(run.id) == runs[0]
    finally:
        store.close()


def test_storage_marks_stale_periodic_runs_failed(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "launcher.db")
    run = PeriodicRun(
        label="running",
        command="python demo.py",
        scheduled_for=datetime.now(),
        status=PeriodicRunStatus.RUNNING,
    )
    try:
        store.upsert_periodic_run(run)
        store.mark_stale_periodic_runs_failed()
        stored = store.list_periodic_runs()[0]
        assert stored.status == PeriodicRunStatus.FAILED
        assert stored.last_error == "launcher restarted while periodic run was running"
    finally:
        store.close()
