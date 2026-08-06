# pyright: reportMissingImports=false
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import cast

import pytest

from process_launcher.log import HeartbeatLogger, OutputLogger
from process_launcher.models import ProcessStatus, RunRequest, ServiceConfig
from process_launcher.process import ProcessManager
from process_launcher.service_monitor import ServiceMonitor


async def wait_for_exit(manager: ProcessManager, pid: int, timeout: float = 3.0) -> None:
    import asyncio

    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        process = manager.get_process(pid)
        if process and process.status != ProcessStatus.RUNNING:
            return
        await asyncio.sleep(0.05)
    raise AssertionError("process did not exit")


@pytest.mark.asyncio
async def test_heartbeat_written_on_start(tmp_path: Path) -> None:
    heartbeat = HeartbeatLogger(tmp_path / "logs")
    output = OutputLogger(tmp_path / "logs")
    manager = ProcessManager(heartbeat, output)
    response = await manager.start_process(RunRequest(command=[sys.executable, "-c", "import time; time.sleep(0.2)"], label="demo"))
    events = heartbeat.read_events(limit=10)
    assert any(event["event"] == "PROCESS_STARTED" and event["pid"] == response.pid for event in events)
    await manager.stop_all()


@pytest.mark.asyncio
async def test_heartbeat_written_on_exit(tmp_path: Path) -> None:
    heartbeat = HeartbeatLogger(tmp_path / "logs")
    output = OutputLogger(tmp_path / "logs")
    manager = ProcessManager(heartbeat, output)
    response = await manager.start_process(RunRequest(command=[sys.executable, "-c", "print('done')"], label="demo"))
    await wait_for_exit(manager, response.pid)
    events = heartbeat.read_events(limit=10, event="PROCESS_EXITED")
    assert any(event["pid"] == response.pid and event["exit_code"] == 0 for event in events)


@pytest.mark.asyncio
async def test_heartbeat_written_on_circuit_breaker(tmp_path: Path) -> None:
    heartbeat = HeartbeatLogger(tmp_path / "logs")
    output = OutputLogger(tmp_path / "logs")
    manager = ProcessManager(heartbeat, output)
    monitor = ServiceMonitor(manager, heartbeat)
    monitor.register_services(
        {
            "demo": ServiceConfig(
                label="demo",
                command=[sys.executable, "-c", "import sys; sys.exit(1)"],
                restart_delay=0.05,
                max_restarts=1,
            )
        }
    )
    await monitor.start_registered_services()
    import asyncio

    await asyncio.sleep(0.2)
    events = heartbeat.read_events(limit=20, event="CIRCUIT_BREAKER")
    assert any(event["label"] == "demo" for event in events)
    await monitor.shutdown()


def test_heartbeat_daily_rotation(tmp_path: Path) -> None:
    heartbeat = HeartbeatLogger(tmp_path / "logs")
    heartbeat.write_event("PROCESS_STARTED", pid=1)
    files = list((tmp_path / "logs").glob("heartbeat_*.jsonl"))
    assert len(files) == 1


def test_heartbeat_cleanup_old_files(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    old_file = log_dir / "heartbeat_2000-01-01.jsonl"
    old_file.write_text("{}\n", encoding="utf-8")
    old_time = time.time() - 40 * 24 * 3600
    os.utime(old_file, (old_time, old_time))
    HeartbeatLogger(log_dir, retention_days=30)
    assert not old_file.exists()


@pytest.mark.asyncio
async def test_output_file_created(tmp_path: Path) -> None:
    heartbeat = HeartbeatLogger(tmp_path / "logs")
    output = OutputLogger(tmp_path / "logs")
    manager = ProcessManager(heartbeat, output)
    response = await manager.start_process(RunRequest(command=[sys.executable, "-c", "print('hello')"], label="demo"))
    await wait_for_exit(manager, response.pid)
    output_file = cast(str, response.output_file)
    assert Path(output_file).exists()


@pytest.mark.asyncio
async def test_output_file_content(tmp_path: Path) -> None:
    heartbeat = HeartbeatLogger(tmp_path / "logs")
    output = OutputLogger(tmp_path / "logs")
    manager = ProcessManager(heartbeat, output)
    response = await manager.start_process(
        RunRequest(command=[sys.executable, "-c", "import sys; print('out'); sys.stderr.write('err\\n')"], label="demo")
    )
    await wait_for_exit(manager, response.pid)
    output_file = cast(str, response.output_file)
    content = Path(output_file).read_text(encoding="utf-8")
    assert "out" in content
    assert "err" in content


def test_output_cleanup_old_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "logs" / "output"
    output_dir.mkdir(parents=True)
    old_file = output_dir / "old.log"
    old_file.write_text("old", encoding="utf-8")
    old_time = time.time() - 40 * 24 * 3600
    os.utime(old_file, (old_time, old_time))
    OutputLogger(tmp_path / "logs", retention_days=30)
    assert not old_file.exists()
