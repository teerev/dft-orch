from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .serialization import append_jsonl


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def log_event(
    log_path: Path,
    *,
    node: str,
    event: str,
    message: str | None = None,
    **fields: Any,
) -> None:
    record: dict[str, Any] = {
        "ts_utc": utc_now_iso(),
        "node": node,
        "event": event,
    }
    if message is not None:
        record["message"] = message
    if fields:
        record.update(fields)
    append_jsonl(log_path, record)
