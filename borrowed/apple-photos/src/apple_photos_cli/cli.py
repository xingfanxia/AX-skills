from __future__ import annotations

import argparse
import importlib.metadata
import importlib.resources
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TextIO

from apple_photos_cli import SCHEMA_VERSION, __version__
from apple_photos_cli.adapters.osxphotos_reader import OSXPHOTOS_VERSION, OsxphotosReader
from apple_photos_cli.adapters.photokit_bridge import PhotoKitProcessBridge
from apple_photos_cli.application import Application
from apple_photos_cli.authorization import AuthorizationService
from apple_photos_cli.contracts import render_json, render_jsonl
from apple_photos_cli.errors import EXIT_PARTIAL, ApplePhotosError, usage_error
from apple_photos_cli.manifests import format_time, load_manifest
from apple_photos_cli.similarity import SimilarityPolicy, compare_image_manifest
from apple_photos_cli.state import ReplayStore, default_state_dir, ensure_state_dir


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        render_json(
            {
                "schema_version": SCHEMA_VERSION,
                "command": "argument.parse",
                "ok": False,
                "status": "failed",
                "errors": [
                    {
                        "code": "E_USAGE",
                        "message": message,
                        "exception_type": "ArgumentError",
                    }
                ],
            },
            sys.stderr,
        )
        raise SystemExit(2)


def _add_read_options(parser: argparse.ArgumentParser, *, library: bool = True) -> None:
    if library:
        parser.add_argument("--library", type=Path, help="Photos library bundle to read")
    parser.add_argument("--format", choices=("json", "jsonl"), default="json")
    parser.add_argument("--output", type=Path, help="Write machine output to this file")


