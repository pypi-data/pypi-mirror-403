
import typer
from datetime import datetime
from rapidfuzz import fuzz
from todox.store import load, save, now
from todox.gitutils import git_info
from todox.tui import TodoApp
from rich.console import Console
from rich.table import Table
from rich import box
from typing import Optional
import os
import sys
import subprocess

app = typer.Typer()

def next_id(todos):
    return max([t["id"] for t in todos], default=0) + 1

console = Console(force_terminal=True, file=sys.stdout)

@app.command()
def add(
    title: str,
    tags: str = "",
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority (low, medium, high)"),
    due: Optional[str] = typer.Option(None, "--due", "-d", help="Due date (YYYY-MM-DD)"),
):
    data = load()
    todos = data["todos"]
    repo, branch = git_info()

    todo = {
        "id": next_id(todos),
        "title": title,
        "done": False,
        "tags": tags.split(",") if tags else [],
        "repo": repo,
        "branch": branch,
        "priority": priority,
        "due_date": due,
        "notes": "",
        "created_at": now(),
        "started_at": None,
        "time_spent": 0
    }
    todos.append(todo)
    data["last_active"] = todo["id"]
    save(data)
    console.print(f"[bold green]Added task {todo['id']}[/bold green]: {title}")

@app.command("list")
def list_todos(
    ctx: bool = typer.Option(False, "--context", "-c", help="Filter by current git context"),
    all: bool = typer.Option(False, "--all", "-a", help="Show done tasks"),
):
    data = load()
    todos = data["todos"]
    
    if ctx:
        repo, branch = git_info()
        if repo:
            todos = [t for t in todos if t.get("repo") == repo]

    if not all:
        todos = [t for t in todos if not t["done"]]

    table = Table(box=box.ROUNDED)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Prio", justify="center")
    table.add_column("Title", style="magenta")
    table.add_column("Due", style="yellow")
    table.add_column("Tags", style="blue")
    
    priority_colors = {"high": "red", "medium": "yellow", "low": "green"}

    for t in todos:
        status = "✓" if t["done"] else " "
        status_style = "green" if t["done"] else "white"
        prio = t.get("priority", "medium")
        prio_color = priority_colors.get(prio, "white")
        due = t.get("due_date") or ""
        tags = ", ".join(t.get("tags", []))
        
        table.add_row(
            str(t["id"]),
            f"[{status_style}]{status}[/{status_style}]",
            f"[{prio_color}]{prio}[/{prio_color}]",
            t["title"],
            due,
            tags
        )
    
    console.print(table)

@app.command()
def done(todo_id: int):
    data = load()
    for t in data["todos"]:
        if t["id"] == todo_id:
            t["done"] = True
    save(data)
    console.print(f"[bold green]Marked {todo_id} as done[/bold green]")

@app.command()
def edit(todo_id: int):
    data = load()
    target = None
    for t in data["todos"]:
        if t["id"] == todo_id:
            target = t
            break
            
    if not target:
        console.print(f"[red]Task {todo_id} not found[/red]")
        return
        
    # Create temp file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode='w+') as tf:
        tf.write(target.get("notes", ""))
        tf_path = tf.name
        
    editor = os.environ.get("EDITOR", "vim")
    subprocess.call([editor, tf_path])
    
    with open(tf_path, 'r') as tf:
        new_notes = tf.read().strip()
        
    target["notes"] = new_notes
    save(data)
    console.print(f"[green]Updated notes for task {todo_id}[/green]")
    os.unlink(tf_path)

@app.command()
def start(todo_id: int):
    data = load()
    for t in data["todos"]:
        if t["id"] == todo_id:
            t["started_at"] = now()
            data["last_active"] = todo_id
    save(data)
    typer.echo("Started")

@app.command()
def stop():
    data = load()
    for t in data["todos"]:
        if t["started_at"]:
            start = datetime.fromisoformat(t["started_at"])
            t["time_spent"] += int((datetime.now() - start).total_seconds())
            t["started_at"] = None
    save(data)
    typer.echo("Stopped")

@app.command()
def resume():
    data = load()
    tid = data.get("last_active")
    for t in data["todos"]:
        if t["id"] == tid:
            typer.echo(f"Resume: {t['title']}")

@app.command()
def search(query: str):
    data = load()
    for t in data["todos"]:
        if fuzz.partial_ratio(query.lower(), t["title"].lower()) > 60:
            typer.echo(f"{t['id']} {t['title']}")

@app.command()
def stats():
    data = load()
    total = sum(t["time_spent"] for t in data["todos"])
    done = len([t for t in data["todos"] if t["done"]])
    typer.echo(f"Completed: {done}")
    typer.echo(f"Time spent: {round(total/3600,2)} hrs")

@app.command()
def ui():
    TodoApp().run()
