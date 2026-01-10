from __future__ import annotations

from pathlib import Path

from dft_graph.nodes.load_structure import load_structure


def _make_run_state(run_dir: Path, structure_path: Path, *, digits: int = 8):
    (run_dir / "input").mkdir(parents=True, exist_ok=True)
    return {
        "run_dir": str(run_dir),
        "log_path": str(run_dir / "logs.jsonl"),
        "manifest_path": str(run_dir / "manifest.json"),
        "resolved_config": {"run": {"precision_digits": digits}},
        "structure_path": str(structure_path),
        "structure_resolved_path": str(structure_path),
        "structure_input_copied_path": str(structure_path),
        "structure_input_hash": None,
        "structure_hash": None,
        "structure_canonical_path": None,
        "structure": None,
    }


def test_structure_hash_is_deterministic_for_same_input(tmp_path: Path):
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"
    xyz = tmp_path / "h2.xyz"
    xyz.write_text(
        "2\nH2\nH 0.0 0.0 0.0\nH 0.0 0.0 0.740000\n",
        encoding="utf-8",
    )

    s1 = load_structure(_make_run_state(run1, xyz))
    s2 = load_structure(_make_run_state(run2, xyz))

    assert s1["structure_hash"] == s2["structure_hash"]
    assert (run1 / "input" / "canonical.xyz").exists()
    assert (run2 / "input" / "canonical.xyz").exists()


def test_structure_hash_changes_when_positions_change(tmp_path: Path):
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"
    xyz1 = tmp_path / "a.xyz"
    xyz2 = tmp_path / "b.xyz"
    xyz1.write_text(
        "2\nH2\nH 0.0 0.0 0.0\nH 0.0 0.0 0.740000\n",
        encoding="utf-8",
    )
    xyz2.write_text(
        "2\nH2\nH 0.0 0.0 0.0\nH 0.0 0.0 0.750000\n",
        encoding="utf-8",
    )

    s1 = load_structure(_make_run_state(run1, xyz1))
    s2 = load_structure(_make_run_state(run2, xyz2))

    assert s1["structure_hash"] != s2["structure_hash"]
