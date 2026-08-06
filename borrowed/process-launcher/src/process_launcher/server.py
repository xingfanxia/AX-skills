from __future__ import annotations

import asyncio
import os
import signal
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query

from .config import load_config
from .log import HeartbeatLogger, OutputLogger
from .models import (
    LauncherConfig,
    PeriodicJobState,
    PeriodicReloadResult,
    PeriodicRun,
    ProcessInfo,
    RunRequest,
    RunResponse,
    ScheduledJob,
    ScheduledUpdateRequest,
)
from .periodic import PeriodicManager
from .process import ProcessManager
from .scheduled import ScheduledManager
from .service_monitor import ServiceMonitor
from .storage import SQLiteStore


def create_app(config_path: str | Path | None = None, config: LauncherConfig | None = None) -> FastAPI:
    resolved_config_path = Path(config_path) if config_path else None

    def get_config() -> LauncherConfig:
        if config is not None:
            return config
        if resolved_config_path is None:
            raise RuntimeError("config path is required")
        return load_config(resolved_config_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await initialize_app_state(app, get_config(), resolved_config_path)
        try:
            yield
        finally:
            await shutdown_app_state(app)

    app = FastAPI(title="Process Launcher", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/run", response_model=RunResponse)
    async def run_command(request: RunRequest) -> RunResponse:
        process_manager: ProcessManager = app.state.process_manager
        if (request.delay_seconds and request.delay_seconds > 0) or request.run_at is not None:
            scheduled_at = datetime.now()
            run_at = request.run_at or scheduled_at + timedelta(seconds=request.delay_seconds or 0)
            job = ScheduledJob(
                label=request.label,
                command=request.command,
                cwd=request.cwd,
                env=request.env,
                timeout=request.timeout,
                scheduled_at=scheduled_at,
                run_at=run_at,
                misfire_policy=request.misfire_policy,
            )
            scheduled_manager: ScheduledManager = app.state.scheduled_manager
            scheduled_manager.add(job)
            scheduled_manager.schedule(process_manager, job, request)
            return RunResponse(
                pid=0,
                label=request.label,
                started_at=scheduled_at,
                output_file=None,
            )
        return await process_manager.start_process(request)

    @app.get("/scheduled", response_model=list[ScheduledJob])
    async def list_scheduled() -> list[ScheduledJob]:
        scheduled_manager: ScheduledManager = app.state.scheduled_manager
        return scheduled_manager.list_jobs()

    @app.get("/periodic", response_model=list[PeriodicJobState])
    async def list_periodic() -> list[PeriodicJobState]:
        periodic_manager: PeriodicManager = app.state.periodic_manager
        return periodic_manager.list_jobs()

    @app.get("/periodic/{label}", response_model=PeriodicJobState)
    async def get_periodic(label: str) -> PeriodicJobState:
        periodic_manager: PeriodicManager = app.state.periodic_manager
        try:
            return periodic_manager.get_job(label)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="periodic job not found") from exc

    @app.get("/periodic/{label}/runs", response_model=list[PeriodicRun])
    async def list_periodic_runs(label: str) -> list[PeriodicRun]:
        periodic_manager: PeriodicManager = app.state.periodic_manager
        try:
            return periodic_manager.list_runs(label)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="periodic job not found") from exc

    @app.get("/periodic/{label}/runs/{run_id}", response_model=PeriodicRun)
    async def get_periodic_run(label: str, run_id: str) -> PeriodicRun:
        periodic_manager: PeriodicManager = app.state.periodic_manager
        try:
            return periodic_manager.get_run(label, run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="periodic run not found") from exc

    @app.post("/periodic/reload", response_model=PeriodicReloadResult)
    async def reload_periodic() -> PeriodicReloadResult:
        if resolved_config_path is None:
            raise HTTPException(status_code=409, detail="config path is required for periodic reload")
        try:
            reloaded_config = load_config(resolved_config_path)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"config reload failed: {exc}") from exc
        periodic_manager: PeriodicManager = app.state.periodic_manager
        process_manager: ProcessManager = app.state.process_manager
        diff = periodic_manager.reload_jobs(process_manager, reloaded_config.periodic_jobs)
        app.state.launcher_config = app.state.launcher_config.model_copy(
            update={"periodic_jobs": reloaded_config.periodic_jobs}
        )
        return PeriodicReloadResult(status="reloaded", **diff)

    @app.post("/scheduled/{job_id}/cancel", response_model=ScheduledJob)
    async def cancel_scheduled(job_id: str) -> ScheduledJob:
        scheduled_manager: ScheduledManager = app.state.scheduled_manager
        try:
            return scheduled_manager.cancel(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="scheduled job not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.patch("/scheduled/{job_id}", response_model=ScheduledJob)
    async def update_scheduled(job_id: str, request: ScheduledUpdateRequest) -> ScheduledJob:
        scheduled_manager: ScheduledManager = app.state.scheduled_manager
        process_manager: ProcessManager = app.state.process_manager
        try:
            return scheduled_manager.update(process_manager, job_id, request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="scheduled job not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/processes", response_model=list[ProcessInfo])
    async def list_processes(running_only: bool = False) -> list[ProcessInfo]:
        process_manager: ProcessManager = app.state.process_manager
        return process_manager.list_processes(running_only=running_only)

    @app.get("/processes/{pid}", response_model=ProcessInfo)
    async def get_process(pid: int) -> ProcessInfo:
        process_manager: ProcessManager = app.state.process_manager
        process = process_manager.get_process(pid)
        if process is None:
            raise HTTPException(status_code=404, detail="process not found")
        return process

    @app.post("/processes/{pid}/stop", response_model=ProcessInfo)
    async def stop_process(pid: int) -> ProcessInfo:
        process_manager: ProcessManager = app.state.process_manager
        try:
            return await process_manager.stop_process(pid)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="process not found") from exc

    @app.get("/processes/{pid}/output")
    async def get_process_output(pid: int, tail: int | None = Query(default=None, ge=1)) -> dict[str, object]:
        process_manager: ProcessManager = app.state.process_manager
        try:
            return process_manager.get_output(pid, tail=tail)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="process not found") from exc

    @app.post("/declared-services/{label}/restart", response_model=ProcessInfo)
    async def restart_declared_service(label: str) -> ProcessInfo:
        service_monitor: ServiceMonitor = app.state.service_monitor
        try:
            return await service_monitor.restart_service(label)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="declared service not found") from exc

    @app.get("/logs/heartbeat")
    async def get_heartbeat_logs(
        limit: int = Query(default=100, ge=1, le=1000),
        event: str | None = None,
        label: str | None = None,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        heartbeat_logger: HeartbeatLogger = app.state.heartbeat_logger
        return heartbeat_logger.read_events(limit=limit, event=event, label=label, since=since)

    @app.get("/logs/output")
    async def list_output_logs() -> list[dict[str, Any]]:
        output_logger: OutputLogger = app.state.output_logger
        return output_logger.list_output_logs()

    @app.get("/logs/output/{filename}")
    async def read_output_log(filename: str, tail: int | None = Query(default=None, ge=1)) -> dict[str, Any]:
        output_logger: OutputLogger = app.state.output_logger
        try:
            return output_logger.read_output_log(filename, tail=tail)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="log file not found") from exc

    @app.post("/shutdown")
    async def shutdown_launcher(background_tasks: BackgroundTasks) -> dict[str, str]:
        background_tasks.add_task(_terminate_self)
        return {"status": "shutting_down"}

    return app


