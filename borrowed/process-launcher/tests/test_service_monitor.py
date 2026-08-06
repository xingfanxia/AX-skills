# pyright: reportMissingImports=false
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from process_launcher.log import HeartbeatLogger, OutputLogger
from process_launcher.models import ProcessStatus, ServiceConfig
from process_launcher.process import ProcessManager
from process_launcher.service_monitor import ServiceMonitor


async def wait_for_service_status(monitor: ServiceMonitor, label: str, status: str, timeout: float = 3.0) -> dict[str, object]:
    import asyncio

    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        for service in monitor.list_services():
            if service["label"] == label and service["status"] == status:
                return service
        await asyncio.sleep(0.05)
    raise AssertionError(f"service {label} did not reach {status}")


async def wait_for_restart_count(
    monitor: ServiceMonitor,
    label: str,
    restart_count: int,
    *,
    status: str | None = None,
    timeout: float = 3.0,
) -> dict[str, object]:
    import asyncio

    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        for service in monitor.list_services():
            if service["label"] != label:
                continue
            if service["restart_count"] != restart_count:
                continue
            if status is not None and service["status"] != status:
                continue
            return service
        await asyncio.sleep(0.05)
    raise AssertionError(f"service {label} did not reach restart_count={restart_count}")


@pytest.fixture
def service_stack(tmp_path: Path) -> tuple[ProcessManager, ServiceMonitor]:
    heartbeat = HeartbeatLogger(tmp_path / "logs")
    output = OutputLogger(tmp_path / "logs")
    manager = ProcessManager(heartbeat, output)
    monitor = ServiceMonitor(manager, heartbeat)
    return manager, monitor


@pytest.mark.asyncio
async def test_service_starts_on_launch(service_stack: tuple[ProcessManager, ServiceMonitor]) -> None:
    manager, monitor = service_stack
    monitor.register_services(
        {"demo": ServiceConfig(label="demo", command=[sys.executable, "-c", "import time; time.sleep(1)"], restart_delay=0.1)}
    )
    await monitor.start_registered_services()
    service = await wait_for_service_status(monitor, "demo", "running")
    assert service["pid"] is not None
    await monitor.shutdown()
    await manager.stop_all()


@pytest.mark.asyncio
async def test_service_restart_on_exit(service_stack: tuple[ProcessManager, ServiceMonitor]) -> None:
    manager, monitor = service_stack
    monitor.register_services(
        {
            "demo": ServiceConfig(
                label="demo",
                command=[sys.executable, "-c", "import sys, time; time.sleep(0.05); sys.exit(1)"],
                restart_delay=0.1,
                max_restarts=10,
            )
        }
    )
    await monitor.start_registered_services()
    service = await wait_for_service_status(monitor, "demo", "running", timeout=2.0)
    first_pid = service["pid"]
    service = await wait_for_restart_count(monitor, "demo", 1, status="running", timeout=2.0)
    assert service["pid"] != first_pid
    await monitor.shutdown()
    await manager.stop_all()


@pytest.mark.asyncio
async def test_circuit_breaker_after_max_restarts(service_stack: tuple[ProcessManager, ServiceMonitor]) -> None:
    manager, monitor = service_stack
    monitor.register_services(
        {
            "demo": ServiceConfig(
                label="demo",
                command=[sys.executable, "-c", "import sys; sys.exit(1)"],
                restart_delay=0.05,
                max_restarts=2,
                restart_window=5,
            )
        }
    )
    await monitor.start_registered_services()
    service = await wait_for_service_status(monitor, "demo", "circuit_breaker", timeout=2.0)
    assert service["restart_count"] == 2
    await monitor.shutdown()
    await manager.stop_all()


@pytest.mark.asyncio
async def test_circuit_breaker_respects_window(service_stack: tuple[ProcessManager, ServiceMonitor]) -> None:
    manager, monitor = service_stack
    monitor.register_services(
        {
            "demo": ServiceConfig(
                label="demo",
                command=[sys.executable, "-c", "import sys; sys.exit(1)"],
                restart_delay=0.2,
                max_restarts=2,
                restart_window=0.05,
            )
        }
    )
    await monitor.start_registered_services()
    service = await wait_for_restart_count(monitor, "demo", 1, status="running", timeout=2.0)
    assert service["restart_count"] == 1
    await monitor.shutdown()
    await manager.stop_all()


@pytest.mark.asyncio
async def test_manual_restart(service_stack: tuple[ProcessManager, ServiceMonitor]) -> None:
    manager, monitor = service_stack
    monitor.register_services(
        {"demo": ServiceConfig(label="demo", command=[sys.executable, "-c", "import time; time.sleep(2)"], restart_delay=0.1)}
    )
    await monitor.start_registered_services()
    service = await wait_for_service_status(monitor, "demo", "running")
    first_pid = service["pid"]
    restarted = await monitor.restart_service("demo")
    assert restarted.pid != first_pid
    await monitor.shutdown()
    await manager.stop_all()


@pytest.mark.asyncio
async def test_reset_circuit_breaker(service_stack: tuple[ProcessManager, ServiceMonitor]) -> None:
    manager, monitor = service_stack
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
    await wait_for_service_status(monitor, "demo", "circuit_breaker", timeout=2.0)
    reset = await monitor.reset_circuit_breaker("demo")
    assert reset.label == "demo"
    await monitor.shutdown()
    await manager.stop_all()


@pytest.mark.asyncio
async def test_restart_delay(service_stack: tuple[ProcessManager, ServiceMonitor]) -> None:
    manager, monitor = service_stack
    monitor.register_services(
        {
            "demo": ServiceConfig(
                label="demo",
                command=[sys.executable, "-c", "import sys; sys.exit(1)"],
                restart_delay=0.3,
                max_restarts=3,
            )
        }
    )
    await monitor.start_registered_services()
    import asyncio

    await asyncio.sleep(0.1)
    service = next(item for item in monitor.list_services() if item["label"] == "demo")
    assert service["status"] == ProcessStatus.EXITED.value
    await monitor.shutdown()
    await manager.stop_all()
