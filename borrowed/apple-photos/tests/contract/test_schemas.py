from __future__ import annotations

import io
import json
from pathlib import Path

from conftest import FIXED_TIME, write_pixel_report
from jsonschema import Draft202012Validator
from PIL import Image

from apple_photos_cli.authorization import AuthorizationService, load_token
from apple_photos_cli.contracts import render_jsonl
from apple_photos_cli.manifests import format_time
from apple_photos_cli.similarity import SimilarityPolicy, compare_image_manifest


def _schema(name: str) -> dict:
    root = Path(__file__).resolve().parents[2]
    return json.loads((root / "schemas" / name).read_text(encoding="utf-8"))


def _assert_valid(name: str, value: dict) -> None:
    Draft202012Validator(_schema(name)).validate(value)


def test_asset_and_backup_schemas(app, fake_reader, tmp_path: Path) -> None:
    asset = fake_reader.assets()[0].to_dict()
    _assert_valid("asset-v1.schema.json", asset)

    backup = app.backup_metadata(tmp_path / "backup")
    _assert_valid("metadata-backup-v1.schema.json", backup)


def test_operation_result_and_authorization_schemas(app, fake_bridge, tmp_path: Path) -> None:
    fake_bridge.add_asset("asset-delete", b"content")
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["asset-delete"])
    manifest = app.plan_delete(report, pairs, output=tmp_path / "delete.json")
    _assert_valid("operation-manifest-v1.schema.json", manifest)

    service = AuthorizationService(
        app.state_dir,
        now=lambda: FIXED_TIME,
        random_bytes=lambda length: b"t" * length,
    )

    class TTY(io.StringIO):
        def isatty(self) -> bool:
            return True

    token_path = tmp_path / "token"
    service.issue(
        manifest,
        stdin=TTY(service.required_phrase(manifest) + "\n"),
        stderr=TTY(),
        output=token_path,
    )
    _assert_valid("authorization-claims-v1.schema.json", load_token(token_path)["claims"])

    result = {
        "schema_version": "1.0",
        "command": "delete.plan",
        "ok": True,
        "status": "planned",
        "counts": {"planned": 1},
    }
    _assert_valid("result-v1.schema.json", result)


def test_every_jsonl_record_validates() -> None:
    stream = io.StringIO()
    render_jsonl(
        command="metadata.dump",
        run_id="run-synthetic",
        records=(("asset", {"local_identifier": "asset-id"}),),
        observed_at=format_time(FIXED_TIME),
        stream=stream,
    )
    records = [json.loads(line) for line in stream.getvalue().splitlines()]

    assert [record["sequence"] for record in records] == [0, 1, 2]
    assert records[-1]["record_type"] == "run_end"
    for record in records:
        _assert_valid("event-v1.schema.json", record)


def test_pixel_similarity_report_schema(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    Image.new("RGB", (2, 2), (10, 20, 30)).save(left)
    Image.new("RGB", (2, 2), (10, 20, 30)).save(right)
    pairs = tmp_path / "pairs.jsonl"
    pairs.write_text(
        json.dumps(
            {
                "pair_id": "pair-1",
                "left": str(left),
                "right": str(right),
                "candidate_local_identifier": "candidate-id",
                "keeper_local_identifier": "keeper-id",
            }
        )
        + "\n"
    )

    report = compare_image_manifest(pairs, tmp_path / "report.json", SimilarityPolicy())

    _assert_valid("pixel-similarity-report-v1.schema.json", report)
