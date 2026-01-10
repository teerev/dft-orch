from __future__ import annotations

from langgraph.graph import END, StateGraph

from .nodes.build_calculator import build_calculator
from .nodes.load_config import load_config
from .nodes.load_structure import load_structure
from .nodes.run_relaxation import run_relaxation
from .nodes.validate_and_report import validate_and_report
from .state import WorkflowState


def build_graph():
    g = StateGraph(WorkflowState)

    g.add_node("load_config", load_config)
    g.add_node("load_structure", load_structure)
    g.add_node("build_calculator", build_calculator)
    g.add_node("run_relaxation", run_relaxation)
    g.add_node("validate_and_report", validate_and_report)

    g.set_entry_point("load_config")
    g.add_edge("load_config", "load_structure")
    g.add_edge("load_structure", "build_calculator")
    g.add_edge("build_calculator", "run_relaxation")
    g.add_edge("run_relaxation", "validate_and_report")
    g.add_edge("validate_and_report", END)

    return g.compile()
