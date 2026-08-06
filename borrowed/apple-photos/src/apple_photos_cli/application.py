from __future__ import annotations

import re
import tempfile
import uuid
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

from apple_photos_cli import SCHEMA_VERSION, __version__
from apple_photos_cli.authorization import AuthorizationService
from apple_photos_cli.canonical import sha256_digest
from apple_photos_cli.contracts import create_metadata_backup
from apple_photos_cli.errors import (
    EXIT_AUTH,
    EXIT_IO,
    EXIT_PARTIAL,
    ApplePhotosError,
    stale,
    unsupported,
    usage_error,
)
from apple_photos_cli.filters import matches_filter
from apple_photos_cli.hashing import (
    inspect_source,
    resource_set_digest,
    source_resource,
    stage_source,
)
from apple_photos_cli.manifests import (
    atomic_write_json,
    format_time,
    fsync_directory,
    load_manifest,
    validate_schema,
    write_manifest,
)
from apple_photos_cli.models import (
    AlbumRecord,
    AssetRecord,
    LibrarySnapshot,
    OperationResult,
    PhotoKitAlbumRecord,
    ResourceRecord,
)
from apple_photos_cli.similarity import load_similarity_report, revalidate_similarity_report
from apple_photos_cli.state import LibraryLock, ReplayStore


class Reader(Protocol):
    def probe(self) -> LibrarySnapshot: ...

    def assets(self) -> list[AssetRecord]: ...

    def albums(self) -> list[AlbumRecord]: ...


class Bridge(Protocol):
    def probe(self) -> LibrarySnapshot: ...

    def list_albums(self) -> list[PhotoKitAlbumRecord]: ...

    def fetch_assets(
        self, local_identifiers: Sequence[str] | None = None
    ) -> list[dict[str, Any]]: ...

    def read_resources(
        self,
        local_identifiers: Sequence[str],
        *,
        network: bool = False,
        output_dir: Path | None = None,
    ) -> list[ResourceRecord]: ...

    def import_assets(self, items: list[dict[str, Any]], album_id: str) -> dict[str, Any]: ...

    def add_assets_to_album(
        self, local_identifiers: Sequence[str], album_id: str
    ) -> dict[str, Any]: ...

    def delete_assets(
        self,
        items: Sequence[dict[str, Any]],
        *,
        authorization_expires_at: str,
        manifest_sha256: str,
        evidence_attestation: dict[str, Any],
        authorization_token: dict[str, Any],
        network_access_allowed: bool = False,
    ) -> dict[str, Any]: ...

    def verify_assets(
        self,
        local_identifiers: Sequence[str],
        *,
        album_id: str | None = None,
        expect_present: bool = True,
    ) -> list[dict[str, Any]]: ...


