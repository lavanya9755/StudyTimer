"""
StudyFlow - Session Model
Defines the data structure for study sessions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class StudySession:
    """Represents a single study session."""
    id: Optional[int] = None
    date: str = ""
    start_time: str = ""
    end_time: str = ""
    duration: str = ""
    duration_seconds: int = 0
    notes: str = ""
    remark: str = ""

    @classmethod
    def from_db_row(cls, row: tuple) -> "StudySession":
        """Create a StudySession from a database row."""
        return cls(
            id=row[0],
            date=row[1],
            start_time=row[2],
            end_time=row[3],
            duration=row[4],
            duration_seconds=row[5],
            notes=row[6],
            remark=row[7],
        )

    def duration_hours(self) -> float:
        """Return duration in decimal hours."""
        return self.duration_seconds / 3600

    def duration_display(self) -> str:
        """Return human-readable duration like '4h 36m'."""
        h = self.duration_seconds // 3600
        m = (self.duration_seconds % 3600) // 60
        if h > 0:
            return f"{h}h {m:02d}m"
        return f"{m}m"