async def _terminate_self() -> None:
    await asyncio.sleep(0.1)
    os.kill(os.getpid(), signal.SIGTERM)


async def initialize_app_state(app: FastAPI, launcher_config: LauncherConfig, config_path: Path | None = None) -> None:
    if getattr(app.state, "process_manager", None) is not None:
        return

    base_dir = config_path.parent.parent if config_path else Path.cwd()
    log_dir = base_dir / launcher_config.logging.dir
    sqlite_path = Path(launcher_config.storage.sqlite_path)
    if not sqlite_path.is_absolute():
        sqlite_path = base_dir / sqlite_path
    heartbeat_logger = HeartbeatLogger(log_dir, retention_days=launcher_config.logging.heartbeat_retention_days)
    output_logger = OutputLogger(log_dir, retention_days=launcher_config.logging.output_retention_days)
    sqlite_store = SQLiteStore(sqlite_path)
    process_manager = ProcessManager(heartbeat_logger, output_logger)
    service_monitor = ServiceMonitor(process_manager, heartbeat_logger)
    service_monitor.register_services(launcher_config.services)
    scheduled_manager = ScheduledManager(sqlite_store)
    periodic_manager = PeriodicManager(sqlite_store, launcher_config.periodic_jobs)

    app.state.launcher_config = launcher_config
    app.state.heartbeat_logger = heartbeat_logger
    app.state.output_logger = output_logger
    app.state.process_manager = process_manager
    app.state.service_monitor = service_monitor
    app.state.scheduled_manager = scheduled_manager
    app.state.periodic_manager = periodic_manager

    scheduled_manager.recover_pending(process_manager)
    periodic_manager.start(process_manager)
    await service_monitor.start_registered_services()


async def shutdown_app_state(app: FastAPI) -> None:
    service_monitor: ServiceMonitor | None = getattr(app.state, "service_monitor", None)
    process_manager: ProcessManager | None = getattr(app.state, "process_manager", None)
    scheduled_manager: ScheduledManager | None = getattr(app.state, "scheduled_manager", None)
    periodic_manager: PeriodicManager | None = getattr(app.state, "periodic_manager", None)
    if periodic_manager is not None:
        periodic_manager.shutdown()
    if scheduled_manager is not None:
        scheduled_manager.shutdown()
    if service_monitor is not None:
        await service_monitor.shutdown()
    if process_manager is not None:
        await process_manager.stop_all()
    if scheduled_manager is not None:
        scheduled_manager.close()

    for attr in ("service_monitor", "process_manager", "heartbeat_logger", "output_logger", "launcher_config", "scheduled_manager", "periodic_manager"):
        if hasattr(app.state, attr):
            delattr(app.state, attr)
