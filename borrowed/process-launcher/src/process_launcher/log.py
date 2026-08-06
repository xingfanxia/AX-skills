from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_iso8601(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class HeartbeatLogger:
    def __init__(self, base_dir: str | Path, retention_days: int = 30) -> None:
        self.base_dir = Path(base_dir)
        self.retention_days = retention_days
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self.cleanup()

    def _file_for_date(self, ts: datetime) -> Path:
        return self.base_dir / f"heartbeat_{ts.astimezone(UTC).date().isoformat()}.jsonl"

    def write_event(self, event: str, **payload: Any) -> dict[str, Any]:
        now = utc_now()
        record = {"ts": to_iso8601(now), "event": event, **payload}
        with self._lock:
            self.cleanup()
            with self._file_for_date(now).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def cleanup(self) -> None:
        cutoff = utc_now() - timedelta(days=self.retention_days)
        for path in self.base_dir.glob("heartbeat_*.jsonl"):
            if datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) < cutoff:
                path.unlink(missing_ok=True)

    def read_events(
        self,
        *,
        limit: int = 100,
        event: str | None = None,
        label: str | None = None,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for path in sorted(self.base_dir.glob("heartbeat_*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if event and record.get("event") != event:
                    continue
                if label and record.get("label") != label:
                    continue
                if since:
                    ts = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
                    if ts < since:
                        continue
                events.append(record)
        events.sort(key=lambda item: item["ts"])
        return events[-limit:]


class OutputLogger:
    def __init__(self, base_dir: str | Path, retention_days: int = 30) -> None:
        self.base_dir = Path(base_dir)
        self.retention_days = retention_days
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cleanup()

    def cleanup(self) -> None:
        cutoff = utc_now() - timedelta(days=self.retention_days)
        for path in self.output_dir.glob("*.log"):
            if datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) < cutoff:
                path.unlink(missing_ok=True)

    def create_output_file(self, label: str | None, started_at: datetime) -> Path:
        self.cleanup()
        safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label or "process")
        stamp = started_at.astimezone(UTC).strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"{safe_label}_{stamp}.log"
        path.touch()
        return path

    def list_output_logs(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in sorted(self.output_dir.glob("*.log")):
            stat = path.stat()
            items.append(
                {
                    "filename": path.name,
                    "label": path.stem.rsplit("_", 2)[0],
                    "created_at": to_iso8601(datetime.fromtimestamp(stat.st_mtime, tz=UTC)),
                    "size_bytes": stat.st_size,
                }
            )
        return items

    def read_output_log(self, filename: str, tail: int | None = None) -> dict[str, Any]:
        path = self.output_dir / filename
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(filename)
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        selected = lines[-tail:] if tail else lines
        return {
            "content": "\n".join(selected),
            "total_lines": len(lines),
            "file": str(path),
            "filename": filename,
        }
