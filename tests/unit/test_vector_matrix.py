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


def test_build_back_matrix_positive_rot_is_clockwise_pdf():
    """Positive degrees = clockwise → PDF matrix uses negative CCW angle."""
    rect = fitz.Rect(0, 0, 200, 200)
    M = build_back_matrix(rect, 10.0, False, 0.0, 0.0)
    expected = (
        fitz.Matrix(1, 0, 0, 1, 100, 100)
        * fitz.Matrix(-10.0)
        * fitz.Matrix(1, 0, 0, 1, -100, -100)
    )
    for attr in ("a", "b", "c", "d", "e", "f"):
        assert abs(getattr(M, attr) - getattr(expected, attr)) < 1e-6


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
