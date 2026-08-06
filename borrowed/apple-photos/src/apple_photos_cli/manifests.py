from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from apple_photos_cli.canonical import canonical_json_bytes, manifest_digest
from apple_photos_cli.errors import EXIT_IO, ApplePhotosError, stale, usage_error


def utc_now() -> datetime:
    return datetime.now(UTC)


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def format_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise usage_error(f"Invalid RFC 3339 timestamp: {value}", code="E_SCHEMA_INVALID") from exc
    if parsed.tzinfo is None:
        raise usage_error("Manifest timestamps must include a timezone.", code="E_SCHEMA_INVALID")
    return parsed.astimezone(UTC)


def schema_directory() -> Path:
    packaged = Path(__file__).resolve().parent / "schemas"
    return packaged if packaged.is_dir() else Path(__file__).resolve().parents[2] / "schemas"


def validate_schema(value: Any, schema_name: str) -> None:
    schema_path = schema_directory() / schema_name
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ApplePhotosError(
            "E_LOCAL_IO", f"Cannot load schema {schema_name}.", EXIT_IO, {"detail": str(exc)}
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path)
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "<root>"
        raise usage_error(
            f"Schema validation failed at {location}: {first.message}", code="E_SCHEMA_INVALID"
        )


def seal_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    manifest = dict(value)
    manifest["manifest_sha256"] = manifest_digest(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any], *, expected_type: str | None = None) -> None:
    validate_schema(manifest, "operation-manifest-v1.schema.json")
    _validate_manifest_semantics(manifest)
    if expected_type and manifest.get("manifest_type") != expected_type:
        raise usage_error(
            f"Expected {expected_type} manifest, received {manifest.get('manifest_type')!r}.",
            code="E_SCHEMA_INVALID",
        )
    expected = manifest_digest(manifest)
    if manifest.get("manifest_sha256") != expected:
        raise stale("Manifest digest does not match its contents.", code="E_MANIFEST_TAMPERED")
    if parse_time(manifest["expires_at"]) <= utc_now():
        raise stale("Manifest has expired.", code="E_MANIFEST_EXPIRED")


def _validate_manifest_semantics(manifest: dict[str, Any]) -> None:
    created_at = parse_time(manifest["created_at"])
    expires_at = parse_time(manifest["expires_at"])
    if expires_at <= created_at or expires_at - created_at > timedelta(hours=24):
        raise usage_error(
            "Manifest lifetime must be positive and no longer than 24 hours.",
            code="E_SCHEMA_INVALID",
        )
    item_ids = [item["item_id"] for item in manifest["items"]]
    if len(item_ids) != len(set(item_ids)):
        raise usage_error("Manifest item identifiers must be unique.", code="E_SCHEMA_INVALID")
    if manifest["manifest_type"] == "apple_photos_delete":
        if any(
            item["planned_action"] != "move_to_recently_deleted"
            for item in manifest["items"]
        ):
            raise usage_error("Delete manifest action is invalid.", code="E_SCHEMA_INVALID")
        policy = manifest["delete_policy"]["policy"]
        if (
            policy["max_rgb_mae"] > 0.01
            or policy["max_luma_mae"] > 0.01
            or policy["max_rgb_p99"] > 0.05
        ):
            raise usage_error(
                "Delete pixel policy exceeds the supported safety thresholds.",
                code="E_SCHEMA_INVALID",
            )
        candidates = [item["local_identifier"] for item in manifest["items"]]
        keepers = {
            item["pixel_similarity_proof"]["keeper_local_identifier"]
            for item in manifest["items"]
        }
        pair_ids = [
            item["pixel_similarity_proof"]["pair_id"] for item in manifest["items"]
        ]
        if (
            len(candidates) != len(set(candidates))
            or len(pair_ids) != len(set(pair_ids))
            or set(candidates) & keepers
        ):
            raise usage_error(
                "Delete pixel candidate, keeper, and pair identifiers are inconsistent.",
                code="E_SCHEMA_INVALID",
            )
        for item in manifest["items"]:
            proof = item["pixel_similarity_proof"]
            metrics = proof["metrics"]
            if (
                proof["candidate_source_sha256"] == proof["keeper_source_sha256"]
                or metrics["rgb_mean_absolute_error"] > policy["max_rgb_mae"]
                or metrics["luma_mean_absolute_error"] > policy["max_luma_mae"]
                or metrics["rgb_p99_absolute_error"] > policy["max_rgb_p99"]
            ):
                raise usage_error(
                    f"Delete pixel proof is not eligible for {item['item_id']}.",
                    code="E_SCHEMA_INVALID",
                )
        return
    if manifest["manifest_type"] != "apple_photos_import":
        return
    preceding: dict[str, dict[str, Any]] = {}
    for item in manifest["items"]:
        action = item["planned_action"]
        exact = item["exact_duplicate_ids"]
        parent_id = item["batch_duplicate_of"]
        valid = True
        if action == "create_asset":
            valid = not exact and parent_id is None
        elif action == "reuse_exact_duplicate":
            valid = len(exact) == 1 and parent_id is None
        elif action == "reuse_batch_duplicate":
            parent = preceding.get(parent_id or "")
            valid = bool(
                not exact
                and parent
                and parent["resource_set_digest"] == item["resource_set_digest"]
                and parent["planned_action"] in {"create_asset", "reuse_exact_duplicate"}
            )
        elif action == "blocked_ambiguous_duplicate":
            valid = len(exact) > 1 and parent_id is None
        elif action == "blocked_duplicate_coverage_incomplete":
            valid = not exact and parent_id is None
        if not valid:
            raise usage_error(
                f"Import action invariants failed for {item['item_id']}.", code="E_SCHEMA_INVALID"
            )
        preceding[item["item_id"]] = item


def load_manifest(path: Path, *, expected_type: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ApplePhotosError("E_LOCAL_IO", f"Cannot read manifest: {path}", EXIT_IO) from exc
    except json.JSONDecodeError as exc:
        raise usage_error(f"Manifest is not valid JSON: {exc}", code="E_SCHEMA_INVALID") from exc
    if not isinstance(value, dict):
        raise usage_error("Manifest root must be a JSON object.", code="E_SCHEMA_INVALID")
    validate_manifest(value, expected_type=expected_type)
    return value


def atomic_write_json(path: Path, value: Any, *, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_json_bytes(value))
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        fsync_directory(path.parent)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def write_manifest(path: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    manifest = seal_manifest(value)
    validate_schema(manifest, "operation-manifest-v1.schema.json")
    _validate_manifest_semantics(manifest)
    atomic_write_json(path, manifest)
    return manifest
