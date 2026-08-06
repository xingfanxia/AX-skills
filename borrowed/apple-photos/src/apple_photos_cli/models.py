from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apple_photos_cli import SCHEMA_VERSION
from apple_photos_cli.canonical import sha256_digest


@dataclass(slots=True, frozen=True)
class LibrarySnapshot:
    kind: str
    canonical_path: str | None
    is_system_library: bool
    physical_identity_verified: bool
    sentinel_asset_ids: tuple[str, ...] = ()
    asset_ids_sha256: str = "sha256:" + "0" * 64
    asset_count: int | None = None
    observed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "canonical_path": self.canonical_path,
            "is_system_library": self.is_system_library,
            "physical_identity_verified": self.physical_identity_verified,
            "sentinel_asset_ids": list(self.sentinel_asset_ids),
            "asset_ids_sha256": self.asset_ids_sha256,
            "asset_count": self.asset_count,
            "observed_at": self.observed_at,
        }

    @property
    def digest(self) -> str:
        stable = self.to_dict()
        stable.pop("observed_at", None)
        return sha256_digest(stable)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> LibrarySnapshot:
        return cls(
            kind=value["kind"],
            canonical_path=value.get("canonical_path"),
            is_system_library=bool(value["is_system_library"]),
            physical_identity_verified=bool(value["physical_identity_verified"]),
            sentinel_asset_ids=tuple(value.get("sentinel_asset_ids", [])),
            asset_ids_sha256=value["asset_ids_sha256"],
            asset_count=value.get("asset_count"),
            observed_at=value.get("observed_at"),
        )


@dataclass(slots=True, frozen=True)
class AlbumRecord:
    osxphotos_album_uuid: str
    title: str
    asset_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "album_id": {
                "namespace": "osxphotos_album_uuid",
                "value": self.osxphotos_album_uuid,
            },
            "title": self.title,
            "asset_count": self.asset_count,
        }


@dataclass(slots=True, frozen=True)
class PhotoKitAlbumRecord:
    photokit_local_identifier: str
    title: str
    asset_count: int | None = None
    can_add_assets: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "album_id": {
                "namespace": "photokit_local_identifier",
                "value": self.photokit_local_identifier,
            },
            "title": self.title,
            "asset_count": self.asset_count,
            "can_add_assets": self.can_add_assets,
        }


@dataclass(slots=True, frozen=True)
class AssetRecord:
    osxphotos_uuid: str
    library_snapshot_digest: str
    media_type: str
    original_filename: str | None
    uti: str | None = None
    date_taken: str | None = None
    date_added: str | None = None
    date_modified: str | None = None
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    media_subtypes: tuple[str, ...] = ()
    osxphotos_album_uuids: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    favorite: bool = False
    hidden: bool = False
    edited: bool = False
    missing: bool = False
    in_trash: bool = False
    cloud_only: bool = False
    original_size_bytes: int | None = None
    title: str | None = None
    description: str | None = None
    sensitive: dict[str, Any] | None = None
    resource_count: int = 0
    asset_sha256: str | None = None
    metadata_backend: str = "synthetic"
    metadata_backend_version: str = "test"
    observed_at: str | None = None
    unavailable_fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "asset_id": {
                "namespace": "osxphotos_uuid",
                "value": self.osxphotos_uuid,
                "library_snapshot_digest": self.library_snapshot_digest,
            },
            "media_type": self.media_type,
            "media_subtypes": sorted(self.media_subtypes),
            "original_filename": self.original_filename,
            "uti": self.uti,
            "date_taken": self.date_taken,
            "date_added": self.date_added,
            "date_modified": self.date_modified,
            "dimensions": {"width": self.width, "height": self.height},
            "duration_ms": self.duration_ms,
            "flags": {
                "favorite": self.favorite,
                "hidden": self.hidden,
                "edited": self.edited,
                "missing": self.missing,
                "in_trash": self.in_trash,
                "cloud_only": self.cloud_only,
            },
            "album_ids": [
                {"namespace": "osxphotos_album_uuid", "value": value}
                for value in sorted(self.osxphotos_album_uuids)
            ],
            "keywords": sorted(self.keywords),
            "sensitive": self.sensitive,
            "resource_summary": {
                "verification": "sha256_verified" if self.asset_sha256 else "not_requested",
                "resource_count": self.resource_count,
                "asset_sha256": self.asset_sha256,
            },
            "provenance": {
                "metadata_backend": self.metadata_backend,
                "metadata_backend_version": self.metadata_backend_version,
                "observed_at": self.observed_at,
                "unavailable_fields": sorted(self.unavailable_fields),
            },
        }

    def filter_value(self, field_name: str) -> Any:
        direct = {
            "osxphotos_uuid": self.osxphotos_uuid,
            "original_filename": self.original_filename,
            "date_taken": self.date_taken,
            "date_added": self.date_added,
            "date_modified": self.date_modified,
            "media_type": self.media_type,
            "media_subtypes": self.media_subtypes,
            "uti": self.uti,
            "osxphotos_album_uuids": self.osxphotos_album_uuids,
            "keywords": self.keywords,
            "favorite": self.favorite,
            "hidden": self.hidden,
            "edited": self.edited,
            "missing": self.missing,
            "in_trash": self.in_trash,
            "cloud_only": self.cloud_only,
            "width": self.width,
            "height": self.height,
            "duration_ms": self.duration_ms,
            "original_size_bytes": self.original_size_bytes,
        }
        return direct[field_name]

    def search_text(self, include_sensitive: bool = False) -> str:
        values: list[str] = []
        for value in (self.original_filename, self.title, self.description):
            if value:
                values.append(value)
        values.extend(self.keywords)
        values.extend(self.osxphotos_album_uuids)
        if include_sensitive and self.sensitive:
            values.extend(str(value) for value in self.sensitive.values())
        return "\n".join(values).casefold()


@dataclass(slots=True, frozen=True)
class ResourceRecord:
    local_identifier: str
    role: str
    uti: str
    byte_count: int
    sha256: str
    availability: str = "available"
    path: str | None = None
    backend_error: str | None = None

    def digest_member(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "uti": self.uti,
            "byte_count": self.byte_count,
            "sha256": self.sha256,
        }


@dataclass(slots=True)
class OperationResult:
    command: str
    run_id: str
    ok: bool
    status: str
    started_at: str
    finished_at: str
    phase: str
    manifest_sha256: str | None = None
    library_snapshot: dict[str, Any] | None = None
    counts: dict[str, int] = field(default_factory=dict)
    items: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    warnings: list[dict[str, Any] | str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "command": self.command,
            "run_id": self.run_id,
            "ok": self.ok,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "phase": self.phase,
            "manifest_sha256": self.manifest_sha256,
            "library_snapshot": self.library_snapshot,
            "counts": self.counts,
            "items": self.items,
            "artifacts": self.artifacts,
            "warnings": self.warnings,
            "errors": self.errors,
        }
