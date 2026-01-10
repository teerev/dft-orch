from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any

from ..state import WorkflowState
from ..utils.logging import log_event
from ..utils.serialization import write_json, write_text

NODE = "validate_and_report"


def _render_report(summary: dict[str, Any]) -> str:
    status = summary.get("status", "unknown")
    passed = summary.get("validation", {}).get("passed")
    reasons = summary.get("validation", {}).get("reasons", [])
    reasons_md = "\n".join([f"- {r}" for r in reasons]) if reasons else "- (none)"
    structure_hash = (summary.get("structure") or {}).get("hash")
    energy_eV = (summary.get("calculation") or {}).get("energy_eV")
    max_force = (summary.get("validation") or {}).get("max_force")
    relax = summary.get("relaxation") or {}
    relax_enabled = relax.get("enabled")
    relax_optimizer = relax.get("optimizer")
    relax_steps = relax.get("steps_taken")
    retry = summary.get("retry") or {}
    retries_used = retry.get("retries_used")
    return (
        "# dft-orch report\n\n"
        f"Run: `{summary.get('run_id')}`  \n"
        f"Material: `{summary.get('material_id')}`\n\n"
        f"Structure hash: `{structure_hash}`\n\n"
        f"Energy (eV): `{energy_eV}`  \n"
        f"Max force (eV/Å): `{max_force}`\n\n"
        f"Relax enabled: `{relax_enabled}`  \n"
        f"Relax optimizer: `{relax_optimizer}`  \n"
        f"Relax steps: `{relax_steps}`\n\n"
        f"Retries used: `{retries_used}`\n\n"
        f"Status: **{status}**  \n"
        f"Passed: **{passed}**\n\n"
        "## Reasons\n\n"
        f"{reasons_md}\n"
    )


def validate_and_report(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    run_dir = Path(state["run_dir"])
    log_path = Path(state["log_path"])

    log_event(
        log_path,
        node=NODE,
        event="start",
    )

    calc = state.get("calculation") or {}
    validate_cfg = (state.get("resolved_config") or {}).get("validate") or {}

    reasons: list[str] = []
    if calc.get("energy_eV") is None:
        reasons.append("energy_missing_or_not_run")
    if validate_cfg.get("require_scf_converged", True) and calc.get("scf_converged") is not True:
        reasons.append("scf_not_converged_or_not_run")

    max_force: float | None = None
    forces = calc.get("forces_eV_per_A")
    if isinstance(forces, list) and forces:
        norms = [math.sqrt(fx * fx + fy * fy + fz * fz) for fx, fy, fz in forces]
        max_force = max(norms) if norms else None
        max_force = None if max_force is None else round(float(max_force), 8)
        threshold = float(validate_cfg.get("max_force", 0.05))
        if max_force is not None and max_force > threshold:
            reasons.append("max_force_exceeded")

    passed = len(reasons) == 0
    state["validation"] = {
        "passed": passed,
        "reasons": reasons,
        "max_force": max_force,
    }

    summary: dict[str, Any] = {
        "status": "no_calculation" if calc.get("energy_eV") is None else "done",
        "run_id": state.get("run_id"),
        "material_id": state.get("material_id"),
        "structure": {
            "hash": state.get("structure_hash"),
            "canonical_path": state.get("structure_canonical_path"),
        },
        "relaxation": state.get("relaxation"),
        "retry": state.get("retry"),
        "calculation": calc,
        "validation": state["validation"],
    }

    results_dir = run_dir / "results"
    write_json(results_dir / "summary.json", summary)
    write_text(results_dir / "report.md", _render_report(summary))

    log_event(
        log_path,
        node=NODE,
        event="end",
        duration_s=round(time.perf_counter() - t0, 6),
        passed=passed,
    )
    return state
