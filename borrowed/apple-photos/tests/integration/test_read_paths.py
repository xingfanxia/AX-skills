from __future__ import annotations

import hashlib
import json
from pathlib import Path


def test_search_list_metadata_and_filter(app) -> None:
    assert [asset.osxphotos_uuid for asset in app.search_assets("ALPHA")] == ["asset-a"]
    assert [asset.osxphotos_uuid for asset in app.list_assets(limit=1)] == ["asset-a"]
    metadata = app.metadata(["asset-a", "missing-id"])
    assert [item["status"] for item in metadata] == ["listed", "not_found"]
    filtered = app.filter_assets({"field": "hidden", "op": "eq", "value": True})
    assert [asset.osxphotos_uuid for asset in filtered] == ["asset-b"]


def test_metadata_backup_is_complete_and_checksummed(app, tmp_path: Path) -> None:
    output = tmp_path / "backup"
    manifest = app.backup_metadata(output)

    assert (output / "COMPLETE").read_text(encoding="utf-8") == "complete\n"
    assert set(manifest["files"]) == {
        "assets.jsonl",
        "albums.jsonl",
        "album_assets.jsonl",
        "errors.jsonl",
    }
    for name, expected in manifest["files"].items():
        content = (output / name).read_bytes()
        assert len(content) == expected["byte_count"]
        assert hashlib.sha256(content).hexdigest() == expected["sha256"]
    stored = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert stored == manifest
