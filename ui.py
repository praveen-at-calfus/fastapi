"""Taskie — a role-based Gradio client for the FastAPI Task Tracker API.

Flow:
  1. Landing screen  — glassy "taskie-taskie" title + Enter button.
  2. Role select     — "As a Task Giver" or "As a Task Doer".
  3a. Giver page     — create tasks, set priority, answer doubts, delete. (No status.)
  3b. Doer page      — see tasks, update status, ask doubts, read answers. (No priority/create.)

Each "screen" is a Gradio Column whose `visible` flag we toggle on button clicks.
The UI never touches the DB directly — it talks to the API over HTTP via httpx.
"""

import os

import gradio as gr
import httpx

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

PRIORITIES = ["low", "medium", "high"]
DOER_STATUSES = ["pending", "in_progress", "done"]

# Both roles can SEE the same columns; the difference is which CONTROLS each page
# exposes (a giver never edits status; a doer never edits priority).
COLUMNS = ["id", "title", "description", "priority", "status", "doubt", "answer"]


# --------------------------------------------------------------------------- #
#  API helpers
# --------------------------------------------------------------------------- #
def _fetch_tasks() -> list[dict]:
    r = httpx.get(f"{API_URL}/tasks", timeout=10)
    r.raise_for_status()
    return r.json()


def _rows(tasks: list[dict]) -> list[list]:
    """Turn API task dicts into table rows (None -> "" so the table stays tidy)."""
    return [[("" if t.get(c) is None else t.get(c)) for c in COLUMNS] for t in tasks]


def load_rows() -> list[list]:
    """Fetch the current task list for the table (empty on connection error)."""
    try:
        return _rows(_fetch_tasks())
    except httpx.HTTPError:
        return []


def _put(task_id: int, payload: dict, ok_msg: str):
    """Shared PUT helper: partial-update a task and return (message, fresh rows)."""
    try:
        r = httpx.put(f"{API_URL}/tasks/{task_id}", json=payload, timeout=10)
        r.raise_for_status()
        return ok_msg, load_rows()
    except httpx.HTTPStatusError as e:
        return f"❌ {e.response.status_code}: {e.response.text}", load_rows()
    except httpx.HTTPError as e:
        return f"❌ Could not reach the API: {e}", load_rows()


# --------------------------------------------------------------------------- #
#  Task GIVER actions (create, answer a doubt, delete) — never sets status
# --------------------------------------------------------------------------- #
def giver_create(title, description, priority):
    if not title or not title.strip():
        return "⚠️ Title is required.", load_rows()
    payload = {
        "title": title.strip(),
        "description": (description or "").strip() or None,
        "priority": priority,
    }  # note: no "status" — the server defaults it to "pending"; the doer owns it
    try:
        r = httpx.post(f"{API_URL}/tasks", json=payload, timeout=10)
        r.raise_for_status()
        t = r.json()
        return f"✅ Created task #{t['id']} — “{t['title']}” (priority: {t['priority']}).", load_rows()
    except httpx.HTTPStatusError as e:
        return f"❌ {e.response.status_code}: {e.response.text}", load_rows()
    except httpx.HTTPError as e:
        return f"❌ Could not reach the API: {e}", load_rows()


def giver_answer(task_id, answer):
    if not task_id:
        return "⚠️ Enter the task id you're answering.", load_rows()
    if not answer or not answer.strip():
        return "⚠️ Write an answer first.", load_rows()
    return _put(int(task_id), {"answer": answer.strip()}, f"✅ Answered the doubt on task #{int(task_id)}.")


def giver_delete(task_id):
    if not task_id:
        return "⚠️ Enter a task id to delete.", load_rows()
    tid = int(task_id)
    try:
        r = httpx.delete(f"{API_URL}/tasks/{tid}", timeout=10)
        r.raise_for_status()
        return f"🗑️ Deleted task #{tid}.", load_rows()
    except httpx.HTTPStatusError as e:
        return f"❌ {e.response.status_code}: {e.response.text}", load_rows()
    except httpx.HTTPError as e:
        return f"❌ Could not reach the API: {e}", load_rows()


# --------------------------------------------------------------------------- #
#  Task DOER actions (update status, ask a doubt) — never sets priority/creates
# --------------------------------------------------------------------------- #
def doer_status(task_id, status):
    if not task_id:
        return "⚠️ Enter the task id.", load_rows()
    return _put(int(task_id), {"status": status}, f"✅ Task #{int(task_id)} marked “{status}”.")


