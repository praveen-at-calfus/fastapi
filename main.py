from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select


# ---------------------------------------------------------------------------
# Enums: restrict a field to a fixed set of values (stored as plain strings).
# ---------------------------------------------------------------------------
class Status(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# ---------------------------------------------------------------------------
# Task: the DATABASE TABLE model. table=True makes it a real table ("task").
# ---------------------------------------------------------------------------
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    status: Status = Field(default=Status.pending)
    priority: Priority = Field(default=Priority.medium)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Schemas: three separate models (no table=True -> pure data shapes, not tables).
# SQLModel is built on Pydantic, so these behave like the BaseModel schemas from
# Phase A, but also read cleanly from Task ORM objects for responses.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Database engine + session dependency (dependency injection).
# ---------------------------------------------------------------------------
engine = create_engine(
    "sqlite:///tasks.db",
    connect_args={"check_same_thread": False},
)


def get_session():
    # One session per request. Code before `yield` = setup (open session);
    # code after (the `with` exit) = teardown (close it) — runs even on error.
    with Session(engine) as session:
        yield session


# Reusable alias so each endpoint can just write `session: SessionDep`.
SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the `task` table (if missing) once at startup.
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="Task Tracker API", lifespan=lifespan)


def get_task_or_404(task_id: int, session: Session) -> Task:
    """Fetch a task by id, or raise 404 if it doesn't exist."""
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Task Tracker API is running"}


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreate, session: SessionDep):
    # Build a Task row from the validated payload (id/created_at auto-filled).
    task = Task(**payload.model_dump())
    session.add(task)      # stage the insert
    session.commit()       # write it to the DB
    session.refresh(task)  # reload so `task` has its DB-assigned id
    return task


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    session: SessionDep,
    status: Status | None = None,
    priority: Priority | None = None,
):
    query = select(Task)
    # Add a WHERE clause per provided filter -> the DB does the filtering.
    if status is not None:
        query = query.where(Task.status == status)
    if priority is not None:
        query = query.where(Task.priority == priority)
    return session.exec(query).all()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, session: SessionDep):
    return get_task_or_404(task_id, session)


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, session: SessionDep):
    task = get_task_or_404(task_id, session)
    # Only the fields the client actually sent (partial update).
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(task, key, value)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, session: SessionDep):
    task = get_task_or_404(task_id, session)
    session.delete(task)
    session.commit()
    return None
