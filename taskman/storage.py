from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from .models import Task


class TaskStorage:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path).expanduser() if path else Path("~/.taskman/tasks.json").expanduser()
        self.tasks: Dict[str, Task] = {}

    def _ensure_dir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _serialize_task(self, task: Task) -> Dict:
        data = asdict(task)
        data["created_at"] = task.created_at.isoformat()
        return data

    def _deserialize_task(self, data: Dict) -> Task:
        created_at_raw = data.get("created_at")
        if isinstance(created_at_raw, str):
            created_at = datetime.fromisoformat(created_at_raw)
        else:
            raise ValueError("Invalid created_at in storage")

        return Task(
            id=str(data["id"]),
            title=str(data["title"]),
            description=str(data.get("description", "")),
            completed=bool(data.get("completed", False)),
            created_at=created_at,
            priority=str(data.get("priority", "medium")),
        )

    def load(self) -> None:
        self._ensure_dir()
        if not self.path.exists():
            self.tasks = {}
            return

        with self.path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        items = payload.get("tasks", []) if isinstance(payload, dict) else payload
        self.tasks = {}
        if items:
            for item in items:
                task = self._deserialize_task(item)
                self.tasks[task.id] = task

    def save(self) -> None:
        self._ensure_dir()
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        data = {
            "tasks": [self._serialize_task(t) for t in self.list_all()],
        }
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, self.path)

    def add(self, task: Task) -> None:
        if task.id in self.tasks:
            raise KeyError(f"Task with id {task.id} already exists")
        self.tasks[task.id] = task

    def get(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def list_all(self) -> List[Task]:
        return sorted(self.tasks.values(), key=lambda t: t.created_at)

    def update(self, task: Task) -> None:
        if task.id not in self.tasks:
            raise KeyError(f"Task with id {task.id} does not exist")
        self.tasks[task.id] = task

    def delete(self, task_id: str) -> None:
        if task_id not in self.tasks:
            raise KeyError(f"Task with id {task_id} does not exist")
        del self.tasks[task_id]
