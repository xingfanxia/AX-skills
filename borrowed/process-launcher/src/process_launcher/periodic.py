from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .models import (
    MisfirePolicy,
    PeriodicJobConfig,
    PeriodicJobState,
    PeriodicOverlapPolicy,
    PeriodicRun,
    PeriodicRunStatus,
    PeriodicRuntime,
    ProcessInfo,
    RunRequest,
)
from .process import ProcessManager
from .storage import SQLiteStore

WEEKDAYS = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


class PeriodicManager:
    """Runs YAML-declared recurring jobs and exposes read-only runtime state."""

    def __init__(self, store: SQLiteStore, jobs: dict[str, PeriodicJobConfig]) -> None:
        self.store = store
        self.jobs = jobs
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._next_run_at: dict[str, datetime | None] = {label: None for label in jobs}
        self._active_runs: dict[str, PeriodicRun] = {}

    def start(self, process_manager: ProcessManager) -> None:
        self.store.mark_stale_periodic_runs_failed()
        for label, job in self.jobs.items():
            if job.enabled:
                self._tasks[label] = asyncio.create_task(self._run_loop(process_manager, job))

    def shutdown(self) -> None:
        for task in self._tasks.values():
            if not task.done():
                task.cancel()

    def reload_jobs(self, process_manager: ProcessManager, jobs: dict[str, PeriodicJobConfig]) -> dict[str, list[str]]:
        """Replace periodic declarations and restart scheduler loops.

        Running child processes are not stopped. Existing run records and active run
        tracking stay intact; the new declarations only affect future starts.
        """
        old_jobs = self.jobs
        added = sorted(set(jobs) - set(old_jobs))
        removed = sorted(set(old_jobs) - set(jobs))
        shared = set(old_jobs) & set(jobs)
        changed = sorted(label for label in shared if old_jobs[label] != jobs[label])
        unchanged = sorted(label for label in shared if old_jobs[label] == jobs[label])

        self.shutdown()
        self._tasks = {}
        self.jobs = jobs
        self._next_run_at = {label: None for label in jobs}
        for label, job in self.jobs.items():
            if job.enabled:
                self._tasks[label] = asyncio.create_task(self._run_loop(process_manager, job))

        return {"added": added, "removed": removed, "changed": changed, "unchanged": unchanged}

    def list_jobs(self) -> list[PeriodicJobState]:
        return [self.get_job(label) for label in sorted(self.jobs)]

    def get_job(self, label: str) -> PeriodicJobState:
        job = self.jobs.get(label)
        if job is None:
            raise KeyError(label)
        runs = self.store.list_periodic_runs(label)
        last_run = runs[-1] if runs else None
        active = self._active_runs.get(label)
        runtime = PeriodicRuntime(
            next_run_at=self._next_run_at.get(label),
            last_run_status=last_run.status if last_run else None,
            last_run_at=last_run.started_at or last_run.scheduled_for if last_run else None,
            active_pid=active.result_pid if active else None,
        )
        return PeriodicJobState(label=label, declared=job, runtime=runtime)

    def list_runs(self, label: str) -> list[PeriodicRun]:
        if label not in self.jobs:
            raise KeyError(label)
        return self.store.list_periodic_runs(label)

    def get_run(self, label: str, run_id: str) -> PeriodicRun:
        if label not in self.jobs:
            raise KeyError(label)
        run = self.store.get_periodic_run(run_id)
        if run is None or run.label != label:
            raise KeyError(run_id)
        return run

    async def _run_loop(self, process_manager: ProcessManager, job: PeriodicJobConfig) -> None:
        now = datetime.now(_schedule_zone(job))
        next_run_at = next_run_after(job, now)
        self._next_run_at[job.label] = next_run_at
        while True:
            try:
                delay = max((next_run_at - datetime.now(next_run_at.tzinfo)).total_seconds(), 0.0)
                await asyncio.sleep(delay)
                scheduled_for = next_run_at
                next_run_at = next_run_after(job, scheduled_for + timedelta(seconds=1))
                self._next_run_at[job.label] = next_run_at
                await self._start_run(process_manager, job, scheduled_for)
            except asyncio.CancelledError:
                return

    async def _start_run(self, process_manager: ProcessManager, job: PeriodicJobConfig, scheduled_for: datetime) -> None:
        active = self._active_runs.get(job.label)
        if active and active.status == PeriodicRunStatus.RUNNING and job.overlap_policy == PeriodicOverlapPolicy.SKIP:
            skipped = PeriodicRun(
                label=job.label,
                command=job.command,
                cwd=job.cwd,
                env=job.env,
                timeout=job.timeout,
                scheduled_for=scheduled_for,
                status=PeriodicRunStatus.SKIPPED,
                last_error="previous periodic run is still active",
                completed_at=datetime.now(),
            )
            self.store.upsert_periodic_run(skipped)
            return

        run = PeriodicRun(
            label=job.label,
            command=job.command,
            cwd=job.cwd,
            env=job.env,
            timeout=job.timeout,
            scheduled_for=scheduled_for,
            status=PeriodicRunStatus.RUNNING,
            started_at=datetime.now(),
        )
        self._active_runs[job.label] = run
        self.store.upsert_periodic_run(run)
        request = RunRequest(command=job.command, cwd=job.cwd, env=job.env, label=job.label, timeout=job.timeout)
        try:
            response = await process_manager.start_process(
                request,
                on_exit=lambda info: _mark_periodic_exit(self, run.id, info),
            )
            self._update_run(run.model_copy(update={"result_pid": response.pid, "output_file": response.output_file}))
        except Exception as exc:
            self._update_run(
                run.model_copy(
                    update={"status": PeriodicRunStatus.FAILED, "last_error": str(exc), "completed_at": datetime.now()}
                )
            )

    def mark_completed(self, run_id: str) -> None:
        run = self.store.get_periodic_run(run_id)
        if run:
            self._update_run(run.model_copy(update={"status": PeriodicRunStatus.COMPLETED, "completed_at": datetime.now()}))

    def mark_failed(self, run_id: str, error: str) -> None:
        run = self.store.get_periodic_run(run_id)
        if run:
            self._update_run(run.model_copy(update={"status": PeriodicRunStatus.FAILED, "last_error": error, "completed_at": datetime.now()}))

    def _update_run(self, run: PeriodicRun) -> None:
        self.store.upsert_periodic_run(run)
        if run.status == PeriodicRunStatus.RUNNING:
            self._active_runs[run.label] = run
        elif self._active_runs.get(run.label, PeriodicRun(id=run.id, label=run.label, command=run.command, scheduled_for=run.scheduled_for)).id == run.id:
            self._active_runs.pop(run.label, None)


