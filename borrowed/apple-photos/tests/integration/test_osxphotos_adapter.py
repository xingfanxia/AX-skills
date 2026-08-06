from __future__ import annotations

import importlib.metadata
import sys
import types
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from apple_photos_cli.adapters.osxphotos_reader import OsxphotosReader
from apple_photos_cli.errors import ApplePhotosError


class SyntheticPhotosDB:
    observed_library_path: str | None = None

    def __init__(self, *, library_path=None, dbfile=None) -> None:
        type(self).observed_library_path = library_path
        album = SimpleNamespace(uuid="album-uuid", title="Synthetic Album", count=1)
        self.album_info = [album]
        self._photos = [
            SimpleNamespace(
                uuid="asset-uuid",
                original_filename="synthetic.jpg",
                filename="synthetic.jpg",
                date=datetime(2029, 1, 1, tzinfo=UTC),
                date_added=datetime(2029, 1, 2, tzinfo=UTC),
                date_modified=None,
                width=10,
                height=20,
                ismovie=False,
                album_info=[album],
                keywords=["synthetic"],
                favorite=True,
                hidden=False,
                hasadjustments=False,
                ismissing=False,
                intrash=False,
                iscloudasset=True,
                path=[],
                uti="public.jpeg",
                title="Synthetic Title",
                description=None,
            )
        ]

    def photos(self):
        return list(self._photos)


def _install_synthetic_module(monkeypatch) -> None:
    module = types.ModuleType("osxphotos")
    module.PhotosDB = SyntheticPhotosDB
    monkeypatch.setitem(sys.modules, "osxphotos", module)
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.76.1")


def test_adapter_uses_public_library_path_and_normalizes_album_ids(monkeypatch) -> None:
    _install_synthetic_module(monkeypatch)
    library = Path("/example/Synthetic.photoslibrary")
    reader = OsxphotosReader(library)

    asset = reader.assets()[0]
    album = reader.albums()[0]

    assert SyntheticPhotosDB.observed_library_path == str(library)
    assert asset.osxphotos_uuid == "asset-uuid"
    assert asset.osxphotos_album_uuids == ("album-uuid",)
    assert asset.cloud_only is True
    assert asset.metadata_backend_version == "0.76.1"
    assert album.osxphotos_album_uuid == "album-uuid"


def test_adapter_rejects_unpinned_version(monkeypatch) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.76.2")
    reader = OsxphotosReader(Path("/example/Synthetic.photoslibrary"))

    with pytest.raises(ApplePhotosError) as captured:
        reader.assets()

    assert captured.value.code == "E_DEPENDENCY_VERSION"
