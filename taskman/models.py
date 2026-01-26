from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


_ALLOWED_PRIORITIES = {"low", "medium", "high"}


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = None  # type: ignore[assignment]
    priority: str = "medium"

    def __post_init__(self) -> None:
        if self.priority not in _ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of {sorted(_ALLOWED_PRIORITIES)}")
        if self.created_at is None:
            raise ValueError("created_at is required")

    @classmethod
    def create(cls, title: str, description: str = "", priority: str = "medium") -> "Task":
        if priority not in _ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of {sorted(_ALLOWED_PRIORITIES)}")
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            completed=False,
            created_at=datetime.now(timezone.utc),
            priority=priority,
        )
