from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
import yaml
from fastapi import FastAPI

from process_launcher.config import load_config
from process_launcher.models import PeriodicRun, PeriodicRunStatus
from process_launcher.server import create_app, initialize_app_state, shutdown_app_state


async def wait_for_process(client: httpx.AsyncClient, pid: int, status: str, timeout: float = 3.0) -> dict[str, Any]:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        response = await client.get(f"/processes/{pid}")
        if response.status_code == 200 and response.json()["status"] == status:
            return response.json()
        await asyncio.sleep(0.05)
    raise AssertionError(f"process {pid} did not reach {status}")


@pytest.mark.asyncio
async def test_health(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_run_command(client: httpx.AsyncClient) -> None:
    response = await client.post("/run", json={"command": [sys.executable, "-c", "print('hello')"]})
    assert response.status_code == 200
    assert response.json()["pid"] > 0
    assert response.json()["output_file"]


@pytest.mark.asyncio
async def test_run_command_with_label(client: httpx.AsyncClient) -> None:
    response = await client.post("/run", json={"command": [sys.executable, "-c", "print('hello')"], "label": "demo"})
    pid = response.json()["pid"]
    process = await wait_for_process(client, pid, "exited")
    assert process["label"] == "demo"


@pytest.mark.asyncio
async def test_run_command_with_timeout(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "import time; time.sleep(5)"], "timeout": 0.2},
    )
    pid = response.json()["pid"]
    process = await wait_for_process(client, pid, "killed")
    assert process["status"] == "killed"


@pytest.mark.asyncio
async def test_list_processes(client: httpx.AsyncClient) -> None:
    await client.post("/run", json={"command": [sys.executable, "-c", "print('one')"]})
    response = await client.get("/processes")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_list_processes_running_only(client: httpx.AsyncClient) -> None:
    await client.post("/run", json={"command": [sys.executable, "-c", "import time; time.sleep(1)"]})
    await client.post("/run", json={"command": [sys.executable, "-c", "print('done')"]})
    await asyncio.sleep(0.1)
    response = await client.get("/processes", params={"running_only": True})
    assert all(item["status"] == "running" for item in response.json())


@pytest.mark.asyncio
async def test_get_process_detail(client: httpx.AsyncClient) -> None:
    response = await client.post("/run", json={"command": [sys.executable, "-c", "print('hi')"]})
    pid = response.json()["pid"]
    detail = await client.get(f"/processes/{pid}")
    assert detail.status_code == 200
    assert detail.json()["pid"] == pid


@pytest.mark.asyncio
async def test_get_process_not_found(client: httpx.AsyncClient) -> None:
    response = await client.get("/processes/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stop_process(client: httpx.AsyncClient) -> None:
    response = await client.post("/run", json={"command": [sys.executable, "-c", "import time; time.sleep(5)"]})
    pid = response.json()["pid"]
    stopped = await client.post(f"/processes/{pid}/stop")
    assert stopped.status_code == 200
    process = await wait_for_process(client, pid, "killed")
    assert process["status"] == "killed"


@pytest.mark.asyncio
async def test_get_output(client: httpx.AsyncClient) -> None:
    response = await client.post("/run", json={"command": [sys.executable, "-c", "print('alpha')"]})
    pid = response.json()["pid"]
    await wait_for_process(client, pid, "exited")
    output = await client.get(f"/processes/{pid}/output")
    assert "alpha" in output.json()["content"]


@pytest.mark.asyncio
async def test_get_output_tail(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "print('1'); print('2'); print('3')"]},
    )
    pid = response.json()["pid"]
    await wait_for_process(client, pid, "exited")
    output = await client.get(f"/processes/{pid}/output", params={"tail": 2})
    assert output.json()["content"] == "2\n3"


