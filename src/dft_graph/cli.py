from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ConfigLoadError, ConfigValidationError
from .graph import build_graph
from .state import WorkflowState


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dft_graph",
        description="Deterministic LangGraph DFT workflow (learning project)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the workflow")
    run.add_argument(
        "--config",
        default="configs/default.yaml",
        help="Path to default config YAML",
    )
    run.add_argument(
        "--material",
        required=True,
        help="Material id (loads configs/materials/<id>.yaml)",
    )
    run.add_argument("--structure", default=None, help="Override structure path")
    run.add_argument("--runs-dir", default=None, help="Override runs output directory")
    run.add_argument(
        "--run-name",
        default=None,
        help="Optional run label (included in run dir name)",
    )

    return p


def cmd_run(args: argparse.Namespace, argv: list[str]) -> int:
    initial_state: WorkflowState = {
        "config_path": str(Path(args.config)),
        "material_id": str(args.material),
        "structure_path_override": None if args.structure is None else str(args.structure),
        "runs_dir_override": None if args.runs_dir is None else str(args.runs_dir),
        "run_name": None if args.run_name is None else str(args.run_name),
        "cli_argv": argv,
        "retry": {"retries_remaining": 0, "retries_used": 0, "history": []},
    }

    graph = build_graph()
    final_state = graph.invoke(initial_state)

    run_dir = final_state.get("run_dir", "<unknown>")
    validation = final_state.get("validation", {})
    calc = final_state.get("calculation", {})

    passed = validation.get("passed")
    energy = calc.get("energy_eV")
    max_force = validation.get("max_force")

    print(f"run_dir: {run_dir}")
    print(f"passed: {passed}")
    if energy is not None:
        print(f"energy_eV: {energy}")
    if max_force is not None:
        print(f"max_force: {max_force}")

    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            return cmd_run(args, argv)
        raise AssertionError(f"Unhandled command: {args.command}")
    except (ConfigLoadError, ConfigValidationError) as e:
        print(str(e), file=sys.stderr)
        return 2
