from __future__ import annotations

import argparse
from datetime import date
from typing import Dict, List, Optional

from .formatting import highlight, render_table, tasks_to_rows
from .storage import TaskStore, filter_tasks, parse_date


PRIORITIES = ("low", "medium", "high")


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="taskman", description="Simple task manager")
    sub = p.add_subparsers(dest="command", required=True)

    # list
    lp = sub.add_parser("list", help="List tasks")
    lp.add_argument(
        "--priority",
        choices=PRIORITIES,
        help="Filter tasks by priority",
    )
    lp.add_argument(
        "--due-before",
        dest="due_before",
        metavar="DATE",
        help="Show tasks due before DATE (YYYY-MM-DD)",
    )
    lp.add_argument(
        "--due-after",
        dest="due_after",
        metavar="DATE",
        help="Show tasks due after DATE (YYYY-MM-DD)",
    )

    # search
    sp = sub.add_parser("search", help="Search tasks")
    sp.add_argument("query", help="Search query")

    # stats
    sub.add_parser("stats", help="Show task statistics")

    return p.parse_args(argv)


def _cmd_list(args: argparse.Namespace, store: TaskStore) -> int:
    tasks = store.all()
    due_before = parse_date(args.due_before)
    due_after = parse_date(args.due_after)
    tasks = filter_tasks(tasks, priority=args.priority, due_before=due_before, due_after=due_after)

    headers = ["ID", "Title", "Priority", "Due", "Status"]
    rows = tasks_to_rows(tasks, include_due=True)
    print(render_table(headers, rows))
    return 0


def _cmd_search(args: argparse.Namespace, store: TaskStore) -> int:
    q = args.query
    tasks = store.all()
    q_lower = q.lower()

    matches = []
    for t in tasks:
        if q_lower in (t.title or "").lower() or q_lower in (t.description or "").lower():
            matches.append(t)

    print(f'Found {len(matches)} tasks matching "{q}":')
    if not matches:
        return 0
    print()

    headers = ["ID", "Title", "Priority", "Status"]
    rows = []
    for t in matches:
        rows.append([t.id, highlight(t.title, q), t.priority, t.status])
    print(render_table(headers, rows))
    return 0


def _cmd_stats(store: TaskStore) -> int:
    tasks = store.all()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.completed)
    pending = total - completed
    today = date.today()
    overdue = sum(1 for t in tasks if (not t.completed) and t.due is not None and t.due < today)

    by_pri: Dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for t in tasks:
        if t.priority in by_pri:
            by_pri[t.priority] += 1
        else:
            by_pri[t.priority] = by_pri.get(t.priority, 0) + 1

    def pct(n: int) -> str:
        return "0%" if total == 0 else f"{round((n / total) * 100)}%"

    print("Task Statistics")
    print("===============" )
    print(f"Total:     {total}")
    print(f"Completed: {completed} ({pct(completed)})")
    print(f"Pending:   {pending} ({pct(pending)})")
    print(f"Overdue:   {overdue}")
    print()
    print("By Priority:")
    print(f"  High:   {by_pri.get('high', 0)}")
    print(f"  Medium: {by_pri.get('medium', 0)}")
    print(f"  Low:    {by_pri.get('low', 0)}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    store = TaskStore()

    if args.command == "list":
        return _cmd_list(args, store)
    if args.command == "search":
        return _cmd_search(args, store)
    if args.command == "stats":
        return _cmd_stats(store)

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
