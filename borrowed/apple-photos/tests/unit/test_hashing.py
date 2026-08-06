import os
from pathlib import Path

import pytest

from apple_photos_cli.errors import ApplePhotosError
from apple_photos_cli.hashing import (
    inspect_source,
    resource_set_digest,
    stage_source,
    verify_source,
)


def test_resource_set_digest_is_order_independent() -> None:
    resources = [
        {"role": "video", "uti": "video/quicktime", "byte_count": 2, "sha256": "b" * 64},
        {"role": "photo", "uti": "image/jpeg", "byte_count": 1, "sha256": "a" * 64},
    ]

    assert resource_set_digest(resources) == resource_set_digest(reversed(resources))


def test_source_change_is_detected(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"before")
    expected = inspect_source(source)
    source.write_bytes(b"after")

    with pytest.raises(ApplePhotosError) as captured:
        verify_source(expected)

    assert captured.value.code == "E_HASH_MISMATCH"


def test_symlink_source_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.jpg"
    target.write_bytes(b"data")
    link = tmp_path / "link.jpg"
    os.symlink(target, link)

    with pytest.raises(ApplePhotosError, match="regular files"):
        inspect_source(link)


def test_staging_copies_verified_bytes_with_private_mode(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"verified")
    expected = inspect_source(source)
    staged = tmp_path / "staging" / "source.jpg"

    stage_source(expected, staged)

    assert staged.read_bytes() == b"verified"
    assert staged.stat().st_mode & 0o777 == 0o600
