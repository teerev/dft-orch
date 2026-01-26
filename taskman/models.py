from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union
from uuid import uuid4


@dataclass
class Task:
    id: str
    title: str
    priority: str = "medium"
    completed: bool = False
    created_at: datetime = None  # type: ignore[assignment]
    due_date: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()

    @staticmethod
    def _parse_due_date(due_date: Optional[Union[str, datetime]]) -> Optional[datetime]:
        if due_date is None:
            return None
        if isinstance(due_date, datetime):
            return due_date
        if isinstance(due_date, str):
            # Expect YYYY-MM-DD
            return datetime.strptime(due_date, "%Y-%m-%d")
        raise TypeError("due_date must be a datetime, YYYY-MM-DD string, or None")

    @classmethod
    def create(
        cls,
        title: str,
        priority: str = "medium",
        due_date: Optional[Union[str, datetime]] = None,
    ) -> "Task":
        return cls(
            id=uuid4().hex[:8],
            title=title,
            priority=priority,
            completed=False,
            created_at=datetime.now(),
            due_date=cls._parse_due_date(due_date),
        )

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        if self.completed:
            return False
        if self.due_date is None:
            return False
        now = now or datetime.now()
        return self.due_date.date() < now.date()

    def days_overdue(self, now: Optional[datetime] = None) -> Optional[int]:
        if not self.is_overdue(now=now):
            return None
        now = now or datetime.now()
        assert self.due_date is not None
        return (now.date() - self.due_date.date()).days
