"""Integration/CLI: calibration solver (direct-read readings → profile, refine)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

SOLVER = Path(__file__).resolve().parents[2] / "tools" / "pnp_calibration_solver.py"

# Readings of a pure +1 mm X / +0.5 mm Y offset (no rotation)
SHIFT_ONLY = [
    "--top-left", "1", "0.5",
    "--top-right", "1", "0.5",
    "--bottom-left", "1", "0.5",
    "--bottom-right", "1", "0.5",
]


def run_solver(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SOLVER), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_help_does_not_write_profile(tmp_path: Path):
    proc = run_solver(["--help"], tmp_path)
    assert proc.returncode == 0
    assert "--top-left" in proc.stdout and "--refine" in proc.stdout
    assert list(tmp_path.iterdir()) == []


def test_missing_readings_fails_without_writing(tmp_path: Path):
    proc = run_solver([], tmp_path)
    assert proc.returncode == 2
    assert "required" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert list(tmp_path.iterdir()) == []


def test_writes_profile_with_mapped_corrections(tmp_path: Path):
    out = tmp_path / "p.json"
    proc = run_solver([*SHIFT_ONLY, "--output", str(out)], tmp_path)
    assert proc.returncode == 0, proc.stderr
    prof = json.loads(out.read_text(encoding="utf-8"))
    assert prof["back_corrections"] == {
        "extra_rot_deg": 0.0,
        "shift_x_mm": 1.0,
        "shift_y_mm": -0.5,
    }
    assert prof["flip_mode"] == "long"
    assert prof["paper"] == {"width_mm": 210.0, "height_mm": 297.0, "orientation": "portrait"}


def test_landscape_letter_paper(tmp_path: Path):
    proc = run_solver(
        [*SHIFT_ONLY, "--orientation", "landscape", "--paper", "letter", "--output", "-"],
        tmp_path,
    )
    assert proc.returncode == 0, proc.stderr
    prof = json.loads(proc.stdout)
    assert prof["paper"] == {"width_mm": 279.4, "height_mm": 215.9, "orientation": "landscape"}
    assert "rotation" in proc.stderr
    assert list(tmp_path.iterdir()) == []


def test_refuses_to_overwrite_without_force(tmp_path: Path):
    out = tmp_path / "p.json"
    out.write_text("keep", encoding="utf-8")
    proc = run_solver([*SHIFT_ONLY, "--output", str(out)], tmp_path)
    assert proc.returncode == 1
    assert "--force" in proc.stderr
    assert out.read_text(encoding="utf-8") == "keep"


def test_refine_adds_residual_and_keeps_profile_fields(tmp_path: Path):
    base = tmp_path / "base.json"
    base.write_text(
        json.dumps(
            {
                "name": "Mine",
                "paper": {"width_mm": 210.0, "height_mm": 297.0, "orientation": "portrait"},
                "margins": {"x_mm": 0, "y_mm": 0},
                "flip_mode": "long",
                "back_corrections": {"extra_rot_deg": -0.15, "shift_x_mm": 1.0, "shift_y_mm": -0.25},
                "_notes": "first pass",
            }
        ),
        encoding="utf-8",
    )
    proc = run_solver([*SHIFT_ONLY, "--refine", str(base), "--output", str(base), "--force"], tmp_path)
    assert proc.returncode == 0, proc.stderr
    prof = json.loads(base.read_text(encoding="utf-8"))
    assert prof["name"] == "Mine"
    assert prof["back_corrections"] == {
        "extra_rot_deg": -0.15,
        "shift_x_mm": 2.0,
        "shift_y_mm": -0.75,
    }
    assert prof["_notes"].startswith("first pass")


def test_refine_missing_base_profile_is_a_clear_error(tmp_path: Path):
    proc = run_solver([*SHIFT_ONLY, "--refine", str(tmp_path / "nope.json"), "--output", "-"], tmp_path)
    assert proc.returncode == 1
    assert "nope.json" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_inconsistent_readings_warn(tmp_path: Path):
    args = [
        "--top-left", "3", "0",
        "--top-right", "0", "0",
        "--bottom-left", "0", "0",
        "--bottom-right", "0", "0",
        "--output", "-",
    ]
    proc = run_solver(args, tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "Warning" in proc.stderr
