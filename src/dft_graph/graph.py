from __future__ import annotations

from langgraph.graph import END, StateGraph

from .nodes.build_calculator import build_calculator
from .nodes.load_config import load_config
from .nodes.load_structure import load_structure
from .nodes.repair_and_retry import repair_and_retry
from .nodes.run_relaxation import run_relaxation
from .nodes.validate_and_report import validate_and_report
from .state import WorkflowState


def build_graph():
    g = StateGraph(WorkflowState)

    g.add_node("load_config", load_config)
    g.add_node("load_structure", load_structure)
    g.add_node("build_calculator", build_calculator)
    g.add_node("run_relaxation", run_relaxation)
    g.add_node("repair_and_retry", repair_and_retry)
    g.add_node("validate_and_report", validate_and_report)

    g.set_entry_point("load_config")
    g.add_edge("load_config", "load_structure")
    g.add_edge("load_structure", "build_calculator")
    g.add_edge("build_calculator", "run_relaxation")

    # Milestone 5: conditional retry loop on SCF failure.
    def _route_after_run(state: WorkflowState) -> str:
        calc = state.get("calculation") or {}
        converged = calc.get("scf_converged") is True
        retry = state.get("retry") or {}
        remaining = int(retry.get("retries_remaining", 0))
        if converged:
            return "validate_and_report"
        if remaining > 0:
            return "repair_and_retry"
        return "validate_and_report"

    g.add_conditional_edges(
        "run_relaxation",
        _route_after_run,
        {
            "repair_and_retry": "repair_and_retry",
            "validate_and_report": "validate_and_report",
        },
    )
    g.add_edge("repair_and_retry", "run_relaxation")
    g.add_edge("validate_and_report", END)

    return g.compile()
