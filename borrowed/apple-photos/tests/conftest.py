from __future__ import annotations

import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from apple_photos_cli.application import Application
from apple_photos_cli.canonical import asset_id_set_digest, sha256_digest
from apple_photos_cli.errors import stale
from apple_photos_cli.hashing import sha256_file
from apple_photos_cli.models import (
    AlbumRecord,
    AssetRecord,
    LibrarySnapshot,
    PhotoKitAlbumRecord,
    ResourceRecord,
)
from apple_photos_cli.similarity import SimilarityPolicy, compare_image_manifest

FIXED_TIME = datetime(2030, 1, 2, 3, 4, 5, tzinfo=UTC)


def write_pixel_report(
    fake_bridge: FakeBridge, path: Path, candidate_ids: list[str]
) -> tuple[Path, Path]:
    pair_manifest = path.with_suffix(".pairs.jsonl")
    records = []
    for index, candidate_id in enumerate(candidate_ids, start=1):
        keeper_id = f"{candidate_id}-keeper"
        candidate_path = path.parent / f"candidate-{index}.png"
        keeper_path = path.parent / f"keeper-{index}.png"
        candidate_buffer = io.BytesIO()
        keeper_buffer = io.BytesIO()
        Image.new("RGB", (8, 8), (100, 100, 100)).save(candidate_buffer, format="PNG")
        Image.new("RGB", (8, 8), (102, 102, 102)).save(keeper_buffer, format="PNG")
        candidate_bytes = candidate_buffer.getvalue()
        keeper_bytes = keeper_buffer.getvalue()
        candidate_path.write_bytes(candidate_bytes)
        keeper_path.write_bytes(keeper_bytes)
        fake_bridge.add_asset(candidate_id, candidate_bytes)
        fake_bridge.add_asset(keeper_id, keeper_bytes)
        records.append(
            {
                "pair_id": f"pair-{index}",
                "left": str(candidate_path),
                "right": str(keeper_path),
                "candidate_local_identifier": candidate_id,
                "keeper_local_identifier": keeper_id,
            }
        )
    pair_manifest.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8"
    )
    compare_image_manifest(pair_manifest, path, SimilarityPolicy())
    return path, pair_manifest


class FakeReader:
    def __init__(self) -> None:
        self.snapshot = LibrarySnapshot(
            kind="selected_osxphotos_snapshot",
            canonical_path="/example/Synthetic.photoslibrary",
            is_system_library=False,
            physical_identity_verified=False,
            sentinel_asset_ids=("asset-a",),
            asset_ids_sha256=asset_id_set_digest(["asset-a", "asset-b"]),
            asset_count=2,
            observed_at="2030-01-02T03:04:05Z",
        )
        self._albums = [AlbumRecord("album-a", "Synthetic Album", 1)]
        self._assets = [
            AssetRecord(
                osxphotos_uuid="asset-a",
                library_snapshot_digest=self.snapshot.digest,
                media_type="image",
                original_filename="alpha.jpg",
                uti="image/jpeg",
                date_taken="2029-01-01T00:00:00Z",
                width=100,
                height=80,
                osxphotos_album_uuids=("album-a",),
                keywords=("sky",),
                favorite=True,
                resource_count=1,
                metadata_backend="synthetic",
                metadata_backend_version="1.0",
                observed_at="2030-01-02T03:04:05Z",
            ),
            AssetRecord(
                osxphotos_uuid="asset-b",
                library_snapshot_digest=self.snapshot.digest,
                media_type="video",
                original_filename="beta.mov",
                uti="video/quicktime",
                date_taken="2029-02-01T00:00:00Z",
                width=1920,
                height=1080,
                duration_ms=1000,
                hidden=True,
                resource_count=1,
                metadata_backend="synthetic",
                metadata_backend_version="1.0",
                observed_at="2030-01-02T03:04:05Z",
            ),
        ]

    def probe(self) -> LibrarySnapshot:
        return self.snapshot

    def assets(self) -> list[AssetRecord]:
        return list(self._assets)

    def albums(self) -> list[AlbumRecord]:
        return list(self._albums)


