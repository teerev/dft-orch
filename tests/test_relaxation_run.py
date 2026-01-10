from __future__ import annotations

import json
from pathlib import Path

from dft_graph.cli import main


def test_relaxation_writes_trajectory_and_final(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    runs_dir = tmp_path / "runs"

    rc = main(
        [
            "run",
            "--config",
            str(repo_root / "configs" / "default.yaml"),
            "--material",
            "h2_relax",
            "--runs-dir",
            str(runs_dir),
            "--run-name",
            "relax",
        ]
    )
    assert rc == 0

    run_dirs = [p for p in runs_dir.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    assert (run_dir / "results" / "trajectory.xyz").exists()
    assert (run_dir / "results" / "final.xyz").exists()

    summary = json.loads((run_dir / "results" / "summary.json").read_text(encoding="utf-8"))
    assert summary["relaxation"]["enabled"] is True
    assert summary["relaxation"]["steps_taken"] is not None
    assert summary["calculation"]["energy_eV"] is not None
    assert summary["calculation"]["forces_eV_per_A"] is not None
    assert summary["validation"]["passed"] is True
