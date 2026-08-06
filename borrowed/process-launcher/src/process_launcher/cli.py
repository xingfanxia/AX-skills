from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import httpx
import uvicorn

from .config import load_config
from .server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(prog="launcher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    default_config = Path("config") / "launcher.yaml"

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--config", default=str(default_config))

    stop_parser = subparsers.add_parser("stop")
    stop_parser.add_argument("--url", default=None)
    stop_parser.add_argument("--config", default=str(default_config))

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--url", default=None)
    status_parser.add_argument("--config", default=str(default_config))

    args = parser.parse_args()
    if args.command == "start":
        start(args.config)
    elif args.command == "stop":
        asyncio.run(stop(args.url, args.config))
    elif args.command == "status":
        asyncio.run(status(args.url, args.config))


def start(config_path: str) -> None:
    config = load_config(config_path)
    app = create_app(config_path=config_path, config=config)
    uvicorn.run(app, host=config.server.host, port=config.server.port)


async def stop(url: str | None, config_path: str) -> None:
    base_url = url or _base_url_from_config(config_path)
    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        response = await client.post("/shutdown")
        response.raise_for_status()
        print(response.text)


async def status(url: str | None, config_path: str) -> None:
    base_url = url or _base_url_from_config(config_path)
    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        processes = await client.get("/processes")
        processes.raise_for_status()
        print(json.dumps({"processes": processes.json()}, indent=2))


def _base_url_from_config(config_path: str) -> str:
    config = load_config(config_path)
    return f"http://{config.server.host}:{config.server.port}"


if __name__ == "__main__":
    main()
