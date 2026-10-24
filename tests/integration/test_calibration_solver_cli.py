"""Integration/CLI: calibration solver arguments, output and overwrite safety."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

SOLVER = Path(__file__).resolve().parents[2] / "tools" / "pnp_calibration_solver.py"

CORNERS = [
    "--top-left", "0.0", "2.0",
    "--top-right", "0.0", "0.2",
    "--bottom-left", "0.8", "2.1",
    "--bottom-right", "1.0", "0.5",
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
    assert "--top-left" in proc.stdout
    assert not (tmp_path / "profiles").exists()


def test_missing_measures_fails_without_writing(tmp_path: Path):
    proc = run_solver([], tmp_path)
    assert proc.returncode == 2
    assert "required" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert not (tmp_path / "profiles").exists()


def test_writes_profile(tmp_path: Path):
    out = tmp_path / "p.json"
    proc = run_solver([*CORNERS, "--center", "0.5", "1.5", "--output", str(out)], tmp_path)
    assert proc.returncode == 0, proc.stderr
    prof = json.loads(out.read_text(encoding="utf-8"))
    assert prof["back_corrections"] == {
        "extra_rot_deg": 0.055,
        "shift_x_mm": 0.46,
        "shift_y_mm": 1.26,
    }


def test_refuses_to_overwrite_without_force(tmp_path: Path):
    out = tmp_path / "p.json"
    out.write_text("keep", encoding="utf-8")
    proc = run_solver([*CORNERS, "--output", str(out)], tmp_path)
    assert proc.returncode == 1
    assert "--force" in proc.stderr
    assert out.read_text(encoding="utf-8") == "keep"

    proc = run_solver([*CORNERS, "--output", str(out), "--force"], tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(out.read_text(encoding="utf-8"))["flip_mode"] == "long"


def test_stdout_output_is_pure_json(tmp_path: Path):
    proc = run_solver([*CORNERS, "--output", "-", "--orientation", "portrait",
                       "--paper-width", "210", "--paper-height", "297"], tmp_path)
    assert proc.returncode == 0, proc.stderr
    prof = json.loads(proc.stdout)
    assert prof["paper"]["orientation"] == "portrait"
    assert "skew" in proc.stderr
    assert list(tmp_path.iterdir()) == []