def doer_ask(task_id, doubt):
    if not task_id:
        return "⚠️ Enter the task id.", load_rows()
    if not doubt or not doubt.strip():
        return "⚠️ Write your doubt first.", load_rows()
    return _put(int(task_id), {"doubt": doubt.strip()}, f"🙋 Doubt sent for task #{int(task_id)}.")


# --------------------------------------------------------------------------- #
#  Navigation: return visibility for [landing, role, giver, doer]
# --------------------------------------------------------------------------- #
def go(screen: str):
    order = ["landing", "role", "giver", "doer"]
    return tuple(gr.update(visible=(name == screen)) for name in order)


# --------------------------------------------------------------------------- #
#  Styling — white screen, glassy blue-green title, rounded gradient buttons
# --------------------------------------------------------------------------- #
CSS = """
/* Force a clean LIGHT look even when the OS/browser is in dark mode. Otherwise
   Gradio renders its dark theme: dark page margins (a black band at the edges)
   and light-colored text that becomes invisible on our white panels. We pin
   Gradio's theme variables to light values and set explicit text colors. */
.gradio-container, .gradio-container.dark, .dark, gradio-app {
  --body-background-fill: #ffffff;
  --background-fill-primary: #ffffff;
  --background-fill-secondary: #f8fafc;
  --block-background-fill: #ffffff;
  --body-text-color: #0f172a;
  --body-text-color-subdued: #475569;
  --block-title-text-color: #0f172a;
  --block-label-text-color: #0f172a;
  /* inputs, dropdowns, borders and tables -> light too (else they stay dark
     navy in dark mode and clash with the white page) */
  --input-background-fill: #ffffff;
  --input-background-fill-focus: #ffffff;
  --input-border-color: #cbd5e1;
  --input-border-color-focus: #14b8a6;
  --input-placeholder-color: #94a3b8;
  --border-color-primary: #e2e8f0;
  --border-color-accent: #99f6e4;
  --table-even-background-fill: #ffffff;
  --table-odd-background-fill: #f8fafc;
  --table-border-color: #e2e8f0;
  --table-text-color: #0f172a;
  color-scheme: light;
}
html, body, gradio-app, .gradio-container {
  background: #ffffff !important;
  color: #0f172a !important;
}
.gradio-container { max-width: 1080px !important; margin: 0 auto !important; }
footer { display: none !important; }

/* Landing + role screens. NOTE: we must NOT set `display` on these columns —
   Gradio toggles their visibility via display:none/block, and an id-selector
   `display:flex` here overrides that and breaks the show/hide (the role screen
   went blank after Enter). So we center with padding + text-align instead. */
#landing, #role { padding-top: 11vh; text-align: center; }

/* Glassy blue-green title card */
.glass-card {
  display: inline-block;
  padding: 46px 76px;
  border-radius: 30px;
  background: linear-gradient(135deg, rgba(16,185,129,0.16), rgba(6,182,212,0.16));
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.75);
  box-shadow: 0 14px 44px rgba(13,148,136,0.28), inset 0 1px 0 rgba(255,255,255,0.7);
}
.glass-text {
  font-size: 4.2rem; font-weight: 800; letter-spacing: 1px;
  background: linear-gradient(120deg, #0e7490, #10b981 55%, #0891b2);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; color: transparent;
}
.center-wrap { width: 100%; text-align: center; }
.role-q { color: #0f766e; font-weight: 700; font-size: 1.6rem; }

/* Enter button — rounded gradient pill, not full width */
.cta { max-width: 240px; margin: 28px auto 0 !important; }
.cta button, button.cta {
  background: linear-gradient(120deg, #0891b2, #10b981) !important;
  color: #fff !important; border: none !important;
  font-size: 1.1rem !important; font-weight: 700 !important;
  padding: 12px 44px !important; border-radius: 999px !important;
  box-shadow: 0 8px 24px rgba(16,185,129,0.35) !important;
}

/* Role choice buttons — big soft cards */
.rolerow { justify-content: center !important; gap: 22px !important; margin-top: 30px; }
.rolebtn { max-width: 300px; }
.rolebtn button {
  color: #0f766e !important;
  font-size: 1.15rem !important; font-weight: 700 !important;
  padding: 30px 18px !important; border-radius: 20px !important;
  border: 1px solid rgba(13,148,136,0.35) !important;
  background: linear-gradient(135deg, rgba(16,185,129,0.10), rgba(6,182,212,0.10)) !important;
}
.rolebtn button:hover {
  border-color: rgba(13,148,136,0.6) !important;
  box-shadow: 0 8px 24px rgba(16,185,129,0.20) !important;
}
"""


