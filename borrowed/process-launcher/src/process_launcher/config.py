from __future__ import annotations

from pathlib import Path

import yaml

from .models import LauncherConfig, PeriodicJobConfig, ServiceConfig


def load_env_file(path: str | Path | None) -> dict[str, str]:
    if path is None:
        return {}

    env_path = Path(path)
    if not env_path.exists():
        raise FileNotFoundError(f"env file not found: {env_path}")

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _merge_service_envs(services: dict[str, ServiceConfig]) -> dict[str, ServiceConfig]:
    merged: dict[str, ServiceConfig] = {}
    for name, service in services.items():
        env_file_values = load_env_file(service.resolved_env_file()) if service.env_file else {}
        merged[name] = service.model_copy(update={"env": {**env_file_values, **service.env}})
    return merged


def _merge_periodic_envs(periodic_jobs: dict[str, PeriodicJobConfig]) -> dict[str, PeriodicJobConfig]:
    merged: dict[str, PeriodicJobConfig] = {}
    for name, job in periodic_jobs.items():
        env_file_values = load_env_file(job.resolved_env_file()) if job.env_file else {}
        merged[name] = job.model_copy(update={"env": {**env_file_values, **job.env}})
    return merged


def load_config(path: str | Path) -> LauncherConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")

    raw_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    config = LauncherConfig.model_validate(raw_data)
    services = _merge_service_envs(config.services)
    periodic_jobs = _merge_periodic_envs(config.periodic_jobs)
    return config.model_copy(update={"services": services, "periodic_jobs": periodic_jobs})
