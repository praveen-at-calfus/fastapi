"""FastAPI application: lifespan, the 5 CRUD routes, and error handling."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select

from app.database import SessionDep, create_db_and_tables
from app.models import Priority, Status, Task
from app.schemas import TaskCreate, TaskResponse, TaskUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Task is imported above, so SQLModel's metadata knows the `task` table
    # before we create it here at startup.
    create_db_and_tables()
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
    changes = payload.model_dump(exclude_unset=True)  # only fields the client sent
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
