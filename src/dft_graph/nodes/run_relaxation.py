from __future__ import annotations

import time
from pathlib import Path

from ..state import WorkflowState
from ..utils.logging import log_event

NODE = "run_relaxation"


def run_relaxation(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    log_path = Path(state["log_path"])

    log_event(
        log_path,
        node=NODE,
        event="start",
    )

    # Milestone 1 stub: do not run any calculation.
    state.setdefault("calculation", {})
    state["calculation"].setdefault("energy_eV", None)
    state["calculation"].setdefault("forces_eV_per_A", None)
    state["calculation"].setdefault("scf_converged", None)
    state["calculation"].setdefault("scf_iterations", None)

    log_event(
        log_path,
        node=NODE,
        event="info",
        message="Stub (milestone 1): no calculation performed",
    )
    log_event(
        log_path,
        node=NODE,
        event="end",
        duration_s=round(time.perf_counter() - t0, 6),
    )
    return state
