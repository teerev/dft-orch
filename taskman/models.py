from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = field(default="")
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("title is required")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            id=data.get("id", str(uuid4())),
            title=data["title"],
            description=data.get("description", ""),
            completed=bool(data.get("completed", False)),
            created_at=created_at if isinstance(created_at, datetime) else datetime.now(),
            completed_at=completed_at if isinstance(completed_at, datetime) else None,
        )
