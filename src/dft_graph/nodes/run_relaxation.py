from __future__ import annotations

import time
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
from ase import Atoms
from ase.calculators.calculator import Calculator, all_changes
from ase.io import write as ase_write
from ase.optimize import BFGS, FIRE
from ase.units import Bohr, Hartree
from pyscf import dft, gto, lib

from ..config import ConfigLoadError
from ..state import WorkflowState
from ..utils.logging import log_event
from ..utils.serialization import write_json

NODE = "run_relaxation"


def _normalize_float(x: float, digits: int) -> float:
    y = round(float(x), digits)
    return 0.0 if y == 0.0 else y


def _pyscf_single_point(
    *,
    symbols: list[str],
    positions_A: list[list[float]],
    basis: str,
    xc: str,
    charge: int,
    spin: int,
    conv_tol: float,
    max_cycle: int,
    digits: int,
) -> dict[str, Any]:
    """Run a minimal PySCF DFT single-point (molecular).

    Notes:
    - Returns energy in eV and forces in eV/Angstrom (if gradients succeed).
    """
    lib.num_threads(1)

    mol = gto.Mole()
    mol.verbose = 0
    mol.unit = "Angstrom"
    mol.atom = list(zip(symbols, positions_A, strict=True))
    mol.basis = basis
    mol.charge = charge
    mol.spin = spin
    mol.build()

    mf = dft.RKS(mol) if spin == 0 else dft.UKS(mol)
    mf.verbose = 0
    mf.xc = xc
    mf.conv_tol = conv_tol
    mf.max_cycle = max_cycle

    scf_solver = "diis"
    mf.kernel()
    converged = bool(getattr(mf, "converged", False))

    # Some systems (esp. "molecule-ified" periodic structures) may not converge
    # with DIIS in a reasonable number of cycles. A deterministic fallback is
    # PySCF's Newton solver, which often converges more robustly.
    if not converged:
        scf_solver = "newton"
        mf = mf.newton()
        mf.verbose = 0
        mf.conv_tol = conv_tol
        mf.max_cycle = max_cycle
        mf.kernel()
        converged = bool(getattr(mf, "converged", False))

    energy_h = float(mf.e_tot)
    energy_eV = _normalize_float(energy_h * Hartree, digits)

    cycles = getattr(mf, "cycles", None)
    scf_iterations = int(cycles) if cycles is not None else None

    forces: list[list[float]] | None = None
    if converged:
        # PySCF gradients are dE/dR in Hartree/Bohr; forces = -grad.
        grad = mf.nuc_grad_method().kernel()
        factor = Hartree / Bohr  # (eV) / (Angstrom) from (Hartree/Bohr)
        forces = [
            [_normalize_float(-float(v) * factor, digits) for v in row.tolist()] for row in grad
        ]

    return {
        "scf_solver": scf_solver,
        "energy_eV": energy_eV,
        "forces_eV_per_A": forces,
        "scf_converged": converged,
        "scf_iterations": scf_iterations,
    }


def _is_periodic_structure(structure: dict[str, Any]) -> bool:
    pbc_flags = structure.get("pbc")
    cell = structure.get("cell_A")
    if not (
        isinstance(pbc_flags, list) and len(pbc_flags) == 3 and all(bool(x) for x in pbc_flags)
    ):
        return False
    if not (
        isinstance(cell, list)
        and len(cell) == 3
        and all(isinstance(r, list) and len(r) == 3 for r in cell)
    ):
        return False
    # Avoid treating a zero-cell as periodic.
    return any(any(float(v) != 0.0 for v in row) for row in cell)


