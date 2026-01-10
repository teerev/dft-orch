from __future__ import annotations

import json
from pathlib import Path

from dft_graph.cli import main


def test_retry_happens_once_and_succeeds(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    runs_dir = tmp_path / "runs"

    rc = main(
        [
            "run",
            "--config",
            str(repo_root / "configs" / "default.yaml"),
            "--material",
            "h2_retry",
            "--runs-dir",
            str(runs_dir),
            "--run-name",
            "retry",
        ]
    )
    assert rc == 0

    run_dirs = [p for p in runs_dir.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    summary = json.loads((run_dir / "results" / "summary.json").read_text(encoding="utf-8"))
    assert summary["validation"]["passed"] is True
    assert summary["retry"]["retries_used"] == 1
    assert summary["retry"]["retries_remaining"] == 0
    assert len(summary["retry"]["history"]) == 1
