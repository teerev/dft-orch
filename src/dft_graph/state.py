from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class RetryState(TypedDict, total=False):
    retries_remaining: int
    retries_used: int
    history: list[dict[str, Any]]


class CalcResults(TypedDict, total=False):
    energy_eV: float | None
    forces_eV_per_A: list[list[float]] | None
    scf_converged: bool | None
    scf_iterations: int | None
    walltime_s: float | None


class ValidationResults(TypedDict, total=False):
    passed: bool
    reasons: list[str]
    max_force: float | None


class WorkflowState(TypedDict, total=False):
    # ---- CLI / inputs
    config_path: str
    material_id: str
    structure_path_override: NotRequired[str | None]
    runs_dir_override: NotRequired[str | None]
    run_name: NotRequired[str | None]
    cli_argv: NotRequired[list[str]]

    # ---- Resolved config
    resolved_config: dict[str, Any]
    config_sources: dict[str, Any]
    config_hash: str

    # ---- Run identification + artifact paths
    run_id: str
    run_dir: str
    manifest_path: str
    log_path: str

    # ---- Structure provenance (milestone 1+2)
    structure_path: str | None
    structure_input_hash: str | None
    structure_input_copied_path: str | None
    structure_hash: str | None  # canonical structure hash (milestone 2)

    # ---- Calculation + validation (milestone 3+)
    calculation: CalcResults
    validation: ValidationResults
    retry: RetryState