with gr.Blocks(title="Taskie") as demo:

    # ----------------------------- 1. Landing ----------------------------- #
    with gr.Column(visible=True, elem_id="landing") as landing:
        gr.HTML('<div class="center-wrap"><div class="glass-card">'
                '<span class="glass-text">taskie-taskie</span></div></div>')
        enter_btn = gr.Button("Enter", elem_classes="cta")

    # --------------------------- 2. Role select --------------------------- #
    with gr.Column(visible=False, elem_id="role") as role:
        gr.HTML('<div class="center-wrap"><span class="role-q">How would you like to continue?</span></div>')
        with gr.Row(elem_classes="rolerow"):
            giver_btn = gr.Button("🧑‍💼 As a Task Giver", elem_classes="rolebtn")
            doer_btn = gr.Button("🛠️ As a Task Doer", elem_classes="rolebtn")

    # ---------------------------- 3a. Giver ------------------------------- #
    with gr.Column(visible=False) as giver:
        gr.Markdown("## 🧑‍💼 Task Giver\nCreate tasks, set their priority, and answer doubts. "
                    "*(You don't set status — the doer does.)*")
        giver_msg = gr.Markdown()
        with gr.Row():
            with gr.Column():
                gr.Markdown("### ➕ Create a task")
                g_title = gr.Textbox(label="Title")
                g_desc = gr.Textbox(label="Description", lines=2)
                g_priority = gr.Dropdown(PRIORITIES, value="medium", label="Priority")
                g_create = gr.Button("Create task", variant="primary")
            with gr.Column():
                gr.Markdown("### 💬 Answer a doubt")
                ga_id = gr.Number(label="Task id", precision=0)
                ga_answer = gr.Textbox(label="Your answer", lines=2)
                ga_btn = gr.Button("Send answer", variant="primary")
                gr.Markdown("### 🗑️ Delete a task")
                gd_id = gr.Number(label="Task id", precision=0)
                gd_btn = gr.Button("Delete", variant="stop")
        gr.Markdown("### 📋 All tasks")
        g_refresh = gr.Button("Refresh")
        giver_table = gr.Dataframe(headers=COLUMNS, interactive=False, wrap=True)
        g_back = gr.Button("← Switch role")

    # ---------------------------- 3b. Doer -------------------------------- #
    with gr.Column(visible=False) as doer:
        gr.Markdown("## 🛠️ Task Doer\nWork through your tasks: update status and ask doubts. "
                    "*(Priority is set by the giver.)*")
        doer_msg = gr.Markdown()
        with gr.Row():
            with gr.Column():
                gr.Markdown("### ✅ Update status")
                ds_id = gr.Number(label="Task id", precision=0)
                ds_status = gr.Dropdown(DOER_STATUSES, value="in_progress", label="Status")
                ds_btn = gr.Button("Update status", variant="primary")
            with gr.Column():
                gr.Markdown("### 🙋 Ask a doubt")
                dq_id = gr.Number(label="Task id", precision=0)
                dq_text = gr.Textbox(label="Your doubt", lines=2)
                dq_btn = gr.Button("Send doubt", variant="primary")
        gr.Markdown("### 📋 Your tasks (answers from the giver show in the *answer* column)")
        d_refresh = gr.Button("Refresh")
        doer_table = gr.Dataframe(headers=COLUMNS, interactive=False, wrap=True)
        d_back = gr.Button("← Switch role")

    # ----------------------------- wiring --------------------------------- #
    screens = [landing, role, giver, doer]

    enter_btn.click(lambda: go("role"), outputs=screens)
    giver_btn.click(lambda: go("giver"), outputs=screens).then(load_rows, outputs=giver_table)
    doer_btn.click(lambda: go("doer"), outputs=screens).then(load_rows, outputs=doer_table)
    g_back.click(lambda: go("role"), outputs=screens)
    d_back.click(lambda: go("role"), outputs=screens)

    # Giver actions
    g_create.click(giver_create, [g_title, g_desc, g_priority], [giver_msg, giver_table])
    ga_btn.click(giver_answer, [ga_id, ga_answer], [giver_msg, giver_table])
    gd_btn.click(giver_delete, [gd_id], [giver_msg, giver_table])
    g_refresh.click(load_rows, outputs=giver_table)

    # Doer actions
    ds_btn.click(doer_status, [ds_id, ds_status], [doer_msg, doer_table])
    dq_btn.click(doer_ask, [dq_id, dq_text], [doer_msg, doer_table])
    d_refresh.click(load_rows, outputs=doer_table)


if __name__ == "__main__":
    # Gradio 6.0 takes css/theme on launch(), not on the Blocks constructor.
    demo.launch(server_port=7860, css=CSS, theme=gr.themes.Soft())
