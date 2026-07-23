# Docker Setup — Task Tracker

This project ships as three containers orchestrated by Docker Compose:

| Service | What it is | Image | Host port |
|---------|-----------|-------|-----------|
| `api`   | FastAPI app (Swagger at `/docs`) | built from `Dockerfile` | 8000 |
| `ui`    | Gradio client (talks to the API over HTTP) | same image, runs `python ui.py` | 7860 |
| `db`    | PostgreSQL 16 | official `postgres:16` | 5432 |

The `api` and `ui` share one image and differ only in the command they run.

---

## How to run

```bash
# 1. Create your local env file (once)
cp .env.example .env          # edit credentials if you like

# 2. Build images and start the whole stack
docker compose up --build     # add -d to run in the background

# 3. Open in a browser
#    API / Swagger:  http://localhost:8000/docs
#    Gradio UI:      http://localhost:7860

# 4. Stop it
docker compose down           # keeps the DB data (named volume)
docker compose down -v        # ALSO wipes the DB data (fresh start)
```

Handy commands:

```bash
docker compose ps                     # status + health of each service
docker compose logs -f api            # follow the API logs
docker compose exec db psql -U taskuser -d tasks   # a psql shell in the db container
```

---

## Connect DBeaver to the containerized Postgres

1. New Connection → **PostgreSQL**.
2. Host `localhost`, Port `5432` (the `POSTGRES_PORT` from `.env`).
3. Database `tasks`, Username `taskuser`, Password `taskpass` (your `.env` values).
4. Test Connection → Finish.
5. Browse **Databases → tasks → Schemas → public → Tables → task** to see rows.

Any create/update/delete you do through the API (`/docs` or the Gradio UI) shows up
here — the API and DBeaver are talking to the *same* Postgres container.

---

## Understand & explain

**Image vs container.** An *image* is the immutable, built template — your code, its
dependencies, and config frozen into layers (`docker build` produces one). A *container*
is a running instance of an image. One image can spawn many containers; here `api` and
`ui` are two containers from the same image.

**Volume & why the DB needs one.** A container's filesystem is disposable — remove the
container and everything written inside it is gone. Postgres stores its data at
`/var/lib/postgresql/data`; we mount the **named volume** `pgdata` there so that data
lives on the host, *outside* the container's lifecycle. It therefore survives restarts,
rebuilds, and `docker compose down`. **Without a volume, removing the db container would
lose every row** — every `down`/rebuild would start from an empty database.

**`down` vs `down -v`.** `docker compose down` stops and removes the containers and the
network but **keeps named volumes**, so your data is safe. `docker compose down -v` does
the same *and* deletes the volumes — a full wipe, so the next `up` starts with an empty
database. Use `-v` only when you want a clean slate.

**Service-name networking (`db`, not `localhost`).** Compose puts all services on one
private network with a built-in DNS resolver, so a service name like `db` resolves to
that container's IP. Inside the `api` container, `localhost` means the api container
*itself* — not the database — so the connection string uses `@db:5432`. Likewise the UI
reaches the API at `http://api:8000`.

---

## Stretch goals implemented

- **Multi-stage build** (`Dockerfile`): a `builder` stage compiles dependency wheels; the
  final `runtime` stage copies only the installed packages + app code, so build tooling
  never ships. Smaller, cleaner image.
- **DB healthcheck + `depends_on` condition**: `db` runs `pg_isready`; `api` starts only
  once `db` reports `service_healthy` (and `ui` waits for `api`). No boot-race crashes.
- **api healthcheck**: `api` is probed on `/` and reports healthy/unhealthy in
  `docker compose ps`.

### Push the image to Docker Hub (run these yourself — they need your account)

```bash
# 1. Log in (opens a prompt for your Docker Hub username + access token)
docker login

# 2. Tag the local image with your Docker Hub namespace
docker tag task-tracker-api:latest <your-dockerhub-username>/task-tracker-api:latest

# 3. Push it
docker push <your-dockerhub-username>/task-tracker-api:latest
```

Afterwards anyone can `docker pull <your-username>/task-tracker-api` and run it without
building. (To use it in Compose, replace `build: .` on the `api` service with
`image: <your-username>/task-tracker-api:latest`.)
