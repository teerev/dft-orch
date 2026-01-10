from __future__ import annotations

from pathlib import Path

import pytest

from dft_graph.config import CliOverrides, ConfigValidationError, resolve_config


def test_config_merge_and_overrides(tmp_path: Path):
    default = tmp_path / "default.yaml"
    materials = tmp_path / "materials"
    materials.mkdir()
    material = materials / "h2.yaml"

    default.write_text(
        """
run:
  runs_dir: "runs"
  precision_digits: 8
structure:
  path: null
calculator:
  backend: "pyscf"
  method: "dft"
  xc: "PBE"
  basis: "def2-svp"
  charge: 0
  spin: 0
  scf:
    conv_tol: 1e-8
    max_cycle: 50
relax:
  enabled: true
  optimizer: "BFGS"
  fmax: 0.05
  steps: 200
validate:
  require_scf_converged: true
  max_force: 0.05
output:
  write_trajectory: true
""".lstrip(),
        encoding="utf-8",
    )

    material.write_text(
        """
structure:
  path: "structures/h2.xyz"
calculator:
  xc: "LDA"
relax:
  enabled: false
""".lstrip(),
        encoding="utf-8",
    )

    resolved = resolve_config(
        default_config_path=default,
        material_id="h2",
        materials_dir=materials,
        overrides=CliOverrides(runs_dir="my_runs", structure_path="override.xyz", run_name="demo"),
    )

    cfg = resolved.resolved
    assert cfg["run"]["runs_dir"] == "my_runs"
    assert cfg["run"]["run_name"] == "demo"
    assert cfg["structure"]["path"] == "override.xyz"
    assert cfg["calculator"]["xc"] == "LDA"
    assert cfg["relax"]["enabled"] is False


def test_config_validation_error_is_clear(tmp_path: Path):
    default = tmp_path / "default.yaml"
    materials = tmp_path / "materials"
    materials.mkdir()

    default.write_text(
        """
run:
  runs_dir: "runs"
  precision_digits: "eight"
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError) as e:
        resolve_config(
            default_config_path=default,
            material_id=None,
            materials_dir=materials,
            overrides=CliOverrides(),
        )
    assert "precision_digits" in str(e.value)
