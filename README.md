# Task Tracker API

A small REST API to manage tasks, backed by a real SQLite database.

**Stack:** FastAPI · SQLModel · SQLite · Uvicorn

## Features

- Full CRUD for tasks (`create` / `list` / `read` / `update` / `delete`)
- Filtering the list by `status` and `priority` via query params
- Separate request/response schemas (`TaskCreate`, `TaskUpdate`, `TaskResponse`)
- Database session via dependency injection (`Depends(get_session)`)
- Proper error handling: `404` for missing tasks, automatic `422` for invalid input
- Auto-generated Swagger UI at `/docs`

## Data model

A `Task` has:

| Field         | Type                                   | Notes                          |
|---------------|----------------------------------------|--------------------------------|
| `id`          | int                                    | primary key, auto-assigned     |
| `title`       | str                                    | required                       |
| `description` | str \| null                            | optional                       |
| `status`      | enum: `pending` / `in_progress` / `done` | defaults to `pending`        |
| `priority`    | enum: `low` / `medium` / `high`        | defaults to `medium`           |
| `created_at`  | datetime                               | set by the server on create    |

## Setup

Requires Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "fastapi[standard]" sqlmodel
```

## Run

```bash
source .venv/bin/activate
uvicorn main:app --reload
# or: fastapi dev main.py
```

The server starts on http://127.0.0.1:8000 and creates a `tasks.db` SQLite file
in the project directory on first startup.

- Swagger UI: http://127.0.0.1:8000/docs

## Endpoints

| Method | Path              | Description                                        |
|--------|-------------------|----------------------------------------------------|
| POST   | `/tasks`          | Create a task                                      |
| GET    | `/tasks`          | List tasks (optional `?status=` and `?priority=`)  |
| GET    | `/tasks/{id}`     | Get one task (404 if missing)                      |
| PUT    | `/tasks/{id}`     | Partial update (send only the fields to change)    |
| DELETE | `/tasks/{id}`     | Delete a task (204 No Content)                     |

### Examples

```bash
# create
curl -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Write the API","priority":"high"}'

# list + filter
curl "http://127.0.0.1:8000/tasks?status=pending&priority=high"

# partial update
curl -X PUT http://127.0.0.1:8000/tasks/1 \
  -H 'Content-Type: application/json' -d '{"status":"done"}'

# delete
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

## Verify the database with DBeaver

1. Install **DBeaver Community Edition** (free).
2. *New Database Connection* → **SQLite** → set the database file to the
   `tasks.db` in this project directory → accept the SQLite driver download →
   *Finish*.
3. Expand *Tables → task → Data*.
4. Perform CRUD operations via `/docs`, then **Refresh** (F5) the Data tab to
   confirm rows are actually created / updated / deleted — don't rely on the
   HTTP `200` alone.
