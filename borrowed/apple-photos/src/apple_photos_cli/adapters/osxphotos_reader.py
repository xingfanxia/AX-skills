from __future__ import annotations

import importlib.metadata
import mimetypes
import os
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from apple_photos_cli.canonical import asset_id_set_digest
from apple_photos_cli.errors import EXIT_DEPENDENCY, ApplePhotosError
from apple_photos_cli.models import AlbumRecord, AssetRecord, LibrarySnapshot

OSXPHOTOS_VERSION = "0.76.1"


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value) if value else None


def _value(source: Any, name: str, default: Any = None) -> Any:
    try:
        value = getattr(source, name)
        return value() if callable(value) else value
    except (AttributeError, TypeError, ValueError):
        return default


def _identifier(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    for name in ("uuid", "local_identifier", "identifier"):
        result = _value(value, name)
        if result:
            return str(result)
    return None


class OsxphotosReader:
    """Read-only normalization adapter for the public osxphotos API."""

    def __init__(self, library: Path | None) -> None:
        self.library = library.expanduser().resolve() if library else None
        self._database: Any = None
        self._snapshot: LibrarySnapshot | None = None

    def _load(self) -> Any:
        try:
            version = importlib.metadata.version("osxphotos")
        except importlib.metadata.PackageNotFoundError as exc:
            raise ApplePhotosError(
                "E_DEPENDENCY_MISSING",
                "osxphotos is not installed. Install the 'photos' extra.",
                EXIT_DEPENDENCY,
            ) from exc
        if version != OSXPHOTOS_VERSION:
            raise ApplePhotosError(
                "E_DEPENDENCY_VERSION",
                f"osxphotos {OSXPHOTOS_VERSION} is required; found {version}.",
                EXIT_DEPENDENCY,
            )
        if self._database is None:
            try:
                from osxphotos import PhotosDB

                if self.library is None:
                    self._database = PhotosDB()
                else:
                    self._database = PhotosDB(library_path=str(self.library))
            except PermissionError as exc:
                raise ApplePhotosError(
                    "E_PERMISSION_LIBRARY_READ",
                    "The selected Photos library is not readable by this process.",
                    EXIT_DEPENDENCY,
                ) from exc
            except Exception as exc:
                raise ApplePhotosError(
                    "E_LIBRARY_READ_FAILED",
                    "osxphotos could not open the selected Photos library.",
                    EXIT_DEPENDENCY,
                    {"exception_type": type(exc).__name__, "detail": str(exc)},
                ) from exc
        return self._database

    def probe(self) -> LibrarySnapshot:
        database = self._load()
        if self._snapshot is not None:
            return self._snapshot
        library_path = self.library
        if library_path is None:
            value = _value(database, "library_path") or _value(database, "dbfile")
            library_path = Path(value).resolve() if value else None
        photos = list(self._photos())
        identifiers = sorted(
            str(_value(photo, "uuid")) for photo in photos if _value(photo, "uuid")
        )
        self._snapshot = LibrarySnapshot(
            kind="selected_osxphotos_snapshot",
            canonical_path=str(library_path) if library_path else None,
            is_system_library=False,
            physical_identity_verified=False,
            sentinel_asset_ids=tuple(identifiers[:3]),
            asset_ids_sha256=asset_id_set_digest(identifiers),
            asset_count=len(photos),
            observed_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        )
        return self._snapshot

    def _photos(self) -> Iterable[Any]:
        database = self._load()
        photos = _value(database, "photos", [])
        return photos or []

    def assets(self) -> list[AssetRecord]:
        snapshot = self.probe()
        return [self._normalize(photo, snapshot.digest) for photo in self._photos()]

    def albums(self) -> list[AlbumRecord]:
        database = self._load()
        values = _value(database, "album_info", []) or []
        albums: list[AlbumRecord] = []
        if isinstance(values, dict):
            values = values.values()
        for value in values:
            identifier = _identifier(value)
            title = _value(value, "title") or _value(value, "name")
            if identifier and title:
                count = _value(value, "count")
                albums.append(
                    AlbumRecord(identifier, str(title), int(count) if count is not None else None)
                )
        return sorted(
            albums, key=lambda album: (album.title.casefold(), album.osxphotos_album_uuid)
        )

    def _normalize(self, photo: Any, snapshot_digest: str) -> AssetRecord:
        filename = _value(photo, "original_filename") or _value(photo, "filename")
        album_values = _value(photo, "album_info", None)
        if album_values is None:
            album_values = _value(photo, "albums", [])
        albums = tuple(
            identifier
            for identifier in (_identifier(album) for album in (album_values or []))
            if identifier
        )
        keywords = tuple(str(value) for value in (_value(photo, "keywords", []) or []))
        uti = _value(photo, "uti")
        if not uti and filename:
            uti = mimetypes.guess_type(str(filename))[0]
        is_movie = bool(_value(photo, "ismovie", False))
        duration = _value(photo, "duration")
        path_values = _value(photo, "path", []) or []
        if isinstance(path_values, (str, Path)):
            path_values = [path_values]
        size = None
        for path in path_values:
            try:
                size = os.path.getsize(path)
                break
            except OSError:
                continue
        return AssetRecord(
            osxphotos_uuid=str(_value(photo, "uuid")),
            library_snapshot_digest=snapshot_digest,
            media_type="video" if is_movie else "image",
            original_filename=str(filename) if filename else None,
            uti=str(uti) if uti else None,
            date_taken=_iso(_value(photo, "date")),
            date_added=_iso(_value(photo, "date_added")),
            date_modified=_iso(_value(photo, "date_modified")),
            width=_value(photo, "width"),
            height=_value(photo, "height"),
            duration_ms=round(float(duration) * 1000) if duration is not None else None,
            osxphotos_album_uuids=albums,
            keywords=keywords,
            favorite=bool(_value(photo, "favorite", False)),
            hidden=bool(_value(photo, "hidden", False)),
            edited=bool(_value(photo, "hasadjustments", False)),
            missing=bool(_value(photo, "ismissing", False)),
            in_trash=bool(_value(photo, "intrash", False)),
            cloud_only=bool(_value(photo, "iscloudasset", False) and not path_values),
            original_size_bytes=size,
            title=_value(photo, "title"),
            description=_value(photo, "description"),
            resource_count=len(path_values),
            metadata_backend="osxphotos",
            metadata_backend_version=OSXPHOTOS_VERSION,
            observed_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        )
