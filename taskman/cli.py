from __future__ import annotations

import argparse
from datetime import datetime
from typing import List, Optional

from .models import Task
from .storage import TaskStorage


def _fmt_due(dt: Optional[datetime]) -> str:
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%d")


def _status(task: Task) -> str:
    return "done" if task.completed else "pending"


def _sort_key(task: Task):
    # Sort by due date soonest first, None last; then by created_at.
    # We use a tuple where None maps to (1, max) and dates map to (0, due).
    if task.due_date is None:
        return (1, datetime.max, task.created_at)
    return (0, task.due_date, task.created_at)


def _print_table(headers: List[str], rows: List[List[str]]) -> None:
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(row: List[str]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    print(fmt_row(headers))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print(fmt_row(r))


def cmd_add(args: argparse.Namespace) -> int:
    storage = TaskStorage()
    task = Task.create(args.title, priority=args.priority, due_date=args.due)
    storage.add(task)
    print(f"✓ Created task: {task.id}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    storage = TaskStorage()
    tasks = storage.list()
    tasks_sorted = sorted(tasks, key=_sort_key)

    headers = ["ID", "Title", "Priority", "Due", "Status"]
    rows: List[List[str]] = []
    for t in tasks_sorted:
        due = _fmt_due(t.due_date)
        if t.is_overdue():
            # Simple highlight without external deps.
            due = f"!{due}!"
        rows.append([t.id, t.title, t.priority, due, _status(t)])

    _print_table(headers, rows)
    return 0


def cmd_overdue(args: argparse.Namespace) -> int:
    storage = TaskStorage()
    tasks = [t for t in storage.list() if t.is_overdue()]
    tasks = sorted(tasks, key=_sort_key)

    headers = ["ID", "Title", "Priority", "Due", "Days Overdue"]
    rows: List[List[str]] = []
    now = datetime.now()
    for t in tasks:
        days = t.days_overdue(now=now)
        rows.append([t.id, t.title, t.priority, _fmt_due(t.due_date), str(days or 0)])

    _print_table(headers, rows)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taskman")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a task")
    p_add.add_argument("title", help="Task title")
    p_add.add_argument("--priority", default="medium", choices=["low", "medium", "high"], help="Task priority")
    p_add.add_argument("--due", default=None, help='Due date in format "YYYY-MM-DD"')
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List tasks")
    p_list.set_defaults(func=cmd_list)

    p_overdue = sub.add_parser("overdue", help="List overdue tasks")
    p_overdue.set_defaults(func=cmd_overdue)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
