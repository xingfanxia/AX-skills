from __future__ import annotations

import asyncio
import sys
from typing import Any, cast

import httpx
import pytest


async def run_and_wait(client: httpx.AsyncClient, label: str) -> int:
    response = await client.post("/run", json={"command": [sys.executable, "-c", f"print('{label}')"], "label": label})
    pid = response.json()["pid"]
    deadline = asyncio.get_running_loop().time() + 3.0
    while asyncio.get_running_loop().time() < deadline:
        detail = await client.get(f"/processes/{pid}")
        if detail.json()["status"] == "exited":
            return pid
        await asyncio.sleep(0.05)
    raise AssertionError("process did not exit")


@pytest.mark.asyncio
async def test_get_heartbeat(client: httpx.AsyncClient) -> None:
    _ = await run_and_wait(client, "hb")
    response = await client.get("/logs/heartbeat")
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_get_heartbeat_filter_by_event(client: httpx.AsyncClient) -> None:
    _ = await run_and_wait(client, "event")
    response = await client.get("/logs/heartbeat", params={"event": "PROCESS_EXITED"})
    assert all(item["event"] == "PROCESS_EXITED" for item in response.json())


@pytest.mark.asyncio
async def test_get_heartbeat_filter_by_label(client: httpx.AsyncClient) -> None:
    _ = await run_and_wait(client, "focus")
    response = await client.get("/logs/heartbeat", params={"label": "focus"})
    assert response.json()
    assert all(item.get("label") == "focus" for item in response.json())


@pytest.mark.asyncio
async def test_get_heartbeat_limit(client: httpx.AsyncClient) -> None:
    _ = await run_and_wait(client, "one")
    _ = await run_and_wait(client, "two")
    response = await client.get("/logs/heartbeat", params={"limit": 1})
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_output_logs(client: httpx.AsyncClient) -> None:
    _ = await run_and_wait(client, "logs")
    response = await client.get("/logs/output")
    assert response.status_code == 200
    assert response.json()


@pytest.mark.asyncio
async def test_read_output_log(client: httpx.AsyncClient) -> None:
    _ = await run_and_wait(client, "readme")
    logs_response = await client.get("/logs/output")
    items = cast(list[dict[str, Any]], logs_response.json())
    filename = cast(str, items[0]["filename"])
    response = await client.get(f"/logs/output/{filename}")
    assert response.status_code == 200
    assert response.json()["filename"] == filename