@pytest.mark.asyncio
async def test_api_based_always_on_is_rejected(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "import time; time.sleep(5)"], "label": "demo", "always_on": True},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_services_endpoint_not_available(client: httpx.AsyncClient) -> None:
    response = await client.get("/services")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_restart_unknown_declared_service_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.post("/declared-services/missing/restart")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_openapi_spec(client: httpx.AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()


@pytest.mark.asyncio
async def test_list_scheduled_empty(client: httpx.AsyncClient) -> None:
    response = await client.get("/scheduled")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_periodic_empty(client: httpx.AsyncClient) -> None:
    response = await client.get("/periodic")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_periodic_write_endpoints_are_not_available(client: httpx.AsyncClient) -> None:
    assert (await client.post("/periodic/demo/run-now")).status_code == 404
    assert (await client.post("/periodic/demo/enable")).status_code == 404
    assert (await client.post("/periodic/demo/disable")).status_code == 404


@pytest.mark.asyncio
async def test_periodic_interval_job_records_run(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "launcher.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "logging": {"dir": "logs"},
                "storage": {"sqlite_path": "state/launcher.db"},
                "periodic_jobs": {
                    "fast_periodic": {
                        "label": "fast_periodic",
                        "command": [sys.executable, "-c", "print('periodic ok')"],
                        "schedule": {"type": "interval", "every_seconds": 0.1},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    config = load_config(config_path)
    application: FastAPI = create_app(config_path=config_path, config=config)
    await initialize_app_state(application, config, config_path)
    try:
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as local_client:
            periodic = await local_client.get("/periodic")
            assert periodic.status_code == 200
            assert periodic.json()[0]["label"] == "fast_periodic"

            deadline = asyncio.get_running_loop().time() + 3.0
            while asyncio.get_running_loop().time() < deadline:
                runs = await local_client.get("/periodic/fast_periodic/runs")
                completed = [run for run in runs.json() if run["status"] == "completed"]
                if completed:
                    detail = await local_client.get(f"/periodic/fast_periodic/runs/{completed[0]['id']}")
                    assert detail.status_code == 200
                    assert detail.json()["output_file"]
                    return
                await asyncio.sleep(0.05)
            raise AssertionError("periodic run did not complete")
    finally:
        await shutdown_app_state(application)


@pytest.mark.asyncio
async def test_reload_periodic_jobs_updates_future_declarations(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "launcher.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "logging": {"dir": "logs"},
                "storage": {"sqlite_path": "state/launcher.db"},
                "periodic_jobs": {
                    "reload_demo": {
                        "label": "reload_demo",
                        "command": [sys.executable, "-c", "print('old')"],
                        "timeout": 300,
                        "schedule": {"type": "daily", "time": "08:00", "timezone": "UTC"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    config = load_config(config_path)
    application: FastAPI = create_app(config_path=config_path, config=config)
    await initialize_app_state(application, config, config_path)
    try:
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as local_client:
            before = await local_client.get("/periodic/reload_demo")
            assert before.json()["declared"]["timeout"] == 300

            config_path.write_text(
                yaml.safe_dump(
                    {
                        "logging": {"dir": "logs"},
                        "storage": {"sqlite_path": "state/launcher.db"},
                        "periodic_jobs": {
                            "reload_demo": {
                                "label": "reload_demo",
                                "command": [sys.executable, "-c", "print('new')"],
                                "timeout": 600,
                                "schedule": {"type": "daily", "time": "08:00", "timezone": "UTC"},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            reload_response = await local_client.post("/periodic/reload")
            assert reload_response.status_code == 200
            assert reload_response.json()["changed"] == ["reload_demo"]

            after = await local_client.get("/periodic/reload_demo")
            assert after.json()["declared"]["timeout"] == 600
            assert after.json()["declared"]["command"][-1] == "print('new')"
    finally:
        await shutdown_app_state(application)


@pytest.mark.asyncio
async def test_reload_periodic_jobs_preserves_active_runs(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "launcher.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "logging": {"dir": "logs"},
                "storage": {"sqlite_path": "state/launcher.db"},
                "periodic_jobs": {
                    "active_demo": {
                        "label": "active_demo",
                        "command": [sys.executable, "-c", "print('scheduled')"],
                        "timeout": 300,
                        "schedule": {"type": "daily", "time": "08:00", "timezone": "UTC"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    config = load_config(config_path)
    application: FastAPI = create_app(config_path=config_path, config=config)
    await initialize_app_state(application, config, config_path)
    try:
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as local_client:
            run_response = await local_client.post(
                "/run",
                json={
                    "command": [sys.executable, "-c", "import time; time.sleep(2)"],
                    "label": "active_demo",
                    "timeout": 300,
                },
            )
            pid = run_response.json()["pid"]
            periodic_manager = application.state.periodic_manager
            active_run = periodic_manager.store.list_periodic_runs("active_demo")
            assert active_run == []

            # Simulate a periodic run already tracked by the manager; reload should
            # not clear it or stop the child process.
            tracked = PeriodicRun(
                label="active_demo",
                command=[sys.executable, "-c", "import time; time.sleep(2)"],
                timeout=300,
                scheduled_for=datetime.now(),
                status=PeriodicRunStatus.RUNNING,
                result_pid=pid,
            )
            periodic_manager._update_run(tracked)

            config_path.write_text(
                yaml.safe_dump(
                    {
                        "logging": {"dir": "logs"},
                        "storage": {"sqlite_path": "state/launcher.db"},
                        "periodic_jobs": {
                            "active_demo": {
                                "label": "active_demo",
                                "command": [sys.executable, "-c", "print('future')"],
                                "timeout": 600,
                                "schedule": {"type": "daily", "time": "08:00", "timezone": "UTC"},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            reload_response = await local_client.post("/periodic/reload")
            assert reload_response.status_code == 200

            state = await local_client.get("/periodic/active_demo")
            assert state.json()["declared"]["timeout"] == 600
            assert state.json()["runtime"]["active_pid"] == pid
            process = await local_client.get(f"/processes/{pid}")
            assert process.json()["status"] == "running"
    finally:
        await shutdown_app_state(application)


@pytest.mark.asyncio
async def test_reload_periodic_jobs_keeps_old_config_on_invalid_yaml(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "launcher.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "logging": {"dir": "logs"},
                "storage": {"sqlite_path": "state/launcher.db"},
                "periodic_jobs": {
                    "stable_demo": {
                        "label": "stable_demo",
                        "command": [sys.executable, "-c", "print('stable')"],
                        "timeout": 300,
                        "schedule": {"type": "daily", "time": "08:00", "timezone": "UTC"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    config = load_config(config_path)
    application: FastAPI = create_app(config_path=config_path, config=config)
    await initialize_app_state(application, config, config_path)
    try:
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as local_client:
            config_path.write_text("periodic_jobs: [", encoding="utf-8")

            reload_response = await local_client.post("/periodic/reload")
            assert reload_response.status_code == 400

            state = await local_client.get("/periodic/stable_demo")
            assert state.status_code == 200
            assert state.json()["declared"]["timeout"] == 300
    finally:
        await shutdown_app_state(application)


@pytest.mark.asyncio
async def test_scheduled_job_appears_while_pending(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "print('delayed')"], "label": "delayed_test", "delay_seconds": 5},
    )
    assert response.status_code == 200
    assert response.json()["pid"] == 0

    scheduled = await client.get("/scheduled")
    assert scheduled.status_code == 200
    jobs = scheduled.json()
    assert len(jobs) == 1
    assert jobs[0]["label"] == "delayed_test"
    assert jobs[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_cancel_scheduled_job(client: httpx.AsyncClient) -> None:
    await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "print('never')"], "label": "cancel_me", "delay_seconds": 60},
    )

    scheduled = await client.get("/scheduled")
    job_id = scheduled.json()[0]["id"]

    cancel = await client.post(f"/scheduled/{job_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    verify = await client.get("/scheduled")
    assert verify.json()[0]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_update_scheduled_job_run_at(client: httpx.AsyncClient) -> None:
    await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "print('updated')"], "label": "update_me", "delay_seconds": 60},
    )
    scheduled = await client.get("/scheduled")
    job = scheduled.json()[0]
    new_run_at = datetime.now() + timedelta(seconds=0.2)

    update = await client.patch(f"/scheduled/{job['id']}", json={"run_at": new_run_at.isoformat()})
    assert update.status_code == 200
    assert update.json()["status"] == "pending"
    assert update.json()["run_at"].startswith(new_run_at.isoformat(timespec="seconds"))

    deadline = asyncio.get_running_loop().time() + 3.0
    while asyncio.get_running_loop().time() < deadline:
        verify = await client.get("/scheduled")
        jobs = [j for j in verify.json() if j["label"] == "update_me"]
        if jobs and jobs[0]["status"] == "completed":
            assert jobs[0]["result_pid"] is not None and jobs[0]["result_pid"] > 0
            return
        await asyncio.sleep(0.05)
    raise AssertionError("updated scheduled job did not complete")


@pytest.mark.asyncio
async def test_update_scheduled_job_rejects_non_pending(client: httpx.AsyncClient) -> None:
    await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "print('done')"], "label": "finished", "delay_seconds": 0.1},
    )
    await asyncio.sleep(1.0)
    scheduled = await client.get("/scheduled")
    job = [j for j in scheduled.json() if j["label"] == "finished"][0]

    update = await client.patch(
        f"/scheduled/{job['id']}",
        json={"run_at": (datetime.now() + timedelta(seconds=10)).isoformat()},
    )
    assert update.status_code == 409


@pytest.mark.asyncio
async def test_update_nonexistent_scheduled_job_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.patch(
        "/scheduled/nonexistent_id",
        json={"run_at": (datetime.now() + timedelta(seconds=10)).isoformat()},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_already_completed_scheduled_job_returns_409(client: httpx.AsyncClient) -> None:
    await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "print('fast')"], "label": "fast_delay", "delay_seconds": 0.1},
    )
    await asyncio.sleep(1.0)

    scheduled = await client.get("/scheduled")
    jobs = [j for j in scheduled.json() if j["label"] == "fast_delay"]
    assert len(jobs) == 1
    assert jobs[0]["status"] == "completed"

    cancel = await client.post(f"/scheduled/{jobs[0]['id']}/cancel")
    assert cancel.status_code == 409


@pytest.mark.asyncio
async def test_cancel_nonexistent_scheduled_job(client: httpx.AsyncClient) -> None:
    response = await client.post("/scheduled/nonexistent_id/cancel")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_scheduled_job_completes_after_delay(client: httpx.AsyncClient) -> None:
    await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "print('done')"], "label": "completes", "delay_seconds": 0.2},
    )
    await asyncio.sleep(1.0)

    scheduled = await client.get("/scheduled")
    jobs = [j for j in scheduled.json() if j["label"] == "completes"]
    assert len(jobs) == 1
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["result_pid"] is not None and jobs[0]["result_pid"] > 0


@pytest.mark.asyncio
async def test_scheduled_job_fails_when_process_exits_nonzero(client: httpx.AsyncClient) -> None:
    await client.post(
        "/run",
        json={"command": [sys.executable, "-c", "import sys; sys.exit(7)"], "label": "fails", "delay_seconds": 0.1},
    )
    deadline = asyncio.get_running_loop().time() + 3.0
    while asyncio.get_running_loop().time() < deadline:
        scheduled = await client.get("/scheduled")
        jobs = [j for j in scheduled.json() if j["label"] == "fails"]
        if jobs and jobs[0]["status"] == "failed":
            assert "exit_code=7" in jobs[0]["last_error"]
            return
        await asyncio.sleep(0.05)
    raise AssertionError("scheduled job did not fail after process exit")