class Application:
    def __init__(
        self,
        *,
        reader: Reader | None,
        bridge: Bridge,
        state_dir: Path,
        now: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.reader = reader
        self.bridge = bridge
        self.state_dir = state_dir
        self.now = now or (lambda: datetime.now(UTC))
        self.id_factory = id_factory or (lambda: uuid.uuid4().hex)

    def _time(self) -> str:
        return format_time(self.now())

    def _run_id(self) -> str:
        return f"run_{self.id_factory()}"

    def _require_reader(self) -> Reader:
        if self.reader is None:
            raise usage_error(
                "This command requires --library or the default Photos library reader."
            )
        return self.reader

    def inspect_library(self) -> dict[str, Any]:
        snapshot = self._require_reader().probe()
        return {
            "schema_version": SCHEMA_VERSION,
            "library_snapshot": snapshot.to_dict(),
            "library_snapshot_digest": snapshot.digest,
        }

    def list_albums(self) -> list[AlbumRecord]:
        return self._require_reader().albums()

    def list_assets(self, *, limit: int | None = None) -> list[AssetRecord]:
        assets = sorted(
            self._require_reader().assets(),
            key=lambda asset: (asset.date_taken or "", asset.osxphotos_uuid),
        )
        return assets[:limit] if limit is not None else assets

    def search_assets(self, query: str, *, include_sensitive: bool = False) -> list[AssetRecord]:
        query_text = query.casefold()
        return [
            asset
            for asset in self.list_assets()
            if query_text in asset.search_text(include_sensitive=include_sensitive)
        ]

    def metadata(self, local_identifiers: Sequence[str]) -> list[dict[str, Any]]:
        indexed = {asset.osxphotos_uuid: asset for asset in self.list_assets()}
        records: list[dict[str, Any]] = []
        for local_identifier in local_identifiers:
            asset = indexed.get(local_identifier)
            records.append(
                {
                    "asset_id": {"namespace": "osxphotos_uuid", "value": local_identifier},
                    "status": "listed" if asset else "not_found",
                    "asset": asset.to_dict() if asset else None,
                }
            )
        return records

    def filter_assets(self, spec: dict[str, Any]) -> list[AssetRecord]:
        return [asset for asset in self.list_assets() if matches_filter(asset, spec)]

    def backup_metadata(self, output: Path) -> dict[str, Any]:
        reader = self._require_reader()
        if output.resolve().exists():
            raise ApplePhotosError(
                "E_LOCAL_IO", f"Backup output already exists: {output.resolve()}", EXIT_IO
            )
        return create_metadata_backup(
            output,
            snapshot=reader.probe(),
            assets=self.list_assets(),
            albums=reader.albums(),
            created_at=self._time(),
        )

    def retrieve(
        self, local_identifiers: Sequence[str], *, output: Path, network: bool = False
    ) -> list[dict[str, Any]]:
        output.mkdir(parents=True, exist_ok=True)
        resources = self.bridge.read_resources(
            local_identifiers, network=network, output_dir=output.resolve()
        )
        grouped: dict[str, list[ResourceRecord]] = {
            identifier: [] for identifier in local_identifiers
        }
        for resource in resources:
            grouped.setdefault(resource.local_identifier, []).append(resource)
        records: list[dict[str, Any]] = []
        for identifier in local_identifiers:
            members = grouped.get(identifier, [])
            if not members:
                records.append(
                    {
                        "asset_id": {"namespace": "photokit_local_identifier", "value": identifier},
                        "status": "not_found_or_no_resources",
                        "resources": [],
                    }
                )
                continue
            records.append(
                {
                    "asset_id": {"namespace": "photokit_local_identifier", "value": identifier},
                    "status": (
                        "retrieved_verified"
                        if all(
                            member.availability == "available" and member.path for member in members
                        )
                        else "resource_unavailable"
                    ),
                    "resources": [
                        {
                            "role": member.role,
                            "uti": member.uti,
                            "byte_count": member.byte_count,
                            "sha256": member.sha256,
                            "availability": member.availability,
                            "path": member.path,
                            "backend_error": member.backend_error,
                        }
                        for member in members
                    ],
                }
            )
        return records

    def _mutation_snapshot(self) -> LibrarySnapshot:
        snapshot = self.bridge.probe()
        if not snapshot.is_system_library or snapshot.kind != "system_photo_library_snapshot":
            raise unsupported(
                "Mutations are supported only for the System Photo Library.",
                code="E_CAPABILITY_UNSUPPORTED",
            )
        return snapshot

    def _album(self, album_id: str) -> PhotoKitAlbumRecord:
        matches = [
            album
            for album in self.bridge.list_albums()
            if album.photokit_local_identifier == album_id and album.can_add_assets
        ]
        if len(matches) != 1:
            raise stale(
                f"Target album does not resolve to one current identifier: {album_id}",
                code="E_NOT_FOUND",
            )
        return matches[0]

    @staticmethod
    def _source_role_and_uti(path: Path) -> tuple[str, str]:
        canonical_types = {
            ".jpg": ("photo", "public.jpeg"),
            ".jpeg": ("photo", "public.jpeg"),
            ".png": ("photo", "public.png"),
            ".heic": ("photo", "public.heic"),
            ".heif": ("photo", "public.heif"),
            ".tif": ("photo", "public.tiff"),
            ".tiff": ("photo", "public.tiff"),
            ".gif": ("photo", "com.compuserve.gif"),
            ".mov": ("video", "com.apple.quicktime-movie"),
            ".mp4": ("video", "public.mpeg-4"),
            ".m4v": ("video", "com.apple.m4v-video"),
        }
        detected = canonical_types.get(path.suffix.casefold())
        if detected:
            return detected
        raise unsupported(
            f"Only ordinary single-resource images and videos are supported: {path.name}",
            code="E_RESOURCE_GROUP_UNSUPPORTED",
        )

    def plan_import(
        self,
        sources: Sequence[Path],
        *,
        album_id: str,
        output: Path,
        network: bool = False,
    ) -> dict[str, Any]:
        if not sources:
            raise usage_error("Import planning requires at least one source file.")
        snapshot = self._mutation_snapshot()
        album = self._album(album_id)
        library_assets = self.bridge.fetch_assets(None)
        asset_ids = [str(asset["local_identifier"]) for asset in library_assets]
        descriptors_by_id = {
            str(asset["local_identifier"]): asset.get("resource_descriptors", [])
            for asset in library_assets
        }
        resources = self.bridge.read_resources(asset_ids, network=network) if asset_ids else []
        grouped: dict[str, list[ResourceRecord]] = {
            local_identifier: [] for local_identifier in asset_ids
        }
        coverage_complete = True
        for resource in resources:
            grouped.setdefault(resource.local_identifier, []).append(resource)
            if resource.availability != "available" or not resource.sha256:
                coverage_complete = False
        if any(not grouped[local_identifier] for local_identifier in asset_ids):
            coverage_complete = False
        library_digests: dict[str, list[str]] = {}
        for local_identifier, members in grouped.items():
            expected_topology = sorted(
                (descriptor.get("role"), descriptor.get("uti"))
                for descriptor in descriptors_by_id.get(local_identifier, [])
            )
            observed_topology = sorted((member.role, member.uti) for member in members)
            members_complete = bool(members) and all(
                member.availability == "available"
                and re.fullmatch(r"[0-9a-f]{64}", member.sha256)
                for member in members
            )
            if observed_topology != expected_topology or not members_complete:
                coverage_complete = False
                continue
            if members:
                library_digests.setdefault(resource_set_digest(members), []).append(
                    local_identifier
                )

        items: list[dict[str, Any]] = []
        batch_digests: dict[str, str] = {}
        for index, source_path in enumerate(sources, start=1):
            source_path = source_path.expanduser()
            source = inspect_source(source_path)
            role, uti = self._source_role_and_uti(source_path)
            source["resource_role"] = role
            source["uti"] = uti
            digest = resource_set_digest([source_resource(source, role, uti)])
            exact = sorted(library_digests.get(digest, []))
            batch_duplicate_of = batch_digests.get(digest)
            if batch_duplicate_of:
                action = "reuse_batch_duplicate"
            elif len(exact) == 1:
                action = "reuse_exact_duplicate"
            elif len(exact) > 1:
                action = "blocked_ambiguous_duplicate"
            elif coverage_complete:
                action = "create_asset"
            else:
                action = "blocked_duplicate_coverage_incomplete"
            item = {
                "item_id": f"src_{index:06d}",
                "source": source,
                "resource_set_digest": digest,
                "planned_action": action,
                "exact_duplicate_ids": exact,
                "weak_candidate_ids": [],
                "batch_duplicate_of": batch_duplicate_of,
            }
            items.append(item)
            if action in {"create_asset", "reuse_exact_duplicate"}:
                batch_digests.setdefault(digest, item["item_id"])
        created_at = self.now().astimezone(UTC)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "manifest_type": "apple_photos_import",
            "manifest_id": f"imp_{self.id_factory()}",
            "created_at": format_time(created_at),
            "expires_at": format_time(created_at + timedelta(hours=24)),
            "generator": {"name": "apple-photos-skill", "version": __version__},
            "library_snapshot": snapshot.to_dict(),
            "library_snapshot_digest": snapshot.digest,
            "target_album": {
                "namespace": "photokit_local_identifier",
                "value": album.photokit_local_identifier,
                "title_at_plan": album.title,
            },
            "duplicate_policy": {
                "proof": "sha256_resource_set",
                "coverage_complete": coverage_complete,
                "on_single_exact": "reuse_and_add_to_album",
                "on_multiple_exact": "block",
            },
            "items": items,
        }
        return write_manifest(output, manifest)

    def apply_import(self, manifest_path: Path) -> OperationResult:
        manifest = load_manifest(manifest_path, expected_type="apple_photos_import")
        blocked = [
            item for item in manifest["items"] if item["planned_action"].startswith("blocked_")
        ]
        if blocked:
            raise stale("Import manifest contains blocked items and cannot be applied.")
        snapshot = self._mutation_snapshot()
        if snapshot.digest != manifest["library_snapshot_digest"]:
            raise stale(
                "System Photo Library snapshot changed after planning.",
                code="E_LIBRARY_SNAPSHOT_MISMATCH",
            )
        album_id = manifest["target_album"]["value"]
        self._album(album_id)
        run_id = self._run_id()
        started = self._time()
        item_results: list[dict[str, Any]] = []
        created_payload: list[dict[str, Any]] = []
        created_expected: dict[str, str] = {}
        created_evidence: dict[str, dict[str, Any]] = {}
        created_ids: dict[str, str] = {}
        reused: dict[str, str] = {}
        resolved: dict[str, str] = {}
        staging_root = self.state_dir / "staging"
        staging_root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f"{run_id}-", dir=staging_root))
        mutation_started = False
        try:
            with LibraryLock(self.state_dir, snapshot.digest):
                current = self._mutation_snapshot()
                if current.digest != snapshot.digest:
                    raise stale("Library snapshot changed during import preflight.")
                for item in manifest["items"]:
                    if item["planned_action"] == "create_asset":
                        source = Path(item["source"]["path"])
                        staged = staging / item["item_id"] / source.name
                        stage_source(item["source"], staged)
                        created_payload.append(
                            {
                                "item_id": item["item_id"],
                                "staged_path": str(staged),
                                "role": item["source"]["resource_role"],
                                "uti": item["source"]["uti"],
                            }
                        )
                        created_expected[item["item_id"]] = item["resource_set_digest"]
                    elif item["planned_action"] == "reuse_exact_duplicate":
                        reused[item["item_id"]] = item["exact_duplicate_ids"][0]
                if self._mutation_snapshot().digest != snapshot.digest:
                    raise stale("Library snapshot changed before the import transaction.")
                self._album(album_id)
                pending = OperationResult(
                    command="import.apply",
                    run_id=run_id,
                    ok=False,
                    status="outcome_unknown",
                    started_at=started,
                    finished_at=self._time(),
                    phase="commit_pending",
                    manifest_sha256=manifest["manifest_sha256"],
                    library_snapshot={"kind": snapshot.kind, "snapshot_digest": snapshot.digest},
                    counts={
                        "planned": len(manifest["items"]),
                        "unknown": len(manifest["items"]),
                    },
                    items=[
                        {"item_id": item["item_id"], "status": "outcome_unknown"}
                        for item in manifest["items"]
                    ],
                    artifacts={"manifest": str(manifest_path.resolve())},
                )
                self._write_receipt(pending)
                mutation_started = True
                created_result = (
                    self.bridge.import_assets(created_payload, album_id)
                    if created_payload
                    else {"status": "succeeded", "items": []}
                )
                created_evidence = {
                    item["item_id"]: item for item in created_result["items"]
                }
                if set(created_evidence) != set(created_expected):
                    raise ApplePhotosError(
                        "E_BACKEND_PROTOCOL",
                        "PhotoKit import result did not acknowledge every item.",
                        EXIT_IO,
                    )
                created_ids = {
                    item_id: item["local_identifier"]
                    for item_id, item in created_evidence.items()
                    if item["status"] == "created_identifier_known"
                }
                terminal_evidence = {
                    item_id: {
                        "status": item["status"],
                        "evidence": item["evidence"],
                    }
                    for item_id, item in created_evidence.items()
                    if item["status"]
                    in {"outcome_unknown", "not_attempted", "not_attempted_after_unknown"}
                }
                resolved.update(created_ids)
                for item in manifest["items"]:
                    duplicate_of = item.get("batch_duplicate_of")
                    if duplicate_of:
                        if duplicate_of in created_ids:
                            reused[item["item_id"]] = created_ids[duplicate_of]
                        elif duplicate_of in reused:
                            reused[item["item_id"]] = reused[duplicate_of]
                        elif duplicate_of in terminal_evidence:
                            parent_status = terminal_evidence[duplicate_of]["status"]
                            if parent_status == "not_attempted_after_unknown":
                                terminal_evidence[item["item_id"]] = {
                                    "status": "not_attempted_after_unknown",
                                    "evidence": (
                                        "batch_duplicate_parent_not_attempted_after_unknown"
                                    ),
                                }
                            elif parent_status == "not_attempted":
                                terminal_evidence[item["item_id"]] = {
                                    "status": "not_attempted",
                                    "evidence": "batch_duplicate_parent_not_attempted",
                                }
                            else:
                                terminal_evidence[item["item_id"]] = {
                                    "status": "outcome_unknown",
                                    "evidence": "batch_duplicate_parent_outcome_unknown",
                                }
                        else:
                            raise ApplePhotosError(
                                "E_BACKEND_PROTOCOL", "Batch duplicate did not resolve.", EXIT_IO
                            )
                resolved.update(reused)
                pending.phase = "commit_reported"
                pending.items = []
                for item in manifest["items"]:
                    item_id = item["item_id"]
                    if item_id in resolved:
                        if item_id in created_evidence:
                            evidence = created_evidence[item_id]["evidence"]
                        elif item.get("batch_duplicate_of"):
                            evidence = "batch_duplicate_parent"
                        else:
                            evidence = "exact_duplicate_sha256"
                        pending.items.append(
                            {
                                "item_id": item_id,
                                "local_identifier": resolved[item_id],
                                "status": "resolution_known",
                                "evidence": evidence,
                            }
                        )
                    else:
                        pending.items.append(
                            {
                                "item_id": item_id,
                                **terminal_evidence[item_id],
                            }
                        )
                pending.finished_at = self._time()
                self._write_receipt(pending)
                if terminal_evidence:
                    unknown_count = sum(
                        item["status"] == "outcome_unknown"
                        for item in terminal_evidence.values()
                    )
                    not_attempted_count = sum(
                        item["status"] in {"not_attempted", "not_attempted_after_unknown"}
                        for item in terminal_evidence.values()
                    )
                    terminal_status = (
                        "outcome_unknown" if unknown_count and not resolved else "partial"
                    )
                    result = OperationResult(
                        command="import.apply",
                        run_id=run_id,
                        ok=False,
                        status=terminal_status,
                        started_at=started,
                        finished_at=self._time(),
                        phase="verification_inconclusive",
                        manifest_sha256=manifest["manifest_sha256"],
                        library_snapshot={
                            "kind": snapshot.kind,
                            "snapshot_digest": snapshot.digest,
                        },
                        counts={
                            "planned": len(manifest["items"]),
                            "resolution_known": len(resolved),
                            "unknown": unknown_count,
                            "not_attempted": not_attempted_count,
                        },
                        items=pending.items,
                        artifacts={"manifest": str(manifest_path.resolve())},
                        errors=[
                            {
                                "code": (
                                    "E_OUTCOME_UNKNOWN"
                                    if unknown_count
                                    else "E_BACKEND_TRANSACTION"
                                ),
                                "message": (
                                    "PhotoKit stopped before a later import transaction began."
                                    if not unknown_count
                                    else (
                                        "PhotoKit stopped after an uncertain import item; "
                                        "do not retry automatically."
                                    )
                                ),
                                "exception_type": "PhotoKitMutationEvidence",
                                "detail": {
                                    "unknown_item_ids": sorted(
                                        item_id
                                        for item_id, item in terminal_evidence.items()
                                        if item["status"] == "outcome_unknown"
                                    ),
                                    "not_attempted_item_ids": sorted(
                                        item_id
                                        for item_id, item in terminal_evidence.items()
                                        if item["status"]
                                        in {"not_attempted", "not_attempted_after_unknown"}
                                    ),
                                },
                            }
                        ],
                    )
                    self._write_receipt(result)
                    return result
                if reused:
                    self.bridge.add_assets_to_album(sorted(set(reused.values())), album_id)
                pending.finished_at = self._time()
                self._write_receipt(pending)
                identifiers = sorted(set(resolved.values()))
                observed_resources = self.bridge.read_resources(identifiers, network=False)
                grouped: dict[str, list[ResourceRecord]] = {
                    identifier: [] for identifier in identifiers
                }
                for resource in observed_resources:
                    grouped.setdefault(resource.local_identifier, []).append(resource)
                verification = {
                    item["local_identifier"]: item
                    for item in self.bridge.verify_assets(
                        identifiers, album_id=album_id, expect_present=True
                    )
                }
                for item in manifest["items"]:
                    identifier = resolved[item["item_id"]]
                    expected_digest = item["resource_set_digest"]
                    observed = grouped.get(identifier, [])
                    resources_ok = bool(observed) and all(
                        member.availability == "available"
                        and re.fullmatch(r"[0-9a-f]{64}", member.sha256)
                        for member in observed
                    )
                    resources_ok = resources_ok and (
                        resource_set_digest(observed) == expected_digest
                    )
                    membership_ok = bool(verification.get(identifier, {}).get("in_album"))
                    ok = resources_ok and membership_ok
                    if item["planned_action"] == "create_asset":
                        status = "imported_verified" if ok else "imported_integrity_failed"
                    else:
                        status = "reused_verified" if ok else "imported_integrity_failed"
                    item_results.append(
                        {
                            "item_id": item["item_id"],
                            "local_identifier": identifier,
                            "status": status,
                            "resource_digest_match": resources_ok,
                            "album_membership_verified": membership_ok,
                        }
                    )
        except (Exception, KeyboardInterrupt) as exc:
            if not mutation_started:
                raise
            error = (
                exc.to_dict()
                if isinstance(exc, ApplePhotosError)
                else {
                    "code": "E_OUTCOME_UNKNOWN",
                    "message": "Mutation outcome could not be established.",
                    "exception_type": type(exc).__name__,
                }
            )
            commit_rejected = (
                isinstance(exc, ApplePhotosError)
                and exc.code
                in {
                    "E_BACKEND_PROTOCOL",
                    "E_PERMISSION_PHOTOS",
                    "E_NOT_FOUND",
                    "E_RESOURCE_UNAVAILABLE",
                    "E_PLAN_STALE",
                    "E_AUTH_EXPIRED",
                }
                and isinstance(exc.detail, dict)
                and exc.detail.get("mutation_phase") == "not_started"
            )
            if commit_rejected:
                created_identifier_set = set(created_ids.values())
                rejected_items = []
                for item in manifest["items"]:
                    item_id = item["item_id"]
                    identifier = resolved.get(item_id)
                    if identifier in created_identifier_set:
                        rejected_items.append(
                            {
                                "item_id": item_id,
                                "local_identifier": identifier,
                                "status": "resolution_known",
                                "evidence": (
                                    created_evidence[item_id]["evidence"]
                                    if item_id in created_evidence
                                    else "batch_duplicate_parent"
                                ),
                            }
                        )
                    else:
                        rejected_items.append(
                            {"item_id": item_id, "status": "not_attempted"}
                        )
                known_count = sum(
                    item["status"] == "resolution_known" for item in rejected_items
                )
            else:
                rejected_items = [
                    {
                        "item_id": item["item_id"],
                        **(
                            {"local_identifier": resolved[item["item_id"]]}
                            if item["item_id"] in resolved
                            else {}
                        ),
                        "status": "outcome_unknown",
                    }
                    for item in manifest["items"]
                ]
                known_count = 0
            result = OperationResult(
                command="import.apply",
                run_id=run_id,
                ok=False,
                status="partial" if commit_rejected else "outcome_unknown",
                started_at=started,
                finished_at=self._time(),
                phase="commit_pending" if commit_rejected else "verification_inconclusive",
                manifest_sha256=manifest["manifest_sha256"],
                library_snapshot={"kind": snapshot.kind, "snapshot_digest": snapshot.digest},
                counts={
                    "planned": len(manifest["items"]),
                    **(
                        {
                            "resolution_known": known_count,
                            "not_attempted": len(manifest["items"]) - known_count,
                        }
                        if commit_rejected
                        else {"unknown": len(manifest["items"])}
                    ),
                },
                items=rejected_items,
                artifacts={"manifest": str(manifest_path.resolve())},
                errors=[error],
            )
            self._write_receipt(result)
            return result
        finally:
            import shutil

            shutil.rmtree(staging, ignore_errors=True)
        failures = sum(item["status"] == "imported_integrity_failed" for item in item_results)
        result = OperationResult(
            command="import.apply",
            run_id=run_id,
            ok=failures == 0,
            status="succeeded" if failures == 0 else "partial",
            started_at=started,
            finished_at=self._time(),
            phase="verified",
            manifest_sha256=manifest["manifest_sha256"],
            library_snapshot={"kind": snapshot.kind, "snapshot_digest": snapshot.digest},
            counts={
                "planned": len(manifest["items"]),
                "created_verified": sum(
                    item["status"] == "imported_verified" for item in item_results
                ),
                "reused_verified": sum(
                    item["status"] == "reused_verified" for item in item_results
                ),
                "failed": failures,
            },
            items=item_results,
            artifacts={"manifest": str(manifest_path.resolve())},
        )
        self._write_receipt(result)
        return result

    @staticmethod
    def _delete_expected(asset: dict[str, Any]) -> dict[str, Any]:
        descriptors = asset.get("resource_descriptors", [])
        return {
            "original_filename": asset.get("original_filename"),
            "media_type": asset.get("media_type"),
            "date_taken": asset.get("date_taken"),
            "date_modified": asset.get("date_modified"),
            "width": asset.get("width"),
            "height": asset.get("height"),
            "resource_descriptor_digest": sha256_digest(descriptors),
            "in_trash": bool(asset.get("in_trash", False)),
        }

    def _photo_resource_digests(
        self, identifiers: Sequence[str], *, network: bool
    ) -> dict[str, set[str]]:
        digests: dict[str, set[str]] = {}
        frozen = list(dict.fromkeys(identifiers))
        for offset in range(0, len(frozen), 50):
            chunk = frozen[offset : offset + 50]
            resources = self.bridge.read_resources(chunk, network=network)
            grouped = {
                identifier: [
                    resource
                    for resource in resources
                    if resource.local_identifier == identifier
                ]
                for identifier in chunk
            }
            if any(
                len(grouped[identifier]) != 1
                or grouped[identifier][0].availability != "available"
                or grouped[identifier][0].role != "photo"
                or not re.fullmatch(
                    r"(?:sha256:)?[0-9a-f]{64}", grouped[identifier][0].sha256
                )
                for identifier in chunk
            ) or any(resource.local_identifier not in grouped for resource in resources):
                raise stale(
                    "Pixel deletion requires exactly one available photo resource per asset.",
                    code="E_RESOURCE_COVERAGE_INCOMPLETE",
                )
            for identifier, records in grouped.items():
                digests[identifier] = {
                    "sha256:" + records[0].sha256.removeprefix("sha256:")
                }
        return digests

    @staticmethod
    def _verify_delete_source_ownership(
        items: Sequence[dict[str, Any]], resource_digests: dict[str, set[str]]
    ) -> None:
        for item in items:
            proof = item["pixel_similarity_proof"]
            candidate = item["local_identifier"]
            keeper = proof["keeper_local_identifier"]
            if proof["candidate_source_sha256"] not in resource_digests.get(candidate, set()):
                raise stale(
                    f"Compared candidate bytes are not a current PhotoKit resource: {candidate}.",
                    code="E_PIXEL_SOURCE_MISMATCH",
                )
            if proof["keeper_source_sha256"] not in resource_digests.get(keeper, set()):
                raise stale(
                    f"Compared keeper bytes are not a current PhotoKit resource: {keeper}.",
                    code="E_PIXEL_SOURCE_MISMATCH",
                )

    def plan_delete(
        self,
        evidence_report: Path,
        pair_manifest: Path,
        *,
        output: Path,
        network: bool = False,
    ) -> dict[str, Any]:
        report = load_similarity_report(evidence_report)
        if len(report["items"]) > 50:
            raise unsupported(
                "Delete plans are limited to 50 pixel pairs per authorization.",
                code="E_DELETE_BATCH_TOO_LARGE",
            )
        revalidate_similarity_report(report, pair_manifest)
        if report["counts"]["byte_identical"]:
            raise unsupported(
                "Byte-identical duplicate deletion is not supported.",
                code="E_PURE_DUPLICATE_UNSUPPORTED",
            )
        if not report["delete_authorizing"]:
            raise stale(
                "Pixel similarity evidence does not authorize deletion.",
                code="E_PIXEL_GATE_FAILED",
            )
        compared = report["items"]
        candidates = [item["candidate_local_identifier"] for item in compared]
        keepers = [item["keeper_local_identifier"] for item in compared]
        frozen = sorted(set(candidates + keepers))
        snapshot = self._mutation_snapshot()
        assets = self.bridge.fetch_assets(frozen)
        indexed = {str(asset["local_identifier"]): asset for asset in assets}
        missing = [identifier for identifier in frozen if identifier not in indexed]
        if missing:
            raise stale("One or more delete targets do not exist.", code="E_NOT_FOUND")
        resource_digests = self._photo_resource_digests(frozen, network=network)
        items = []
        for index, evidence in enumerate(compared, start=1):
            identifier = evidence["candidate_local_identifier"]
            keeper_identifier = evidence["keeper_local_identifier"]
            if (
                indexed[identifier].get("media_type") != "image"
                or indexed[keeper_identifier].get("media_type") != "image"
                or len(indexed[identifier].get("resource_descriptors", [])) != 1
                or len(indexed[keeper_identifier].get("resource_descriptors", [])) != 1
                or indexed[identifier]["resource_descriptors"][0].get("role") != "photo"
                or indexed[keeper_identifier]["resource_descriptors"][0].get("role") != "photo"
            ):
                raise unsupported(
                    "Pixel deletion supports single-resource still-image PhotoKit assets only.",
                    code="E_SIMILARITY_MEDIA_UNSUPPORTED",
                )
            candidate_digest = evidence["left"]["sha256"]
            keeper_digest = evidence["right"]["sha256"]
            if candidate_digest not in resource_digests.get(identifier, set()):
                raise stale(
                    f"Compared candidate bytes are not a current PhotoKit resource: {identifier}.",
                    code="E_PIXEL_SOURCE_MISMATCH",
                )
            if keeper_digest not in resource_digests.get(keeper_identifier, set()):
                raise stale(
                    "Compared keeper bytes are not a current PhotoKit resource: "
                    f"{keeper_identifier}.",
                    code="E_PIXEL_SOURCE_MISMATCH",
                )
            expected = self._delete_expected(indexed[identifier])
            if expected["in_trash"]:
                raise stale(f"Delete target is already in Recently Deleted: {identifier}")
            keeper_expected = self._delete_expected(indexed[keeper_identifier])
            if keeper_expected["in_trash"]:
                raise stale(f"Pixel keeper is already in Recently Deleted: {keeper_identifier}")
            items.append(
                {
                    "item_id": f"del_{index:06d}",
                    "local_identifier": identifier,
                    "expected": expected,
                    "pixel_similarity_proof": {
                        "pair_id": evidence["pair_id"],
                        "keeper_local_identifier": keeper_identifier,
                        "keeper_expected": keeper_expected,
                        "candidate_source_sha256": candidate_digest,
                        "keeper_source_sha256": keeper_digest,
                        "bytes_different": not evidence["byte_identical"],
                        "dimensions": {
                            "width": evidence["left"]["decode"]["width"],
                            "height": evidence["left"]["decode"]["height"],
                        },
                        "metrics": evidence["metrics"],
                    },
                    "planned_action": "move_to_recently_deleted",
                }
            )
        created_at = self.now().astimezone(UTC)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "manifest_type": "apple_photos_delete",
            "manifest_id": f"del_{self.id_factory()}",
            "created_at": format_time(created_at),
            "expires_at": format_time(created_at + timedelta(hours=24)),
            "generator": {"name": "apple-photos-skill", "version": __version__},
            "library_snapshot": snapshot.to_dict(),
            "library_snapshot_digest": snapshot.digest,
            "effect": "move_to_recently_deleted",
            "delete_policy": {
                "proof": "pixel_similarity",
                "pure_byte_duplicates": "unsupported",
                "report_sha256": report["report_sha256"],
                "source_manifest_sha256": report["source_manifest_sha256"],
                "pair_manifest_path": str(pair_manifest.resolve()),
                "network_access_allowed": network,
                "policy": report["policy"],
            },
            "items": items,
        }
        manifest["evidence_attestation"] = AuthorizationService(
            self.state_dir
        ).attest_delete_evidence(manifest)
        return write_manifest(output, manifest)

    def apply_delete(
        self,
        manifest_path: Path,
        token_path: Path,
        authorization: AuthorizationService,
        replay: ReplayStore,
    ) -> OperationResult:
        from apple_photos_cli.authorization import load_token

        manifest = load_manifest(manifest_path, expected_type="apple_photos_delete")
        authorization.verify_delete_evidence(manifest)
        token = load_token(token_path)
        claims = authorization.verify(token, manifest)
        if replay.is_consumed(claims["nonce"]):
            raise ApplePhotosError(
                "E_AUTH_REPLAY", "Authorization token was already consumed.", EXIT_AUTH
            )
        snapshot = self._mutation_snapshot()
        if snapshot.digest != manifest["library_snapshot_digest"]:
            raise stale(
                "System Photo Library snapshot changed after planning.",
                code="E_LIBRARY_SNAPSHOT_MISMATCH",
            )
        identifiers = [item["local_identifier"] for item in manifest["items"]]
        run_id = self._run_id()
        started = self._time()
        mutation_started = False
        pending_written = False
        try:
            with LibraryLock(self.state_dir, snapshot.digest):
                if self._mutation_snapshot().digest != snapshot.digest:
                    raise stale("Library snapshot changed during delete preflight.")
                pending = OperationResult(
                    command="delete.apply",
                    run_id=run_id,
                    ok=False,
                    status="outcome_unknown",
                    started_at=started,
                    finished_at=self._time(),
                    phase="commit_pending",
                    manifest_sha256=manifest["manifest_sha256"],
                    library_snapshot={"kind": snapshot.kind, "snapshot_digest": snapshot.digest},
                    counts={
                        "planned": len(manifest["items"]),
                        "unknown": len(manifest["items"]),
                    },
                    items=[
                        {
                            "item_id": item["item_id"],
                            "local_identifier": item["local_identifier"],
                            "status": "outcome_unknown",
                        }
                        for item in manifest["items"]
                    ],
                    artifacts={"manifest": str(manifest_path.resolve())},
                )
                self._write_receipt(pending)
                pending_written = True
                authorization.verify(token, manifest)
                replay.consume(claims["nonce"], manifest["manifest_sha256"], self._time())
                mutation_started = True
                acknowledged = self.bridge.delete_assets(
                    manifest["items"],
                    authorization_expires_at=claims["expires_at"],
                    manifest_sha256=manifest["manifest_sha256"],
                    evidence_attestation=manifest["evidence_attestation"],
                    authorization_token=token,
                    network_access_allowed=manifest["delete_policy"][
                        "network_access_allowed"
                    ],
                )
                if acknowledged["local_identifiers"] != identifiers:
                    raise ApplePhotosError(
                        "E_OUTCOME_UNKNOWN",
                        "Delete response identifiers did not exactly match the request.",
                        EXIT_PARTIAL,
                    )
                pending.phase = "commit_reported"
                pending.counts = {
                    "planned": len(manifest["items"]),
                    "acknowledged": len(identifiers),
                    "unknown": len(identifiers),
                }
                pending.finished_at = self._time()
                self._write_receipt(pending)
                verified = {
                    item["local_identifier"]: item
                    for item in self.bridge.verify_assets(identifiers, expect_present=False)
                }
        except (Exception, KeyboardInterrupt) as exc:
            if not mutation_started:
                if pending_written:
                    error = (
                        exc.to_dict()
                        if isinstance(exc, ApplePhotosError)
                        else {
                            "code": "E_LOCAL_IO",
                            "message": "Delete precommit processing failed.",
                            "exception_type": type(exc).__name__,
                        }
                    )
                    rejected = OperationResult(
                        command="delete.apply",
                        run_id=run_id,
                        ok=False,
                        status="partial",
                        started_at=started,
                        finished_at=self._time(),
                        phase="commit_pending",
                        manifest_sha256=manifest["manifest_sha256"],
                        library_snapshot={
                            "kind": snapshot.kind,
                            "snapshot_digest": snapshot.digest,
                        },
                        counts={
                            "planned": len(manifest["items"]),
                            "not_attempted": len(manifest["items"]),
                        },
                        items=[
                            {
                                "item_id": item["item_id"],
                                "local_identifier": item["local_identifier"],
                                "status": "not_attempted",
                            }
                            for item in manifest["items"]
                        ],
                        artifacts={"manifest": str(manifest_path.resolve())},
                        errors=[error],
                    )
                    self._write_receipt(rejected)
                raise
            error = (
                exc.to_dict()
                if isinstance(exc, ApplePhotosError)
                else {
                    "code": "E_OUTCOME_UNKNOWN",
                    "message": "Delete outcome could not be established.",
                    "exception_type": type(exc).__name__,
                }
            )
            commit_rejected = (
                isinstance(exc, ApplePhotosError)
                and exc.code
                in {
                    "E_BACKEND_PROTOCOL",
                    "E_PERMISSION_PHOTOS",
                    "E_NOT_FOUND",
                    "E_RESOURCE_UNAVAILABLE",
                    "E_PLAN_STALE",
                    "E_PIXEL_SOURCE_MISMATCH",
                    "E_AUTH_EXPIRED",
                    "E_AUTH_REPLAY",
                }
                and isinstance(exc.detail, dict)
                and exc.detail.get("mutation_phase") == "not_started"
            )
            result = OperationResult(
                command="delete.apply",
                run_id=run_id,
                ok=False,
                status="partial" if commit_rejected else "outcome_unknown",
                started_at=started,
                finished_at=self._time(),
                phase="commit_pending" if commit_rejected else "verification_inconclusive",
                manifest_sha256=manifest["manifest_sha256"],
                library_snapshot={"kind": snapshot.kind, "snapshot_digest": snapshot.digest},
                counts={
                    "planned": len(manifest["items"]),
                    "not_attempted" if commit_rejected else "unknown": len(manifest["items"]),
                },
                items=[
                    {
                        "item_id": item["item_id"],
                        "local_identifier": item["local_identifier"],
                        "status": (
                            "not_attempted" if commit_rejected else "outcome_unknown"
                        ),
                    }
                    for item in manifest["items"]
                ],
                artifacts={"manifest": str(manifest_path.resolve())},
                errors=[error],
            )
            self._write_receipt(result)
            return result
        item_results = []
        for item in manifest["items"]:
            identifier = item["local_identifier"]
            absent = verified.get(identifier, {}).get("present") is False
            item_results.append(
                {
                    "item_id": item["item_id"],
                    "local_identifier": identifier,
                    "status": "deleted_confirmed" if absent else "outcome_unknown",
                }
            )
        unknown = sum(item["status"] == "outcome_unknown" for item in item_results)
        status = (
            "succeeded"
            if unknown == 0
            else ("outcome_unknown" if unknown == len(item_results) else "partial")
        )
        result = OperationResult(
            command="delete.apply",
            run_id=run_id,
            ok=unknown == 0,
            status=status,
            started_at=started,
            finished_at=self._time(),
            phase="verified" if unknown == 0 else "verification_inconclusive",
            manifest_sha256=manifest["manifest_sha256"],
            library_snapshot={"kind": snapshot.kind, "snapshot_digest": snapshot.digest},
            counts={
                "planned": len(item_results),
                "deleted_confirmed": len(item_results) - unknown,
                "unknown": unknown,
            },
            items=item_results,
            artifacts={"manifest": str(manifest_path.resolve())},
        )
        self._write_receipt(result)
        return result

    def _write_receipt(self, result: OperationResult) -> None:
        runs = self.state_dir / "runs"
        existed = runs.is_dir()
        runs.mkdir(parents=True, exist_ok=True)
        if not existed:
            fsync_directory(self.state_dir)
        value = result.to_dict()
        validate_schema(value, "mutation-receipt-v1.schema.json")
        atomic_write_json(runs / f"{result.run_id}.json", value, mode=0o600)

    def status(self, run_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"run_[A-Za-z0-9_-]{1,128}", run_id):
            raise usage_error("Run identifier is invalid.", code="E_SCHEMA_INVALID")
        path = self.state_dir / "runs" / f"{run_id}.json"
        try:
            import json

            value = json.loads(path.read_text(encoding="utf-8"))
            validate_schema(value, "mutation-receipt-v1.schema.json")
            return value
        except OSError as exc:
            raise stale(f"Run receipt not found: {run_id}", code="E_NOT_FOUND") from exc
        except json.JSONDecodeError as exc:
            raise ApplePhotosError(
                "E_LOCAL_IO", f"Run receipt is not valid JSON: {run_id}", EXIT_IO
            ) from exc
