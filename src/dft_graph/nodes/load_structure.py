from __future__ import annotations

import time
from pathlib import Path

from ..state import WorkflowState
from ..utils.logging import log_event

NODE = "load_structure"


def load_structure(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    log_path = Path(state["log_path"])

    log_event(
        log_path,
        node=NODE,
        event="start",
        structure_path=state.get("structure_path"),
    )

    # Milestone 1 stub: real ASE structure loading + canonical hashing is milestone 2.
    state["structure_hash"] = None

    log_event(
        log_path,
        node=NODE,
        event="info",
        message="Stub (milestone 1): structure loading not implemented yet",
        structure_path=state.get("structure_path"),
        structure_input_copied_path=state.get("structure_input_copied_path"),
    )
    log_event(
        log_path,
        node=NODE,
        event="end",
        duration_s=round(time.perf_counter() - t0, 6),
    )
    return state
