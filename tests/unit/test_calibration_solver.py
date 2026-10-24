"""Unit: calibration solver math (characterization of the original hardcoded example)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SOLVER = Path(__file__).resolve().parents[2] / "tools" / "pnp_calibration_solver.py"
_spec = importlib.util.spec_from_file_location("pnp_calibration_solver", SOLVER)
solver = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(solver)

# Values that used to be hardcoded in the script
EXAMPLE = {
    "top_left": {"dx": 0.0, "dy": 2.0},
    "top_right": {"dx": 0.0, "dy": 0.2},
    "bottom_left": {"dx": 0.8, "dy": 2.1},
    "bottom_right": {"dx": 1.0, "dy": 0.5},
    "center": {"dx": 0.5, "dy": 1.5},
}


def test_solve_matches_original_example():
    sol = solver.solve(EXAMPLE, 210.0)
    assert sol["rot_deg"] == pytest.approx(0.0546, abs=1e-4)
    assert sol["shift_x_mm"] == pytest.approx(0.46)
    assert sol["shift_y_mm"] == pytest.approx(1.26)


def test_center_is_optional():
    corners = {k: v for k, v in EXAMPLE.items() if k != "center"}
    sol = solver.solve(corners, 210.0)
    assert sol["shift_x_mm"] == pytest.approx(0.45)
    assert sol["shift_y_mm"] == pytest.approx(1.2)


def test_build_profile_rounds_and_keeps_contract():
    sol = solver.solve(EXAMPLE, 210.0)
    prof = solver.build_profile(
        sol,
        name="X",
        paper_width_mm=297.0,
        paper_height_mm=210.0,
        orientation="landscape",
        flip_mode="long",
    )
    assert prof["back_corrections"] == {
        "extra_rot_deg": 0.055,
        "shift_x_mm": 0.46,
        "shift_y_mm": 1.26,
    }
    assert prof["flip_mode"] == "long"
    assert prof["paper"] == {"width_mm": 297.0, "height_mm": 210.0, "orientation": "landscape"}
