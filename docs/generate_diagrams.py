"""Generate the project diagrams as SVG + PNG using Graphviz.

Requires the `dot` binary (`brew install graphviz`) and the `graphviz` pip
package. Run from anywhere:

    python docs/generate_diagrams.py

Writes docs/architecture.{svg,png} and docs/learning-flow.{svg,png}.
"""

import os

from graphviz import Digraph

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))


def _save(graph: Digraph, name: str) -> None:
    for fmt in ("svg", "png"):
        graph.format = fmt
        graph.render(filename=name, directory=DOCS_DIR, cleanup=True)
    print(f"wrote {name}.svg and {name}.png")


def architecture() -> Digraph:
    g = Digraph("architecture")
    g.attr(rankdir="LR", bgcolor="white", fontname="Helvetica")
    g.attr("node", fontname="Helvetica", shape="box", style="rounded,filled")
    g.attr("edge", fontname="Helvetica", fontsize="10")

    g.node("user", "User\n(browser)", shape="oval", fillcolor="#e8eaf6")
    g.node("gradio", "Gradio UI\nui.py  (:7860)", fillcolor="#fff3e0")
    g.node("db", "SQLite\ntasks.db", shape="cylinder", fillcolor="#e0f2f1")
    g.node("dbeaver", "DBeaver\n(inspect / verify)", shape="oval", fillcolor="#f3e5f5")

    with g.subgraph(name="cluster_api") as c:
        c.attr(label="FastAPI process (:8000)", style="rounded", color="#90a4ae", fontname="Helvetica")
        c.node("routes", "app/main.py\nroutes + Swagger /docs", fillcolor="#e3f2fd")
        c.node("schemas", "app/schemas.py\nCreate / Update / Response\n(validation → 422)", fillcolor="#e3f2fd")
        c.node("database", "app/database.py\nengine + get_session (DI)", fillcolor="#e3f2fd")
        c.node("models", "app/models.py\nTask ORM + enums", fillcolor="#e3f2fd")

    g.edge("user", "gradio", label="uses")
    g.edge("gradio", "routes", label="httpx · HTTP /tasks")
    g.edge("routes", "schemas", label="validate in/out")
    g.edge("routes", "database", label="Depends(session)")
    g.edge("routes", "models", label="build / query Task")
    g.edge("database", "db", label="SQL via engine")
    g.edge("dbeaver", "db", label="SELECT", style="dashed", dir="back")
    return g


def learning_flow() -> Digraph:
    g = Digraph("learning-flow")
    g.attr(rankdir="TB", bgcolor="white", fontname="Helvetica")
    g.attr("node", fontname="Helvetica", shape="box", style="rounded,filled")
    g.attr("edge", fontname="Helvetica")

    g.node("start", "Environment setup\nPython 3.13 venv + pip", fillcolor="#eceff1")

    with g.subgraph(name="cluster_a") as c:
        c.attr(label="Phase A — pure FastAPI (in-memory)", style="rounded", color="#66bb6a", fontname="Helvetica")
        c.attr("node", fillcolor="#e8f5e9")
        c.node("a1", "App + routing\n(uvicorn / ASGI)")
        c.node("a2", "Request/response schemas\n(3 separate models)")
        c.node("a3", "Path parameters\n/tasks/{id}")
        c.node("a4", "404 via HTTPException\n+ automatic 422")
        c.node("a5", "Query-param filters")
        c.node("a6", "Partial update + 204")
        c.node("a7", "Auto Swagger /docs")

    with g.subgraph(name="cluster_b") as c:
        c.attr(label="Phase B — the database", style="rounded", color="#42a5f5", fontname="Helvetica")
        c.attr("node", fillcolor="#e3f2fd")
        c.node("b1", "Engine + Task table\n(tasks.db on startup)")
        c.node("b2", "Dependency injection\nDepends(get_session)")
        c.node("b3", "Session CRUD → SQL")
        c.node("b4", "Persistence\n(restart-proof data)")

    with g.subgraph(name="cluster_c") as c:
        c.attr(label="Phase C — productionize", style="rounded", color="#ab47bc", fontname="Helvetica")
        c.attr("node", fillcolor="#f3e5f5")
        c.node("c1", "Modularize into app/ package")
        c.node("c2", "Gradio UI (httpx → API)")
        c.node("c3", "Diagrams + one-command run")

    chain = ["start", "a1", "a2", "a3", "a4", "a5", "a6", "a7",
             "b1", "b2", "b3", "b4", "c1", "c2", "c3"]
    for src, dst in zip(chain, chain[1:]):
        g.edge(src, dst)
    return g


if __name__ == "__main__":
    _save(architecture(), "architecture")
    _save(learning_flow(), "learning-flow")
