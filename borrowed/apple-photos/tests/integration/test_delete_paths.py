from __future__ import annotations

import io
import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from conftest import FIXED_TIME, write_pixel_report

from apple_photos_cli.authorization import AuthorizationService, load_token
from apple_photos_cli.errors import EXIT_PARTIAL, ApplePhotosError
from apple_photos_cli.manifests import atomic_write_json, seal_manifest
from apple_photos_cli.models import ResourceRecord
from apple_photos_cli.similarity import SimilarityPolicy, compare_image_manifest
from apple_photos_cli.state import ReplayStore


class TTY(io.StringIO):
    def isatty(self) -> bool:
        return True


def _authorize(app, manifest, tmp_path: Path):
    service = AuthorizationService(
        app.state_dir,
        now=lambda: FIXED_TIME,
        random_bytes=lambda length: b"u" * length,
    )
    path = tmp_path / "delete.token"
    service.issue(
        manifest,
        stdin=TTY(service.required_phrase(manifest) + "\n"),
        stderr=TTY(),
        output=path,
    )
    return service, path


def _plan(app, fake_bridge, tmp_path: Path, candidate_ids: list[str]):
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", candidate_ids)
    return app.plan_delete(report, pairs, output=tmp_path / "delete.json")


def test_delete_plan_authorize_apply_and_replay_rejection(app, fake_bridge, tmp_path: Path) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])

    assert "delete-assets" not in fake_bridge.calls
    service, token_path = _authorize(app, manifest, tmp_path)
    replay = ReplayStore(app.state_dir)
    result = app.apply_delete(manifest_path, token_path, service, replay)

    assert result.ok
    assert result.items[0]["status"] == "deleted_confirmed"
    assert replay.is_consumed(load_token(token_path)["claims"]["nonce"])

    with pytest.raises(ApplePhotosError) as captured:
        app.apply_delete(manifest_path, token_path, service, replay)
    assert captured.value.code == "E_AUTH_REPLAY"


def test_native_delete_precondition_drift_is_known_rejection(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)
    token = load_token(token_path)
    fake_bridge.assets["delete-id"]["original_filename"] = "changed.jpg"
    replay = ReplayStore(app.state_dir)

    result = app.apply_delete(manifest_path, token_path, service, replay)

    assert result.status == "partial"
    assert result.phase == "commit_pending"
    assert result.errors[0]["code"] == "E_PLAN_STALE"
    assert result.items[0]["status"] == "not_attempted"
    assert replay.is_consumed(token["claims"]["nonce"])
    assert "delete-assets" not in fake_bridge.calls


def test_unknown_delete_postcondition_is_not_success(app, fake_bridge, tmp_path: Path) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    fake_bridge.force_unknown_delete = True
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)

    result = app.apply_delete(
        manifest_path,
        token_path,
        service,
        ReplayStore(app.state_dir),
    )

    assert not result.ok
    assert result.status == "outcome_unknown"
    assert result.items[0]["status"] == "outcome_unknown"


def test_equal_count_asset_set_drift_rejects_before_nonce(app, fake_bridge, tmp_path: Path) -> None:
    for identifier in ("a", "b", "c", "d"):
        fake_bridge.add_asset(identifier, identifier.encode())
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["d"])
    service, token_path = _authorize(app, manifest, tmp_path)
    token = load_token(token_path)
    del fake_bridge.assets["c"]
    fake_bridge.resources.pop("c")
    fake_bridge.add_asset("e", b"e")
    replay = ReplayStore(app.state_dir)

    with pytest.raises(ApplePhotosError) as captured:
        app.apply_delete(manifest_path, token_path, service, replay)

    assert captured.value.code == "E_LIBRARY_SNAPSHOT_MISMATCH"
    assert not replay.is_consumed(token["claims"]["nonce"])


def test_delete_revalidates_at_native_mutation_boundary(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)
    token = load_token(token_path)
    replay = ReplayStore(app.state_dir)
    original = fake_bridge.delete_assets

    def delete(items, **kwargs):
        fake_bridge.assets["delete-id"]["original_filename"] = "changed-at-boundary.jpg"
        return original(items, **kwargs)

    monkeypatch.setattr(fake_bridge, "delete_assets", delete)
    result = app.apply_delete(manifest_path, token_path, service, replay)

    assert result.status == "partial"
    assert result.phase == "commit_pending"
    assert result.errors[0]["code"] == "E_PLAN_STALE"
    assert replay.is_consumed(token["claims"]["nonce"])
    assert "delete-assets" not in fake_bridge.calls


