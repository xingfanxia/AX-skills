from apple_photos_cli.canonical import canonical_json_bytes, manifest_digest, sha256_digest


def test_key_order_and_whitespace_do_not_change_digest() -> None:
    left = {"z": [1, True], "a": {"b": "value"}}
    right = {"a": {"b": "value"}, "z": [1, True]}

    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert sha256_digest(left) == sha256_digest(right)


def test_value_change_changes_manifest_digest() -> None:
    first = {"manifest_sha256": "ignored", "items": [{"id": "a"}]}
    second = {"manifest_sha256": "different", "items": [{"id": "b"}]}

    assert manifest_digest(first) != manifest_digest(second)
