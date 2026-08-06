import json
from pathlib import Path

import pytest

from apple_photos_cli.errors import EXIT_PARTIAL, ApplePhotosError
from apple_photos_cli.manifests import atomic_write_json, seal_manifest
from apple_photos_cli.models import ResourceRecord


def test_import_plan_is_dry_run_and_apply_creates_verified_asset(
    app, fake_bridge, tmp_path: Path
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"new-image")
    manifest_path = tmp_path / "import.json"

    manifest = app.plan_import([source], album_id="album-target", output=manifest_path)

    assert manifest["items"][0]["planned_action"] == "create_asset"
    assert "import-assets" not in fake_bridge.calls

    result = app.apply_import(manifest_path)

    assert result.ok
    assert result.items[0]["status"] == "imported_verified"
    assert "import-assets" in fake_bridge.calls
    assert result.counts["created_verified"] == 1


def test_exact_duplicate_reuses_asset_despite_different_filename(
    app, fake_bridge, tmp_path: Path
) -> None:
    data = b"same-bytes"
    fake_bridge.add_asset("existing-id", data, filename="different-name.jpg")
    source = tmp_path / "source.jpg"
    source.write_bytes(data)
    manifest_path = tmp_path / "import.json"

    manifest = app.plan_import([source], album_id="album-target", output=manifest_path)
    assert manifest["items"][0]["planned_action"] == "reuse_exact_duplicate"

    result = app.apply_import(manifest_path)

    assert result.ok
    assert result.items[0]["local_identifier"] == "existing-id"
    assert result.items[0]["status"] == "reused_verified"
    assert "import-assets" not in fake_bridge.calls
    assert "add-assets-to-album" in fake_bridge.calls


def test_same_name_and_size_with_different_bytes_is_not_exact(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("existing-id", b"AAAA", filename="source.jpg")
    source = tmp_path / "source.jpg"
    source.write_bytes(b"BBBB")

    manifest = app.plan_import([source], album_id="album-target", output=tmp_path / "import.json")

    assert manifest["items"][0]["planned_action"] == "create_asset"
    assert manifest["items"][0]["exact_duplicate_ids"] == []


def test_incomplete_resource_coverage_blocks_apply(app, fake_bridge, tmp_path: Path) -> None:
    fake_bridge.assets["cloud-id"] = {
        "local_identifier": "cloud-id",
        "media_type": "image",
        "original_filename": "cloud.jpg",
        "date_taken": None,
        "in_trash": False,
        "resource_descriptors": [],
    }
    fake_bridge.resources["cloud-id"] = [
        ResourceRecord("cloud-id", "photo", "image/jpeg", 0, "", "unavailable")
    ]
    source = tmp_path / "source.jpg"
    source.write_bytes(b"new")
    path = tmp_path / "import.json"

    manifest = app.plan_import([source], album_id="album-target", output=path)
    assert manifest["items"][0]["planned_action"] == "blocked_duplicate_coverage_incomplete"

    with pytest.raises(ApplePhotosError, match="blocked"):
        app.apply_import(path)
    assert "import-assets" not in fake_bridge.calls


def test_import_hash_postcondition_failure_is_partial(app, fake_bridge, tmp_path: Path) -> None:
    fake_bridge.force_bad_import_digest = True
    source = tmp_path / "source.jpg"
    source.write_bytes(b"source")
    path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=path)

    result = app.apply_import(path)

    assert not result.ok
    assert result.status == "partial"
    assert result.items[0]["status"] == "imported_integrity_failed"


def test_batch_duplicate_creates_once_and_reuses_result(app, fake_bridge, tmp_path: Path) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"same")
    second.write_bytes(b"same")
    path = tmp_path / "import.json"

    manifest = app.plan_import([first, second], album_id="album-target", output=path)
    assert [item["planned_action"] for item in manifest["items"]] == [
        "create_asset",
        "reuse_batch_duplicate",
    ]

    result = app.apply_import(path)
    assert result.ok
    assert result.items[0]["local_identifier"] == result.items[1]["local_identifier"]
    assert len([call for call in fake_bridge.calls if call == "import-assets"]) == 1


