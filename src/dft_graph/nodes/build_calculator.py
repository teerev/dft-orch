from __future__ import annotations

import time
from pathlib import Path

from ..state import WorkflowState
from ..utils.logging import log_event

NODE = "build_calculator"


def build_calculator(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    log_path = Path(state["log_path"])

    log_event(
        log_path,
        node=NODE,
        event="start",
    )

    # Milestone 1 stub: no calculator built yet.
    log_event(
        log_path,
        node=NODE,
        event="info",
        message="Stub (milestone 1): calculator build not implemented yet",
    )
    log_event(
        log_path,
        node=NODE,
        event="end",
        duration_s=round(time.perf_counter() - t0, 6),
    )
    return state
