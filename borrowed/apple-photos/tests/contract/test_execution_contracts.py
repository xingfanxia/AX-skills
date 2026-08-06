from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from conftest import FIXED_TIME, write_pixel_report

from apple_photos_cli import cli
from apple_photos_cli.authorization import AuthorizationService
from apple_photos_cli.errors import ApplePhotosError


class TTY(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_retrieve_returns_terminal_record_for_every_requested_id(app, tmp_path: Path) -> None:
    records = app.retrieve(["missing-a", "missing-b"], output=tmp_path / "output")

    assert [record["asset_id"]["value"] for record in records] == [
        "missing-a",
        "missing-b",
    ]
    assert {record["status"] for record in records} == {"not_found_or_no_resources"}


@pytest.mark.parametrize("run_id", ["../private", "/tmp/private", "run_ok/../../private"])
def test_status_rejects_path_traversal(app, run_id: str) -> None:
    with pytest.raises(ApplePhotosError) as captured:
        app.status(run_id)
    assert captured.value.code == "E_SCHEMA_INVALID"


def test_cli_delete_without_apply_is_json_usage_error(
    app, fake_bridge, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(cli, "_application", lambda args, reader: app)
    exit_code = cli.main(
        [
            "delete",
            "apply",
            "--manifest",
            "missing.json",
            "--authorization-token",
            "missing.token",
        ]
    )

    error = json.loads(capsys.readouterr().err)
    assert exit_code == 2
    assert error["status"] == "failed"
    assert error["command"] == "delete"
    assert "delete-assets" not in fake_bridge.calls


def test_argparse_failure_is_json(capsys) -> None:
    with pytest.raises(SystemExit) as captured:
        cli.main(["delete", "apply"])

    error = json.loads(capsys.readouterr().err)
    assert captured.value.code == 2
    assert error["command"] == "argument.parse"
    assert error["errors"][0]["code"] == "E_USAGE"


def test_cli_delete_success_outputs_receipt(
    app, fake_bridge, tmp_path: Path, monkeypatch, capsys
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["delete-id"])
    manifest = app.plan_delete(report, pairs, output=manifest_path)
    token_path = tmp_path / "delete.token"
    service = AuthorizationService(
        app.state_dir,
        now=lambda: FIXED_TIME,
        random_bytes=lambda length: b"z" * length,
    )
    service.issue(
        manifest,
        stdin=TTY(service.required_phrase(manifest) + "\n"),
        stderr=TTY(),
        output=token_path,
    )
    monkeypatch.setattr(cli, "_application", lambda args, reader: app)

    exit_code = cli.main(
        [
            "delete",
            "apply",
            "--manifest",
            str(manifest_path),
            "--authorization-token",
            str(token_path),
            "--apply",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["status"] == "succeeded"
    assert output["phase"] == "verified"


def test_cli_delete_plan_authorize_apply_complete_chain(
    app, fake_bridge, tmp_path: Path, monkeypatch, capsys
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    token_path = tmp_path / "delete.token"
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["delete-id"])
    monkeypatch.setattr(cli, "_application", lambda args, reader: app)

    assert cli.main(
        [
            "delete",
            "plan",
            "--evidence-report",
            str(report),
            "--pair-manifest",
            str(pairs),
            "--output",
            str(manifest_path),
        ]
    ) == 0
    plan_output = json.loads(capsys.readouterr().out)
    assert plan_output["status"] == "planned"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    phrase = AuthorizationService.required_phrase(manifest)
    prompt = TTY()

    assert cli.main(
        [
            "delete",
            "authorize",
            "--manifest",
            str(manifest_path),
            "--output",
            str(token_path),
        ],
        stdin=TTY(phrase + "\n"),
        stderr=prompt,
    ) == 0
    authorize_output = json.loads(capsys.readouterr().out)
    assert authorize_output["status"] == "authorized"
    assert "Type exactly" in prompt.getvalue()

    assert cli.main(
        [
            "delete",
            "apply",
            "--manifest",
            str(manifest_path),
            "--authorization-token",
            str(token_path),
            "--apply",
        ]
    ) == 0
    apply_output = json.loads(capsys.readouterr().out)
    assert apply_output["status"] == "succeeded"
    assert "delete-assets" in fake_bridge.calls


def test_cli_authorize_rejects_non_tty_and_wrong_phrase(
    app, fake_bridge, tmp_path: Path, monkeypatch, capsys
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["delete-id"])
    app.plan_delete(report, pairs, output=manifest_path)
    monkeypatch.setattr(cli, "_application", lambda args, reader: app)
    argv = [
        "delete",
        "authorize",
        "--manifest",
        str(manifest_path),
        "--output",
        str(tmp_path / "delete.token"),
    ]

    non_tty_error = io.StringIO()
    assert cli.main(argv, stdin=io.StringIO(), stderr=non_tty_error) == 4
    assert json.loads(non_tty_error.getvalue())["errors"][0]["code"] == "E_AUTH_REQUIRED"
    assert capsys.readouterr().out == ""

    wrong_phrase_error = TTY()
    assert cli.main(argv, stdin=TTY("WRONG\n"), stderr=wrong_phrase_error) == 4
    error = json.loads(wrong_phrase_error.getvalue().splitlines()[-1])
    assert error["errors"][0]["code"] == "E_AUTH_REQUIRED"
    assert not (tmp_path / "delete.token").exists()


def test_cli_wrong_delete_token_is_auth_error_without_mutation(
    app, fake_bridge, tmp_path: Path, monkeypatch, capsys
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["delete-id"])
    manifest = app.plan_delete(report, pairs, output=manifest_path)
    token_path = tmp_path / "delete.token"
    service = AuthorizationService(app.state_dir)
    service.issue(
        manifest,
        stdin=TTY(service.required_phrase(manifest) + "\n"),
        stderr=TTY(),
        output=token_path,
    )
    token = json.loads(token_path.read_text(encoding="utf-8"))
    token["signature"] = "AAAA"
    token_path.write_text(json.dumps(token), encoding="utf-8")
    monkeypatch.setattr(cli, "_application", lambda args, reader: app)

    assert cli.main(
        [
            "delete",
            "apply",
            "--manifest",
            str(manifest_path),
            "--authorization-token",
            str(token_path),
            "--apply",
        ]
    ) == 4
    error = json.loads(capsys.readouterr().err)
    assert error["errors"][0]["code"] == "E_AUTH_INVALID"
    assert "delete-assets" not in fake_bridge.calls


def test_cli_import_partial_returns_exit_8(
    app, fake_bridge, tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"source")
    manifest_path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=manifest_path)
    fake_bridge.force_bad_import_digest = True
    monkeypatch.setattr(cli, "_application", lambda args, reader: app)

    assert cli.main(
        ["import", "apply", "--manifest", str(manifest_path), "--apply"]
    ) == 8
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["status"] == "partial"
    assert captured.err == ""


def test_cli_interrupt_after_dispatch_returns_unknown_and_status_receipt(
    app, fake_bridge, tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"source")
    manifest_path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=manifest_path)

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(fake_bridge, "import_assets", interrupt)
    monkeypatch.setattr(cli, "_application", lambda args, reader: app)
    assert cli.main(
        ["import", "apply", "--manifest", str(manifest_path), "--apply"]
    ) == 8
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["status"] == "outcome_unknown"
    assert output["errors"][0]["exception_type"] == "KeyboardInterrupt"
    assert captured.err == ""

    assert cli.main(["import", "status", output["run_id"]]) == 0
    status_output = json.loads(capsys.readouterr().out)
    assert status_output == output


def test_cli_jsonl_and_output_file_contract(
    app, tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(cli, "_application", lambda args, reader: app)
    output_path = tmp_path / "assets.jsonl"

    assert cli.main(
        ["asset", "list", "--format", "jsonl", "--output", str(output_path)]
    ) == 0
    assert capsys.readouterr().out == ""
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert records[0]["record_type"] == "run_start"
    assert records[-1]["record_type"] == "run_end"
    assert records[-1]["counts"] == {"asset": 2}
