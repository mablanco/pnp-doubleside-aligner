"""Unit tests for mm_to_pt (already-correct helper)."""

from geometry import mm_to_pt


def test_mm_to_pt_zero():
    assert mm_to_pt(0.0) == 0.0


def test_mm_to_pt_25_4_is_72():
    assert abs(mm_to_pt(25.4) - 72.0) < 1e-9


def test_mm_to_pt_linear():
    assert abs(mm_to_pt(10.0) - (10.0 * 72.0 / 25.4)) < 1e-9