def test_partial_resource_topology_blocks_duplicate_coverage(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("compound", b"photo")
    fake_bridge.assets["compound"]["resource_descriptors"].append(
        {"role": "paired_video", "uti": "com.apple.quicktime-movie"}
    )
    source = tmp_path / "source.jpg"
    source.write_bytes(b"new")

    manifest = app.plan_import(
        [source], album_id="album-target", output=tmp_path / "import.json"
    )
    assert manifest["duplicate_policy"]["coverage_complete"] is False
    assert manifest["items"][0]["planned_action"] == "blocked_duplicate_coverage_incomplete"


def test_unavailable_resource_with_plausible_hash_does_not_verify(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("existing", b"same")
    resource = fake_bridge.resources["existing"][0]
    fake_bridge.resources["existing"] = [
        ResourceRecord(
            resource.local_identifier,
            resource.role,
            resource.uti,
            resource.byte_count,
            resource.sha256,
            "unavailable",
        )
    ]
    source = tmp_path / "source.jpg"
    source.write_bytes(b"same")

    manifest = app.plan_import(
        [source], album_id="album-target", output=tmp_path / "import.json"
    )
    assert manifest["duplicate_policy"]["coverage_complete"] is False
    assert manifest["items"][0]["planned_action"] == "blocked_duplicate_coverage_incomplete"


def test_post_dispatch_import_error_writes_unknown_receipt(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"new")
    manifest_path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=manifest_path)

    def fail(*args, **kwargs):
        raise ApplePhotosError("E_OUTCOME_UNKNOWN", "Synthetic timeout.", EXIT_PARTIAL)

    monkeypatch.setattr(fake_bridge, "import_assets", fail)
    result = app.apply_import(manifest_path)

    assert result.status == "outcome_unknown"
    assert app.status(result.run_id) == result.to_dict()


def test_missing_placeholder_preserves_sibling_evidence_and_stops_mutations(
    app, fake_bridge, tmp_path: Path
) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    third = tmp_path / "third.jpg"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    third.write_bytes(b"third")
    manifest_path = tmp_path / "import.json"
    app.plan_import([first, second, third], album_id="album-target", output=manifest_path)
    fake_bridge.unknown_import_item_ids.add("src_000002")
    fake_bridge.calls.clear()

    result = app.apply_import(manifest_path)

    assert result.status == "partial"
    assert result.counts == {
        "planned": 3,
        "resolution_known": 1,
        "unknown": 1,
        "not_attempted": 1,
    }
    assert result.items == [
        {
            "item_id": "src_000001",
            "local_identifier": "created-1",
            "status": "resolution_known",
            "evidence": "photokit_placeholder",
        },
        {
            "item_id": "src_000002",
            "status": "outcome_unknown",
            "evidence": "placeholder_missing_after_creation_registered",
        },
        {
            "item_id": "src_000003",
            "status": "not_attempted_after_unknown",
            "evidence": "not_attempted_after_unknown",
        },
    ]
    assert result.errors[0]["code"] == "E_OUTCOME_UNKNOWN"
    assert app.status(result.run_id) == result.to_dict()
    assert "add-assets-to-album" not in fake_bridge.calls
    assert "read-resources" not in fake_bridge.calls
    assert "verify-assets" not in fake_bridge.calls
    assert set(fake_bridge.assets) == {"created-1"}


def test_unknown_creation_propagates_to_batch_duplicate(app, fake_bridge, tmp_path: Path) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"same")
    second.write_bytes(b"same")
    manifest_path = tmp_path / "import.json"
    app.plan_import([first, second], album_id="album-target", output=manifest_path)
    fake_bridge.unknown_import_item_ids.add("src_000001")

    result = app.apply_import(manifest_path)

    assert result.status == "outcome_unknown"
    assert result.counts == {
        "planned": 2,
        "resolution_known": 0,
        "unknown": 2,
        "not_attempted": 0,
    }
    assert [item["status"] for item in result.items] == [
        "outcome_unknown",
        "outcome_unknown",
    ]
    assert result.items[1]["evidence"] == "batch_duplicate_parent_outcome_unknown"


def test_blocked_coverage_batch_does_not_reference_blocked_parent(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.assets["offline"] = {
        "local_identifier": "offline",
        "media_type": "image",
        "original_filename": "offline.jpg",
        "date_taken": None,
        "in_trash": False,
        "resource_descriptors": [{"role": "photo", "uti": "public.jpeg"}],
    }
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"same")
    second.write_bytes(b"same")

    manifest = app.plan_import(
        [first, second], album_id="album-target", output=tmp_path / "blocked.json"
    )

    assert [item["planned_action"] for item in manifest["items"]] == [
        "blocked_duplicate_coverage_incomplete",
        "blocked_duplicate_coverage_incomplete",
    ]
    assert [item["batch_duplicate_of"] for item in manifest["items"]] == [None, None]


def test_ambiguous_duplicate_batch_does_not_reference_blocked_parent(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("existing-a", b"same")
    fake_bridge.add_asset("existing-b", b"same")
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"same")
    second.write_bytes(b"same")

    manifest = app.plan_import(
        [first, second], album_id="album-target", output=tmp_path / "blocked.json"
    )

    assert [item["planned_action"] for item in manifest["items"]] == [
        "blocked_ambiguous_duplicate",
        "blocked_ambiguous_duplicate",
    ]
    assert [item["batch_duplicate_of"] for item in manifest["items"]] == [None, None]


@pytest.mark.parametrize("mode", ["unavailable", "missing", "extra"])
def test_import_apply_rejects_incomplete_or_extra_observed_resources(
    app, fake_bridge, tmp_path: Path, monkeypatch, mode: str
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"source")
    manifest_path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=manifest_path)
    original = fake_bridge.read_resources

    def observed(identifiers, *, network=False, output_dir=None):
        resources = original(identifiers, network=network, output_dir=output_dir)
        if mode == "missing":
            return []
        if mode == "extra":
            return [
                *resources,
                ResourceRecord(
                    identifiers[0], "paired_video", "com.apple.quicktime-movie", 1, "a" * 64
                )
            ]
        resource = resources[0]
        return [
            ResourceRecord(
                resource.local_identifier,
                resource.role,
                resource.uti,
                resource.byte_count,
                resource.sha256,
                "unavailable",
            )
        ]

    monkeypatch.setattr(fake_bridge, "read_resources", observed)
    result = app.apply_import(manifest_path)

    assert result.status == "partial"
    assert result.items[0]["status"] == "imported_integrity_failed"
    assert result.items[0]["resource_digest_match"] is False


