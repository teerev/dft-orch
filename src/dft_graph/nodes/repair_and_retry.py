from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..state import WorkflowState
from ..utils.logging import log_event
from ..utils.serialization import write_json

NODE = "repair_and_retry"


def _get_scf_cfg(state: WorkflowState) -> dict[str, Any]:
    cfg = state.get("resolved_config") or {}
    # Ensure the nested dict exists for in-place updates.
    cfg.setdefault("calculator", {}).setdefault("scf", {})
    return cfg["calculator"]["scf"]


def repair_and_retry(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    log_path = Path(state["log_path"])
    manifest_path = Path(state["manifest_path"])

    retry = state.get("retry") or {}
    remaining = int(retry.get("retries_remaining", 0))
    used = int(retry.get("retries_used", 0))

    log_event(
        log_path,
        node=NODE,
        event="start",
        retries_remaining=remaining,
        retries_used=used,
    )

    if remaining <= 0:
        log_event(log_path, node=NODE, event="info", message="No retries remaining (skipping)")
        log_event(
            log_path,
            node=NODE,
            event="end",
            duration_s=round(time.perf_counter() - t0, 6),
        )
        return state

    scf_cfg = _get_scf_cfg(state)
    prev_max_cycle = int(scf_cfg.get("max_cycle", 50))
    prev_conv_tol = float(scf_cfg.get("conv_tol", 1e-8))

    # Deterministic repair policy:
    # - ensure max_cycle is at least 50, otherwise bump to 50
    # - otherwise double max_cycle up to a hard cap
    new_max_cycle = 50 if prev_max_cycle < 50 else min(prev_max_cycle * 2, 400)

    # Slightly relax conv_tol if user set an extremely tight tolerance.
    new_conv_tol = max(prev_conv_tol, 1e-8)

    changes = {
        "calculator.scf.max_cycle": {"old": prev_max_cycle, "new": new_max_cycle},
        "calculator.scf.conv_tol": {"old": prev_conv_tol, "new": new_conv_tol},
    }

    scf_cfg["max_cycle"] = new_max_cycle
    scf_cfg["conv_tol"] = new_conv_tol

    # Update retry bookkeeping
    used += 1
    remaining -= 1
    retry.setdefault("history", [])
    retry["history"].append(
        {
            "attempt": used,
            "changes": changes,
            "reason": "scf_not_converged",
        }
    )
    retry["retries_used"] = used
    retry["retries_remaining"] = remaining
    state["retry"] = retry

    log_event(
        log_path,
        node=NODE,
        event="info",
        message="Applied retry modifications",
        attempt=used,
        **changes,
    )

    # Update manifest deterministically with retry history (no timestamps).
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        manifest = {}
    manifest["retry"] = state["retry"]
    write_json(manifest_path, manifest)

    log_event(
        log_path,
        node=NODE,
        event="end",
        duration_s=round(time.perf_counter() - t0, 6),
        retries_remaining=remaining,
        retries_used=used,
    )
    return state
