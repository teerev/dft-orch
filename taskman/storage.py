from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from .models import Task


class StorageError(Exception):
    """Base storage error."""


class TaskNotFoundError(StorageError):
    """Raised when a task cannot be found."""


class AmbiguousTaskIdError(StorageError):
    """Raised when a partial task id matches more than one task."""


_DEFAULT_DIR = Path(os.environ.get("TASKMAN_HOME", Path.home() / ".taskman"))
_DEFAULT_PATH = _DEFAULT_DIR / "tasks.json"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_tasks(path: Path = _DEFAULT_PATH) -> List[Task]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    tasks: List[Task] = []
    for item in data or []:
        tasks.append(Task(**item))
    return tasks


def _save_tasks(tasks: List[Task], path: Path = _DEFAULT_PATH) -> None:
    _ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump([asdict(t) for t in tasks], f, indent=2, ensure_ascii=False)


def list_tasks(path: Path = _DEFAULT_PATH) -> List[Task]:
    return _load_tasks(path)


def add_task(title: str, path: Path = _DEFAULT_PATH) -> Task:
    tasks = _load_tasks(path)
    t = Task(id=uuid.uuid4().hex, title=title, completed=False)
    tasks.append(t)
    _save_tasks(tasks, path)
    return t


def find_by_id(task_id: str, path: Path = _DEFAULT_PATH) -> Optional[Task]:
    tasks = _load_tasks(path)
    for t in tasks:
        if t.id == task_id:
            return t
    return None


def find_by_partial_id(partial_id: str, path: Path = _DEFAULT_PATH) -> Task | None:
    """Resolve a task by partial id.

    Returns:
        The matching task if exactly one matches, or None if none match.

    Raises:
        AmbiguousTaskIdError: if more than one task matches the partial id.
    """
    partial = (partial_id or "").strip()
    if not partial:
        return None

    tasks = _load_tasks(path)
    matches = [t for t in tasks if t.id.startswith(partial)]
    if not matches:
        return None
    if len(matches) > 1:
        raise AmbiguousTaskIdError(
            f"Ambiguous task id '{partial_id}': matches {len(matches)} tasks"
        )
    return matches[0]


def complete_task(task: Task, path: Path = _DEFAULT_PATH) -> Task:
    tasks = _load_tasks(path)
    updated = None
    for i, t in enumerate(tasks):
        if t.id == task.id:
            tasks[i] = Task(id=t.id, title=t.title, completed=True)
            updated = tasks[i]
            break
    if updated is None:
        raise TaskNotFoundError(f"Task not found: {task.id}")
    _save_tasks(tasks, path)
    return updated


def delete_task(task: Task, path: Path = _DEFAULT_PATH) -> None:
    tasks = _load_tasks(path)
    new_tasks = [t for t in tasks if t.id != task.id]
    if len(new_tasks) == len(tasks):
        raise TaskNotFoundError(f"Task not found: {task.id}")
    _save_tasks(new_tasks, path)
