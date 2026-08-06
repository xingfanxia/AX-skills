from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

from apple_photos_cli.errors import usage_error


def _key_order(value: str) -> bytes:
    return value.encode("utf-16-be", errors="surrogatepass")


def _serialize(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise usage_error(
                "Canonical JSON does not permit NaN or infinity.", code="E_SCHEMA_INVALID"
            )
        if value == 0:
            return "0"
        return json.dumps(value, allow_nan=False, separators=(",", ":"))
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise usage_error(
                "Canonical JSON object keys must be strings.", code="E_SCHEMA_INVALID"
            )
        members = []
        for key in sorted(value, key=_key_order):
            members.append(f"{_serialize(key)}:{_serialize(value[key])}")
        return "{" + ",".join(members) + "}"
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return "[" + ",".join(_serialize(item) for item in value) + "]"
    raise usage_error(
        f"Unsupported canonical JSON value: {type(value).__name__}.",
        code="E_SCHEMA_INVALID",
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize the supported JSON data model using this project's deterministic encoding."""
    return _serialize(value).encode("utf-8")


def sha256_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def asset_id_set_digest(identifiers: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for identifier in sorted(set(identifiers)):
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def manifest_digest(manifest: Mapping[str, Any]) -> str:
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256", None)
    return sha256_digest(unsigned)
