from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ConfigLoadError(RuntimeError):
    """Raised when config YAML cannot be loaded."""


class ConfigValidationError(RuntimeError):
    """Raised when config YAML fails schema validation."""


def _deep_merge_dicts(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge overlay onto base, returning a new dict (no mutation)."""
    out: dict[str, Any] = dict(base)
    for k, v in overlay.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge_dicts(out[k], v)
        else:
            out[k] = v
    return out


def _set_nested(d: dict[str, Any], path: list[str], value: Any) -> None:
    cur: dict[str, Any] = d
    for key in path[:-1]:
        nxt = cur.get(key)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[key] = nxt
        cur = nxt
    cur[path[-1]] = value


def load_yaml_file(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ConfigLoadError(f"Failed to read YAML config at {path}") from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigLoadError(f"Config at {path} must be a YAML mapping/object at the top level")
    return data


class SCFConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conv_tol: float = Field(default=1e-8, gt=0)
    max_cycle: int = Field(default=50, ge=1)


class PBCConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # None -> auto (use PBC if structure indicates periodicity)
    enabled: bool | None = Field(default=None)

    # Defaults chosen for "toy but works" gamma-point solids in PySCF PBC.
    basis: str = Field(default="gth-szv-molopt-sr")
    pseudo: str | None = Field(default="gth-pbe")

    # FFT mesh used by PBC DFT. Keep modest to avoid huge memory allocations.
    mesh: list[int] = Field(default_factory=lambda: [25, 25, 25])

    # Gamma-only for now; k-point meshes can be added later without changing interfaces.
    kpts: list[int] = Field(default_factory=lambda: [1, 1, 1])

    # Required for nuclear gradients in PySCF PBC RKS.
    use_multigrid: bool = Field(default=True)


class CalculatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="pyscf")
    method: str = Field(default="dft")
    xc: str = Field(default="PBE")
    basis: str = Field(default="def2-svp")
    charge: int = Field(default=0)
    spin: int = Field(default=0)
    scf: SCFConfig = Field(default_factory=SCFConfig)
    pbc: PBCConfig = Field(default_factory=PBCConfig)


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runs_dir: str = Field(default="runs")
    precision_digits: int = Field(default=8, ge=0, le=16)
    run_name: str | None = Field(default=None)
    retries: int = Field(default=1, ge=0, le=2)


class StructureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str | None = Field(default=None)


class RelaxConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True)
    optimizer: str = Field(default="BFGS")
    fmax: float = Field(default=0.05, gt=0)
    steps: int = Field(default=200, ge=0)


class ValidationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    require_scf_converged: bool = Field(default=True)
    max_force: float = Field(default=0.05, gt=0)


class OutputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    write_trajectory: bool = Field(default=True)


class RootConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run: RunConfig = Field(default_factory=RunConfig)
    structure: StructureConfig = Field(default_factory=StructureConfig)
    calculator: CalculatorConfig = Field(default_factory=CalculatorConfig)
    relax: RelaxConfig = Field(default_factory=RelaxConfig)
    validate_: ValidationConfig = Field(default_factory=ValidationConfig, alias="validate")
    output: OutputConfig = Field(default_factory=OutputConfig)


@dataclass(frozen=True)
class CliOverrides:
    runs_dir: str | None = None
    structure_path: str | None = None
    run_name: str | None = None


@dataclass(frozen=True)
class ResolvedConfig:
    config: RootConfig
    resolved: dict[str, Any]
    sources: dict[str, Any]
    project_root: Path


def infer_project_root(config_path: Path) -> Path:
    # common case: <root>/configs/default.yaml -> <root>
    if config_path.parent.name == "configs":
        return config_path.parent.parent
    return Path.cwd()


def resolve_config(
    *,
    default_config_path: Path,
    material_id: str | None,
    materials_dir: Path,
    overrides: CliOverrides,
) -> ResolvedConfig:
    """Load/merge/validate YAML config.

    Merge order:
    1) configs/default.yaml
    2) configs/materials/<material>.yaml (if provided)
    3) CLI overrides (runs_dir, run_name, structure path)
    """
    default_config_path = default_config_path.resolve()
    project_root = infer_project_root(default_config_path)

    default_raw = load_yaml_file(default_config_path)

    sources: dict[str, Any] = {"default": str(default_config_path)}
    merged = default_raw

    if material_id:
        material_path = (materials_dir / f"{material_id}.yaml").resolve()
        if not material_path.exists():
            raise ConfigLoadError(
                f"Material config not found for material_id={material_id!r}. "
                f"Expected: {material_path}"
            )
        material_raw = load_yaml_file(material_path)
        merged = _deep_merge_dicts(merged, material_raw)
        sources["material"] = str(material_path)

    if overrides.runs_dir is not None:
        _set_nested(merged, ["run", "runs_dir"], overrides.runs_dir)
        sources.setdefault("overrides", {})["run.runs_dir"] = overrides.runs_dir
    if overrides.run_name is not None:
        _set_nested(merged, ["run", "run_name"], overrides.run_name)
        sources.setdefault("overrides", {})["run.run_name"] = overrides.run_name
    if overrides.structure_path is not None:
        _set_nested(merged, ["structure", "path"], overrides.structure_path)
        sources.setdefault("overrides", {})["structure.path"] = overrides.structure_path

    try:
        cfg = RootConfig.model_validate(merged)
    except ValidationError as e:
        msg = (
            "Config validation failed for "
            f"default={default_config_path} material={material_id!r}.\n{e}"
        )
        raise ConfigValidationError(msg) from e

    resolved = cfg.model_dump(mode="json", by_alias=True)
    return ResolvedConfig(
        config=cfg,
        resolved=resolved,
        sources=sources,
        project_root=project_root,
    )
