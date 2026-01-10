from __future__ import annotations

import json
import time
from pathlib import Path

from ..config import ConfigValidationError
from ..state import WorkflowState
from ..utils.logging import log_event
from ..utils.serialization import write_json

NODE = "build_calculator"


def build_calculator(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    log_path = Path(state["log_path"])
    manifest_path = Path(state["manifest_path"])

    log_event(
        log_path,
        node=NODE,
        event="start",
    )

    cfg = state.get("resolved_config") or {}
    calc_cfg = cfg.get("calculator") or {}
    structure = state.get("structure") or {}

    backend = str(calc_cfg.get("backend", "pyscf")).lower()
    method = str(calc_cfg.get("method", "dft")).lower()
    if backend != "pyscf":
        msg = f"Unsupported calculator.backend={backend!r} (only 'pyscf' supported)"
        raise ConfigValidationError(msg)
    if method != "dft":
        msg = f"Unsupported calculator.method={method!r} (only 'dft' supported)"
        raise ConfigValidationError(msg)

    scf_cfg = calc_cfg.get("scf") or {}
    conv_tol = float(scf_cfg.get("conv_tol", 1e-8))
    max_cycle = int(scf_cfg.get("max_cycle", 50))

    # Decide molecular vs PBC mode.
    pbc_cfg = calc_cfg.get("pbc") or {}
    pbc_enabled = pbc_cfg.get("enabled")
    pbc_flags = structure.get("pbc")
    cell = structure.get("cell_A")
    is_periodic_structure = (
        isinstance(pbc_flags, list)
        and len(pbc_flags) == 3
        and all(bool(x) for x in pbc_flags)
        and isinstance(cell, list)
        and len(cell) == 3
        and any(any(float(v) != 0.0 for v in row) for row in cell if isinstance(row, list))
    )
    use_pbc = is_periodic_structure if pbc_enabled is None else bool(pbc_enabled)

    plan = {
        "mode": "pbc" if use_pbc else "molecule",
        "backend": backend,
        "method": method,
        "xc": str(calc_cfg.get("xc", "PBE")),
        "basis": str(calc_cfg.get("basis", "def2-svp")),
        "charge": int(calc_cfg.get("charge", 0)),
        "spin": int(calc_cfg.get("spin", 0)),
        "scf": {
            "conv_tol": conv_tol,
            "max_cycle": max_cycle,
            "fallback_newton": True,
        },
        "pbc": (
            {
                "enabled": True,
                "basis": str(pbc_cfg.get("basis", "gth-szv-molopt-sr")),
                "pseudo": pbc_cfg.get("pseudo", "gth-pbe"),
                "mesh": list(pbc_cfg.get("mesh", [25, 25, 25])),
                "kpts": list(pbc_cfg.get("kpts", [1, 1, 1])),
                "use_multigrid": bool(pbc_cfg.get("use_multigrid", True)),
            }
            if use_pbc
            else {
                "enabled": False,
            }
        ),
        "compute_forces": True,
    }

    state.setdefault("calculation", {})
    state["calculation"].update(
        {
            "mode": plan["mode"],
            "backend": backend,
            "method": method,
            "xc": plan["xc"],
            "basis": plan["basis"],
            "charge": plan["charge"],
            "spin": plan["spin"],
            "energy_eV": None,
            "forces_eV_per_A": None,
            "scf_converged": None,
            "scf_iterations": None,
            "walltime_s": None,
            "error": None,
            "scf_solver": None,
        }
    )

    log_event(
        log_path,
        node=NODE,
        event="info",
        message="Prepared calculator plan",
        **plan,
    )

    # Update manifest with the calculation plan (distinct from raw config).
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        manifest = {}
    manifest["calculation_plan"] = plan
    write_json(manifest_path, manifest)

    log_event(
        log_path,
        node=NODE,
        event="end",
        duration_s=round(time.perf_counter() - t0, 6),
    )
    return state
