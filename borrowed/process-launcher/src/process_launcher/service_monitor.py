from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime

from .log import HeartbeatLogger, utc_now
from .models import ProcessInfo, ProcessStatus, RunRequest, ServiceConfig
from .process import ProcessManager


@dataclass
class ServiceRuntime:
    config: ServiceConfig
    pid: int | None = None
    status: ProcessStatus = ProcessStatus.EXITED
    restart_count: int = 0
    failure_chain_start: datetime | None = None
    last_exit_code: int | None = None
    restarting_task: asyncio.Task[None] | None = None


class ServiceMonitor:
    def __init__(self, process_manager: ProcessManager, heartbeat_logger: HeartbeatLogger) -> None:
        self.process_manager = process_manager
        self.heartbeat_logger = heartbeat_logger
        self._services: dict[str, ServiceRuntime] = {}
        self._shutting_down = False

    def register_services(self, services: dict[str, ServiceConfig]) -> None:
        for service in services.values():
            self._services[service.label] = ServiceRuntime(config=service)

    async def start_registered_services(self) -> None:
        for label in list(self._services):
            await self._start_service(label)

    async def shutdown(self) -> None:
        self._shutting_down = True
        for runtime in self._services.values():
            if runtime.restarting_task is not None:
                runtime.restarting_task.cancel()

    async def restart_service(self, label: str) -> ProcessInfo:
        runtime = self._get_runtime(label)
        runtime.restart_count = 0
        runtime.failure_chain_start = None
        runtime.status = ProcessStatus.EXITED
        if runtime.pid is not None:
            try:
                await self.process_manager.stop_process(runtime.pid)
            except KeyError:
                pass
        return await self._start_service(label)

    async def reset_circuit_breaker(self, label: str) -> ProcessInfo:
        runtime = self._get_runtime(label)
        runtime.restart_count = 0
        runtime.failure_chain_start = None
        runtime.status = ProcessStatus.EXITED
        self.heartbeat_logger.write_event("CIRCUIT_BREAKER_RESET", label=label)
        return await self._start_service(label)

    def list_services(self) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for label, runtime in sorted(self._services.items()):
            process = self.process_manager.get_process(runtime.pid) if runtime.pid is not None else None
            items.append(
                {
                    "label": label,
                    "pid": runtime.pid,
                    "status": runtime.status.value,
                    "restart_count": runtime.restart_count,
                    "exit_code": process.exit_code if process else runtime.last_exit_code,
                    "command": process.command if process else " ".join(self._command_list(runtime.config.command)),
                }
            )
        return items

    async def _start_service(self, label: str) -> ProcessInfo:
        runtime = self._get_runtime(label)
        request = RunRequest(
            command=runtime.config.command,
            cwd=runtime.config.cwd,
            env=runtime.config.env,
            label=runtime.config.label,
        )
        response = await self.process_manager.start_process(
            request,
            restart_count=runtime.restart_count,
            on_exit=lambda info, service_label=label: self._handle_exit(service_label, info),
        )
        runtime.pid = response.pid
        runtime.status = ProcessStatus.RUNNING
        process = self.process_manager.get_process(response.pid)
        if process is None:
            raise RuntimeError(f"failed to track service process for {label}")
        return process

    async def _handle_exit(self, label: str, info: ProcessInfo) -> None:
        if self._shutting_down:
            return

        runtime = self._get_runtime(label)
        runtime.last_exit_code = info.exit_code
        if info.status == ProcessStatus.KILLED:
            runtime.status = ProcessStatus.KILLED
            return

        now = utc_now()
        if runtime.failure_chain_start is None or (now - runtime.failure_chain_start).total_seconds() > runtime.config.restart_window:
            runtime.failure_chain_start = now
            runtime.restart_count = 1
        else:
            runtime.restart_count += 1

        if runtime.restart_count >= runtime.config.max_restarts:
            runtime.status = ProcessStatus.CIRCUIT_BREAKER
            self.heartbeat_logger.write_event(
                "CIRCUIT_BREAKER",
                label=label,
                consecutive_failures=runtime.restart_count,
            )
            return

        runtime.status = ProcessStatus.EXITED
        self.heartbeat_logger.write_event(
            "RESTART",
            label=label,
            attempt=runtime.restart_count,
            reason=f"exit_code={info.exit_code}",
        )
        runtime.restarting_task = asyncio.create_task(self._restart_after_delay(label, runtime.config.restart_delay))

    async def _restart_after_delay(self, label: str, delay: float) -> None:
        await asyncio.sleep(delay)
        if self._shutting_down:
            return
        await self._start_service(label)

    def _get_runtime(self, label: str) -> ServiceRuntime:
        runtime = self._services.get(label)
        if runtime is None:
            raise KeyError(label)
        return runtime

    def _command_list(self, command: list[str] | str) -> list[str]:
        return command if isinstance(command, list) else [command]
