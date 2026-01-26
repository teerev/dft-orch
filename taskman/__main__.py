from __future__ import annotations

from typing import Optional

import typer

from .storage import add_task, list_tasks

app = typer.Typer(add_completion=False)


@app.command()
def add(
    title: str = typer.Argument(..., help="Task title"),
    description: Optional[str] = typer.Option(None, "--description", help="Optional description"),
    priority: str = typer.Option(
        "medium",
        "--priority",
        case_sensitive=False,
        help="Task priority: low|medium|high",
    ),
):
    p = priority.lower()
    if p not in {"low", "medium", "high"}:
        raise typer.BadParameter("priority must be one of: low, medium, high")

    task_id = add_task(title=title, description=description, priority=p)
    typer.echo(f"\u2713 Created task: {task_id[:8]}")


@app.command(name="list")
def list_cmd(
    all: bool = typer.Option(False, "--all", help="Show all tasks"),
    completed: bool = typer.Option(False, "--completed", help="Show only completed tasks"),
    pending: bool = typer.Option(False, "--pending", help="Show only pending tasks"),
):
    tasks = list_tasks(show_all=all, completed_only=completed, pending_only=pending)

    headers = ["ID", "Title", "Priority", "Status", "Created"]
    rows = []
    for t in tasks:
        rows.append(
            [
                str(t.get("id", ""))[:8],
                str(t.get("title", "")),
                str(t.get("priority", "")),
                str(t.get("status", "")),
                str(t.get("created", "")),
            ]
        )

    if not rows:
        typer.echo("No tasks found")
        return

    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(parts):
        return "  ".join(parts[i].ljust(widths[i]) for i in range(len(parts)))

    typer.echo(fmt_row(headers))
    typer.echo(fmt_row(["-" * w for w in widths]))
    for r in rows:
        typer.echo(fmt_row(r))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
