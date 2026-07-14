"""Request/response schemas — three separate models, one per job.

These are plain data shapes (no table=True), used by FastAPI to validate
requests and shape responses. SQLModel is built on Pydantic, so they behave
like Pydantic models and also read cleanly from Task ORM objects.
"""

from datetime import datetime

from sqlmodel import SQLModel

from app.models import Priority, Status


class TaskCreate(SQLModel):
    """What a client may SEND to create a task. No id/created_at (server-set)."""
    title: str
    description: str | None = None
    status: Status = Status.pending
    priority: Priority = Priority.medium


class TaskUpdate(SQLModel):
    """What a client may SEND to update. Every field optional = partial update."""
    title: str | None = None
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None


class TaskResponse(SQLModel):
    """What we SEND BACK. Includes the server-generated id and created_at."""
    id: int
    title: str
    description: str | None
    status: Status
    priority: Priority
    created_at: datetime
