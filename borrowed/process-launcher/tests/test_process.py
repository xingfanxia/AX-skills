# pyright: reportMissingImports=false
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, cast

import pytest

from process_launcher.log import HeartbeatLogger, OutputLogger
from process_launcher.models import ProcessStatus, RunRequest
from process_launcher.process import ProcessManager


async def wait_for_status(manager: ProcessManager, pid: int, status: ProcessStatus, timeout: float = 3.0) -> None:
    import asyncio

    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        process = manager.get_process(pid)
        if process and process.status == status:
            return
        await asyncio.sleep(0.05)
    raise AssertionError(f"process {pid} did not reach {status}")


@pytest.fixture
def process_manager(tmp_path: Path) -> ProcessManager:
    heartbeat = HeartbeatLogger(tmp_path / "logs")
    output = OutputLogger(tmp_path / "logs")
    return ProcessManager(heartbeat, output)


@pytest.mark.asyncio
async def test_start_process(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(RunRequest(command=[sys.executable, "-c", "import time; time.sleep(0.3)"]))
    process = process_manager.get_process(response.pid)
    assert process is not None
    assert process.status == ProcessStatus.RUNNING
    await process_manager.stop_all()


@pytest.mark.asyncio
async def test_start_process_with_cwd(process_manager: ProcessManager, tmp_path: Path) -> None:
    response = await process_manager.start_process(
        RunRequest(command=[sys.executable, "-c", "import pathlib; print(pathlib.Path.cwd())"], cwd=str(tmp_path))
    )
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    output = cast(dict[str, Any], process_manager.get_output(response.pid))
    assert str(tmp_path) in str(output["content"])


@pytest.mark.asyncio
async def test_start_process_with_env(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(
        RunRequest(
            command=[sys.executable, "-c", "import os; print(os.environ['DEMO_TOKEN'])"],
            env={"DEMO_TOKEN": "secret"},
        )
    )
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    output = cast(dict[str, Any], process_manager.get_output(response.pid))
    assert "secret" in str(output["content"])


@pytest.mark.asyncio
async def test_process_exits_normally(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(RunRequest(command=[sys.executable, "-c", "print('hello')"]))
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    process = process_manager.get_process(response.pid)
    assert process is not None
    assert process.exit_code == 0


@pytest.mark.asyncio
async def test_process_exits_with_error(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(RunRequest(command=[sys.executable, "-c", "import sys; sys.exit(1)"]))
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    process = process_manager.get_process(response.pid)
    assert process is not None
    assert process.exit_code == 1


@pytest.mark.asyncio
async def test_stop_process(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(RunRequest(command=[sys.executable, "-c", "import time; time.sleep(5)"]))
    await process_manager.stop_process(response.pid)
    await wait_for_status(process_manager, response.pid, ProcessStatus.KILLED)


@pytest.mark.asyncio
async def test_output_captured(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(RunRequest(command=[sys.executable, "-c", "print('hello')"], label="hello"))
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    output = cast(dict[str, Any], process_manager.get_output(response.pid))
    assert "hello" in str(output["content"])


@pytest.mark.asyncio
async def test_stderr_captured(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(
        RunRequest(command=[sys.executable, "-c", "import sys; sys.stderr.write('err\\n')"], label="stderr")
    )
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    output = cast(dict[str, Any], process_manager.get_output(response.pid))
    assert "err" in str(output["content"])


@pytest.mark.asyncio
async def test_zombie_reaped(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(RunRequest(command=[sys.executable, "-c", "pass"]))
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    with pytest.raises(ChildProcessError):
        os.waitpid(response.pid, os.WNOHANG)


@pytest.mark.asyncio
async def test_string_command_uses_shell(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(
        RunRequest(command="echo hello | tr a-z A-Z", label="shell_test")
    )
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    output = cast(dict[str, Any], process_manager.get_output(response.pid))
    assert "HELLO" in str(output["content"])


@pytest.mark.asyncio
async def test_string_command_supports_chain(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(
        RunRequest(command="echo first && echo second", label="chain_test")
    )
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    output = cast(dict[str, Any], process_manager.get_output(response.pid))
    assert "first" in str(output["content"])
    assert "second" in str(output["content"])


@pytest.mark.asyncio
async def test_array_command_no_shell(process_manager: ProcessManager) -> None:
    response = await process_manager.start_process(
        RunRequest(command=[sys.executable, "-c", "print('direct')"], label="array_test")
    )
    await wait_for_status(process_manager, response.pid, ProcessStatus.EXITED)
    output = cast(dict[str, Any], process_manager.get_output(response.pid))
    assert "direct" in str(output["content"])


@pytest.mark.asyncio
async def test_concurrent_processes(process_manager: ProcessManager) -> None:
    first = await process_manager.start_process(RunRequest(command=[sys.executable, "-c", "import time; time.sleep(0.2)"]))
    second = await process_manager.start_process(RunRequest(command=[sys.executable, "-c", "import time; time.sleep(0.2)"]))
    await wait_for_status(process_manager, first.pid, ProcessStatus.EXITED)
    await wait_for_status(process_manager, second.pid, ProcessStatus.EXITED)
    assert len(process_manager.list_processes()) == 2
