from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .exporter import export_tasks, filter_tasks


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    completed: bool = False
    priority: str = "medium"
    due_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


def _load_tasks() -> List[Task]:
    # Minimal in-memory task list (no persistence in this workspace).
    now = datetime.utcnow().replace(microsecond=0)
    return [
        Task(
            id="a1b2c3d4-0000-0000-0000-000000000000",
            title="Buy groceries",
            description="",
            completed=False,
            priority="high",
            due_date=None,
            created_at=now,
        )
    ]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taskman")
    sub = parser.add_subparsers(dest="command", required=True)

    exp = sub.add_parser("export", help="Export tasks")
    exp.add_argument("--format", default="json", choices=["json", "csv", "markdown"], help="Export format")
    exp.add_argument("--output", default=None, help="Output file (default: stdout)")
    exp.add_argument("--completed", action="store_true", help="Export only completed tasks")
    exp.add_argument("--pending", action="store_true", help="Export only pending tasks")

    return parser


def cmd_export(args: argparse.Namespace) -> int:
    tasks = _load_tasks()
    tasks = filter_tasks(tasks, completed=args.completed, pending=args.pending)

    content = export_tasks(tasks, fmt=args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        print(f"✓ Exported {len(tasks)} tasks to {args.output}")
    else:
        sys.stdout.write(content)

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "export":
        return cmd_export(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
