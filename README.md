# dft-orch

Deterministic, **LangGraph-orchestrated** “DFT-style” workflows (learning project).  
No LLMs in the workflow: LangGraph is used purely for orchestration, conditional routing, retries, and artifact discipline.

## What this repo is

- **Goal**: learn LangGraph by orchestrating a small, deterministic workflow that will (in later milestones) run a minimal PySCF+ASE calculation and optional ASE geometry relaxation.
- **Priority**: determinism, clear state passing, clean structure, reproducible run artifacts (manifest/logs/results).

## Repo layout

```
src/dft_graph/                # library + CLI + LangGraph workflow
configs/                      # YAML configs (default + materials overlays)
structures/                   # local structure inputs (XYZ/CIF/etc)
runs/                         # created at runtime (ignored in git)
tests/                        # pytest
```

## Tooling

- **Python**: 3.11+
- **Dependency workflow**: **pip-tools** (pinned `requirements*.txt`)
- **Lint**: ruff
- **Tests**: pytest

### Setup (venv + deps)

```bash
cd /Users/user/repos/dft-orch
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements-dev.txt
```

### Run

```bash
python -m dft_graph run --material tio2_rutile
```

Useful overrides:

```bash
python -m dft_graph run --material tio2_rutile --runs-dir runs --run-name demo
python -m dft_graph run --material tio2_rutile --structure structures/h2.xyz
```

### Lint / format

```bash
ruff check .
ruff format .
```

### Tests

```bash
pytest
```

## Outputs

Each run creates a deterministic run directory under `runs/`:

```
runs/<timestamp>_<material>_<hash>_<gitsha?>_<run_name?>/
  manifest.json
  logs.jsonl
  input/
    structure.<ext>         # copied input (if provided)
  results/
    summary.json
    report.md
```

## Milestones (tracked in code)

- **Milestone 0–1 (implemented)**: repo skeleton + config system + deterministic run dirs + manifest/log/summary/report + graph scaffolding.
- **Milestone 2 (next)**: structure loading (ASE) + canonical structure hashing.
- **Milestone 3+**: minimal PySCF energy/forces, relaxation, validation, conditional retry.
