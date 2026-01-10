from __future__ import annotations

from pathlib import Path

from dft_graph.utils.hashing import sha256_file, short_hash_from_obj, stable_json_dumps


def test_stable_json_is_order_independent():
    a = {"b": 1, "a": 2, "nested": {"z": 0, "y": 1}}
    b = {"nested": {"y": 1, "z": 0}, "a": 2, "b": 1}

    assert stable_json_dumps(a) == stable_json_dumps(b)
    assert short_hash_from_obj(a) == short_hash_from_obj(b)


def test_sha256_file_changes_with_content(tmp_path: Path):
    p = tmp_path / "x.txt"
    p.write_text("a", encoding="utf-8")
    h1 = sha256_file(p)
    p.write_text("b", encoding="utf-8")
    h2 = sha256_file(p)
    assert h1 != h2
