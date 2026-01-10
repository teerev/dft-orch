from __future__ import annotations

from pathlib import Path

from dft_graph.cli import main


def test_smoke_run_creates_artifacts(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    runs_dir = tmp_path / "runs"

    rc = main(
        [
            "run",
            "--config",
            str(repo_root / "configs" / "default.yaml"),
            "--material",
            "tio2_rutile",
            "--runs-dir",
            str(runs_dir),
            "--run-name",
            "smoke",
        ]
    )
    assert rc == 0

    run_dirs = [p for p in runs_dir.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "logs.jsonl").exists()
    assert (run_dir / "results" / "summary.json").exists()
    assert (run_dir / "results" / "report.md").exists()

    # If structure path exists, load_config copies it into input/
    input_dir = run_dir / "input"
    assert input_dir.exists()
    structure_copies = list(input_dir.glob("structure.*"))
    assert len(structure_copies) == 1
