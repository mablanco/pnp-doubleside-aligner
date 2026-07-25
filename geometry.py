"""Pure geometry helpers: units, page-order, vector/raster sign conventions."""

from __future__ import annotations

from typing import Any

import fitz


def mm_to_pt(mm: float) -> float:
    """Convert millimeters to PDF points (1 in = 25.4 mm = 72 pt)."""
    return mm * 72.0 / 25.4


def effective_total(total: int, order: str, on_odd: str) -> int:
    """
    Compute the effective number of pages to process.

    For fronts_then_backs with an odd page count:
    - add_blank → total + 1
    - drop_last → total - 1
    - warn → unchanged (caller should emit stderr warning)
    """
    if order == "fronts_then_backs" and (total % 2 == 1):
        if on_odd == "add_blank":
            return total + 1
        if on_odd == "drop_last":
            return total - 1
    return total


def is_back_page(index0: int, total_eff: int, order: str) -> bool:
    """Return True if zero-based index is a back page under the given order mode."""
    if order == "single_sided":
        return False
    if order == "interleaved":
        return (index0 % 2) == 1
    if order == "fronts_then_backs":
        half = total_eff // 2
        return index0 >= half
    if order == "last_back":
        return index0 == (total_eff - 1)
    return False


def build_back_matrix(
    rect: Any,
    extra_rot: float,
    rotate180: bool,
    shift_x_pt: float,
    shift_y_pt: float,
) -> fitz.Matrix:
    """
    Build the PDF transformation matrix for a back page.

    Sign contract (docs/calibration_guide.md):
    - positive rotation = clockwise → PDF Matrix uses negated CCW angle
    - positive X = right
    - positive Y = downward → PDF user-space Y is up, so translate by -shift_y
    """
    M = fitz.Matrix(1, 0, 0, 1, 0, 0)

    if abs(extra_rot) > 1e-6:
        cx = rect.width / 2.0
        cy = rect.height / 2.0
        # fitz.Matrix(degrees) is counter-clockwise; negate for clockwise contract
        M = (
            fitz.Matrix(1, 0, 0, 1, cx, cy)
            * fitz.Matrix(-extra_rot)
            * fitz.Matrix(1, 0, 0, 1, -cx, -cy)
            * M
        )

    if rotate180:
        cx = rect.width / 2.0
        cy = rect.height / 2.0
        M = (
            fitz.Matrix(1, 0, 0, 1, cx, cy)
            * fitz.Matrix(180)
            * fitz.Matrix(1, 0, 0, 1, -cx, -cy)
            * M
        )

    if abs(shift_x_pt) > 1e-6 or abs(shift_y_pt) > 1e-6:
        # PDF +Y is up; contract +Y is down
        shift_matrix = fitz.Matrix(1, 0, 0, 1, shift_x_pt, -shift_y_pt)
        M = shift_matrix * M

    return M


def raster_rotation_angle(extra_rot: float) -> float:
    """PIL Image.rotate is CCW for positive angles; contract is clockwise."""
    return -extra_rot


def reportlab_shift_y(shift_y_pt: float) -> float:
    """ReportLab canvas origin is bottom-left (+Y up); contract +Y is down."""
    return -shift_y_pt
