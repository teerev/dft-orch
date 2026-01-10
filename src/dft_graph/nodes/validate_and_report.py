from __future__ import annotations

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
    return (
        "# dft-orch report\n\n"
        f"Run: `{summary.get('run_id')}`  \n"
        f"Material: `{summary.get('material_id')}`\n\n"
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

    passed = len(reasons) == 0
    state["validation"] = {
        "passed": passed,
        "reasons": reasons,
        "max_force": None,
    }

    summary: dict[str, Any] = {
        "status": "no_calculation" if calc.get("energy_eV") is None else "done",
        "run_id": state.get("run_id"),
        "material_id": state.get("material_id"),
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
