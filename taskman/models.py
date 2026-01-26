from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    priority: str = "medium"

    @classmethod
    def create(cls, title, description="", priority="medium"):
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            priority=priority
        )
