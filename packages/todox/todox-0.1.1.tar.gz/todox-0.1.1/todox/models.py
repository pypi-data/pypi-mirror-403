
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Todo:
    id: int
    title: str
    done: bool = False
    tags: List[str] = field(default_factory=list)
    repo: Optional[str] = None
    branch: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[str] = None
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    time_spent: int = 0  # seconds
