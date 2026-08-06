def test_search_is_case_insensitive_and_sensitive_fields_are_opt_in(fake_reader) -> None:
    asset = fake_reader.assets()[0]

    assert "alpha.jpg" in asset.search_text()
    assert "SKY".casefold() in asset.search_text()
    assert asset.sensitive is None


def test_normalized_asset_has_scoped_identifier(fake_reader) -> None:
    value = fake_reader.assets()[0].to_dict()

    assert value["asset_id"]["namespace"] == "osxphotos_uuid"
    assert value["asset_id"]["library_snapshot_digest"].startswith("sha256:")
    assert value["flags"]["favorite"] is True
