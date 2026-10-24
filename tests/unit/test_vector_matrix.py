"""Unit tests for vector matrix construction (no rotation= kwarg; PDF Y sign)."""

import fitz
import pytest

from geometry import build_back_matrix, mm_to_pt


def test_build_back_matrix_identity_when_no_corrections():
    rect = fitz.Rect(0, 0, 200, 200)
    M = build_back_matrix(rect, 0.0, False, 0.0, 0.0)
    assert abs(M.a - 1) < 1e-9 and abs(M.d - 1) < 1e-9
    assert abs(M.b) < 1e-9 and abs(M.c) < 1e-9
    assert abs(M.e) < 1e-9 and abs(M.f) < 1e-9


def test_build_back_matrix_no_rotation_keyword():
    """Construction must not use fitz.Matrix(rotation=…)."""
    rect = fitz.Rect(0, 0, 200, 200)
    # Must not raise TypeError from rotation=
    M = build_back_matrix(rect, 5.0, False, 0.0, 0.0)
    assert M is not None


def _apply(M, x, y):
    """Transform a PDF user-space point (Y up) as the content stream `cm` does."""
    p = fitz.Point(x, y) * M
    return p.x, p.y


@pytest.mark.parametrize("rot", [0.3, -0.3, 10.0])
def test_build_back_matrix_rotation_keeps_page_center_fixed(rot):
    rect = fitz.Rect(0, 0, 595, 842)
    M = build_back_matrix(rect, rot, False, 0.0, 0.0)
    x, y = _apply(M, 297.5, 421)
    assert x == pytest.approx(297.5, abs=1e-6)
    assert y == pytest.approx(421, abs=1e-6)


def test_build_back_matrix_positive_rot_is_clockwise_pdf():
    """Positive degrees = clockwise: a point above the center moves right."""
    rect = fitz.Rect(0, 0, 200, 200)
    M = build_back_matrix(rect, 10.0, False, 0.0, 0.0)
    x, y = _apply(M, 100, 180)  # PDF Y up: above the center
    assert x > 100
    assert y < 180


def test_build_back_matrix_rotate180_keeps_page_on_page():
    rect = fitz.Rect(0, 0, 595, 842)
    M = build_back_matrix(rect, 0.0, True, 0.0, 0.0)
    assert _apply(M, 0, 0) == pytest.approx((595, 842))
    assert _apply(M, 595, 842) == pytest.approx((0, 0))


def test_build_back_matrix_shift_is_in_final_page_space_with_rotate180():
    """Shift applies after the 180° turn, as in the raster path."""
    rect = fitz.Rect(0, 0, 200, 200)
    shift = mm_to_pt(5.0)
    M = build_back_matrix(rect, 0.0, True, shift, shift)
    x, y = _apply(M, 100, 100)
    assert x == pytest.approx(100 + shift)
    assert y == pytest.approx(100 - shift)  # +Y contract = down = PDF -Y


def test_build_back_matrix_shift_is_not_rotated():
    """Shift is applied after rotation, so its direction is not rotated."""
    rect = fitz.Rect(0, 0, 200, 200)
    shift = mm_to_pt(5.0)
    M = build_back_matrix(rect, 10.0, False, shift, 0.0)
    x, y = _apply(M, 100, 100)
    assert x == pytest.approx(100 + shift)
    assert y == pytest.approx(100)


def test_build_back_matrix_positive_y_shifts_down_in_pdf():
    """+Y downward (printed) → negative PDF Y translation."""
    rect = fitz.Rect(0, 0, 200, 200)
    shift = mm_to_pt(5.0)
    M = build_back_matrix(rect, 0.0, False, 0.0, shift)
    assert abs(M.e) < 1e-9
    assert abs(M.f - (-shift)) < 1e-6


def test_build_back_matrix_positive_x_shifts_right():
    rect = fitz.Rect(0, 0, 200, 200)
    shift = mm_to_pt(5.0)
    M = build_back_matrix(rect, 0.0, False, shift, 0.0)
    assert abs(M.e - shift) < 1e-6
    assert abs(M.f) < 1e-9
