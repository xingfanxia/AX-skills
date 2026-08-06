"""
Live integration test — starts a real launcher process on port 7976,
exercises the full API surface, then shuts it down and cleans up.

Not included in normal pytest runs. Run explicitly:

    python scripts/smoke_test.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:7976"
PROJECT_DIR = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
CONFIG_DIR = PROJECT_DIR / "smoke_test_config"
LOG_DIR = CONFIG_DIR / "logs"
LAUNCHER_PROC: subprocess.Popen[str] | None = None


def step(name: str) -> None:
    print(f"\n>>> {name}")


def check(name: str, condition: bool) -> None:
    status = "OK" if condition else "FAIL"
    print(f"    [{status}] {name}")
    if not condition:
        raise AssertionError(f"Failed: {name}")


def cleanup() -> None:
    global LAUNCHER_PROC
    if LAUNCHER_PROC is not None:
        try:
            httpx.post(f"{BASE_URL}/shutdown", timeout=3)
            LAUNCHER_PROC.wait(timeout=5)
        except Exception:
            LAUNCHER_PROC.kill()
            LAUNCHER_PROC.wait(timeout=3)
        LAUNCHER_PROC = None
    if CONFIG_DIR.exists():
        shutil.rmtree(CONFIG_DIR, ignore_errors=True)


def setup() -> None:
    global LAUNCHER_PROC
    cleanup()

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "launcher.yaml").write_text(
        "server:\n  host: 127.0.0.1\n  port: 7976\n"
        "logging:\n  dir: logs\n  heartbeat_retention_days: 30\n  output_retention_days: 30\n"
        "services: {}\n",
        encoding="utf-8",
    )

    cmd = [
        str(VENV_PYTHON), "-m", "process_launcher", "start",
        "--config", str(CONFIG_DIR / "launcher.yaml"),
    ]
    LAUNCHER_PROC = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    for _ in range(30):
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=1)
            if r.status_code == 200:
                return
        except (httpx.ConnectError, httpx.ConnectTimeout):
            pass
        time.sleep(0.3)
    raise RuntimeError("Launcher did not start within 10s")


def main() -> None:
    try:
        setup()

        step("1. Health check")
        r = httpx.get(f"{BASE_URL}/health", timeout=3)
        check("GET /health returns 200", r.status_code == 200)
        check("status is ok", r.json()["status"] == "ok")

        step("2. Run immediate command")
        r = httpx.post(
            f"{BASE_URL}/run",
            json={"command": ["echo", "hello from smoke test"], "label": "smoke_echo"},
            timeout=10,
        )
        check("POST /run returns 200", r.status_code == 200)
        body = r.json()
        pid = body["pid"]
        check("got a valid pid", pid > 0)
        check("label is smoke_echo", body["label"] == "smoke_echo")

        time.sleep(1)

        step("3. Verify process exited")
        r = httpx.get(f"{BASE_URL}/processes/{pid}", timeout=3)
        check("GET /processes/{{pid}} returns 200", r.status_code == 200)
        proc = r.json()
        check("status is exited", proc["status"] == "exited")
        check("exit_code is 0", proc["exit_code"] == 0)

        step("4. Verify output log")
        r = httpx.get(f"{BASE_URL}/processes/{pid}/output", timeout=3)
        check("GET /processes/{{pid}}/output returns 200", r.status_code == 200)
        check("output contains expected text", "hello from smoke test" in r.json()["content"])

        step("5. Verify output log file exists on disk")
        r = httpx.get(f"{BASE_URL}/logs/output", timeout=3)
        files = r.json()
        check("output log files listed", len(files) > 0)
        check("a file mentions smoke_echo", any("smoke_echo" in f.get("filename", "") for f in files))

        step("6. Submit delayed command (5s)")
        before = time.time()
        r = httpx.post(
            f"{BASE_URL}/run",
            json={
                "command": ["echo", "delayed hello"],
                "label": "smoke_delayed",
                "delay_seconds": 5,
            },
            timeout=10,
        )
        check("delayed run returns 200", r.status_code == 200)
        check("pid is 0 (not started yet)", r.json()["pid"] == 0)

        step("7. Wait for delayed command to complete")
        time.sleep(7)

        r = httpx.get(f"{BASE_URL}/processes", timeout=3)
        procs = r.json()
        delayed = [p for p in procs if p.get("label") == "smoke_delayed"]
        check("delayed process found", len(delayed) == 1)
        if delayed:
            check("delayed process exited", delayed[0]["status"] == "exited")
            check("delayed process exit_code 0", delayed[0]["exit_code"] == 0)

        step("8. Check heartbeat log")
        r = httpx.get(f"{BASE_URL}/logs/heartbeat?limit=20", timeout=3)
        events = r.json()
        check("heartbeat events exist", len(events) > 0)
        start_events = [e for e in events if e.get("event") == "PROCESS_STARTED"]
        check("has PROCESS_STARTED events", len(start_events) >= 2)
        exit_events = [e for e in events if e.get("event") == "PROCESS_EXITED"]
        check("has PROCESS_EXITED events", len(exit_events) >= 2)

        step("9. Shutdown")
        r = httpx.post(f"{BASE_URL}/shutdown", timeout=5)
        check("POST /shutdown returns 200", r.status_code == 200)

        print("\n✅ All smoke tests passed.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