def test_source_change_aborts_application_before_helper(
    app, fake_bridge, tmp_path: Path
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"before")
    manifest_path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=manifest_path)
    source.write_bytes(b"after!")

    with pytest.raises(ApplePhotosError) as captured:
        app.apply_import(manifest_path)

    assert captured.value.code == "E_HASH_MISMATCH"
    assert "import-assets" not in fake_bridge.calls


def test_import_apply_rejects_unsealed_tamper_before_staging(
    app, fake_bridge, tmp_path: Path
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"source")
    manifest_path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=manifest_path)
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value["items"][0]["source"]["sha256"] = "0" * 64
    atomic_write_json(manifest_path, value)

    with pytest.raises(ApplePhotosError) as captured:
        app.apply_import(manifest_path)

    assert captured.value.code == "E_MANIFEST_TAMPERED"
    assert "import-assets" not in fake_bridge.calls
    assert not (app.state_dir / "staging").exists()


def test_import_apply_rejects_resealed_malformed_manifest_before_helper(
    app, fake_bridge, tmp_path: Path
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"source")
    manifest_path = tmp_path / "import.json"
    manifest = app.plan_import([source], album_id="album-target", output=manifest_path)
    manifest["items"][0]["planned_action"] = "retain"
    atomic_write_json(manifest_path, seal_manifest(manifest))

    with pytest.raises(ApplePhotosError) as captured:
        app.apply_import(manifest_path)

    assert captured.value.code == "E_SCHEMA_INVALID"
    assert "import-assets" not in fake_bridge.calls


def test_created_identifier_is_durable_before_postcondition_failure(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"source")
    manifest_path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=manifest_path)

    def fail(*args, **kwargs):
        pending = app.status("run_fixed-id")
        assert pending["phase"] == "commit_reported"
        assert pending["items"] == [
            {
                "item_id": "src_000001",
                "local_identifier": "created-1",
                "status": "resolution_known",
                "evidence": "photokit_placeholder",
            }
        ]
        raise ApplePhotosError("E_BACKEND_PROTOCOL", "Synthetic read failure.", EXIT_PARTIAL)

    monkeypatch.setattr(fake_bridge, "read_resources", fail)
    result = app.apply_import(manifest_path)

    assert result.status == "outcome_unknown"
    assert result.items[0]["local_identifier"] == "created-1"
    assert app.status(result.run_id)["items"][0]["local_identifier"] == "created-1"


def test_import_interrupt_after_dispatch_becomes_terminal_unknown(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"source")
    manifest_path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=manifest_path)

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(fake_bridge, "import_assets", interrupt)
    result = app.apply_import(manifest_path)

    assert result.status == "outcome_unknown"
    assert result.errors[0]["exception_type"] == "KeyboardInterrupt"
    assert app.status(result.run_id)["status"] == "outcome_unknown"


def test_import_known_precommit_rejection_is_not_attempted(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"source")
    manifest_path = tmp_path / "import.json"
    app.plan_import([source], album_id="album-target", output=manifest_path)

    def reject(*args, **kwargs):
        raise ApplePhotosError(
            "E_PERMISSION_PHOTOS",
            "Synthetic permission rejection.",
            EXIT_PARTIAL,
            {"mutation_phase": "not_started"},
        )

    monkeypatch.setattr(fake_bridge, "import_assets", reject)
    result = app.apply_import(manifest_path)

    assert result.status == "partial"
    assert result.phase == "commit_pending"
    assert result.items[0]["status"] == "not_attempted"


def test_later_precommit_rejection_preserves_created_identifier(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    fake_bridge.add_asset("existing", b"duplicate")
    new_source = tmp_path / "new.jpg"
    duplicate_source = tmp_path / "duplicate.jpg"
    new_source.write_bytes(b"new")
    duplicate_source.write_bytes(b"duplicate")
    manifest_path = tmp_path / "import.json"
    app.plan_import(
        [new_source, duplicate_source], album_id="album-target", output=manifest_path
    )

    def reject(*args, **kwargs):
        raise ApplePhotosError(
            "E_PERMISSION_PHOTOS",
            "Synthetic album rejection.",
            EXIT_PARTIAL,
            {"mutation_phase": "not_started"},
        )

    monkeypatch.setattr(fake_bridge, "add_assets_to_album", reject)
    result = app.apply_import(manifest_path)

    assert result.status == "partial"
    assert result.counts == {
        "planned": 2,
        "resolution_known": 1,
        "not_attempted": 1,
    }
    assert result.items[0]["status"] == "resolution_known"
    assert result.items[0]["local_identifier"] == "created-1"
    assert result.items[1]["status"] == "not_attempted"
