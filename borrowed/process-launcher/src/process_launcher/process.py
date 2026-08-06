from __future__ import annotations

import asyncio
import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from .log import HeartbeatLogger, OutputLogger, to_iso8601, utc_now
from .models import ProcessInfo, ProcessStatus, RunRequest, RunResponse

ExitCallback = Callable[[ProcessInfo], Awaitable[None] | None]


@dataclass
class TrackedProcess:
    popen: subprocess.Popen[str]
    info: ProcessInfo
    output_path: Path
    stop_requested: bool = False
    timeout_task: asyncio.Task[None] | None = None
    output_thread: threading.Thread | None = None


class ProcessManager:
    def __init__(self, heartbeat_logger: HeartbeatLogger, output_logger: OutputLogger) -> None:
        self.heartbeat_logger = heartbeat_logger
        self.output_logger = output_logger
        self.processes: dict[int, TrackedProcess] = {}
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def start_process(
        self,
        request: RunRequest,
        *,
        restart_count: int = 0,
        on_exit: ExitCallback | None = None,
    ) -> RunResponse:
        self._loop = asyncio.get_running_loop()
        started_at = utc_now()
        output_path = self.output_logger.create_output_file(request.label, started_at)
        if isinstance(request.command, str):
            use_shell = True
            popen_args = request.command
            display_command = request.command
        else:
            use_shell = False
            popen_args = list(request.command)
            display_command = " ".join(popen_args)
        env = os.environ.copy()
        env.update(request.env)

        popen = subprocess.Popen(
            popen_args,
            cwd=request.cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=use_shell,
        )
        pid = popen.pid
        info = ProcessInfo(
            pid=pid,
            label=request.label,
            command=display_command,
            cwd=request.cwd,
            status=ProcessStatus.RUNNING,
            started_at=started_at,
            output_file=str(output_path),
            restart_count=restart_count,
        )
        handle = TrackedProcess(popen=popen, info=info, output_path=output_path)
        with self._lock:
            self.processes[pid] = handle

        self.heartbeat_logger.write_event(
            "PROCESS_STARTED",
            pid=pid,
            label=request.label,
            command=info.command,
            cwd=request.cwd,
            output_file=str(output_path),
            restart_count=restart_count,
        )

        output_thread = threading.Thread(target=self._stream_output, args=(handle,), daemon=True)
        handle.output_thread = output_thread
        output_thread.start()
        watcher = threading.Thread(target=self._wait_for_exit, args=(handle, on_exit), daemon=True)
        watcher.start()

        if request.timeout:
            handle.timeout_task = asyncio.create_task(self._enforce_timeout(pid, request.timeout))

        return RunResponse(pid=pid, label=request.label, started_at=started_at, output_file=str(output_path))

    async def stop_process(self, pid: int, *, grace_period: float = 1.0) -> ProcessInfo:
        handle = self._get_handle(pid)
        if handle.info.status != ProcessStatus.RUNNING:
            return handle.info

        handle.stop_requested = True
        handle.popen.terminate()
        try:
            await asyncio.to_thread(handle.popen.wait, grace_period)
        except subprocess.TimeoutExpired:
            handle.popen.kill()
            await asyncio.to_thread(handle.popen.wait)
        return handle.info

    async def stop_all(self, *, grace_period: float = 1.0) -> None:
        running = [pid for pid, handle in self.processes.items() if handle.info.status == ProcessStatus.RUNNING]
        for pid in running:
            await self.stop_process(pid, grace_period=grace_period)

    def list_processes(self, *, running_only: bool = False) -> list[ProcessInfo]:
        items = [handle.info for handle in self.processes.values()]
        if running_only:
            items = [info for info in items if info.status == ProcessStatus.RUNNING]
        return sorted(items, key=lambda info: info.started_at)

    def get_process(self, pid: int) -> ProcessInfo | None:
        handle = self.processes.get(pid)
        return handle.info if handle else None

    def get_output(self, pid: int, tail: int | None = None) -> dict[str, object]:
        handle = self._get_handle(pid)
        output_path = Path(handle.info.output_file or handle.output_path)
        lines = output_path.read_text(encoding="utf-8", errors="replace").splitlines()
        selected = lines[-tail:] if tail else lines
        return {
            "content": "\n".join(selected),
            "total_lines": len(lines),
            "file": str(output_path),
        }

    def _get_handle(self, pid: int) -> TrackedProcess:
        handle = self.processes.get(pid)
        if handle is None:
            raise KeyError(pid)
        return handle

    def _stream_output(self, handle: TrackedProcess) -> None:
        stdout = handle.popen.stdout
        if stdout is None:
            return
        with handle.output_path.open("a", encoding="utf-8") as output_file:
            for line in iter(stdout.readline, ""):
                output_file.write(line)
                output_file.flush()
        stdout.close()

    def _wait_for_exit(self, handle: TrackedProcess, on_exit: ExitCallback | None) -> None:
        exit_code = handle.popen.wait()
        if handle.output_thread is not None:
            handle.output_thread.join(timeout=5.0)
        exited_at = utc_now()
        duration = max((exited_at - handle.info.started_at).total_seconds(), 0.0)
        if handle.stop_requested:
            status = ProcessStatus.KILLED
        else:
            status = ProcessStatus.EXITED

        handle.info = handle.info.model_copy(
            update={
                "status": status,
                "exit_code": exit_code,
                "exited_at": exited_at,
            }
        )
        with self._lock:
            self.processes[handle.info.pid] = handle

        self.heartbeat_logger.write_event(
            "PROCESS_EXITED",
            pid=handle.info.pid,
            label=handle.info.label,
            exit_code=exit_code,
            duration_s=duration,
            output_file=handle.info.output_file,
            status=status.value,
            exited_at=to_iso8601(exited_at),
        )

        if handle.timeout_task is not None:
            handle.timeout_task.cancel()

        if on_exit and self._loop is not None and not self._loop.is_closed():
            result = on_exit(handle.info)
            if asyncio.iscoroutine(result):
                self._loop.call_soon_threadsafe(asyncio.create_task, result)

    async def _enforce_timeout(self, pid: int, timeout: float) -> None:
        try:
            await asyncio.sleep(timeout)
            handle = self.processes.get(pid)
            if handle and handle.info.status == ProcessStatus.RUNNING:
                await self.stop_process(pid)
        except asyncio.CancelledError:
            return
