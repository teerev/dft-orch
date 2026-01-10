from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class RetryState(TypedDict, total=False):
    retries_remaining: int
    retries_used: int
    history: list[dict[str, Any]]


class CalcResults(TypedDict, total=False):
    backend: str | None
    method: str | None
    xc: str | None
    basis: str | None
    charge: int | None
    spin: int | None
    energy_eV: float | None
    forces_eV_per_A: list[list[float]] | None
    scf_converged: bool | None
    scf_iterations: int | None
    walltime_s: float | None
    error: str | None


class ValidationResults(TypedDict, total=False):
    passed: bool
    reasons: list[str]
    max_force: float | None


class RelaxationResults(TypedDict, total=False):
    enabled: bool
    optimizer: str | None
    fmax: float | None
    steps: int | None
    steps_taken: int | None
    trajectory_path: str | None
    final_structure_path: str | None


class WorkflowState(TypedDict, total=False):
    # ---- CLI / inputs
    config_path: str
    material_id: str
    structure_path_override: NotRequired[str | None]
    runs_dir_override: NotRequired[str | None]
    run_name: NotRequired[str | None]
    cli_argv: NotRequired[list[str]]

    # ---- Resolved config
    project_root: str
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
    structure_resolved_path: str | None
    structure_input_hash: str | None
    structure_input_copied_path: str | None
    structure_hash: str | None  # canonical structure hash (milestone 2)
    structure_canonical_path: str | None
    structure: dict[str, Any] | None

    # ---- Calculation + validation (milestone 3+)
    calculation: CalcResults
    relaxation: RelaxationResults
    validation: ValidationResults
    retry: RetryState
