# ============================================================================
#  Multi-stage Dockerfile for the Task Tracker (used by BOTH the api and ui
#  services — they share one image and differ only in the command they run).
#
#  "Multi-stage" = we use TWO temporary build environments (stages). The first
#  stage installs the Python packages; the second, final stage copies only the
#  installed packages + our code. Build tools and caches from stage 1 are
#  thrown away, so the shipped image is smaller.
# ============================================================================

# ---------- Stage 1: "builder" — install dependencies into a wheelhouse ------
FROM python:3.12-slim AS builder

# Don't write .pyc files, and don't buffer stdout/stderr (so logs appear live).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# psycopg2-binary ships prebuilt wheels, so we need no compiler here.
# Copy ONLY requirements first: this layer is cached and only re-runs when
# requirements.txt changes — not every time our source code changes.
COPY requirements.txt .

# Build wheels for all deps into /app/wheels. Doing this in the builder stage
# means the final stage installs from local wheels (fast, no network needed).
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# ---------- Stage 2: "runtime" — the lean image we actually ship -------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Bring in the prebuilt wheels from the builder stage and install them, then
# delete the wheels — they're not needed once installed.
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Copy the application code (the app/ package and the Gradio ui.py).
COPY app/ ./app/
COPY ui.py ./ui.py

# Run as a non-root user for safety (containers should not run as root).
# Everything COPY'd above is owned by root, so we hand /app to appuser —
# otherwise the non-root process can't write files (e.g. a local SQLite DB)
# into its own working directory.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Document the port the API listens on. EXPOSE is informational — the actual
# host mapping happens with `-p` (run) or `ports:` (compose).
EXPOSE 8000

# Default command: start the FastAPI app. IMPORTANT: bind to 0.0.0.0, not
# 127.0.0.1 — inside a container, 127.0.0.1 is only reachable from within the
# container itself, so the host could never connect. 0.0.0.0 = all interfaces.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
