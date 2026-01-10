from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def format_utc_compact(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    dt = dt.astimezone(UTC)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def sanitize_component(value: str, *, max_len: int = 64) -> str:
    v = value.strip()
    v = v.replace(" ", "-")
    v = _SAFE_COMPONENT_RE.sub("-", v)
    v = v.strip("-_.")
    v = v[:max_len]
    return v or "x"


def best_effort_git_short_sha(*, cwd: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    sha = proc.stdout.strip()
    return sha or None


def build_run_id(
    *,
    created_at_utc: datetime,
    material_id: str,
    config_hash: str,
    git_sha: str | None,
    run_name: str | None,
) -> str:
    ts = format_utc_compact(created_at_utc)
    material = sanitize_component(material_id, max_len=48)
    cfg = sanitize_component(config_hash, max_len=16)
    parts = [ts, material, cfg]
    if git_sha:
        parts.append(sanitize_component(git_sha, max_len=16))
    if run_name:
        parts.append(sanitize_component(run_name, max_len=48).lower())
    return "_".join(parts)


def create_run_dir(*, runs_dir: Path, run_id: str) -> Path:
    runs_dir = runs_dir.expanduser().resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)

    base = runs_dir / run_id
    if not base.exists():
        base.mkdir(parents=False, exist_ok=False)
        return base

    # deterministic collision handling (rare; e.g., multiple runs in same second)
    for i in range(1, 1000):
        candidate = runs_dir / f"{run_id}__{i:02d}"
        if not candidate.exists():
            candidate.mkdir(parents=False, exist_ok=False)
            return candidate
    raise RuntimeError(f"Unable to create unique run directory for run_id={run_id!r} in {runs_dir}")