def _pyscf_pbc_single_point(
    *,
    symbols: list[str],
    positions_A: list[list[float]],
    cell_A: list[list[float]],
    basis: str,
    pseudo: str | None,
    mesh: list[int],
    kpts: list[int],
    xc: str,
    charge: int,
    spin: int,
    conv_tol: float,
    max_cycle: int,
    digits: int,
    use_multigrid: bool,
) -> dict[str, Any]:
    """Run a minimal PySCF PBC gamma-point DFT single-point."""
    if kpts != [1, 1, 1]:
        raise ConfigLoadError(f"Only gamma-point kpts=[1,1,1] supported right now (got {kpts})")

    from pyscf.pbc import dft as pbc_dft
    from pyscf.pbc import gto as pbc_gto
    from pyscf.pbc.dft import multigrid

    lib.num_threads(1)

    cell = pbc_gto.Cell()
    cell.verbose = 0
    cell.unit = "Angstrom"
    cell.a = cell_A
    cell.atom = list(zip(symbols, positions_A, strict=True))
    cell.basis = basis
    if pseudo is not None:
        cell.pseudo = pseudo
    cell.charge = charge
    cell.spin = spin
    cell.mesh = mesh
    cell.build()

    mf = pbc_dft.RKS(cell) if spin == 0 else pbc_dft.UKS(cell)
    mf.verbose = 0
    mf.xc = xc
    mf.conv_tol = conv_tol
    mf.max_cycle = max_cycle
    if use_multigrid:
        mf._numint = multigrid.MultiGridNumInt2(cell)

    scf_solver = "diis"
    mf.kernel()
    converged = bool(getattr(mf, "converged", False))

    if not converged:
        scf_solver = "newton"
        mf = mf.newton()
        mf.verbose = 0
        mf.conv_tol = conv_tol
        mf.max_cycle = max_cycle
        if use_multigrid:
            mf._numint = multigrid.MultiGridNumInt2(cell)
        mf.kernel()
        converged = bool(getattr(mf, "converged", False))

    energy_h = float(mf.e_tot)
    energy_eV = _normalize_float(energy_h * Hartree, digits)

    cycles = getattr(mf, "cycles", None)
    scf_iterations = int(cycles) if cycles is not None else None

    forces: list[list[float]] | None = None
    if converged:
        if use_multigrid:
            grad = mf.nuc_grad_method().kernel()
            factor = Hartree / Bohr  # (eV) / (Angstrom) from (Hartree/Bohr)
            forces = [
                [_normalize_float(-float(v) * factor, digits) for v in row.tolist()] for row in grad
            ]
        else:
            # PySCF PBC gradients require MultiGridNumInt2; keep deterministic and explicit.
            forces = None

    return {
        "scf_solver": scf_solver,
        "energy_eV": energy_eV,
        "forces_eV_per_A": forces,
        "scf_converged": converged,
        "scf_iterations": scf_iterations,
    }


class _AsePyScfCalculator(Calculator):
    implemented_properties: ClassVar[list[str]] = ["energy", "forces"]

    def __init__(self, *, compute_fn, digits: int):
        super().__init__()
        self._compute_fn = compute_fn
        self._digits = digits
        self.last_result: dict[str, Any] | None = None

    def calculate(self, atoms=None, properties=("energy", "forces"), system_changes=all_changes):
        super().calculate(atoms, properties, system_changes)
        if atoms is None:
            raise RuntimeError("ASE calculator called without atoms")

        result = self._compute_fn(atoms)
        self.last_result = result

        energy = result.get("energy_eV")
        forces = result.get("forces_eV_per_A")
        if energy is None:
            raise RuntimeError("PySCF computation returned no energy")
        if forces is None:
            raise RuntimeError("PySCF computation returned no forces")

        self.results["energy"] = _normalize_float(float(energy), self._digits)
        self.results["forces"] = np.asarray(forces, dtype=float)


def _atoms_from_structure(structure: dict[str, Any]) -> Atoms:
    return Atoms(
        symbols=list(structure["symbols"]),
        positions=structure["positions_A"],
        cell=structure["cell_A"],
        pbc=structure["pbc"],
    )


