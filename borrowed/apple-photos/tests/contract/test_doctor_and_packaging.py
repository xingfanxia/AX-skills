from __future__ import annotations

import json
import os
from pathlib import Path

from apple_photos_cli import cli
from apple_photos_cli.errors import EXIT_IO, ApplePhotosError


def _set_read_dependency_ready(monkeypatch) -> None:
    monkeypatch.setattr(cli.importlib.metadata, "version", lambda name: "0.76.1")


def test_doctor_read_capability_ignores_missing_helper(monkeypatch, capsys) -> None:
    _set_read_dependency_ready(monkeypatch)
    monkeypatch.delenv("APPLE_PHOTOS_HELPER", raising=False)

    assert cli.main(["doctor", "--capability", "read"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is True
    assert output["read_ready"] is True
    assert output["mutation_ready"] is None
    assert output["photokit_helper"]["live_probe_performed"] is False


def test_doctor_mutation_capability_fails_for_missing_helper(monkeypatch, capsys) -> None:
    _set_read_dependency_ready(monkeypatch)
    monkeypatch.delenv("APPLE_PHOTOS_HELPER", raising=False)

    assert cli.main(["doctor", "--capability", "mutation"]) == 6
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is False
    assert output["mutation_ready"] is False


def test_doctor_mutation_capability_fails_for_non_executable_helper(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    _set_read_dependency_ready(monkeypatch)
    helper = tmp_path / "PhotoKitHelper"
    helper.write_text("synthetic", encoding="utf-8")
    os.chmod(helper, 0o644)
    monkeypatch.setenv("APPLE_PHOTOS_HELPER", str(helper))

    assert cli.main(["doctor", "--capability", "mutation"]) == 6
    output = json.loads(capsys.readouterr().out)
    assert output["photokit_helper"]["exists"] is True
    assert output["photokit_helper"]["executable"] is False
    assert output["photokit_helper"]["live_probe_performed"] is False


def test_doctor_mutation_capability_fails_for_probe_error(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    _set_read_dependency_ready(monkeypatch)
    helper = tmp_path / "PhotoKitHelper"
    helper.write_text("synthetic", encoding="utf-8")
    os.chmod(helper, 0o755)
    monkeypatch.setenv("APPLE_PHOTOS_HELPER", str(helper))

    def fail_probe(self):
        raise ApplePhotosError("E_BACKEND_PROTOCOL", "Synthetic probe failure.", EXIT_IO)

    monkeypatch.setattr(cli.PhotoKitProcessBridge, "probe", fail_probe)
    assert cli.main(["doctor", "--capability", "mutation"]) == 6
    output = json.loads(capsys.readouterr().out)
    assert output["photokit_helper"]["live_probe_performed"] is True
    assert output["photokit_helper"]["probe"]["error"]["code"] == "E_BACKEND_PROTOCOL"


def test_doctor_all_requires_both_capabilities(
    monkeypatch, capsys, tmp_path: Path, fake_bridge
) -> None:
    _set_read_dependency_ready(monkeypatch)
    helper = tmp_path / "PhotoKitHelper"
    helper.write_text("synthetic", encoding="utf-8")
    os.chmod(helper, 0o755)
    monkeypatch.setenv("APPLE_PHOTOS_HELPER", str(helper))
    monkeypatch.setattr(cli.PhotoKitProcessBridge, "probe", lambda self: fake_bridge.probe())

    assert cli.main(["doctor", "--capability", "all"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["read_ready"] is True
    assert output["mutation_ready"] is True
    assert output["ok"] is True


def test_helper_source_command_finds_checkout(capsys) -> None:
    assert cli.main(["helper-source"]) == 0
    output = json.loads(capsys.readouterr().out)
    source = Path(output["helper_source"]["path"])
    assert output["helper_source"]["layout"] == "source_checkout"
    assert output["helper_source"]["build_argv"] == [
        "swift", "build", "-c", "release", "--package-path", str(source)
    ]
    assert "build_command" not in output["helper_source"]
    assert (source / "Package.swift").is_file()

    assert cli.main(["helper-source", "--format", "path"]) == 0
    assert Path(capsys.readouterr().out.strip()) == source
