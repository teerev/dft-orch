from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from datetime import datetime
from typing import Iterable, List, Optional


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.replace(microsecond=0).isoformat()


def filter_tasks(tasks: Iterable, completed: bool = False, pending: bool = False) -> List:
    """Filter tasks by completion status.

    If neither completed nor pending is True, returns all tasks.
    """

    tasks_list = list(tasks)

    if completed and not pending:
        return [t for t in tasks_list if bool(getattr(t, "completed", False))]
    if pending and not completed:
        return [t for t in tasks_list if not bool(getattr(t, "completed", False))]
    # If both flags are set (or neither), export all.
    return tasks_list


def task_to_export_dict(task) -> dict:
    """Convert a task object to the export schema."""

    # Prefer dataclasses for internal representation.
    if hasattr(task, "__dataclass_fields__"):
        data = asdict(task)
    elif isinstance(task, dict):
        data = dict(task)
    else:
        # Fallback: best-effort attribute extraction
        data = {
            "id": getattr(task, "id", None),
            "title": getattr(task, "title", ""),
            "description": getattr(task, "description", ""),
            "completed": bool(getattr(task, "completed", False)),
            "priority": getattr(task, "priority", None),
            "due_date": getattr(task, "due_date", None),
            "created_at": getattr(task, "created_at", None),
        }

    return {
        "id": str(data.get("id") or ""),
        "title": data.get("title") or "",
        "description": data.get("description") or "",
        "completed": bool(data.get("completed", False)),
        "priority": str(data.get("priority") or "").lower() if data.get("priority") is not None else "",
        "due_date": _iso(data.get("due_date")) if isinstance(data.get("due_date"), datetime) else (data.get("due_date") if data.get("due_date") is None else str(data.get("due_date"))),
        "created_at": _iso(data.get("created_at")) if isinstance(data.get("created_at"), datetime) else (data.get("created_at") if data.get("created_at") is None else str(data.get("created_at"))),
    }


def export_json(tasks: Iterable, exported_at: Optional[datetime] = None) -> str:
    exported_at = exported_at or datetime.utcnow()
    task_dicts = [task_to_export_dict(t) for t in tasks]
    payload = {
        "exported_at": _iso(exported_at),
        "total": len(task_dicts),
        "tasks": task_dicts,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def export_csv(tasks: Iterable) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "title", "description", "completed", "priority", "due_date", "created_at"],
        lineterminator="\n",
    )
    writer.writeheader()

    for t in tasks:
        d = task_to_export_dict(t)
        writer.writerow(
            {
                "id": d["id"],
                "title": d["title"],
                "description": d["description"],
                "completed": "true" if d["completed"] else "false",
                "priority": d["priority"],
                "due_date": d["due_date"] or "",
                "created_at": d["created_at"] or "",
            }
        )

    return output.getvalue()


def _md_escape(text: str) -> str:
    # Minimal escaping to avoid breaking headings.
    return (text or "").replace("\r", "").replace("\n", " ")


def export_markdown(tasks: Iterable, exported_at: Optional[datetime] = None) -> str:
    exported_at = exported_at or datetime.utcnow()
    task_list = [task_to_export_dict(t) for t in tasks]

    pending = [t for t in task_list if not t["completed"]]
    completed = [t for t in task_list if t["completed"]]

    def fmt_dt(s: Optional[str]) -> str:
        if not s:
            return ""
        # Try to render "YYYY-MM-DD HH:MM" like the example when ISO.
        try:
            dt = datetime.fromisoformat(s)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return s

    lines = []
    lines.append("# Tasks Export")
    lines.append("")
    lines.append(f"Exported: {fmt_dt(_iso(exported_at))}")

    def section(title: str, items: List[dict]) -> None:
        lines.append("")
        lines.append(f"## {title}")
        if not items:
            lines.append("")
            lines.append("_No tasks._")
            return
        for t in items:
            pr = (t.get("priority") or "").upper() or "MEDIUM"
            title_txt = _md_escape(t.get("title") or "")
            check = " ✓" if t.get("completed") else ""
            lines.append("")
            lines.append(f"### [{pr}] {title_txt}{check}")
            tid = (t.get("id") or "")
            lines.append(f"- ID: {tid.split('-')[0] if tid else ''}")
            created = t.get("created_at")
            if created:
                # Prefer just the date in markdown sample
                try:
                    dt = datetime.fromisoformat(created)
                    lines.append(f"- Created: {dt.strftime('%Y-%m-%d')}")
                except Exception:
                    lines.append(f"- Created: {created}")
            if t.get("completed"):
                lines.append("- Completed")
            if t.get("due_date"):
                lines.append(f"- Due: {t['due_date']}")
            desc = (t.get("description") or "").strip()
            if desc:
                lines.append(f"- Notes: {_md_escape(desc)}")

    section("Pending Tasks", pending)
    section("Completed Tasks", completed)

    return "\n".join(lines).rstrip() + "\n"


def export_tasks(tasks: Iterable, fmt: str = "json", exported_at: Optional[datetime] = None) -> str:
    fmt = (fmt or "json").lower()
    if fmt == "json":
        return export_json(tasks, exported_at=exported_at)
    if fmt == "csv":
        return export_csv(tasks)
    if fmt in {"md", "markdown"}:
        return export_markdown(tasks, exported_at=exported_at)
    raise ValueError(f"Unsupported export format: {fmt}")
