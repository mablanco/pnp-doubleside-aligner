"""Unit: direct-read calibration math (pure) and geometric round-trip through the aligner."""

from __future__ import annotations

import math
from typing import Dict, Tuple

import fitz
import pytest

import calibration as cal
from geometry import build_back_matrix, mm_to_pt

Point = Tuple[float, float]


def test_page_size_per_paper_and_orientation():
    assert cal.page_size_mm("a4", "portrait") == (210.0, 297.0)
    assert cal.page_size_mm("a4", "landscape") == (297.0, 210.0)
    assert cal.page_size_mm("letter", "portrait") == pytest.approx((215.9, 279.4))
    with pytest.raises(ValueError):
        cal.page_size_mm("a3", "portrait")


def test_targets_are_inset_from_edges_and_centered():
    t = cal.targets(297.0, 210.0)
    assert t["top_left"] == (25.0, 25.0)
    assert t["bottom_right"] == (272.0, 185.0)
    assert t["center"] == (148.5, 105.0)


def _model_readings(rot_deg: float, tx: float, ty: float, w: float, h: float) -> Dict[str, Point]:
    return {
        name: cal.predicted_offset(rot_deg, tx, ty, p, w, h)
        for name, p in cal.targets(w, h).items()
    }


def test_fit_recovers_rotation_and_shift():
    readings = _model_readings(0.4, 1.5, 0.75, 210.0, 297.0)
    fit = cal.fit_readings(readings, 210.0, 297.0)
    assert fit.rot_deg == pytest.approx(0.4)
    assert fit.tx_mm == pytest.approx(1.5)
    assert fit.ty_mm == pytest.approx(0.75)
    assert max(fit.residuals_mm.values()) == pytest.approx(0.0, abs=1e-9)


def test_fit_center_is_optional():
    readings = _model_readings(-0.2, 0.5, -1.0, 297.0, 210.0)
    del readings["center"]
    fit = cal.fit_readings(readings, 297.0, 210.0)
    assert fit.rot_deg == pytest.approx(-0.2)
    assert (fit.tx_mm, fit.ty_mm) == pytest.approx((0.5, -1.0))
    assert set(fit.residuals_mm) == {"top_left", "top_right", "bottom_left", "bottom_right"}


def test_fit_reports_residual_for_a_misread_point():
    readings = _model_readings(0.0, 0.0, 0.0, 210.0, 297.0)
    readings["top_left"] = (2.0, 0.0)
    fit = cal.fit_readings(readings, 210.0, 297.0)
    assert max(fit.residuals_mm, key=fit.residuals_mm.get) == "top_left"
    assert fit.residuals_mm["top_left"] > 1.0


def test_fit_requires_the_four_corners():
    readings = _model_readings(0.0, 0.0, 0.0, 210.0, 297.0)
    del readings["bottom_left"]
    with pytest.raises(ValueError):
        cal.fit_readings(readings, 210.0, 297.0)


def test_mapping_to_back_corrections_negates_only_y_without_rotation():
    fit = cal.Fit(rot_deg=0.0, tx_mm=1.2, ty_mm=0.8, residuals_mm={})
    assert cal.to_back_corrections(fit) == pytest.approx(
        {"extra_rot_deg": 0.0, "shift_x_mm": 1.2, "shift_y_mm": -0.8}
    )


def test_mapping_counter_rotates_the_shift():
    """The printer rotates the correcting shift too; the mapping compensates it."""
    fit = cal.Fit(rot_deg=1.0, tx_mm=5.0, ty_mm=0.0, residuals_mm={})
    bc = cal.to_back_corrections(fit)
    assert bc["extra_rot_deg"] == 1.0
    assert bc["shift_x_mm"] == pytest.approx(5.0 * math.cos(math.radians(1.0)))
    assert bc["shift_y_mm"] == pytest.approx(5.0 * math.sin(math.radians(1.0)))


def test_refine_adds_residual_corrections():
    base = {"extra_rot_deg": -0.15, "shift_x_mm": 1.0, "shift_y_mm": -0.25}
    delta = {"extra_rot_deg": 0.05, "shift_x_mm": 0.4, "shift_y_mm": 0.0}
    assert cal.refine_corrections(base, delta) == pytest.approx(
        {"extra_rot_deg": -0.10, "shift_x_mm": 1.4, "shift_y_mm": -0.25}
    )


# --- Geometric round-trip -------------------------------------------------
#
# Simulates the physical duplex print of the calibration sheet:
#   back scale zero for target T is drawn at (W - Tx, Ty) on the back page
#   (mirrored in X) → the aligner applies build_back_matrix in PDF space →
#   the sheet is flipped (front view x = W - x_back) → the printer adds a
#   rigid error (clockwise rotation about the page centre + shift).
# The reading at T is where the back zero lands minus T (front view, Y down).


def _read_sheet(
    corrections: Dict[str, float],
    printer_rot_deg: float,
    printer_shift: Point,
    w: float,
    h: float,
) -> Dict[str, Point]:
    rect = fitz.Rect(0, 0, mm_to_pt(w), mm_to_pt(h))
    m = build_back_matrix(
        rect,
        corrections["extra_rot_deg"],
        False,
        mm_to_pt(corrections["shift_x_mm"]),
        mm_to_pt(corrections["shift_y_mm"]),
    )
    a = math.radians(printer_rot_deg)
    cx, cy = w / 2, h / 2
    out = {}
    for name, (tx, ty) in cal.targets(w, h).items():
        xb, yb = w - tx, ty  # back page, mm, Y down
        p = fitz.Point(mm_to_pt(xb), mm_to_pt(h - yb)) * m  # PDF space, Y up
        xb, yb = p.x * 25.4 / 72, h - p.y * 25.4 / 72
        xf, yf = w - xb, yb  # seen from the front
        # clockwise rotation for Y down about the centre, then shift
        vx, vy = xf - cx, yf - cy
        xf = cx + vx * math.cos(a) - vy * math.sin(a) + printer_shift[0]
        yf = cy + vx * math.sin(a) + vy * math.cos(a) + printer_shift[1]
        out[name] = (xf - tx, yf - ty)
    return out


IDENTITY = {"extra_rot_deg": 0.0, "shift_x_mm": 0.0, "shift_y_mm": 0.0}


@pytest.mark.parametrize("orientation", ["portrait", "landscape"])
@pytest.mark.parametrize(
    "rot,shift",
    [(0.4, (1.5, 0.75)), (-1.0, (-5.0, 3.0)), (0.15, (0.0, -2.0)), (1.0, (5.0, 5.0))],
)
def test_round_trip_profile_cancels_printer_error(orientation, rot, shift):
    w, h = cal.page_size_mm("a4", orientation)
    readings = _read_sheet(IDENTITY, rot, shift, w, h)
    corrections = cal.to_back_corrections(cal.fit_readings(readings, w, h))
    residual = _read_sheet(corrections, rot, shift, w, h)
    worst = max(math.hypot(dx, dy) for dx, dy in residual.values())
    assert worst < 0.01


def test_round_trip_refine_converges_from_a_partial_profile():
    w, h = cal.page_size_mm("a4", "portrait")
    partial = {"extra_rot_deg": -0.1, "shift_x_mm": 1.0, "shift_y_mm": -0.25}
    residual = _read_sheet(partial, -0.3, (1.4, 0.3), w, h)
    delta = cal.to_back_corrections(cal.fit_readings(residual, w, h))
    refined = cal.refine_corrections(partial, delta)
    after = _read_sheet(refined, -0.3, (1.4, 0.3), w, h)
    assert max(math.hypot(dx, dy) for dx, dy in after.values()) < 0.01
