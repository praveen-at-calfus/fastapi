"""Database table model and the enums it uses."""

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


# Enums restrict a field to a fixed set of values. Subclassing `str` keeps the
# values as plain strings while FastAPI rejects anything outside the set (422)
# and Swagger renders a dropdown.
class Status(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# table=True makes this a REAL database table (default table name: "task").
# Each annotated attribute becomes a column.
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    status: Status = Field(default=Status.pending)
    priority: Priority = Field(default=Priority.medium)
    # default_factory runs at insert time, so each row gets its own timestamp.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
