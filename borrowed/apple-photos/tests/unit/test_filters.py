import pytest

from apple_photos_cli.errors import ApplePhotosError
from apple_photos_cli.filters import matches_filter


def test_nested_filter_matches(fake_reader) -> None:
    spec = {
        "schema_version": "1.0",
        "all": [
            {"field": "media_type", "op": "eq", "value": "image"},
            {
                "any": [
                    {"field": "keywords", "op": "contains", "value": "sky"},
                    {"field": "favorite", "op": "eq", "value": False},
                ]
            },
        ],
    }

    assert matches_filter(fake_reader.assets()[0], spec)
    assert not matches_filter(fake_reader.assets()[1], spec)


def test_datetime_filter_compares_instants_not_timestamp_strings(fake_reader) -> None:
    asset = fake_reader.assets()[0]
    spec = {"field": "date_taken", "op": "eq", "value": "2028-12-31T16:00:00-08:00"}

    assert matches_filter(asset, spec)


@pytest.mark.parametrize(
    "spec",
    [
        {"field": "private_sql", "op": "eq", "value": "x"},
        {"field": "media_type", "op": "eval", "value": "x"},
        {"field": "date_taken", "op": "gte", "value": "2029-01-01"},
        {"all": []},
    ],
)
def test_filter_rejects_unknown_or_unsafe_contract(spec, fake_reader) -> None:
    with pytest.raises(ApplePhotosError, match=r"Filter|filter") as captured:
        matches_filter(fake_reader.assets()[0], spec)

    assert captured.value.code == "E_FILTER_INVALID"
