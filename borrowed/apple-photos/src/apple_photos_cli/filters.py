from __future__ import annotations

from datetime import datetime
from typing import Any

from apple_photos_cli.canonical import sha256_digest
from apple_photos_cli.errors import usage_error
from apple_photos_cli.models import AssetRecord

FIELD_OPS: dict[str, set[str]] = {
    "osxphotos_uuid": {"eq", "in", "prefix"},
    "original_filename": {"eq", "in", "prefix"},
    "date_taken": {"eq", "gte", "gt", "lte", "lt"},
    "date_added": {"eq", "gte", "gt", "lte", "lt"},
    "date_modified": {"eq", "gte", "gt", "lte", "lt"},
    "media_type": {"eq", "in"},
    "media_subtypes": {"eq", "in", "contains"},
    "uti": {"eq", "in", "contains"},
    "osxphotos_album_uuids": {"contains", "contains_any", "contains_all"},
    "keywords": {"contains", "contains_any", "contains_all"},
    "favorite": {"eq"},
    "hidden": {"eq"},
    "edited": {"eq"},
    "missing": {"eq"},
    "in_trash": {"eq"},
    "cloud_only": {"eq"},
    "width": {"eq", "gte", "gt", "lte", "lt"},
    "height": {"eq", "gte", "gt", "lte", "lt"},
    "duration_ms": {"eq", "gte", "gt", "lte", "lt"},
    "original_size_bytes": {"eq", "gte", "gt", "lte", "lt"},
}

DATE_FIELDS = {"date_taken", "date_added", "date_modified"}


def _validate_datetime(value: Any) -> None:
    if not isinstance(value, str):
        raise usage_error("Filter datetime values must be strings.", code="E_FILTER_INVALID")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise usage_error(
            "Filter datetime values must use RFC 3339.", code="E_FILTER_INVALID"
        ) from exc
    if parsed.tzinfo is None:
        raise usage_error(
            "Filter datetime values must include a timezone.", code="E_FILTER_INVALID"
        )


def validate_filter(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") not in (None, "1.0"):
        raise usage_error("Unsupported filter schema_version.", code="E_FILTER_INVALID")
    _validate_node({key: value for key, value in spec.items() if key != "schema_version"})


def _validate_node(node: Any) -> None:
    if not isinstance(node, dict):
        raise usage_error("Each filter node must be an object.", code="E_FILTER_INVALID")
    logical = [key for key in ("all", "any", "not") if key in node]
    if logical:
        if len(logical) != 1 or len(node) != 1:
            raise usage_error(
                "A logical filter node must contain exactly one operator.", code="E_FILTER_INVALID"
            )
        key = logical[0]
        if key == "not":
            _validate_node(node[key])
            return
        children = node[key]
        if not isinstance(children, list) or not children:
            raise usage_error(
                f"Filter '{key}' requires a non-empty array.", code="E_FILTER_INVALID"
            )
        for child in children:
            _validate_node(child)
        return
    if set(node) != {"field", "op", "value"}:
        raise usage_error(
            "A filter predicate requires field, op, and value.", code="E_FILTER_INVALID"
        )
    field_name = node["field"]
    operation = node["op"]
    if field_name not in FIELD_OPS or operation not in FIELD_OPS[field_name]:
        raise usage_error(
            f"Unsupported filter field or operation: {field_name!r} {operation!r}.",
            code="E_FILTER_INVALID",
        )
    if operation in {"in", "contains_any", "contains_all"} and not isinstance(node["value"], list):
        raise usage_error(
            f"Filter operation '{operation}' requires an array.", code="E_FILTER_INVALID"
        )
    if field_name in DATE_FIELDS:
        values = node["value"] if operation == "in" else [node["value"]]
        for value in values:
            _validate_datetime(value)


def filter_digest(spec: dict[str, Any]) -> str:
    validate_filter(spec)
    return sha256_digest(spec)


def matches_filter(asset: AssetRecord, spec: dict[str, Any]) -> bool:
    validate_filter(spec)
    node = {key: value for key, value in spec.items() if key != "schema_version"}
    return _matches_node(asset, node)


def _matches_node(asset: AssetRecord, node: dict[str, Any]) -> bool:
    if "all" in node:
        return all(_matches_node(asset, child) for child in node["all"])
    if "any" in node:
        return any(_matches_node(asset, child) for child in node["any"])
    if "not" in node:
        return not _matches_node(asset, node["not"])
    current = asset.filter_value(node["field"])
    operation = node["op"]
    expected = node["value"]
    if current is None:
        return operation == "eq" and expected is None
    if node["field"] in DATE_FIELDS:
        current = datetime.fromisoformat(current.replace("Z", "+00:00"))
        expected = datetime.fromisoformat(expected.replace("Z", "+00:00"))
    if operation == "eq":
        return current == expected
    if operation == "in":
        if isinstance(current, (tuple, list, set)):
            return any(value in expected for value in current)
        return current in expected
    if operation == "prefix":
        return isinstance(current, str) and current.startswith(expected)
    if operation == "contains":
        return expected in current
    if operation == "contains_any":
        return any(value in current for value in expected)
    if operation == "contains_all":
        return all(value in current for value in expected)
    if operation == "gte":
        return current >= expected
    if operation == "gt":
        return current > expected
    if operation == "lte":
        return current <= expected
    if operation == "lt":
        return current < expected
    raise AssertionError(f"Validated operation not implemented: {operation}")
