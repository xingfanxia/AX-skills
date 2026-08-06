from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from apple_photos_cli import PROTOCOL_VERSION
from apple_photos_cli.errors import (
    EXIT_BACKEND,
    EXIT_IO,
    EXIT_PARTIAL,
    ApplePhotosError,
    unsupported,
)
from apple_photos_cli.models import LibrarySnapshot, PhotoKitAlbumRecord, ResourceRecord

Runner = Callable[..., subprocess.CompletedProcess[str]]


class PhotoKitProcessBridge:
    def __init__(
        self,
        executable: Path | None,
        *,
        runner: Runner = subprocess.run,
        timeout: float = 300,
    ) -> None:
        self.executable = executable
        self.runner = runner
        self.timeout = timeout

    def _request(self, operation: str, payload: dict[str, Any] | None = None) -> Any:
        mutation = operation in {"import-assets", "add-assets-to-album", "delete-assets"}
        if self.executable is None:
            raise unsupported(
                "PhotoKit helper is not configured. Build it and set APPLE_PHOTOS_HELPER.",
                code="E_CAPABILITY_UNSUPPORTED",
            )
        if not self.executable.is_file():
            raise unsupported(
                f"PhotoKit helper does not exist: {self.executable}",
                code="E_CAPABILITY_UNSUPPORTED",
            )
        request = {
            "protocol_version": PROTOCOL_VERSION,
            "operation": operation,
            "payload": payload or {},
        }
        allowed_environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"HOME", "PATH", "TMPDIR", "LANG", "LC_ALL"}
        }
        try:
            completed = self.runner(
                [str(self.executable)],
                input=json.dumps(request, separators=(",", ":")) + "\n",
                text=True,
                capture_output=True,
                check=False,
                timeout=None if operation == "delete-assets" else self.timeout,
                env=allowed_environment,
            )
        except subprocess.TimeoutExpired as exc:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN" if mutation else "E_BACKEND_PROTOCOL",
                (
                    "PhotoKit helper timed out after a mutation may have started."
                    if mutation
                    else "PhotoKit helper timed out."
                ),
                EXIT_PARTIAL if mutation else EXIT_IO,
                {"operation": operation},
            ) from exc
        except OSError as exc:
            raise ApplePhotosError(
                "E_BACKEND_PROTOCOL",
                "PhotoKit helper could not be started.",
                EXIT_IO,
                {
                    "operation": operation,
                    "os_error": str(exc),
                    **({"mutation_phase": "not_started"} if mutation else {}),
                },
            ) from exc
        if completed.returncode != 0:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN" if mutation else "E_BACKEND_PROTOCOL",
                (
                    "PhotoKit helper exited before reporting a mutation outcome."
                    if mutation
                    else "PhotoKit helper exited with a nonzero status."
                ),
                EXIT_PARTIAL if mutation else EXIT_IO,
                {
                    "operation": operation,
                    "returncode": completed.returncode,
                    "stderr": completed.stderr[-4000:],
                },
            )
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if len(lines) != 1:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN" if mutation else "E_BACKEND_PROTOCOL",
                (
                    "PhotoKit helper returned an ambiguous response after mutation dispatch."
                    if mutation
                    else "PhotoKit helper must return exactly one JSON response."
                ),
                EXIT_PARTIAL if mutation else EXIT_IO,
                {"operation": operation, "line_count": len(lines)},
            )
        try:
            response = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN" if mutation else "E_BACKEND_PROTOCOL",
                "PhotoKit helper returned malformed JSON.",
                EXIT_PARTIAL if mutation else EXIT_IO,
            ) from exc
        if not isinstance(response, dict):
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN" if mutation else "E_BACKEND_PROTOCOL",
                "PhotoKit helper response root must be an object.",
                EXIT_PARTIAL if mutation else EXIT_IO,
            )
        if response.get("protocol_version") != PROTOCOL_VERSION:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN" if mutation else "E_BACKEND_PROTOCOL",
                "PhotoKit helper protocol version does not match.",
                EXIT_PARTIAL if mutation else EXIT_IO,
            )
        if response.get("ok") is not True:
            error = response.get("error") or {}
            if not isinstance(error, dict):
                raise ApplePhotosError(
                    "E_OUTCOME_UNKNOWN" if mutation else "E_BACKEND_PROTOCOL",
                    "PhotoKit helper error envelope is malformed.",
                    EXIT_PARTIAL if mutation else EXIT_IO,
                )
            code = error.get("code", "E_BACKEND_TRANSACTION")
            message = error.get("message", "PhotoKit helper reported an error.")
            detail = error.get("detail")
            if (
                not isinstance(code, str)
                or not isinstance(message, str)
                or (detail is not None and not isinstance(detail, dict))
            ):
                raise ApplePhotosError(
                    "E_OUTCOME_UNKNOWN" if mutation else "E_BACKEND_PROTOCOL",
                    "PhotoKit helper error envelope has malformed fields.",
                    EXIT_PARTIAL if mutation else EXIT_IO,
                )
            if mutation:
                known_precommit_codes = {
                    "E_BACKEND_PROTOCOL",
                    "E_PERMISSION_PHOTOS",
                    "E_NOT_FOUND",
                    "E_RESOURCE_UNAVAILABLE",
                    "E_PLAN_STALE",
                    "E_AUTH_EXPIRED",
                    "E_AUTH_REPLAY",
                }
                phase = detail.get("mutation_phase") if isinstance(detail, dict) else None
                valid_phase = phase in {"not_started", "commit_attempted"}
                phase_matches_code = not (
                    (code == "E_BACKEND_TRANSACTION" and phase != "commit_attempted")
                    or (code in known_precommit_codes and phase != "not_started")
                )
                if not valid_phase or not phase_matches_code:
                    raise ApplePhotosError(
                        "E_OUTCOME_UNKNOWN",
                        "PhotoKit helper mutation phase is malformed or contradictory.",
                        EXIT_PARTIAL,
                    )
            exit_code = EXIT_BACKEND if code == "E_BACKEND_TRANSACTION" else EXIT_IO
            raise ApplePhotosError(code, message, exit_code, detail)
        if "result" not in response:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN" if mutation else "E_BACKEND_PROTOCOL",
                "PhotoKit helper response has no result.",
                EXIT_PARTIAL if mutation else EXIT_IO,
            )
        return response["result"]

    @staticmethod
    def _object(
        result: Any, operation: str, *, mutation_ambiguity: bool = False
    ) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN" if mutation_ambiguity else "E_BACKEND_PROTOCOL",
                f"PhotoKit {operation} result must be an object.",
                EXIT_PARTIAL if mutation_ambiguity else EXIT_IO,
            )
        return result

    @classmethod
    def _array(
        cls,
        result: Any,
        key: str,
        operation: str,
        *,
        mutation_ambiguity: bool = False,
    ) -> list[Any]:
        value = cls._object(
            result, operation, mutation_ambiguity=mutation_ambiguity
        ).get(key)
        if not isinstance(value, list):
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN" if mutation_ambiguity else "E_BACKEND_PROTOCOL",
                f"PhotoKit {operation} result requires a {key} array.",
                EXIT_PARTIAL if mutation_ambiguity else EXIT_IO,
            )
        return value

    def probe(self) -> LibrarySnapshot:
        result = self._request("probe-library")
        snapshot = self._object(result, "probe-library").get("library_snapshot")
        if not isinstance(snapshot, dict):
            raise ApplePhotosError(
                "E_BACKEND_PROTOCOL", "PhotoKit probe requires library_snapshot.", EXIT_IO
            )
        return LibrarySnapshot.from_dict(snapshot)

    def list_albums(self) -> list[PhotoKitAlbumRecord]:
        result = self._request("list-albums")
        records = []
        for album in self._array(result, "albums", "list-albums"):
            if not isinstance(album, dict):
                raise ApplePhotosError(
                    "E_BACKEND_PROTOCOL", "PhotoKit album record must be an object.", EXIT_IO
                )
            try:
                records.append(
                    PhotoKitAlbumRecord(
                        photokit_local_identifier=str(album["local_identifier"]),
                        title=str(album["title"]),
                        asset_count=int(album["asset_count"]),
                        can_add_assets=bool(album.get("can_add_assets", False)),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ApplePhotosError(
                    "E_BACKEND_PROTOCOL", "PhotoKit album record is malformed.", EXIT_IO
                ) from exc
        return records

    def fetch_assets(self, local_identifiers: Sequence[str] | None = None) -> list[dict[str, Any]]:
        result = self._request(
            "fetch-assets",
            {
                "local_identifiers": list(local_identifiers or []),
                "include_all": local_identifiers is None,
            },
        )
        assets = self._array(result, "assets", "fetch-assets")
        if not all(
            isinstance(asset, dict)
            and isinstance(asset.get("local_identifier"), str)
            and isinstance(asset.get("resource_descriptors"), list)
            for asset in assets
        ):
            raise ApplePhotosError("E_BACKEND_PROTOCOL", "Asset record is malformed.", EXIT_IO)
        return assets

    def read_resources(
        self,
        local_identifiers: Sequence[str],
        *,
        network: bool = False,
        output_dir: Path | None = None,
    ) -> list[ResourceRecord]:
        result = self._request(
            "read-resources",
            {
                "local_identifiers": list(local_identifiers),
                "network_access_allowed": network,
                "output_directory": str(output_dir) if output_dir else None,
            },
        )
        resources = self._array(result, "resources", "read-resources")
        if not all(isinstance(resource, dict) for resource in resources):
            raise ApplePhotosError("E_BACKEND_PROTOCOL", "Resource record is malformed.", EXIT_IO)
        try:
            return [ResourceRecord(**resource) for resource in resources]
        except (TypeError, ValueError) as exc:
            raise ApplePhotosError(
                "E_BACKEND_PROTOCOL", "Resource record fields are malformed.", EXIT_IO
            ) from exc

    def import_assets(self, items: list[dict[str, Any]], album_id: str) -> dict[str, Any]:
        result = self._request("import-assets", {"items": items, "album_id": album_id})
        root = self._object(result, "import-assets", mutation_ambiguity=True)
        values = self._array(root, "items", "import-assets", mutation_ambiguity=True)
        status = root.get("status")
        if status not in {"succeeded", "partial", "outcome_unknown"}:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN", "Import result status is malformed.", EXIT_PARTIAL
            )
        normalized: list[dict[str, Any]] = []
        for item in values:
            if not isinstance(item, dict):
                raise ApplePhotosError(
                    "E_OUTCOME_UNKNOWN", "Import result item is malformed.", EXIT_PARTIAL
                )
            item_id = item.get("item_id")
            item_status = item.get("status")
            identifier = item.get("local_identifier")
            evidence = item.get("evidence")
            evidence_matches_status = (
                item_status == "created_identifier_known"
                and evidence == "photokit_placeholder"
            ) or (
                item_status == "outcome_unknown"
                and evidence
                in {
                    "placeholder_missing_after_creation_registered",
                    "transaction_outcome_unknown",
                }
            ) or (
                item_status == "not_attempted"
                and evidence in {"transaction_not_started", "not_attempted"}
            ) or (
                item_status == "not_attempted_after_unknown"
                and evidence == "not_attempted_after_unknown"
            )
            valid = (
                isinstance(item_id, str)
                and bool(item_id)
                and item_status
                in {
                    "created_identifier_known",
                    "outcome_unknown",
                    "not_attempted",
                    "not_attempted_after_unknown",
                }
                and isinstance(evidence, str)
                and bool(evidence)
                and evidence_matches_status
                and (
                    (
                        item_status == "created_identifier_known"
                        and isinstance(identifier, str)
                        and bool(identifier)
                    )
                    or (
                        item_status
                        in {"outcome_unknown", "not_attempted", "not_attempted_after_unknown"}
                        and identifier is None
                    )
                )
            )
            if not valid:
                raise ApplePhotosError(
                    "E_OUTCOME_UNKNOWN", "Import result item is malformed.", EXIT_PARTIAL
                )
            normalized.append(
                {
                    "item_id": item_id,
                    "local_identifier": identifier,
                    "status": item_status,
                    "evidence": evidence,
                }
            )
        if len({item["item_id"] for item in normalized}) != len(normalized):
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN", "Import result contains duplicate item IDs.", EXIT_PARTIAL
            )
        expected_item_ids = [item.get("item_id") for item in items]
        returned_item_ids = [item["item_id"] for item in normalized]
        if returned_item_ids != expected_item_ids:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN",
                "Import result did not acknowledge the requested item sequence.",
                EXIT_PARTIAL,
            )
        stop_kind: str | None = None
        for item in normalized:
            if stop_kind == "unknown" and item["status"] != "not_attempted_after_unknown":
                raise ApplePhotosError(
                    "E_OUTCOME_UNKNOWN",
                    "Import result continued after an uncertain item.",
                    EXIT_PARTIAL,
                )
            if stop_kind == "known" and item["status"] != "not_attempted":
                raise ApplePhotosError(
                    "E_OUTCOME_UNKNOWN",
                    "Import result continued after a known precommit rejection.",
                    EXIT_PARTIAL,
                )
            if item["status"] == "not_attempted_after_unknown" and stop_kind != "unknown":
                raise ApplePhotosError(
                    "E_OUTCOME_UNKNOWN",
                    "Import result marked an item not attempted before any uncertainty.",
                    EXIT_PARTIAL,
                )
            if item["status"] == "outcome_unknown":
                stop_kind = "unknown"
            if item["status"] == "not_attempted":
                stop_kind = "known"
        known = sum(item["status"] == "created_identifier_known" for item in normalized)
        unknown = sum(
            item["status"] in {"outcome_unknown", "not_attempted_after_unknown"}
            for item in normalized
        )
        not_attempted = sum(item["status"] == "not_attempted" for item in normalized)
        expected_status = (
            ("outcome_unknown" if known == 0 else "partial")
            if unknown
            else ("partial" if not_attempted else "succeeded")
        )
        if status != expected_status:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN", "Import result status contradicts item evidence.", EXIT_PARTIAL
            )
        return {"status": status, "items": normalized}

    def add_assets_to_album(
        self, local_identifiers: Sequence[str], album_id: str
    ) -> dict[str, Any]:
        return self._request(
            "add-assets-to-album",
            {"local_identifiers": list(local_identifiers), "album_id": album_id},
        )

    def delete_assets(
        self,
        items: Sequence[dict[str, Any]],
        *,
        authorization_expires_at: str,
        manifest_sha256: str,
        evidence_attestation: dict[str, Any],
        authorization_token: dict[str, Any],
        network_access_allowed: bool = False,
    ) -> dict[str, Any]:
        result = self._request(
            "delete-assets",
            {
                "items": list(items),
                "authorization_expires_at": authorization_expires_at,
                "manifest_sha256": manifest_sha256,
                "evidence_attestation": evidence_attestation,
                "authorization_token": authorization_token,
                "network_access_allowed": network_access_allowed,
            },
        )
        value = self._object(result, "delete-assets", mutation_ambiguity=True)
        identifiers = value.get("local_identifiers")
        if not isinstance(identifiers, list) or not all(
            isinstance(identifier, str) for identifier in identifiers
        ):
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN",
                "PhotoKit delete-assets result requires string local_identifiers.",
                EXIT_PARTIAL,
            )
        requested = [item.get("local_identifier") for item in items]
        if identifiers != requested:
            raise ApplePhotosError(
                "E_OUTCOME_UNKNOWN",
                "PhotoKit delete acknowledgement does not match the request.",
                EXIT_PARTIAL,
            )
        return value

    def verify_assets(
        self,
        local_identifiers: Sequence[str],
        *,
        album_id: str | None = None,
        expect_present: bool = True,
    ) -> list[dict[str, Any]]:
        result = self._request(
            "verify-assets",
            {
                "local_identifiers": list(local_identifiers),
                "album_id": album_id,
                "expect_present": expect_present,
            },
        )
        values = self._array(result, "assets", "verify-assets")
        requested = list(local_identifiers)
        if len(values) != len(requested) or any(
            not isinstance(item, dict)
            or item.get("local_identifier") != requested[index]
            or not isinstance(item.get("present"), bool)
            or not (item.get("in_album") is None or isinstance(item.get("in_album"), bool))
            for index, item in enumerate(values)
        ):
            raise ApplePhotosError(
                "E_BACKEND_PROTOCOL", "Verification record is malformed.", EXIT_IO
            )
        return values
