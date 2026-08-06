from __future__ import annotations

import time

import pytest

pytestmark = pytest.mark.live_integration


def test_health(live_client):
    r = live_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_run_immediate_and_verify_output(live_client):
    r = live_client.post(
        "/run",
        json={"command": ["echo", "hello from live test"], "label": "live_echo"},
    )
    assert r.status_code == 200
    pid = r.json()["pid"]
    assert pid > 0

    time.sleep(1)

    r = live_client.get(f"/processes/{pid}")
    proc = r.json()
    assert proc["status"] == "exited"
    assert proc["exit_code"] == 0

    r = live_client.get(f"/processes/{pid}/output")
    assert "hello from live test" in r.json()["content"]


def test_delayed_run(live_client):
    r = live_client.post(
        "/run",
        json={
            "command": ["echo", "delayed hello"],
            "label": "live_delayed",
            "delay_seconds": 3,
        },
    )
    assert r.status_code == 200
    assert r.json()["pid"] == 0

    time.sleep(5)

    r = live_client.get("/processes")
    delayed = [p for p in r.json() if p.get("label") == "live_delayed"]
    assert len(delayed) == 1
    assert delayed[0]["status"] == "exited"
    assert delayed[0]["exit_code"] == 0


def test_heartbeat_and_output_logs(live_client):
    r = live_client.get("/logs/heartbeat?limit=20")
    events = r.json()
    assert len(events) > 0

    starts = [e for e in events if e.get("event") == "PROCESS_STARTED"]
    exits = [e for e in events if e.get("event") == "PROCESS_EXITED"]
    assert len(starts) >= 1
    assert len(exits) >= 1

    r = live_client.get("/logs/output")
    files = r.json()
    assert len(files) > 0
    assert any("live_echo" in f.get("filename", "") for f in files)


def test_services_endpoint_not_available(live_client):
    r = live_client.get("/services")
    assert r.status_code == 404


def test_declared_service_restart_not_found(live_client):
    r = live_client.post("/declared-services/missing/restart")
    assert r.status_code == 404


def test_process_not_found(live_client):
    r = live_client.get("/processes/999999")
    assert r.status_code == 404


def test_scheduled_list_and_cancel(live_client):
    r = live_client.post(
        "/run",
        json={
            "command": ["echo", "never runs"],
            "label": "live_scheduled_cancel",
            "delay_seconds": 300,
        },
    )
    assert r.status_code == 200

    r = live_client.get("/scheduled")
    jobs = [j for j in r.json() if j.get("label") == "live_scheduled_cancel"]
    assert len(jobs) == 1
    assert jobs[0]["status"] == "pending"

    job_id = jobs[0]["id"]
    r = live_client.post(f"/scheduled/{job_id}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    r = live_client.get("/scheduled")
    verify = [j for j in r.json() if j.get("id") == job_id]
    assert verify[0]["status"] == "cancelled"


def test_scheduled_completes_after_delay(live_client):
    r = live_client.post(
        "/run",
        json={
            "command": ["echo", "scheduled done"],
            "label": "live_scheduled_done",
            "delay_seconds": 2,
        },
    )
    assert r.status_code == 200

    r = live_client.get("/scheduled")
    jobs = [j for j in r.json() if j.get("label") == "live_scheduled_done"]
    assert len(jobs) == 1
    assert jobs[0]["status"] == "pending"

    time.sleep(4)

    r = live_client.get("/scheduled")
    jobs = [j for j in r.json() if j.get("label") == "live_scheduled_done"]
    assert len(jobs) == 1
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["result_pid"] is not None and jobs[0]["result_pid"] > 0