def test_delete_does_not_repeat_python_asset_fetch(app, fake_bridge, tmp_path: Path) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)
    fake_bridge.calls.clear()

    result = app.apply_delete(
        manifest_path, token_path, service, ReplayStore(app.state_dir)
    )

    assert result.ok
    assert "fetch-assets" not in fake_bridge.calls


def test_token_expiry_at_commit_boundary_does_not_consume_nonce(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)
    token = load_token(token_path)
    times = iter([FIXED_TIME, FIXED_TIME + timedelta(minutes=16)])
    service.now = lambda: next(times)
    replay = ReplayStore(app.state_dir)

    with pytest.raises(ApplePhotosError) as captured:
        app.apply_delete(manifest_path, token_path, service, replay)

    assert captured.value.code == "E_AUTH_EXPIRED"
    assert not replay.is_consumed(token["claims"]["nonce"])
    assert "delete-assets" not in fake_bridge.calls
    receipts = list((app.state_dir / "runs").glob("*.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert receipt["status"] == "partial"
    assert receipt["items"][0]["status"] == "not_attempted"


def test_mismatched_delete_acknowledgement_is_outcome_unknown(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    fake_bridge.add_asset("a", b"a")
    fake_bridge.add_asset("b", b"b")
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["a", "b"])
    service, token_path = _authorize(app, manifest, tmp_path)

    monkeypatch.setattr(
        fake_bridge,
        "delete_assets",
        lambda items, **kwargs: {"local_identifiers": ["b", "a"]},
    )
    result = app.apply_delete(
        manifest_path, token_path, service, ReplayStore(app.state_dir)
    )

    assert result.status == "outcome_unknown"
    assert result.errors[0]["code"] == "E_OUTCOME_UNKNOWN"


def test_unknown_delete_consumes_nonce_and_writes_receipt(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)
    token = load_token(token_path)
    replay = ReplayStore(app.state_dir)

    def fail(items, **kwargs):
        assert replay.is_consumed(token["claims"]["nonce"])
        raise ApplePhotosError("E_OUTCOME_UNKNOWN", "Synthetic timeout.", EXIT_PARTIAL)

    monkeypatch.setattr(fake_bridge, "delete_assets", fail)
    result = app.apply_delete(manifest_path, token_path, service, replay)

    assert result.status == "outcome_unknown"
    assert app.status(result.run_id) == result.to_dict()
    assert replay.is_consumed(token["claims"]["nonce"])


def test_resealed_post_authorization_change_rejects_old_token(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)
    token = load_token(token_path)
    changed = dict(manifest)
    changed["items"] = [dict(manifest["items"][0])]
    changed["items"][0]["expected"] = dict(changed["items"][0]["expected"])
    changed["items"][0]["expected"]["original_filename"] = "attacker-change.jpg"
    changed = seal_manifest(changed)
    atomic_write_json(manifest_path, changed)
    replay = ReplayStore(app.state_dir)

    with pytest.raises(ApplePhotosError) as captured:
        app.apply_delete(manifest_path, token_path, service, replay)

    assert captured.value.code == "E_AUTH_INVALID"
    assert not replay.is_consumed(token["claims"]["nonce"])
    assert "delete-assets" not in fake_bridge.calls


def test_delete_interrupt_after_dispatch_becomes_terminal_unknown(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest_path = tmp_path / "delete.json"
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)
    token = load_token(token_path)
    replay = ReplayStore(app.state_dir)

    def interrupt(items, **kwargs):
        assert replay.is_consumed(token["claims"]["nonce"])
        raise KeyboardInterrupt

    monkeypatch.setattr(fake_bridge, "delete_assets", interrupt)
    result = app.apply_delete(manifest_path, token_path, service, replay)

    assert result.status == "outcome_unknown"
    assert result.errors[0]["exception_type"] == "KeyboardInterrupt"
    assert app.status(result.run_id)["status"] == "outcome_unknown"


def test_plan_rejects_pixel_source_not_owned_by_candidate(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["delete-id"])
    fake_bridge.add_asset("delete-id", b"different-current-resource")

    with pytest.raises(ApplePhotosError) as captured:
        app.plan_delete(report, pairs, output=tmp_path / "delete.json")

    assert captured.value.code == "E_PIXEL_SOURCE_MISMATCH"


def test_apply_rejects_pixel_source_drift_at_native_boundary(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)
    token = load_token(token_path)
    current = fake_bridge.resources["delete-id"][0]
    fake_bridge.resources["delete-id"] = [
        replace(current, sha256="0" * 64)
    ]
    replay = ReplayStore(app.state_dir)

    result = app.apply_delete(tmp_path / "delete.json", token_path, service, replay)

    assert result.status == "partial"
    assert result.errors[0]["code"] == "E_PIXEL_SOURCE_MISMATCH"
    assert replay.is_consumed(token["claims"]["nonce"])
    assert "delete-assets" not in fake_bridge.calls


def test_mixed_delete_verification_is_partial(
    app, fake_bridge, tmp_path: Path, monkeypatch
) -> None:
    for identifier in ("a", "b"):
        fake_bridge.add_asset(identifier, identifier.encode())
    manifest = _plan(app, fake_bridge, tmp_path, ["a", "b"])
    service, token_path = _authorize(app, manifest, tmp_path)

    monkeypatch.setattr(
        fake_bridge,
        "verify_assets",
        lambda identifiers, **kwargs: [
            {"local_identifier": identifiers[0], "present": False},
            {"local_identifier": identifiers[1], "present": True},
        ],
    )
    result = app.apply_delete(
        tmp_path / "delete.json",
        token_path,
        service,
        ReplayStore(app.state_dir),
    )

    assert result.status == "partial"
    assert result.counts == {"planned": 2, "deleted_confirmed": 1, "unknown": 1}


def test_keeper_drift_is_rejected_at_native_boundary(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    manifest = _plan(app, fake_bridge, tmp_path, ["delete-id"])
    service, token_path = _authorize(app, manifest, tmp_path)
    keeper = manifest["items"][0]["pixel_similarity_proof"]["keeper_local_identifier"]
    fake_bridge.assets[keeper]["original_filename"] = "changed-keeper.jpg"

    result = app.apply_delete(
        tmp_path / "delete.json",
        token_path,
        service,
        ReplayStore(app.state_dir),
    )

    assert result.status == "partial"
    assert result.errors[0]["code"] == "E_PLAN_STALE"


def test_plan_explicitly_rejects_byte_identical_pair(
    app, fake_bridge, tmp_path: Path
) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["delete-id"])
    pair = json.loads(pairs.read_text(encoding="utf-8"))
    candidate_bytes = Path(pair["left"]).read_bytes()
    Path(pair["right"]).write_bytes(candidate_bytes)
    fake_bridge.add_asset(pair["keeper_local_identifier"], candidate_bytes)
    compare_image_manifest(pairs, report, SimilarityPolicy())

    with pytest.raises(ApplePhotosError) as captured:
        app.plan_delete(report, pairs, output=tmp_path / "delete.json")

    assert captured.value.code == "E_PURE_DUPLICATE_UNSUPPORTED"


def test_plan_rejects_compound_photo_asset(app, fake_bridge, tmp_path: Path) -> None:
    fake_bridge.add_asset("delete-id", b"delete")
    report, pairs = write_pixel_report(fake_bridge, tmp_path / "pixel.json", ["delete-id"])
    extra = ResourceRecord(
        "delete-id", "paired_video", "com.apple.quicktime-movie", 5, "1" * 64
    )
    fake_bridge.resources["delete-id"].append(extra)
    fake_bridge.assets["delete-id"]["resource_descriptors"].append(extra.digest_member())

    with pytest.raises(ApplePhotosError) as captured:
        app.plan_delete(report, pairs, output=tmp_path / "delete.json")

    assert captured.value.code == "E_RESOURCE_COVERAGE_INCOMPLETE"


def test_evidence_rejects_more_than_50_pairs(fake_bridge, tmp_path: Path) -> None:
    identifiers = [f"delete-{index}" for index in range(51)]

    with pytest.raises(ApplePhotosError) as captured:
        write_pixel_report(fake_bridge, tmp_path / "pixel.json", identifiers)

    assert captured.value.code == "E_DELETE_BATCH_TOO_LARGE"
