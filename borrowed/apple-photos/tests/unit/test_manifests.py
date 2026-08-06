import json
from datetime import timedelta
from pathlib import Path

import pytest
from conftest import FIXED_TIME, write_pixel_report

from apple_photos_cli.errors import ApplePhotosError
from apple_photos_cli.manifests import format_time, load_manifest, seal_manifest


def test_manifest_tamper_is_rejected(app, fake_bridge, tmp_path: Path) -> None:
    fake_bridge.add_asset("asset-delete", b"bytes")
    path = tmp_path / "delete.json"
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["asset-delete"])
    app.plan_delete(report, pairs, output=path)
    value = json.loads(path.read_text())
    value["items"][0]["local_identifier"] = "different-id"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ApplePhotosError) as captured:
        load_manifest(path, expected_type="apple_photos_delete")

    assert captured.value.code == "E_MANIFEST_TAMPERED"


def test_manifest_type_is_enforced(app, fake_bridge, tmp_path: Path) -> None:
    fake_bridge.add_asset("asset-delete", b"bytes")
    path = tmp_path / "delete.json"
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["asset-delete"])
    app.plan_delete(report, pairs, output=path)

    with pytest.raises(ApplePhotosError) as captured:
        load_manifest(path, expected_type="apple_photos_import")

    assert captured.value.code == "E_SCHEMA_INVALID"


def test_manifest_lifetime_is_capped_at_24_hours(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("asset-delete", b"bytes")
    path = tmp_path / "delete.json"
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["asset-delete"])
    manifest = app.plan_delete(report, pairs, output=path)
    manifest["expires_at"] = format_time(FIXED_TIME + timedelta(hours=25))
    path.write_text(json.dumps(seal_manifest(manifest)), encoding="utf-8")

    with pytest.raises(ApplePhotosError) as captured:
        load_manifest(path, expected_type="apple_photos_delete")

    assert captured.value.code == "E_SCHEMA_INVALID"
