from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from apple_photos_cli.canonical import sha256_digest
from apple_photos_cli.errors import EXIT_IO, ApplePhotosError, stale
from apple_photos_cli.models import ResourceRecord


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_source(path: Path) -> dict[str, Any]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ApplePhotosError(
            "E_LOCAL_IO", f"Cannot inspect source file: {path}", EXIT_IO, {"os_error": str(exc)}
        ) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ApplePhotosError(
            "E_RESOURCE_GROUP_UNSUPPORTED",
            "Import sources must be regular files and must not be symbolic links.",
            EXIT_IO,
        )
    return {
        "path": str(path.resolve()),
        "byte_count": info.st_size,
        "sha256": sha256_file(path),
        "file_identity": {
            "device": info.st_dev,
            "inode": info.st_ino,
            "mode": stat.S_IMODE(info.st_mode),
        },
    }


def verify_source(expected: dict[str, Any]) -> Path:
    path = Path(expected["path"])
    observed = inspect_source(path)
    comparable = ("byte_count", "sha256", "file_identity")
    if any(observed[key] != expected[key] for key in comparable):
        raise stale(f"Source changed after planning: {path}", code="E_HASH_MISMATCH")
    return path


def stage_source(expected: dict[str, Any], destination: Path) -> None:
    """Copy a planned source through a no-follow descriptor and verify the copied bytes."""
    path = Path(expected["path"])
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        source_fd = os.open(path, flags)
    except OSError as exc:
        raise stale(f"Source cannot be opened safely: {path}", code="E_HASH_MISMATCH") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    try:
        observed = os.fstat(source_fd)
        identity = {
            "device": observed.st_dev,
            "inode": observed.st_ino,
            "mode": stat.S_IMODE(observed.st_mode),
        }
        if (
            not stat.S_ISREG(observed.st_mode)
            or observed.st_size != expected["byte_count"]
            or identity != expected["file_identity"]
        ):
            raise stale(f"Source changed after planning: {path}", code="E_HASH_MISMATCH")
        with os.fdopen(source_fd, "rb", closefd=False) as source, destination.open("xb") as target:
            os.chmod(destination, 0o600)
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                target.write(chunk)
                digest.update(chunk)
            target.flush()
            os.fsync(target.fileno())
    finally:
        os.close(source_fd)
    if digest.hexdigest() != expected["sha256"]:
        destination.unlink(missing_ok=True)
        raise stale(f"Source bytes changed after planning: {path}", code="E_HASH_MISMATCH")


def resource_set_digest(resources: Iterable[ResourceRecord | dict[str, Any]]) -> str:
    members = []
    for resource in resources:
        if isinstance(resource, ResourceRecord):
            member = resource.digest_member()
        else:
            member = {
                "role": resource["role"],
                "uti": resource["uti"],
                "byte_count": resource["byte_count"],
                "sha256": resource["sha256"],
            }
        members.append(member)
    members.sort(key=lambda item: (item["role"], item["uti"], item["byte_count"], item["sha256"]))
    return sha256_digest(members)


def source_resource(path_info: dict[str, Any], role: str, uti: str) -> dict[str, Any]:
    return {
        "role": role,
        "uti": uti,
        "byte_count": path_info["byte_count"],
        "sha256": path_info["sha256"],
    }
