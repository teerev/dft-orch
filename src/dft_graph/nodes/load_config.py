from __future__ import annotations

import platform
import shutil
import sys
import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

from ..config import CliOverrides, ConfigLoadError, ConfigValidationError, resolve_config
from ..state import WorkflowState
from ..utils.hashing import sha256_file, short_hash_from_obj
from ..utils.logging import log_event
from ..utils.paths import best_effort_git_short_sha, build_run_id, create_run_dir
from ..utils.serialization import write_json, write_text

NODE = "load_config"


def _pkg_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def _resolve_maybe_relative(path_str: str, *, project_root: Path) -> Path:
    p = Path(path_str).expanduser()
    if p.is_absolute():
        return p
    return (project_root / p).resolve()


def load_config(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()

    config_path = Path(state["config_path"])
    material_id = state["material_id"]
    overrides = CliOverrides(
        runs_dir=state.get("runs_dir_override"),
        structure_path=state.get("structure_path_override"),
        run_name=state.get("run_name"),
    )

    # ---- Resolve config (default + material + CLI overrides)
    materials_dir = config_path.resolve().parent / "materials"
    try:
        resolved = resolve_config(
            default_config_path=config_path,
            material_id=material_id,
            materials_dir=materials_dir,
            overrides=overrides,
        )
    except (ConfigLoadError, ConfigValidationError):
        # Don't swallow: CLI should surface a clear error.
        raise

    resolved_config = resolved.resolved
    state["resolved_config"] = resolved_config
    state["config_sources"] = resolved.sources

    # ---- Hash (used in run_id)
    config_hash = short_hash_from_obj(
        {
            "resolved_config": resolved_config,
        },
        length=10,
    )
    state["config_hash"] = config_hash

    # ---- Run directory
    created_at = datetime.now(UTC)
    git_sha = best_effort_git_short_sha(cwd=resolved.project_root)
    run_id = build_run_id(
        created_at_utc=created_at,
        material_id=material_id,
        config_hash=config_hash,
        git_sha=git_sha,
        run_name=resolved_config["run"].get("run_name"),
    )

    runs_dir_cfg = resolved_config["run"]["runs_dir"]
    runs_dir_override = state.get("runs_dir_override")
    runs_dir = Path(runs_dir_cfg) if runs_dir_override is None else Path(runs_dir_override)
    if not runs_dir.is_absolute():
        runs_dir = (resolved.project_root / runs_dir).resolve()

    run_dir = create_run_dir(runs_dir=runs_dir, run_id=run_id)
    input_dir = run_dir / "input"
    results_dir = run_dir / "results"
    input_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = run_dir / "manifest.json"
    log_path = run_dir / "logs.jsonl"

    state["run_id"] = run_id
    state["run_dir"] = str(run_dir)
    state["manifest_path"] = str(manifest_path)
    state["log_path"] = str(log_path)

    log_event(
        log_path,
        node=NODE,
        event="start",
        material_id=material_id,
        run_id=run_id,
        runs_dir=str(runs_dir),
    )

    # ---- Structure input copy (best-effort; canonical handling comes in milestone 2)
    structure_path_cfg = resolved_config["structure"].get("path")
    state["structure_path"] = None if structure_path_cfg is None else str(structure_path_cfg)
    state["structure_input_hash"] = None
    state["structure_input_copied_path"] = None

    if structure_path_cfg:
        src = _resolve_maybe_relative(structure_path_cfg, project_root=resolved.project_root)
        if src.exists() and src.is_file():
            dest = input_dir / f"structure{src.suffix or ''}"
            shutil.copy2(src, dest)
            state["structure_input_copied_path"] = str(dest)
            state["structure_input_hash"] = sha256_file(dest)[:16]
            log_event(
                log_path,
                node=NODE,
                event="info",
                message="Copied structure input",
                structure_src=str(src),
                structure_dest=str(dest),
                structure_input_hash=state["structure_input_hash"],
            )
        else:
            log_event(
                log_path,
                node=NODE,
                event="error",
                message="Structure path does not exist (skipping copy)",
                structure_src=str(src),
            )

    # ---- Write early artifacts
    summary_path = results_dir / "summary.json"
    report_path = results_dir / "report.md"

    placeholder_summary: dict[str, Any] = {
        "status": "initialized",
        "run_id": run_id,
        "material_id": material_id,
    }
    write_json(summary_path, placeholder_summary)
    write_text(report_path, f"# dft-orch report\n\nRun: `{run_id}`\n\nStatus: initialized\n")

    manifest: dict[str, Any] = {
        "run_id": run_id,
        "created_at_utc": created_at.isoformat(),
        "material_id": material_id,
        "run_dir": str(run_dir),
        "config_hash": config_hash,
        "config_sources": resolved.sources,
        "resolved_config": resolved_config,
        "structure": {
            "path": structure_path_cfg,
            "input_hash": state.get("structure_input_hash"),
            "copied_path": state.get("structure_input_copied_path"),
        },
        "git": {"commit_short": git_sha},
        "env": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "packages": {
            "dft-orch": _pkg_version("dft-orch"),
            "langgraph": _pkg_version("langgraph"),
            "pydantic": _pkg_version("pydantic"),
            "PyYAML": _pkg_version("PyYAML"),
        },
    }
    write_json(manifest_path, manifest)

    log_event(
        log_path,
        node=NODE,
        event="end",
        duration_s=round(time.perf_counter() - t0, 6),
        manifest_path=str(manifest_path),
    )
    return state
