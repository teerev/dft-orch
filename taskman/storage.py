from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import Task


class TaskStorage:
    def __init__(self, path: Optional[str] = None) -> None:
        default_path = Path.home() / ".taskman" / "tasks.json"
        self.path = Path(path) if path else default_path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> List[Task]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        tasks: List[Task] = []
        for item in data:
            created_at = item.get("created_at")
            due_date = item.get("due_date")
            tasks.append(
                Task(
                    id=item["id"],
                    title=item["title"],
                    priority=item.get("priority", "medium"),
                    completed=bool(item.get("completed", False)),
                    created_at=datetime.fromisoformat(created_at) if created_at else datetime.now(),
                    due_date=datetime.fromisoformat(due_date) if due_date else None,
                )
            )
        return tasks

    def save(self, tasks: List[Task]) -> None:
        serializable = []
        for t in tasks:
            d = asdict(t)
            d["created_at"] = t.created_at.isoformat() if t.created_at else None
            d["due_date"] = t.due_date.isoformat() if t.due_date else None
            serializable.append(d)
        self.path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")

    def add(self, task: Task) -> None:
        tasks = self.load()
        tasks.append(task)
        self.save(tasks)

    def update(self, task: Task) -> None:
        tasks = self.load()
        updated = False
        for i, t in enumerate(tasks):
            if t.id == task.id:
                tasks[i] = task
                updated = True
                break
        if not updated:
            tasks.append(task)
        self.save(tasks)

    def list(self) -> List[Task]:
        return self.load()
