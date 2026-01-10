from __future__ import annotations

from pathlib import Path

from dft_graph.nodes.run_relaxation import run_relaxation
from dft_graph.nodes.validate_and_report import validate_and_report


def test_pbc_single_point_h2_in_box(tmp_path: Path):
    run_dir = tmp_path / "run"
    (run_dir / "results").mkdir(parents=True, exist_ok=True)

    state = {
        "run_id": "test",
        "material_id": "h2_pbc",
        "run_dir": str(run_dir),
        "log_path": str(run_dir / "logs.jsonl"),
        "resolved_config": {
            "run": {"precision_digits": 8},
            "relax": {"enabled": False},
            "validate": {"require_scf_converged": True, "max_force": 1e6},
            "calculator": {
                "backend": "pyscf",
                "method": "dft",
                "xc": "PBE",
                "charge": 0,
                "spin": 0,
                "scf": {"conv_tol": 1e-8, "max_cycle": 50},
                "pbc": {
                    "enabled": True,
                    "basis": "gth-szv-molopt-sr",
                    "pseudo": "gth-pbe",
                    "mesh": [15, 15, 15],
                    "kpts": [1, 1, 1],
                    "use_multigrid": True,
                },
            },
        },
        "structure_hash": "x",
        "structure_canonical_path": str(run_dir / "input" / "canonical.xyz"),
        "structure": {
            "symbols": ["H", "H"],
            "positions_A": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.74]],
            "cell_A": [[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]],
            "pbc": [True, True, True],
        },
    }

    state = run_relaxation(state)
    assert state["calculation"]["mode"] == "pbc"
    assert state["calculation"]["energy_eV"] is not None
    assert state["calculation"]["scf_converged"] is True
    assert state["calculation"]["forces_eV_per_A"] is not None

    state = validate_and_report(state)
    assert state["validation"]["passed"] is True
