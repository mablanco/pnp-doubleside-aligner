"""Integration: vector geometry — backs move, fronts identity; shift-only ≠ identity."""

from __future__ import annotations

from pathlib import Path

import fitz


def _label_rect(page: fitz.Page, label: str):
    hits = page.search_for(label)
    assert hits, f"label {label!r} not found"
    return hits[0]


def test_vector_nonzero_profile_moves_backs_fronts_identity(
    run_main_cli,
    sample_interleaved: Path,
    profile_nonzero: Path,
    tmp_output: Path,
):
    out = tmp_output / "nonzero_vector.pdf"
    proc = run_main_cli(
        [
            "--input",
            str(sample_interleaved),
            "--output",
            str(out),
            "--profile",
            str(profile_nonzero),
            "--order",
            "interleaved",
            "--mode",
            "vector",
            "--flip-mode",
            "long",
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert out.is_file()

    src = fitz.open(sample_interleaved)
    dst = fitz.open(out)
    try:
        # Fronts (even indices): unchanged label position
        for i, label in ((0, "F0"), (2, "F2")):
            assert abs(_label_rect(src[i], label).x0 - _label_rect(dst[i], label).x0) < 0.5
            assert abs(_label_rect(src[i], label).y0 - _label_rect(dst[i], label).y0) < 0.5
        # Backs (odd): must move
        for i, label in ((1, "B1"), (3, "B3")):
            s = _label_rect(src[i], label)
            d = _label_rect(dst[i], label)
            moved = abs(s.x0 - d.x0) > 1.0 or abs(s.y0 - d.y0) > 1.0
            assert moved, f"back page {i} label did not move"
    finally:
        src.close()
        dst.close()


def test_vector_shift_only_backs_differ_from_identity(
    run_main_cli,
    sample_interleaved: Path,
    profile_shift_only: Path,
    tmp_output: Path,
):
    out = tmp_output / "shift_only.pdf"
    proc = run_main_cli(
        [
            "--input",
            str(sample_interleaved),
            "--output",
            str(out),
            "--profile",
            str(profile_shift_only),
            "--order",
            "interleaved",
            "--mode",
            "vector",
            "--flip-mode",
            "long",
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout

    src = fitz.open(sample_interleaved)
    dst = fitz.open(out)
    try:
        s = _label_rect(src[1], "B1")
        d = _label_rect(dst[1], "B1")
        assert abs(s.x0 - d.x0) > 1.0, "shift-only back must not be identity copy"
    finally:
        src.close()
        dst.close()
