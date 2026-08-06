from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, TextIO

from apple_photos_cli import SCHEMA_VERSION, __version__
from apple_photos_cli.canonical import canonical_json_bytes
from apple_photos_cli.manifests import atomic_write_json, fsync_directory
from apple_photos_cli.models import AlbumRecord, AssetRecord, LibrarySnapshot


def render_json(value: Any, stream: TextIO) -> None:
    stream.write(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    stream.write("\n")


def render_jsonl(
    *,
    command: str,
    run_id: str,
    records: Iterable[tuple[str, Mapping[str, Any]]],
    observed_at: str,
    stream: TextIO,
) -> None:
    sequence = 0
    render_json(
        {
            "schema_version": SCHEMA_VERSION,
            "record_type": "run_start",
            "run_id": run_id,
            "sequence": sequence,
            "command": command,
            "observed_at": observed_at,
        },
        stream,
    )
    counts: dict[str, int] = {}
    for record_type, value in records:
        sequence += 1
        counts[record_type] = counts.get(record_type, 0) + 1
        render_json(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": record_type,
                "run_id": run_id,
                "sequence": sequence,
                record_type: value,
            },
            stream,
        )
    sequence += 1
    render_json(
        {
            "schema_version": SCHEMA_VERSION,
            "record_type": "run_end",
            "run_id": run_id,
            "sequence": sequence,
            "status": "succeeded",
            "counts": counts,
        },
        stream,
    )


def _write_jsonl_file(path: Path, records: Iterable[Mapping[str, Any]]) -> tuple[int, int, str]:
    digest = hashlib.sha256()
    count = 0
    with path.open("wb") as handle:
        for record in records:
            line = canonical_json_bytes(record) + b"\n"
            handle.write(line)
            digest.update(line)
            count += 1
        handle.flush()
        os.fsync(handle.fileno())
    return count, path.stat().st_size, digest.hexdigest()


def create_metadata_backup(
    output: Path,
    *,
    snapshot: LibrarySnapshot,
    assets: list[AssetRecord],
    albums: list[AlbumRecord],
    created_at: str,
) -> dict[str, Any]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"Backup output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        file_specs: dict[str, tuple[int, int, str]] = {}
        file_specs["assets.jsonl"] = _write_jsonl_file(
            temporary / "assets.jsonl", (asset.to_dict() for asset in assets)
        )
        file_specs["albums.jsonl"] = _write_jsonl_file(
            temporary / "albums.jsonl", (album.to_dict() for album in albums)
        )
        memberships = (
            {
                "album_id": {"namespace": "osxphotos_album_uuid", "value": album_id},
                "asset_id": {"namespace": "osxphotos_uuid", "value": asset.osxphotos_uuid},
            }
            for asset in assets
            for album_id in sorted(asset.osxphotos_album_uuids)
        )
        file_specs["album_assets.jsonl"] = _write_jsonl_file(
            temporary / "album_assets.jsonl", memberships
        )
        file_specs["errors.jsonl"] = _write_jsonl_file(temporary / "errors.jsonl", ())
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "backup_type": "apple_photos_metadata",
            "created_at": created_at,
            "complete": True,
            "library_snapshot": snapshot.to_dict(),
            "library_snapshot_digest": snapshot.digest,
            "generator": {"name": "apple-photos-skill", "version": __version__},
            "files": {
                name: {"record_count": values[0], "byte_count": values[1], "sha256": values[2]}
                for name, values in sorted(file_specs.items())
            },
        }
        atomic_write_json(temporary / "manifest.json", manifest)
        os.replace(temporary, output)
        fsync_directory(output.parent)
        complete = output / "COMPLETE"
        with complete.open("xb") as handle:
            handle.write(b"complete\n")
            handle.flush()
            os.fsync(handle.fileno())
        fsync_directory(output)
        return manifest
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
