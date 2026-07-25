"""Unit tests for page-order classification and odd-page effective totals."""

import pytest

from geometry import effective_total, is_back_page


@pytest.mark.parametrize(
    "total,order,on_odd,expected",
    [
        (4, "interleaved", "warn", 4),
        (3, "interleaved", "warn", 3),
        (3, "fronts_then_backs", "warn", 3),
        (3, "fronts_then_backs", "add_blank", 4),
        (3, "fronts_then_backs", "drop_last", 2),
        (4, "fronts_then_backs", "add_blank", 4),
        (5, "last_back", "warn", 5),
        (2, "single_sided", "warn", 2),
    ],
)
def test_effective_total(total, order, on_odd, expected):
    assert effective_total(total, order, on_odd) == expected


@pytest.mark.parametrize(
    "index0,total_eff,order,expected",
    [
        (0, 4, "interleaved", False),
        (1, 4, "interleaved", True),
        (2, 4, "interleaved", False),
        (3, 4, "interleaved", True),
        (0, 4, "fronts_then_backs", False),
        (1, 4, "fronts_then_backs", False),
        (2, 4, "fronts_then_backs", True),
        (3, 4, "fronts_then_backs", True),
        (0, 3, "fronts_then_backs", False),
        (1, 3, "fronts_then_backs", True),
        (2, 3, "fronts_then_backs", True),
        (0, 3, "last_back", False),
        (1, 3, "last_back", False),
        (2, 3, "last_back", True),
        (0, 4, "single_sided", False),
        (1, 4, "single_sided", False),
        (3, 4, "single_sided", False),
    ],
)
def test_is_back_page(index0, total_eff, order, expected):
    assert is_back_page(index0, total_eff, order) is expected
