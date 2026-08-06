# pyright: reportMissingImports=false
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
import yaml
from fastapi import FastAPI

from process_launcher.config import load_config
from process_launcher.server import create_app, initialize_app_state, shutdown_app_state

PROJECT_DIR = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
LIVE_PORT = 7976
BASE_URL = f"http://127.0.0.1:{LIVE_PORT}"
_launcher_proc: subprocess.Popen[str] | None = None


@pytest.fixture
def tmp_log_dir(tmp_path: Path) -> Path:
    path = tmp_path / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def tmp_config_dir(tmp_path: Path, tmp_log_dir: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "launcher.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "server": {"host": "127.0.0.1", "port": 7997},
                "logging": {
                    "dir": str(tmp_log_dir.relative_to(tmp_path)),
                    "heartbeat_retention_days": 30,
                    "output_retention_days": 30,
                },
                "services": {},
            }
        ),
        encoding="utf-8",
    )
    return config_dir


@pytest_asyncio.fixture
async def app(tmp_config_dir: Path):
    config_path = tmp_config_dir / "launcher.yaml"
    config = load_config(config_path)
    application: FastAPI = create_app(config_path=config_path, config=config)
    await initialize_app_state(application, config, config_path)
    try:
        yield application
    finally:
        await shutdown_app_state(application)


@pytest_asyncio.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


def _is_port_free() -> bool:
    try:
        httpx.get(f"{BASE_URL}/health", timeout=1)
        return False
    except (httpx.ConnectError, httpx.ConnectTimeout):
        return True


@pytest.fixture(scope="session")
def live_launcher(tmp_path_factory):
    global _launcher_proc
    if not _is_port_free():
        pytest.skip(f"Port {LIVE_PORT} is already in use, skipping live integration tests")

    config_dir = tmp_path_factory.mktemp("smoke_config")
    (config_dir / "logs").mkdir()
    (config_dir / "launcher.yaml").write_text(
        f"server:\n  host: 127.0.0.1\n  port: {LIVE_PORT}\n"
        "logging:\n  dir: logs\n  heartbeat_retention_days: 30\n  output_retention_days: 30\n"
        "services: {}\n",
    )

    _launcher_proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "process_launcher", "start", "--config", str(config_dir / "launcher.yaml")],
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    for _ in range(30):
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=1)
            if r.status_code == 200:
                yield BASE_URL
                break
        except (httpx.ConnectError, httpx.ConnectTimeout):
            pass
        time.sleep(0.3)
    else:
        _launcher_proc.kill()
        _launcher_proc.wait(timeout=3)
        _launcher_proc = None
        pytest.skip(f"Launcher failed to start on port {LIVE_PORT}")

    try:
        httpx.post(f"{BASE_URL}/shutdown", timeout=3)
        _launcher_proc.wait(timeout=5)
    except Exception:
        _launcher_proc.kill()
        _launcher_proc.wait(timeout=3)
    finally:
        _launcher_proc = None
        shutil.rmtree(config_dir, ignore_errors=True)


@pytest.fixture
def live_client(live_launcher):
    with httpx.Client(base_url=live_launcher, timeout=30) as c:
        yield c