def _add_status_parser(parent: argparse._SubParsersAction[Any]) -> None:
    status = parent.add_parser("status", help="Read a local mutation run receipt")
    status.add_argument("run_id")


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        prog="apple-photos",
        description="Inspect Apple Photos and plan safety-gated System Photo Library mutations.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="Check requested runtime capability readiness")
    doctor.add_argument(
        "--capability", choices=("read", "mutation", "all"), default="all"
    )
    helper_source = commands.add_parser(
        "helper-source", help="Locate the buildable Swift helper source"
    )
    helper_source.add_argument("--format", choices=("json", "path"), default="json")

    library = commands.add_parser("library", help="Inspect Photos libraries")
    library_commands = library.add_subparsers(dest="library_command", required=True)
    library_list = library_commands.add_parser("list", help="List the selected or default library")
    _add_read_options(library_list)
    library_inspect = library_commands.add_parser("inspect", help="Inspect a library snapshot")
    _add_read_options(library_inspect)

    album = commands.add_parser("album", help="Inspect albums")
    album_commands = album.add_subparsers(dest="album_command", required=True)
    album_list = album_commands.add_parser("list", help="List normalized albums")
    _add_read_options(album_list)
    mutation_albums = album_commands.add_parser(
        "mutation-list", help="List writable PhotoKit albums and mutation identifiers"
    )
    _add_read_options(mutation_albums, library=False)

    asset = commands.add_parser("asset", help="Inspect and retrieve assets")
    asset_commands = asset.add_subparsers(dest="asset_command", required=True)
    search = asset_commands.add_parser(
        "search", help="Run case-insensitive lexical metadata search"
    )
    search.add_argument("query")
    search.add_argument("--include-sensitive", action="store_true")
    _add_read_options(search)
    listing = asset_commands.add_parser("list", help="List assets deterministically")
    listing.add_argument("--limit", type=int)
    _add_read_options(listing)
    metadata = asset_commands.add_parser("metadata", help="Read assets by frozen local identifier")
    metadata.add_argument("asset_ids", nargs="+")
    _add_read_options(metadata)
    filtering = asset_commands.add_parser("filter", help="Apply an allowlisted JSON filter")
    filtering.add_argument("--filter", type=Path, required=True, dest="filter_path")
    _add_read_options(filtering)
    retrieve = asset_commands.add_parser("retrieve", help="Export original PhotoKit resources")
    retrieve.add_argument("asset_ids", nargs="+")
    retrieve.add_argument("--destination", type=Path, required=True)
    retrieve.add_argument("--network", choices=("allow", "deny"), default="deny")
    _add_read_options(retrieve, library=False)
    mutation_assets = asset_commands.add_parser(
        "mutation-list", help="List PhotoKit assets and mutation identifiers"
    )
    _add_read_options(mutation_assets, library=False)

    metadata_group = commands.add_parser("metadata", help="Dump or back up normalized metadata")
    metadata_commands = metadata_group.add_subparsers(dest="metadata_command", required=True)
    dump = metadata_commands.add_parser("dump", help="Stream the normalized asset view")
    _add_read_options(dump)
    backup = metadata_commands.add_parser("backup", help="Create an atomic metadata backup bundle")
    backup.add_argument("--library", type=Path)
    backup.add_argument("--output", type=Path, required=True)

    evidence = commands.add_parser("evidence", help="Build pixel comparison evidence")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    compare = evidence_commands.add_parser(
        "compare-images", help="Compare frozen image pairs using deterministic pixel metrics"
    )
    compare.add_argument("--input-manifest", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
    compare.add_argument("--max-rgb-mae", type=float, default=0.01)
    compare.add_argument("--max-luma-mae", type=float, default=0.01)
    compare.add_argument("--max-rgb-p99", type=float, default=0.05)

    import_group = commands.add_parser("import", help="Plan or apply one-resource imports")
    import_commands = import_group.add_subparsers(dest="import_command", required=True)
    import_plan = import_commands.add_parser(
        "plan", help="Create an integrity-checksummed dry-run import plan"
    )
    import_plan.add_argument("source", type=Path)
    import_plan.add_argument("--album-id", required=True)
    import_plan.add_argument("--network", choices=("allow", "deny"), default="deny")
    import_plan.add_argument("--output", type=Path, required=True)
    import_apply = import_commands.add_parser("apply", help="Apply a reviewed import manifest")
    import_apply.add_argument("--manifest", type=Path, required=True)
    import_apply.add_argument("--apply", action="store_true", help="Confirm mutation intent")
    _add_status_parser(import_commands)

    import_batch = commands.add_parser("import-batch", help="Plan or apply import batches")
    import_batch_commands = import_batch.add_subparsers(dest="import_batch_command", required=True)
    import_batch_plan = import_batch_commands.add_parser(
        "plan", help="Create an import plan from a JSONL source manifest"
    )
    import_batch_plan.add_argument("--input-manifest", type=Path, required=True)
    import_batch_plan.add_argument("--album-id", required=True)
    import_batch_plan.add_argument("--network", choices=("allow", "deny"), default="deny")
    import_batch_plan.add_argument("--output", type=Path, required=True)
    import_batch_apply = import_batch_commands.add_parser(
        "apply", help="Apply a batch import manifest"
    )
    import_batch_apply.add_argument("--manifest", type=Path, required=True)
    import_batch_apply.add_argument("--apply", action="store_true", help="Confirm mutation intent")
    _add_status_parser(import_batch_commands)

    delete = commands.add_parser(
        "delete", help="Plan, authorize, or apply pixel-verified deletion"
    )
    delete_commands = delete.add_subparsers(dest="delete_command", required=True)
    delete_plan = delete_commands.add_parser(
        "plan", help="Create a delete plan from authorizing pixel evidence"
    )
    delete_plan.add_argument("--evidence-report", type=Path, required=True)
    delete_plan.add_argument("--pair-manifest", type=Path, required=True)
    delete_plan.add_argument("--network", choices=("allow", "deny"), default="deny")
    delete_plan.add_argument("--output", type=Path, required=True)
    _add_delete_authorize(delete_commands)
    _add_delete_apply(delete_commands)
    _add_status_parser(delete_commands)

    delete_batch = commands.add_parser(
        "delete-batch", help="Plan, authorize, or apply batch deletion"
    )
    delete_batch_commands = delete_batch.add_subparsers(dest="delete_batch_command", required=True)
    delete_batch_plan = delete_batch_commands.add_parser(
        "plan", help="Create a batch delete plan from authorizing pixel evidence"
    )
    delete_batch_plan.add_argument("--evidence-report", type=Path, required=True)
    delete_batch_plan.add_argument("--pair-manifest", type=Path, required=True)
    delete_batch_plan.add_argument("--network", choices=("allow", "deny"), default="deny")
    delete_batch_plan.add_argument("--output", type=Path, required=True)
    _add_delete_authorize(delete_batch_commands)
    _add_delete_apply(delete_batch_commands)
    _add_status_parser(delete_batch_commands)
    return parser


def _add_delete_authorize(parent: argparse._SubParsersAction[Any]) -> None:
    authorize = parent.add_parser(
        "authorize", help="Issue a short-lived manifest-bound delete token"
    )
    authorize.add_argument("--manifest", type=Path, required=True)
    authorize.add_argument("--output", type=Path, required=True)


def _add_delete_apply(parent: argparse._SubParsersAction[Any]) -> None:
    apply_parser = parent.add_parser("apply", help="Apply a reviewed and authorized delete plan")
    apply_parser.add_argument("--manifest", type=Path, required=True)
    apply_parser.add_argument("--authorization-token", type=Path, required=True)
    apply_parser.add_argument("--apply", action="store_true", help="Confirm mutation intent")


def _helper_path() -> Path | None:
    configured = os.environ.get("APPLE_PHOTOS_HELPER")
    return Path(configured).expanduser() if configured else None


def _helper_source_path() -> tuple[Path, str]:
    checkout = Path(__file__).resolve().parents[2] / "native" / "PhotoKitHelper"
    if (checkout / "Package.swift").is_file():
        return checkout, "source_checkout"
    bundled = importlib.resources.files("apple_photos_cli").joinpath(
        "bundled", "native", "PhotoKitHelper"
    )
    bundled_path = Path(str(bundled))
    if (bundled_path / "Package.swift").is_file():
        return bundled_path, "installed_wheel"
    raise usage_error(
        "Buildable PhotoKit helper source is not installed.",
        code="E_CAPABILITY_UNSUPPORTED",
    )


def _application(args: argparse.Namespace, *, reader: bool) -> Application:
    state_dir = ensure_state_dir(default_state_dir())
    selected_reader = OsxphotosReader(getattr(args, "library", None)) if reader else None
    return Application(
        reader=selected_reader,
        bridge=PhotoKitProcessBridge(_helper_path()),
        state_dir=state_dir,
    )


def _open_output(args: argparse.Namespace) -> tuple[TextIO, bool]:
    output = getattr(args, "output", None)
    if output is None:
        return sys.stdout, False
    output.parent.mkdir(parents=True, exist_ok=True)
    return output.open("w", encoding="utf-8", newline="\n"), True


def _emit_items(
    args: argparse.Namespace, command: str, record_type: str, items: list[dict[str, Any]]
) -> None:
    stream, should_close = _open_output(args)
    try:
        if args.format == "jsonl":
            from datetime import UTC, datetime

            render_jsonl(
                command=command,
                run_id="run_read",
                records=((record_type, item) for item in items),
                observed_at=format_time(datetime.now(UTC)),
                stream=stream,
            )
        else:
            render_json(
                {
                    "schema_version": SCHEMA_VERSION,
                    "command": command,
                    "ok": True,
                    "status": "succeeded",
                    "counts": {record_type: len(items)},
                    "items": items,
                    "errors": [],
                },
                stream,
            )
    finally:
        if should_close:
            stream.close()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise usage_error(f"Cannot read JSON file {path}: {exc}", code="E_SCHEMA_INVALID") from exc


def _load_jsonl_sources(path: Path) -> list[Path]:
    sources = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise usage_error(f"Cannot read source manifest: {path}") from exc
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            sources.append(Path(value["path"]))
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise usage_error(f"Invalid source manifest record on line {number}.") from exc
    return sources


def _doctor(capability: str) -> dict[str, Any]:
    try:
        installed = importlib.metadata.version("osxphotos")
    except importlib.metadata.PackageNotFoundError:
        installed = None
    helper = _helper_path()
    helper_exists = bool(helper and helper.is_file())
    helper_probe: dict[str, Any] | None = None
    helper_executable = bool(helper_exists and os.access(helper, os.X_OK))
    check_mutation = capability in {"mutation", "all"}
    if helper_executable and check_mutation:
        try:
            snapshot = PhotoKitProcessBridge(helper).probe()
            helper_probe = {
                "ok": True,
                "snapshot_digest": snapshot.digest,
                "physical_identity_verified": snapshot.physical_identity_verified,
            }
        except ApplePhotosError as exc:
            helper_probe = {"ok": False, "error": exc.to_dict()}
    read_ready = bool(sys.version_info >= (3, 11) and installed == OSXPHOTOS_VERSION)
    mutation_ready = bool(
        sys.version_info >= (3, 11) and helper_probe and helper_probe["ok"]
    )
    requested_ready = {
        "read": read_ready,
        "mutation": mutation_ready,
        "all": read_ready and mutation_ready,
    }[capability]
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "command": "doctor",
        "capability_requested": capability,
        "ok": requested_ready,
        "status": "succeeded" if requested_ready else "failed",
        "read_ready": read_ready,
        "mutation_ready": mutation_ready if check_mutation else None,
        "python": {"version": sys.version.split()[0], "supported": sys.version_info >= (3, 11)},
        "osxphotos": {
            "required": OSXPHOTOS_VERSION,
            "installed": installed,
            "compatible": installed == OSXPHOTOS_VERSION,
            "role": "read_only",
        },
        "photokit_helper": {
            "configured": helper is not None,
            "exists": helper_exists,
            "executable": helper_executable,
            "path": str(helper) if helper else None,
            "packaging": "source_included_binary_build_required",
            "live_probe_performed": helper_executable and check_mutation,
            "probe": helper_probe,
            "mutation_ready": mutation_ready if check_mutation else None,
        },
    }
    return result


