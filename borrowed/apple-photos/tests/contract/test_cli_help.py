import pytest

from apple_photos_cli.cli import build_parser


@pytest.mark.parametrize(
    "path",
    [
        [],
        ["library"],
        ["library", "inspect"],
        ["album", "list"],
        ["asset", "search"],
        ["asset", "list"],
        ["asset", "metadata"],
        ["asset", "filter"],
        ["asset", "retrieve"],
        ["metadata", "dump"],
        ["metadata", "backup"],
        ["evidence", "compare-images"],
        ["import", "plan"],
        ["import", "apply"],
        ["import-batch", "plan"],
        ["delete", "authorize"],
        ["delete", "apply"],
        ["delete-batch", "plan"],
    ],
)
def test_help_renders_without_loading_optional_photos_dependency(path, capsys) -> None:
    with pytest.raises(SystemExit) as captured:
        build_parser().parse_args([*path, "--help"])

    assert captured.value.code == 0
    assert "usage:" in capsys.readouterr().out
