# pyright: reportMissingImports=false
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from process_launcher.config import load_config, load_env_file


def test_load_valid_config(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    env_file = tmp_path / ".env"
    env_file.write_text("TOKEN=abc\n", encoding="utf-8")
    config_path = config_dir / "launcher.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "server": {"host": "127.0.0.1", "port": 8123},
                "logging": {"dir": "logs"},
                "services": {
                    "demo": {
                        "label": "demo",
                        "command": ["python", "-c", "print('hi')"],
                        "cwd": str(tmp_path),
                        "env_file": str(env_file),
                    }
                },
                "periodic_jobs": {
                    "daily": {
                        "label": "daily",
                        "command": ["python", "daily.py"],
                        "cwd": str(tmp_path),
                        "env_file": str(env_file),
                        "schedule": {"type": "daily", "time": "19:00", "timezone": "America/Los_Angeles"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.server.port == 8123
    assert config.services["demo"].label == "demo"
    assert config.services["demo"].env["TOKEN"] == "abc"
    assert config.periodic_jobs["daily"].env["TOKEN"] == "abc"
    assert config.periodic_jobs["daily"].schedule.time == "19:00"


def test_load_missing_config_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "missing.yaml")


def test_load_empty_services(tmp_path: Path) -> None:
    config_path = tmp_path / "launcher.yaml"
    config_path.write_text(yaml.safe_dump({"services": {}}), encoding="utf-8")

    config = load_config(config_path)

    assert config.services == {}


def test_default_values(tmp_path: Path) -> None:
    config_path = tmp_path / "launcher.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "services": {
                    "demo": {
                        "label": "demo",
                        "command": ["python", "-c", "print('ok')"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.server.port == 7997
    assert config.services["demo"].max_restarts == 3
    assert config.services["demo"].restart_delay == 10


def test_weekly_periodic_config(tmp_path: Path) -> None:
    config_path = tmp_path / "launcher.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "periodic_jobs": {
                    "weekly": {
                        "label": "weekly",
                        "command": "python weekly.py",
                        "schedule": {
                            "type": "weekly",
                            "days_of_week": ["thu"],
                            "time": "07:30",
                            "timezone": "America/Los_Angeles",
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.periodic_jobs["weekly"].schedule.days_of_week == ["thu"]


def test_env_file_loading(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n# comment\nexport BAZ=qux\n", encoding="utf-8")

    env = load_env_file(env_file)

    assert env == {"FOO": "bar", "BAZ": "qux"}
