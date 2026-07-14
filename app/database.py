"""Database engine, table creation, and the session dependency (DI)."""

import os
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///tasks.db"

# echo=True makes SQLModel/SQLAlchemy print every SQL statement it generates.
# Toggle it on with `SQL_ECHO=1` to SEE the SQL behind each ORM call.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=os.getenv("SQL_ECHO") == "1",
)


def create_db_and_tables() -> None:
    """Create any tables that don't exist yet (called once at startup)."""
    SQLModel.metadata.create_all(engine)


def get_session():
    # One session per request. Code before `yield` = setup (open session);
    # code after (the `with` exit) = teardown (close it) — runs even on error.
    with Session(engine) as session:
        yield session


# Reusable alias so each route can just write `session: SessionDep`.
SessionDep = Annotated[Session, Depends(get_session)]