def run(args: argparse.Namespace, *, stdin: TextIO = sys.stdin, stderr: TextIO = sys.stderr) -> int:
    if args.command == "doctor":
        result = _doctor(args.capability)
        render_json(result, sys.stdout)
        return 0 if result["ok"] else 6
    if args.command == "helper-source":
        path, layout = _helper_source_path()
        if args.format == "path":
            sys.stdout.write(str(path) + "\n")
        else:
            render_json(
                {
                    "schema_version": SCHEMA_VERSION,
                    "command": "helper-source",
                    "ok": True,
                    "status": "succeeded",
                    "helper_source": {
                        "path": str(path),
                        "layout": layout,
                        "build_argv": [
                            "swift", "build", "-c", "release", "--package-path", str(path)
                        ],
                    },
                },
                sys.stdout,
            )
        return 0

    if args.command == "library":
        app = _application(args, reader=True)
        value = app.inspect_library()
        _emit_items(args, f"library.{args.library_command}", "library", [value])
        return 0
    if args.command == "album":
        if args.album_command == "mutation-list":
            bridge = PhotoKitProcessBridge(_helper_path())
            items = [album.to_dict() for album in bridge.list_albums()]
            command = "album.mutation-list"
        else:
            app = _application(args, reader=True)
            items = [album.to_dict() for album in app.list_albums()]
            command = "album.list"
        _emit_items(args, command, "album", items)
        return 0
    if args.command == "asset":
        app = _application(
            args, reader=args.asset_command not in {"retrieve", "mutation-list"}
        )
        if args.asset_command == "search":
            assets = app.search_assets(args.query, include_sensitive=args.include_sensitive)
            items = [asset.to_dict() for asset in assets]
        elif args.asset_command == "list":
            if args.limit is not None and args.limit < 0:
                raise usage_error("--limit must be zero or greater.")
            items = [asset.to_dict() for asset in app.list_assets(limit=args.limit)]
        elif args.asset_command == "metadata":
            items = app.metadata(args.asset_ids)
        elif args.asset_command == "filter":
            value = _load_json(args.filter_path)
            if not isinstance(value, dict):
                raise usage_error("Filter root must be a JSON object.", code="E_FILTER_INVALID")
            items = [asset.to_dict() for asset in app.filter_assets(value)]
        elif args.asset_command == "retrieve":
            items = app.retrieve(
                args.asset_ids,
                output=args.destination,
                network=args.network == "allow",
            )
        else:
            items = []
            for asset in app.bridge.fetch_assets(None):
                value = dict(asset)
                identifier = value.pop("local_identifier")
                value["asset_id"] = {
                    "namespace": "photokit_local_identifier",
                    "value": identifier,
                }
                items.append(value)
        _emit_items(args, f"asset.{args.asset_command}", "asset", items)
        return 0
    if args.command == "evidence":
        policy = SimilarityPolicy(
            max_rgb_mae=args.max_rgb_mae,
            max_luma_mae=args.max_luma_mae,
            max_rgb_p99=args.max_rgb_p99,
        )
        report = compare_image_manifest(args.input_manifest, args.output, policy)
        delete_authorizing = report["delete_authorizing"]
        render_json(
            {
                "schema_version": SCHEMA_VERSION,
                "command": "evidence.compare-images",
                "ok": delete_authorizing,
                "status": "succeeded" if delete_authorizing else "partial",
                "gate_passed": report["gate_passed"],
                "delete_authorizing": delete_authorizing,
                "counts": report["counts"],
                "artifacts": {"report": str(args.output.resolve())},
                "warnings": []
                if delete_authorizing
                else ["Pixel evidence does not authorize delete planning."],
            },
            sys.stdout,
        )
        return 0 if delete_authorizing else EXIT_PARTIAL
    if args.command == "metadata":
        app = _application(args, reader=True)
        if args.metadata_command == "dump":
            _emit_items(
                args, "metadata.dump", "asset", [asset.to_dict() for asset in app.list_assets()]
            )
        else:
            manifest = app.backup_metadata(args.output)
            render_json(
                {
                    "schema_version": SCHEMA_VERSION,
                    "command": "metadata.backup",
                    "ok": True,
                    "status": "succeeded",
                    "artifacts": {"backup": str(args.output.resolve())},
                    "backup": manifest,
                },
                sys.stdout,
            )
        return 0

    group_command = getattr(args, f"{args.command.replace('-', '_')}_command")
    app = _application(args, reader=False)
    if group_command == "status":
        render_json(app.status(args.run_id), sys.stdout)
        return 0
    if args.command in {"import", "import-batch"}:
        if group_command == "plan":
            sources = (
                [args.source]
                if args.command == "import"
                else _load_jsonl_sources(args.input_manifest)
            )
            manifest = app.plan_import(
                sources,
                album_id=args.album_id,
                output=args.output,
                network=args.network == "allow",
            )
            render_json(
                {
                    "schema_version": SCHEMA_VERSION,
                    "command": f"{args.command}.plan",
                    "ok": True,
                    "status": "planned",
                    "manifest_sha256": manifest["manifest_sha256"],
                    "counts": {"planned": len(manifest["items"])},
                    "artifacts": {"manifest": str(args.output.resolve())},
                },
                sys.stdout,
            )
            return 0
        if not args.apply:
            raise usage_error("Import apply requires explicit --apply.")
        result = app.apply_import(args.manifest)
        render_json(result.to_dict(), sys.stdout)
        return 0 if result.ok else EXIT_PARTIAL

    if group_command == "plan":
        manifest = app.plan_delete(
            args.evidence_report,
            args.pair_manifest,
            output=args.output,
            network=args.network == "allow",
        )
        render_json(
            {
                "schema_version": SCHEMA_VERSION,
                "command": f"{args.command}.plan",
                "ok": True,
                "status": "planned",
                "effect": "move_to_recently_deleted",
                "manifest_sha256": manifest["manifest_sha256"],
                "counts": {"planned": len(manifest["items"])},
                "artifacts": {"manifest": str(args.output.resolve())},
            },
            sys.stdout,
        )
        return 0
    state_dir = app.state_dir
    authorization = AuthorizationService(state_dir)
    if group_command == "authorize":
        manifest = load_manifest(args.manifest, expected_type="apple_photos_delete")
        token = authorization.issue(manifest, stdin=stdin, stderr=stderr, output=args.output)
        render_json(
            {
                "schema_version": SCHEMA_VERSION,
                "command": f"{args.command}.authorize",
                "ok": True,
                "status": "authorized",
                "expires_at": token["claims"]["expires_at"],
                "artifacts": {"authorization_token": str(args.output.resolve())},
            },
            sys.stdout,
        )
        return 0
    if not args.apply:
        raise usage_error("Delete apply requires explicit --apply.")
    result = app.apply_delete(
        args.manifest,
        args.authorization_token,
        authorization,
        ReplayStore(state_dir),
    )
    render_json(result.to_dict(), sys.stdout)
    return 0 if result.ok else EXIT_PARTIAL


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    stdin = stdin or sys.stdin
    stderr = stderr or sys.stderr
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args, stdin=stdin, stderr=stderr)
    except ApplePhotosError as exc:
        if stderr.isatty():
            stderr.write("\n")
        render_json(
            {
                "schema_version": SCHEMA_VERSION,
                "command": getattr(args, "command", "unknown"),
                "ok": False,
                "status": "failed",
                "errors": [exc.to_dict()],
            },
            stderr,
        )
        return exc.exit_code
    except KeyboardInterrupt:
        if stderr.isatty():
            stderr.write("\n")
        render_json(
            {
                "schema_version": SCHEMA_VERSION,
                "command": getattr(args, "command", "unknown"),
                "ok": False,
                "status": "cancelled",
                "errors": [
                    {
                        "code": "E_INTERRUPTED",
                        "message": "Interrupted.",
                        "exception_type": "KeyboardInterrupt",
                    }
                ],
            },
            stderr,
        )
        return 130
