from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional, Sequence

from .storage import Task


def _supports_ansi() -> bool:
    # Conservative; enable if stdout is a TTY.
    try:
        import sys

        return sys.stdout.isatty()
    except Exception:
        return False


def highlight(text: str, query: str, *, enabled: Optional[bool] = None) -> str:
    if enabled is None:
        enabled = _supports_ansi()
    if not enabled:
        return text
    if not query:
        return text

    pattern = re.compile(re.escape(query), re.IGNORECASE)

    def repl(m: re.Match) -> str:
        # Bold + yellow
        return "\033[1;33m" + m.group(0) + "\033[0m"

    return pattern.sub(repl, text)


@dataclass
class Column:
    header: str
    values: List[str]

    @property
    def width(self) -> int:
        return max([len(self.header)] + [len(v) for v in self.values] + [0])


def _fmt_due(d: Optional[date]) -> str:
    return d.isoformat() if d else ""


def render_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    cols = [
        Column(header=h, values=[r[i] for r in rows] if rows else [])
        for i, h in enumerate(headers)
    ]
    widths = [c.width for c in cols]

    def fmt_row(items: Sequence[str]) -> str:
        return "  ".join(items[i].ljust(widths[i]) for i in range(len(items)))

    lines = []
    lines.append(fmt_row(headers))
    lines.append("  ".join("-" * w for w in widths))
    for r in rows:
        lines.append(fmt_row(r))
    return "\n".join(lines)


def tasks_to_rows(tasks: Iterable[Task], *, include_due: bool = True) -> List[List[str]]:
    rows: List[List[str]] = []
    for t in tasks:
        base = [t.id, t.title, t.priority]
        if include_due:
            base.append(_fmt_due(t.due))
        base.append(t.status)
        rows.append(base)
    return rows
