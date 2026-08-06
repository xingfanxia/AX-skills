import ast
import re
from pathlib import Path

import pytest

REPLAY_SQL_ALLOWLIST = {
    "CREATE TABLE IF NOT EXISTS consumed_nonce (nonce TEXT PRIMARY KEY, "
    "manifest_sha256 TEXT NOT NULL, consumed_at TEXT NOT NULL)",
    "SELECT 1 FROM consumed_nonce WHERE nonce = ?",
    "INSERT INTO consumed_nonce (nonce, manifest_sha256, consumed_at) VALUES (?, ?, ?)",
}
SQLITE_EXECUTION_APIS = {"execute", "executemany", "executescript"}
REPLAY_SQL_FIXTURE = """
connection.execute(
    "CREATE TABLE IF NOT EXISTS consumed_nonce (nonce TEXT PRIMARY KEY, "
    "manifest_sha256 TEXT NOT NULL, consumed_at TEXT NOT NULL)"
)
connection.execute("SELECT 1 FROM consumed_nonce WHERE nonce = ?", (nonce,))
connection.execute(
    "INSERT INTO consumed_nonce (nonce, manifest_sha256, consumed_at) VALUES (?, ?, ?)",
    values,
)
"""


def _sqlite_statements(source: str) -> set[str]:
    statements = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        api = node.func.attr
        if "execute" not in api.casefold():
            continue
        assert api in SQLITE_EXECUTION_APIS, f"Unrecognized SQLite execution API: {api}"
        assert api != "executescript", "SQLite executescript is prohibited"
        assert node.args, "SQLite execution must have a SQL argument"
        sql = node.args[0]
        assert isinstance(sql, ast.Constant) and isinstance(sql.value, str), (
            "Dynamic SQL is prohibited"
        )
        statements.add(" ".join(sql.value.split()))
    return statements


def _assert_only_replay_sql(source: str) -> None:
    assert _sqlite_statements(source) == REPLAY_SQL_ALLOWLIST


def test_read_adapter_contains_no_mutation_or_sql_write_path() -> None:
    root = Path(__file__).resolve().parents[2]
    adapter = (root / "src/apple_photos_cli/adapters/osxphotos_reader.py").read_text(
        encoding="utf-8"
    )
    lowered = adapter.lower()

    assert "import_photos" not in lowered
    assert "photoscript" not in lowered
    assert "sqlite3" not in lowered
    assert " insert " not in lowered
    assert " update " not in lowered
    assert " delete from " not in lowered


def test_only_replay_ledger_may_import_sqlite_and_no_photos_dml_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    python_sources = list((root / "src").rglob("*.py"))
    native_sources = list((root / "native").rglob("*.swift"))
    dml = re.compile(
        r"\b(?:INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|ALTER\s+TABLE|"
        r"DROP\s+TABLE|VACUUM)\b",
        re.IGNORECASE,
    )
    for path in python_sources:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        assert "photos.sqlite" not in lowered, path
        assert "photos.db" not in lowered, path
        if path.name != "state.py":
            tree = ast.parse(text)
            imported = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imported.update(
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            )
            assert "sqlite3" not in imported, path
            assert not dml.search(text), path
    state_path = root / "src/apple_photos_cli/state.py"
    _assert_only_replay_sql(state_path.read_text(encoding="utf-8"))
    for path in native_sources:
        text = path.read_text(encoding="utf-8")
        assert not dml.search(text), path
        assert "photos.sqlite" not in text.lower(), path


@pytest.mark.parametrize("statement", ["DELETE FROM ZASSET", "VACUUM"])
def test_replay_sql_allowlist_rejects_additional_literal_sql(statement: str) -> None:
    with pytest.raises(AssertionError):
        _assert_only_replay_sql(
            REPLAY_SQL_FIXTURE + f'\nconnection.execute("{statement}")\n'
        )


@pytest.mark.parametrize("statement", ["DELETE FROM ZASSET", "VACUUM"])
def test_replay_sql_allowlist_rejects_executescript(statement: str) -> None:
    with pytest.raises(AssertionError, match="executescript is prohibited"):
        _assert_only_replay_sql(
            REPLAY_SQL_FIXTURE + f'\nconnection.executescript("{statement}")\n'
        )


def test_replay_sql_allowlist_rejects_unrecognized_execution_api() -> None:
    with pytest.raises(AssertionError, match="Unrecognized SQLite execution API"):
        _sqlite_statements('connection.execute_batch("DELETE FROM ZASSET")')


def test_replay_sql_allowlist_rejects_dynamic_sql() -> None:
    with pytest.raises(AssertionError, match="Dynamic SQL"):
        _sqlite_statements("connection.executemany(statement, values)")


def test_native_helper_uses_no_applescript_or_gui_automation() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "native/PhotoKitHelper/Sources/PhotoKitHelper/main.swift").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "applescript" not in lowered
    assert "osascript" not in lowered
    assert "systemevents" not in lowered
    assert "photos.sqlite" not in lowered


def test_native_delete_uses_fixed_signed_trust_boundary() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "native/PhotoKitHelper/Sources/PhotoKitHelper/main.swift").read_text(
        encoding="utf-8"
    )

    assert "APPLE_PHOTOS_AUTH_SECRET_FILE" not in source
    assert "homeDirectoryForCurrentUser" not in source
    assert "getpwuid(getuid())" in source
    assert "HMAC<SHA256>.isValidAuthenticationCode" in source
    assert "native-nonces" in source
    assert "O_EXCL" in source
    assert "items.count <= 50" in source
