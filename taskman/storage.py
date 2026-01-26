from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _today() -> date:
    return date.today()


def parse_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    # Expect ISO YYYY-MM-DD
    return datetime.strptime(value, "%Y-%m-%d").date()


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    priority: str = "medium"  # low|medium|high
    due: Optional[date] = None
    completed: bool = False
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

    @property
    def status(self) -> str:
        return "completed" if self.completed else "pending"

    def is_overdue(self, today: Optional[date] = None) -> bool:
        if today is None:
            today = _today()
        return (not self.completed) and self.due is not None and self.due < today

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["due"] = self.due.isoformat() if self.due else None
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "Task":
        due = parse_date(d.get("due"))
        return cls(
            id=d["id"],
            title=d.get("title", ""),
            description=d.get("description", ""),
            priority=d.get("priority", "medium"),
            due=due,
            completed=bool(d.get("completed", False)),
            created_at=d.get("created_at"),
            completed_at=d.get("completed_at"),
        )


class TaskStore:
    def __init__(self, path: Optional[Path] = None):
        if path is None:
            base = Path(os.environ.get("TASKMAN_HOME", Path.home() / ".taskman"))
            base.mkdir(parents=True, exist_ok=True)
            path = base / "tasks.json"
        self.path = path

    def load(self) -> List[Task]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        return [Task.from_dict(x) for x in data]

    def save(self, tasks: Iterable[Task]) -> None:
        data = [t.to_dict() for t in tasks]
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def all(self) -> List[Task]:
        return self.load()


def filter_tasks(
    tasks: Iterable[Task],
    *,
    priority: Optional[str] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
) -> List[Task]:
    out: List[Task] = []
    for t in tasks:
        if priority is not None and t.priority != priority:
            continue
        if due_before is not None:
            # "due before" implies tasks with a due date strictly before
            if t.due is None or not (t.due < due_before):
                continue
        if due_after is not None:
            # "due after" implies tasks with a due date strictly after
            if t.due is None or not (t.due > due_after):
                continue
        out.append(t)
    return out
