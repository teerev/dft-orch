from __future__ import annotations

from datetime import UTC, datetime

from dft_graph.utils.paths import build_run_id, sanitize_component


def test_sanitize_component_is_safe():
    assert sanitize_component(" My Run Name! ") == "My-Run-Name"
    assert sanitize_component("a/b/c") == "a-b-c"


def test_build_run_id_deterministic():
    dt = datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC)
    run_id = build_run_id(
        created_at_utc=dt,
        material_id="tio2_rutile",
        config_hash="abc12345",
        git_sha="deadbee",
        run_name="My Run",
    )
    assert run_id == "20200102T030405Z_tio2_rutile_abc12345_deadbee_my-run"


def test_build_run_id_without_optional_parts():
    dt = datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC)
    run_id = build_run_id(
        created_at_utc=dt,
        material_id="mat",
        config_hash="hsh",
        git_sha=None,
        run_name=None,
    )
    assert run_id == "20200102T030405Z_mat_hsh"
