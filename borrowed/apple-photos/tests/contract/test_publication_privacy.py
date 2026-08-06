import re
import subprocess
from pathlib import Path


def _publication_candidates(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [root / value.decode("utf-8") for value in completed.stdout.split(b"\0") if value]


def test_publication_candidates_have_no_user_home_or_absolute_file_links() -> None:
    root = Path(__file__).resolve().parents[2]
    home_patterns = [
        re.compile("/" + "Users" + r"/[A-Za-z0-9._-]+/"),
        re.compile("/" + "home" + r"/[A-Za-z0-9._-]+/"),
        re.compile(r"[A-Za-z]:\\" + "Users" + r"\\[A-Za-z0-9._-]+\\"),
    ]
    file_url = "file:" + "///"
    offenders = []
    for path in _publication_candidates(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if file_url in text or any(pattern.search(text) for pattern in home_patterns):
            offenders.append(str(path.relative_to(root)))
    assert offenders == []


def test_publication_candidates_have_no_credentials_or_email_addresses() -> None:
    root = Path(__file__).resolve().parents[2]
    email = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    secret_locators = ["op:" + "//", "BEGIN " + "PRIVATE KEY"]
    offenders = []
    for path in _publication_candidates(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if email.search(text) or any(value in text for value in secret_locators):
            offenders.append(str(path.relative_to(root)))
    assert offenders == []