class FakeBridge:
    def __init__(self) -> None:
        self.snapshot = LibrarySnapshot(
            kind="system_photo_library_snapshot",
            canonical_path=None,
            is_system_library=True,
            physical_identity_verified=False,
            sentinel_asset_ids=(),
            asset_ids_sha256=asset_id_set_digest([]),
            asset_count=0,
            observed_at="2030-01-02T03:04:05Z",
        )
        self.albums = [PhotoKitAlbumRecord("album-target", "Target Album", 0, True)]
        self.assets: dict[str, dict[str, Any]] = {}
        self.resources: dict[str, list[ResourceRecord]] = {}
        self.memberships: set[tuple[str, str]] = set()
        self.deleted: set[str] = set()
        self.calls: list[str] = []
        self.force_unknown_delete = False
        self.force_bad_import_digest = False
        self.unknown_import_item_ids: set[str] = set()

    def probe(self) -> LibrarySnapshot:
        self.calls.append("probe")
        identifiers = sorted(
            identifier for identifier in self.assets if identifier not in self.deleted
        )
        return LibrarySnapshot(
            kind="system_photo_library_snapshot",
            canonical_path=None,
            is_system_library=True,
            physical_identity_verified=False,
            sentinel_asset_ids=tuple(identifiers[:3]),
            asset_ids_sha256=asset_id_set_digest(identifiers),
            asset_count=len(identifiers),
            observed_at="2030-01-02T03:04:05Z",
        )

    def list_albums(self) -> list[PhotoKitAlbumRecord]:
        self.calls.append("list-albums")
        return list(self.albums)

    def fetch_assets(self, local_identifiers: list[str] | None = None) -> list[dict[str, Any]]:
        self.calls.append("fetch-assets")
        values = self.assets.values()
        if local_identifiers is not None:
            selected = set(local_identifiers)
            values = (asset for identifier, asset in self.assets.items() if identifier in selected)
        return [dict(asset) for asset in values if asset["local_identifier"] not in self.deleted]

    def read_resources(
        self,
        local_identifiers: list[str],
        *,
        network: bool = False,
        output_dir: Path | None = None,
    ) -> list[ResourceRecord]:
        self.calls.append("read-resources")
        return [
            resource
            for identifier in local_identifiers
            for resource in self.resources.get(identifier, [])
        ]

    def import_assets(self, items: list[dict[str, Any]], album_id: str) -> dict[str, Any]:
        self.calls.append("import-assets")
        results = []
        stopped = False
        for index, item in enumerate(items, start=1):
            if stopped:
                results.append(
                    {
                        "item_id": item["item_id"],
                        "local_identifier": None,
                        "status": "not_attempted_after_unknown",
                        "evidence": "not_attempted_after_unknown",
                    }
                )
                continue
            if item["item_id"] in self.unknown_import_item_ids:
                results.append(
                    {
                        "item_id": item["item_id"],
                        "local_identifier": None,
                        "status": "outcome_unknown",
                        "evidence": "placeholder_missing_after_creation_registered",
                    }
                )
                stopped = True
                continue
            identifier = f"created-{index}"
            path = Path(item["staged_path"])
            digest = sha256_file(path)
            if self.force_bad_import_digest:
                digest = hashlib.sha256(b"different").hexdigest()
            resource = ResourceRecord(
                identifier,
                item["role"],
                item["uti"],
                path.stat().st_size,
                digest,
            )
            self.resources[identifier] = [resource]
            self.assets[identifier] = {
                "local_identifier": identifier,
                "media_type": "video" if item["role"] == "video" else "image",
                "original_filename": path.name,
                "date_taken": None,
                "in_trash": False,
                "resource_descriptors": [resource.digest_member()],
            }
            self.memberships.add((album_id, identifier))
            results.append(
                {
                    "item_id": item["item_id"],
                    "local_identifier": identifier,
                    "status": "created_identifier_known",
                    "evidence": "photokit_placeholder",
                }
            )
        known = sum(item["status"] == "created_identifier_known" for item in results)
        unknown = len(results) - known
        status = "succeeded" if unknown == 0 else ("outcome_unknown" if known == 0 else "partial")
        return {"status": status, "items": results}

    def add_assets_to_album(self, local_identifiers: list[str], album_id: str) -> dict[str, Any]:
        self.calls.append("add-assets-to-album")
        for identifier in local_identifiers:
            self.memberships.add((album_id, identifier))
        return {"local_identifiers": local_identifiers}

    def delete_assets(
        self,
        items: list[dict[str, Any]],
        *,
        authorization_expires_at: str,
        manifest_sha256: str,
        evidence_attestation: dict[str, Any],
        authorization_token: dict[str, Any],
        network_access_allowed: bool = False,
    ) -> dict[str, Any]:
        assert authorization_expires_at
        assert manifest_sha256
        assert evidence_attestation
        assert authorization_token
        assert isinstance(network_access_allowed, bool)
        local_identifiers = [item["local_identifier"] for item in items]
        for item in items:
            proof = item["pixel_similarity_proof"]
            candidate_resources = self.resources.get(item["local_identifier"], [])
            keeper_resources = self.resources.get(proof["keeper_local_identifier"], [])
            if (
                len(candidate_resources) != 1
                or candidate_resources[0].role != "photo"
                or candidate_resources[0].availability != "available"
                or "sha256:" + candidate_resources[0].sha256.removeprefix("sha256:")
                != proof["candidate_source_sha256"]
                or len(keeper_resources) != 1
                or keeper_resources[0].role != "photo"
                or keeper_resources[0].availability != "available"
                or "sha256:" + keeper_resources[0].sha256.removeprefix("sha256:")
                != proof["keeper_source_sha256"]
            ):
                raise stale(
                    "Synthetic native pixel source changed.",
                    code="E_PIXEL_SOURCE_MISMATCH",
                    detail={"mutation_phase": "not_started"},
                )
            for identifier, planned in (
                (item["local_identifier"], item["expected"]),
                (proof["keeper_local_identifier"], proof["keeper_expected"]),
            ):
                asset = self.assets.get(identifier)
                if asset is None:
                    raise stale(
                        "Synthetic native delete target is missing.",
                        code="E_NOT_FOUND",
                        detail={"mutation_phase": "not_started"},
                    )
                expected = {
                    "original_filename": asset.get("original_filename"),
                    "media_type": asset.get("media_type"),
                    "date_taken": asset.get("date_taken"),
                    "date_modified": asset.get("date_modified"),
                    "width": asset.get("width"),
                    "height": asset.get("height"),
                    "resource_descriptor_digest": sha256_digest(
                        asset.get("resource_descriptors", [])
                    ),
                    "in_trash": bool(asset.get("in_trash", False)),
                }
                if expected != planned:
                    raise stale(
                        "Synthetic native delete precondition changed.",
                        detail={"mutation_phase": "not_started"},
                    )
        self.calls.append("delete-assets")
        self.deleted.update(local_identifiers)
        return {"local_identifiers": local_identifiers}

    def verify_assets(
        self,
        local_identifiers: list[str],
        *,
        album_id: str | None = None,
        expect_present: bool = True,
    ) -> list[dict[str, Any]]:
        self.calls.append("verify-assets")
        records = []
        for identifier in local_identifiers:
            present = identifier in self.assets and identifier not in self.deleted
            if not expect_present and self.force_unknown_delete:
                present = True
            records.append(
                {
                    "local_identifier": identifier,
                    "present": present,
                    "in_album": bool(album_id and (album_id, identifier) in self.memberships),
                }
            )
        return records

    def add_asset(self, identifier: str, data: bytes, *, filename: str = "existing.jpg") -> None:
        digest = hashlib.sha256(data).hexdigest()
        resource = ResourceRecord(identifier, "photo", "public.jpeg", len(data), digest)
        self.resources[identifier] = [resource]
        self.assets[identifier] = {
            "local_identifier": identifier,
            "media_type": "image",
            "original_filename": filename,
            "date_taken": "2029-01-01T00:00:00Z",
            "date_modified": None,
            "width": 8,
            "height": 8,
            "in_trash": False,
            "resource_descriptors": [resource.digest_member()],
        }


@pytest.fixture
def fake_reader() -> FakeReader:
    return FakeReader()


@pytest.fixture
def fake_bridge() -> FakeBridge:
    return FakeBridge()


@pytest.fixture
def app(tmp_path: Path, fake_reader: FakeReader, fake_bridge: FakeBridge) -> Application:
    return Application(
        reader=fake_reader,
        bridge=fake_bridge,
        state_dir=tmp_path / "state",
        now=lambda: FIXED_TIME,
        id_factory=lambda: "fixed-id",
    )
