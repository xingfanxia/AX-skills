import os
import pwd
from pathlib import Path

from apple_photos_cli.state import default_state_dir


def test_default_state_dir_ignores_home_environment(monkeypatch) -> None:
    monkeypatch.setenv("HOME", "/tmp/caller-selected-home")

    assert default_state_dir() == (
        Path(pwd.getpwuid(os.getuid()).pw_dir)
        / "Library"
        / "Application Support"
        / "apple-photos-skill"
    )
