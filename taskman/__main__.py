from __future__ import annotations

import argparse
import sys

from . import storage


def _format_task_line(t: storage.Task | object) -> str:
    # Storage exposes Task model; keep formatting simple.
    if hasattr(t, "completed") and getattr(t, "completed"):
        prefix = "[x]"
    else:
        prefix = "[ ]"
    return f"{prefix} {getattr(t, 'id', '')[:8]} {getattr(t, 'title', '')}"


def cmd_add(args: argparse.Namespace) -> int:
    t = storage.add_task(args.title)
    print(f"Added: {t.title} ({t.id[:8]})")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    tasks = storage.list_tasks()
    if not tasks:
        print("No tasks.")
        return 0
    for t in tasks:
        if args.all or not t.completed:
            print(_format_task_line(t))
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    try:
        t = storage.find_by_partial_id(args.task_id)
    except storage.AmbiguousTaskIdError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if t is None:
        print(f"Error: Task not found for id '{args.task_id}'", file=sys.stderr)
        return 2

    updated = storage.complete_task(t)
    print(f"✓ Completed: {updated.title}")
    return 0


def _confirm(prompt: str) -> bool:
    resp = input(prompt).strip().lower()
    return resp in {"y", "yes"}


def cmd_delete(args: argparse.Namespace) -> int:
    try:
        t = storage.find_by_partial_id(args.task_id)
    except storage.AmbiguousTaskIdError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if t is None:
        print(f"Error: Task not found for id '{args.task_id}'", file=sys.stderr)
        return 2

    if not args.force:
        if not _confirm(f"Delete \"{t.title}\"? [y/N]: "):
            print("Cancelled.")
            return 0

    storage.delete_task(t)
    print(f"✓ Deleted: {t.title}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="taskman")
    sub = p.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Add a new task")
    add_p.add_argument("title", help="Task title")
    add_p.set_defaults(func=cmd_add)

    list_p = sub.add_parser("list", help="List tasks")
    list_p.add_argument("--all", action="store_true", help="Include completed tasks")
    list_p.set_defaults(func=cmd_list)

    complete_p = sub.add_parser("complete", help="Mark a task as completed")
    complete_p.add_argument("task_id", help="Task id (full or unique prefix)")
    complete_p.set_defaults(func=cmd_complete)

    delete_p = sub.add_parser("delete", help="Delete a task permanently")
    delete_p.add_argument("task_id", help="Task id (full or prefix)")
    delete_p.add_argument(
        "--force", action="store_true", help="Do not ask for confirmation"
    )
    delete_p.set_defaults(func=cmd_delete)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
