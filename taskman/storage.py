from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _default_data() -> Dict[str, Any]:
    return {"tasks": []}


def _load(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return _default_data()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "tasks" not in data or not isinstance(data["tasks"], list):
            return _default_data()
        return data
    except (OSError, json.JSONDecodeError):
        return _default_data()


def _save(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def default_store_path() -> str:
    env = os.environ.get("TASKMAN_STORE")
    if env:
        return env
    return os.path.join(os.getcwd(), ".taskman", "tasks.json")


def add_task(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    store_path: Optional[str] = None,
) -> str:
    sp = store_path or default_store_path()
    data = _load(sp)

    task_id = uuid4().hex
    task = {
        "id": task_id,
        "title": title,
        "description": description or "",
        "priority": priority,
        "status": "pending",
        "created": _now_iso(),
        "completed": None,
    }
    data["tasks"].append(task)
    _save(sp, data)
    return task_id


def list_tasks(
    *,
    show_all: bool = False,
    completed_only: bool = False,
    pending_only: bool = False,
    store_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    sp = store_path or default_store_path()
    data = _load(sp)
    tasks: List[Dict[str, Any]] = list(data.get("tasks", []))

    if show_all:
        return tasks

    if completed_only and pending_only:
        return tasks

    if completed_only:
        return [t for t in tasks if t.get("status") == "completed"]
    if pending_only or (not completed_only and not pending_only):
        return [t for t in tasks if t.get("status") != "completed"]

    return tasks