def next_run_after(job: PeriodicJobConfig, after: datetime) -> datetime:
    schedule = job.schedule
    if schedule.type == "interval":
        return after + timedelta(seconds=schedule.every_seconds or 0)
    if schedule.type == "daily":
        return _next_daily(after, schedule.time or "00:00", schedule.timezone)
    if schedule.type == "weekly":
        return _next_weekly(after, schedule.time or "00:00", schedule.timezone, schedule.days_of_week)
    if schedule.type == "cron":
        return _next_cron(after, schedule.expression or "* * * * *", schedule.timezone)
    raise ValueError(f"unsupported schedule type: {schedule.type}")


def _next_daily(after: datetime, time_text: str, timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    local_after = after.astimezone(tz) if after.tzinfo else after.replace(tzinfo=tz)
    hour, minute = _parse_time(time_text)
    candidate = local_after.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= local_after:
        candidate += timedelta(days=1)
    return candidate


def _next_weekly(after: datetime, time_text: str, timezone: str, days_of_week: list[str]) -> datetime:
    tz = ZoneInfo(timezone)
    local_after = after.astimezone(tz) if after.tzinfo else after.replace(tzinfo=tz)
    hour, minute = _parse_time(time_text)
    days = sorted(_parse_weekday(day) for day in days_of_week)
    for offset in range(8):
        day = local_after + timedelta(days=offset)
        if day.weekday() not in days:
            continue
        candidate = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate > local_after:
            return candidate
    raise ValueError("could not compute next weekly run")


def _next_cron(after: datetime, expression: str, timezone: str) -> datetime:
    minute_field, hour_field, _dom, _month, dow_field = expression.split()
    tz = ZoneInfo(timezone)
    candidate = (after.astimezone(tz) if after.tzinfo else after.replace(tzinfo=tz)).replace(second=0, microsecond=0)
    candidate += timedelta(minutes=1)
    for _ in range(366 * 24 * 60):
        if _matches_cron(candidate, minute_field, hour_field, dow_field):
            return candidate
        candidate += timedelta(minutes=1)
    raise ValueError("could not compute next cron run")


def _matches_cron(value: datetime, minute_field: str, hour_field: str, dow_field: str) -> bool:
    return (
        _field_matches(value.minute, minute_field, 0, 59)
        and _field_matches(value.hour, hour_field, 0, 23)
        and _dow_matches(value, dow_field)
    )


def _field_matches(value: int, field: str, minimum: int, maximum: int) -> bool:
    if field == "*":
        return True
    for part in field.split(","):
        if part.startswith("*/"):
            step = int(part[2:])
            if (value - minimum) % step == 0:
                return True
        elif "-" in part:
            start, end = (int(piece) for piece in part.split("-", 1))
            if start <= value <= end:
                return True
        elif minimum <= int(part) <= maximum and value == int(part):
            return True
    return False


def _dow_matches(value: datetime, field: str) -> bool:
    if field == "*":
        return True
    cron_dow = (value.weekday() + 1) % 7
    return _field_matches(cron_dow, field, 0, 6)


def _parse_time(value: str) -> tuple[int, int]:
    hour_text, minute_text = value.split(":", 1)
    hour = int(hour_text)
    minute = int(minute_text)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("time must be HH:MM")
    return hour, minute


def _parse_weekday(value: str) -> int:
    key = value.strip().lower()
    if key not in WEEKDAYS:
        raise ValueError(f"invalid weekday: {value}")
    return WEEKDAYS[key]


def _schedule_zone(job: PeriodicJobConfig) -> ZoneInfo:
    return ZoneInfo(job.schedule.timezone)


def _mark_periodic_exit(periodic_manager: PeriodicManager, run_id: str, info: ProcessInfo) -> None:
    if info.exit_code == 0 and info.status.value == "exited":
        periodic_manager.mark_completed(run_id)
    else:
        periodic_manager.mark_failed(run_id, f"process exited with status={info.status.value} exit_code={info.exit_code}")