def _write_extxyz(path: Path, atoms: Atoms, *, append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ase_write(path, atoms, format="extxyz", append=append)


def run_relaxation(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    run_dir = Path(state["run_dir"])
    log_path = Path(state["log_path"])

    log_event(
        log_path,
        node=NODE,
        event="start",
    )

    structure = state.get("structure")
    if not structure:
        raise ConfigLoadError(
            "Structure not loaded (expected `state['structure']` from load_structure)"
        )

    digits = int((state.get("resolved_config") or {}).get("run", {}).get("precision_digits", 8))
    calc_cfg = (state.get("resolved_config") or {}).get("calculator") or {}
    scf_cfg = calc_cfg.get("scf") or {}
    pbc_cfg = calc_cfg.get("pbc") or {}

    backend = str(calc_cfg.get("backend", "pyscf")).lower()
    method = str(calc_cfg.get("method", "dft")).lower()
    if backend != "pyscf" or method != "dft":
        raise ConfigLoadError(f"Unsupported calculator backend/method: {backend}/{method}")

    pbc_enabled = pbc_cfg.get("enabled")
    is_periodic = _is_periodic_structure(structure)
    use_pbc = is_periodic if pbc_enabled is None else bool(pbc_enabled)

    state.setdefault("calculation", {})
    state["calculation"].update(
        {
            "mode": "pbc" if use_pbc else "molecule",
            "backend": backend,
            "method": method,
            "xc": str(calc_cfg.get("xc", "PBE")),
            "basis": None,
            "pbc_basis": None,
            "pbc_pseudo": None,
            "pbc_mesh": None,
            "pbc_kpts": None,
            "charge": int(calc_cfg.get("charge", 0)),
            "spin": int(calc_cfg.get("spin", 0)),
            "energy_eV": None,
            "forces_eV_per_A": None,
            "scf_converged": None,
            "scf_iterations": None,
            "walltime_s": None,
            "error": None,
            "scf_solver": None,
        }
    )

    relax_cfg = (state.get("resolved_config") or {}).get("relax") or {}
    relax_enabled = bool(relax_cfg.get("enabled", True))
    output_cfg = (state.get("resolved_config") or {}).get("output") or {}
    write_trajectory = bool(output_cfg.get("write_trajectory", True))

    results_dir = run_dir / "results"
    trajectory_path = results_dir / "trajectory.xyz"
    final_path = results_dir / "final.xyz"

    def _compute_atoms(atoms: Atoms) -> dict[str, Any]:
        sym = atoms.get_chemical_symbols()
        pos = atoms.get_positions().tolist()
        if use_pbc:
            basis = str(pbc_cfg.get("basis", "gth-szv-molopt-sr"))
            pseudo = pbc_cfg.get("pseudo", "gth-pbe")
            mesh = list(pbc_cfg.get("mesh", [25, 25, 25]))
            kpts = list(pbc_cfg.get("kpts", [1, 1, 1]))
            use_multigrid = bool(pbc_cfg.get("use_multigrid", True))
            return _pyscf_pbc_single_point(
                symbols=sym,
                positions_A=pos,
                cell_A=atoms.get_cell().array.tolist(),
                basis=basis,
                pseudo=pseudo,
                mesh=mesh,
                kpts=kpts,
                xc=state["calculation"]["xc"] or "PBE",
                charge=state["calculation"]["charge"] or 0,
                spin=state["calculation"]["spin"] or 0,
                conv_tol=float(scf_cfg.get("conv_tol", 1e-8)),
                max_cycle=int(scf_cfg.get("max_cycle", 50)),
                digits=digits,
                use_multigrid=use_multigrid,
            )
        basis = str(calc_cfg.get("basis", "def2-svp"))
        return _pyscf_single_point(
            symbols=sym,
            positions_A=pos,
            basis=basis,
            xc=state["calculation"]["xc"] or "PBE",
            charge=state["calculation"]["charge"] or 0,
            spin=state["calculation"]["spin"] or 0,
            conv_tol=float(scf_cfg.get("conv_tol", 1e-8)),
            max_cycle=int(scf_cfg.get("max_cycle", 50)),
            digits=digits,
        )

    # Populate calculation fields that are fixed for this run (basis/pseudo/mesh/kpts).
    if use_pbc:
        state["calculation"]["pbc_basis"] = str(pbc_cfg.get("basis", "gth-szv-molopt-sr"))
        state["calculation"]["pbc_pseudo"] = pbc_cfg.get("pseudo", "gth-pbe")
        state["calculation"]["pbc_mesh"] = list(pbc_cfg.get("mesh", [25, 25, 25]))
        state["calculation"]["pbc_kpts"] = list(pbc_cfg.get("kpts", [1, 1, 1]))
    else:
        state["calculation"]["basis"] = str(calc_cfg.get("basis", "def2-svp"))

    atoms = _atoms_from_structure(structure)
    atoms.calc = _AsePyScfCalculator(compute_fn=_compute_atoms, digits=digits)

    state.setdefault("relaxation", {})
    state["relaxation"].update(
        {
            "enabled": relax_enabled,
            "optimizer": None,
            "fmax": None,
            "steps": None,
            "steps_taken": None,
            "trajectory_path": str(trajectory_path) if relax_enabled and write_trajectory else None,
            "final_structure_path": str(final_path),
        }
    )

    try:
        if relax_enabled:
            optimizer_name = str(relax_cfg.get("optimizer", "BFGS")).upper()
            fmax = float(relax_cfg.get("fmax", 0.05))
            max_steps = int(relax_cfg.get("steps", 200))

            if optimizer_name == "BFGS":
                opt = BFGS(atoms, logfile=None)
            elif optimizer_name == "FIRE":
                opt = FIRE(atoms, logfile=None)
            else:
                msg = f"Unsupported relax.optimizer={optimizer_name!r} (use BFGS or FIRE)"
                raise ConfigLoadError(msg)

            step_counter = {"n": 0}

            if write_trajectory:
                # Write the initial structure, then append after each optimizer step.
                _write_extxyz(trajectory_path, atoms, append=False)

                def _write_step():
                    _write_extxyz(trajectory_path, atoms, append=True)
                    step_counter["n"] += 1

                opt.attach(_write_step, interval=1)
            else:

                def _count_step():
                    step_counter["n"] += 1

                opt.attach(_count_step, interval=1)

            opt.run(fmax=fmax, steps=max_steps)

            # Ensure final energy/forces are evaluated and captured.
            _ = atoms.get_potential_energy()
            _ = atoms.get_forces()

            last = atoms.calc.last_result or {}
            state["calculation"].update(last)

            _write_extxyz(final_path, atoms, append=False)

            state["relaxation"].update(
                {
                    "optimizer": optimizer_name,
                    "fmax": fmax,
                    "steps": max_steps,
                    "steps_taken": int(step_counter["n"]),
                }
            )
            log_event(
                log_path,
                node=NODE,
                event="info",
                message="Relaxation complete",
                optimizer=optimizer_name,
                steps_taken=step_counter["n"],
                fmax=fmax,
            )
        else:
            # Single-point (no relaxation), but still write final.xyz for artifact discipline.
            _ = atoms.get_potential_energy()
            _ = atoms.get_forces()

            last = atoms.calc.last_result or {}
            state["calculation"].update(last)
            _write_extxyz(final_path, atoms, append=False)
            log_event(
                log_path,
                node=NODE,
                event="info",
                message="Single-point complete (no relaxation)",
                mode=state["calculation"]["mode"],
                energy_eV=state["calculation"]["energy_eV"],
                scf_converged=state["calculation"]["scf_converged"],
                scf_iterations=state["calculation"]["scf_iterations"],
                scf_solver=state["calculation"].get("scf_solver"),
                forces_present=state["calculation"]["forces_eV_per_A"] is not None,
            )
    except Exception as e:
        state["calculation"]["error"] = str(e)
        state["calculation"]["scf_converged"] = False
        log_event(
            log_path,
            node=NODE,
            event="error",
            message="Run failed",
            error=str(e),
        )

    state["calculation"]["walltime_s"] = _normalize_float(time.perf_counter() - t0, 6)

    # Write intermediate summary (validate_and_report will write final summary with validation).
    results_dir = run_dir / "results"
    summary_path = results_dir / "summary.json"
    summary: dict[str, Any] = {
        "status": (
            "calculated" if state["calculation"].get("energy_eV") is not None else "no_calculation"
        ),
        "run_id": state.get("run_id"),
        "material_id": state.get("material_id"),
        "structure": {
            "hash": state.get("structure_hash"),
            "canonical_path": state.get("structure_canonical_path"),
        },
        "relaxation": state.get("relaxation"),
        "calculation": state.get("calculation"),
    }
    write_json(summary_path, summary)

    log_event(
        log_path,
        node=NODE,
        event="end",
        duration_s=round(time.perf_counter() - t0, 6),
    )
    return state
