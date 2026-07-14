"""Gradio UI for the Task Tracker API.

Runs as its own process (port 7860) and talks to the FastAPI service over HTTP
via httpx -- it never touches the database directly. This is a real API client.
"""

import os

import gradio as gr
import httpx

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

STATUSES = ["pending", "in_progress", "done"]
PRIORITIES = ["low", "medium", "high"]
COLUMNS = ["id", "title", "description", "status", "priority", "created_at"]
UNCHANGED = "(unchanged)"  # dropdown sentinel meaning "don't change this field"


def _rows(tasks: list[dict]) -> list[list]:
    """Turn API task dicts into rows for the Dataframe."""
    return [
        [t["id"], t["title"], t.get("description") or "", t["status"], t["priority"], t["created_at"]]
        for t in tasks
    ]


def list_tasks(status_filter: str = "all", priority_filter: str = "all") -> list[list]:
    """GET /tasks (optionally filtered) and return rows for the table."""
    params = {}
    if status_filter and status_filter != "all":
        params["status"] = status_filter
    if priority_filter and priority_filter != "all":
        params["priority"] = priority_filter
    try:
        r = httpx.get(f"{API_URL}/tasks", params=params, timeout=10)
        r.raise_for_status()
        return _rows(r.json())
    except httpx.HTTPError as e:
        raise gr.Error(f"Could not reach the API at {API_URL}: {e}")


def create_task(title, description, status, priority):
    """POST /tasks then refresh the (unfiltered) table."""
    if not title or not title.strip():
        return "⚠️ Title is required.", list_tasks()
    payload = {
        "title": title.strip(),
        "description": (description or "").strip() or None,
        "status": status,
        "priority": priority,
    }
    try:
        r = httpx.post(f"{API_URL}/tasks", json=payload, timeout=10)
        r.raise_for_status()
        t = r.json()
        return f"✅ Created task #{t['id']} — “{t['title']}”.", list_tasks()
    except httpx.HTTPStatusError as e:
        return f"❌ {e.response.status_code}: {e.response.text}", list_tasks()
    except httpx.HTTPError as e:
        return f"❌ {e}", []


def load_task(task_id):
    """GET /tasks/{id} and prefill the Manage fields with its current values."""
    if not task_id:
        return gr.update(), gr.update(), gr.update(), gr.update(), "⚠️ Enter a task id."
    tid = int(task_id)
    try:
        r = httpx.get(f"{API_URL}/tasks/{tid}", timeout=10)
        r.raise_for_status()
        t = r.json()
        return t["title"], t.get("description") or "", t["status"], t["priority"], f"✏️ Loaded task #{tid} for editing."
    except httpx.HTTPStatusError as e:
        return gr.update(), gr.update(), gr.update(), gr.update(), f"❌ {e.response.status_code}: {e.response.text}"
    except httpx.HTTPError as e:
        return gr.update(), gr.update(), gr.update(), gr.update(), f"❌ {e}"


def update_task(task_id, new_title, new_description, new_status, new_priority):
    """PUT /tasks/{id} with ONLY the fields the user changed (partial update)."""
    if not task_id:
        return "⚠️ Enter a task id.", list_tasks()
    tid = int(task_id)

    # Build a partial payload: include a field only if the user set it.
    payload = {}
    if new_title and new_title.strip():
        payload["title"] = new_title.strip()
    if new_description and new_description.strip():
        payload["description"] = new_description.strip()
    if new_status and new_status != UNCHANGED:
        payload["status"] = new_status
    if new_priority and new_priority != UNCHANGED:
        payload["priority"] = new_priority

    if not payload:
        return "⚠️ Nothing to update — fill at least one field (or pick a status/priority).", list_tasks()

    try:
        r = httpx.put(f"{API_URL}/tasks/{tid}", json=payload, timeout=10)
        r.raise_for_status()
        return f"✅ Updated task #{tid}: changed {', '.join(payload)}.", list_tasks()
    except httpx.HTTPStatusError as e:
        return f"❌ {e.response.status_code}: {e.response.text}", list_tasks()
    except httpx.HTTPError as e:
        return f"❌ {e}", []


def delete_task(task_id):
    """DELETE /tasks/{id} (expects 204)."""
    if not task_id:
        return "⚠️ Enter a task id.", list_tasks()
    tid = int(task_id)
    try:
        r = httpx.delete(f"{API_URL}/tasks/{tid}", timeout=10)
        r.raise_for_status()
        return f"🗑️ Deleted task #{tid}.", list_tasks()
    except httpx.HTTPStatusError as e:
        return f"❌ {e.response.status_code}: {e.response.text}", list_tasks()
    except httpx.HTTPError as e:
        return f"❌ {e}", []


with gr.Blocks(title="Task Tracker") as demo:
    gr.Markdown("# 📋 Task Tracker\nA Gradio client for the FastAPI Task Tracker API.")
    message = gr.Markdown()

    with gr.Tabs():
        with gr.Tab("📖 Tasks"):
            with gr.Row():
                filter_status = gr.Dropdown(["all"] + STATUSES, value="all", label="Filter: status")
                filter_priority = gr.Dropdown(["all"] + PRIORITIES, value="all", label="Filter: priority")
                refresh_btn = gr.Button("Refresh")
            table = gr.Dataframe(headers=COLUMNS, label="task table", interactive=False, wrap=True)

        with gr.Tab("➕ Create"):
            title = gr.Textbox(label="Title")
            description = gr.Textbox(label="Description", lines=2)
            create_status = gr.Dropdown(STATUSES, value="pending", label="Status")
            create_priority = gr.Dropdown(PRIORITIES, value="medium", label="Priority")
            create_btn = gr.Button("Create", variant="primary")

        with gr.Tab("✏️ Manage"):
            with gr.Row():
                task_id = gr.Number(label="Task id", precision=0)
                load_btn = gr.Button("Load current values")
            gr.Markdown("Fill only the fields you want to change (blank / “(unchanged)” = leave as-is).")
            new_title = gr.Textbox(label="New title")
            new_description = gr.Textbox(label="New description", lines=2)
            new_status = gr.Dropdown([UNCHANGED] + STATUSES, value=UNCHANGED, label="New status")
            new_priority = gr.Dropdown([UNCHANGED] + PRIORITIES, value=UNCHANGED, label="New priority")
            with gr.Row():
                update_btn = gr.Button("Update", variant="primary")
                delete_btn = gr.Button("Delete", variant="stop")

    create_btn.click(create_task, [title, description, create_status, create_priority], [message, table])
    load_btn.click(load_task, [task_id], [new_title, new_description, new_status, new_priority, message])
    update_btn.click(update_task, [task_id, new_title, new_description, new_status, new_priority], [message, table])
    delete_btn.click(delete_task, [task_id], [message, table])
    refresh_btn.click(list_tasks, [filter_status, filter_priority], [table])
    # Populate the table on page load.
    demo.load(list_tasks, [filter_status, filter_priority], [table])


if __name__ == "__main__":
    demo.launch(server_port=7860)
