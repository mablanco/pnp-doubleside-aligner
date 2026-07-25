"""Unit tests for batch smart page-order detection helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BATCH_PATH = REPO_ROOT / "tools" / "pnp_batch_align.py"


@pytest.fixture(scope="module")
def batch():
    spec = importlib.util.spec_from_file_location("pnp_batch_align", BATCH_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


# --- name hint / page count (T008) ---


@pytest.mark.parametrize(
    "name,expected",
    [
        ("game_interleaved.pdf", "interleaved"),
        ("deck_fronts_then_backs.pdf", "fronts_then_backs"),
        ("pack_halves.pdf", "fronts_then_backs"),
        ("book_last_back.pdf", "last_back"),
        ("sheet_single_sided.pdf", "single_sided"),
        ("sheet_single.pdf", "single_sided"),
        ("plain_cards.pdf", None),
    ],
)
def test_name_hint_to_order(batch, name, expected):
    assert batch.name_hint_to_order(name) == expected


@pytest.mark.parametrize(
    "total,expected_order,reason_prefix",
    [
        (0, "single_sided", "pages:1"),
        (1, "single_sided", "pages:1"),
        (3, "last_back", "pages:odd(3)"),
        (5, "last_back", "pages:odd(5)"),
        (2, None, None),
        (4, None, None),
    ],
)
def test_detect_order_by_page_count(batch, total, expected_order, reason_prefix):
    order, reason = batch.detect_order_by_page_count(total)
    assert order == expected_order
    if reason_prefix is None:
        assert reason is None
    else:
        assert reason == reason_prefix


# --- avg_sim_block (T009) ---


def test_avg_sim_block_identical(batch):
    v = [1.0, 0.0, -1.0]
    fps = [v, v, v]
    assert batch.avg_sim_block(fps, 0, 3) == pytest.approx(1.0)


def test_avg_sim_block_orthogonal_pair(batch):
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    fps = [a, b]
    assert batch.avg_sim_block(fps, 0, 2) == pytest.approx(0.0)


def test_avg_sim_block_single_or_empty(batch):
    fps = [[1.0, 0.0]]
    assert batch.avg_sim_block(fps, 0, 1) == 0.0
    assert batch.avg_sim_block(fps, 0, 0) == 0.0


# --- common-back decision (T010) ---


def test_decide_common_back_interleaved(batch):
    order, reason = batch.decide_by_common_back(0.95, 0.70, "fronts_then_backs")
    assert order == "interleaved"
    assert reason.startswith("visual:odd-cluster")


def test_decide_common_back_fronts_then_backs(batch):
    order, reason = batch.decide_by_common_back(0.70, 0.95, "interleaved")
    assert order == "fronts_then_backs"
    assert reason.startswith("visual:second-half")


def test_decide_common_back_tie_uses_even_default(batch):
    order, reason = batch.decide_by_common_back(0.50, 0.52, "fronts_then_backs")
    assert order == "fronts_then_backs"
    assert reason.startswith("visual:tie")
    assert "fronts_then_backs" in reason


def test_decide_common_back_both_high_insufficient_margin(batch):
    # Both above T but margin < M → tie
    order, reason = batch.decide_by_common_back(0.90, 0.88, "interleaved")
    assert order == "interleaved"
    assert "visual:tie" in reason


# --- name-hint precedence (T017) ---


def test_name_hint_wins_over_visual(batch, fixtures_dir: Path, tmp_path: Path):
    """Copy fronts_then_backs content under an interleaved name → name hint wins."""
    src = fixtures_dir / "sample_fronts_then_backs.pdf"
    hinted = tmp_path / "demo_interleaved.pdf"
    hinted.write_bytes(src.read_bytes())
    order, reason = batch.detect_order_smart(str(hinted), even_default="fronts_then_backs")
    assert order == "interleaved"
    assert reason.startswith("name-hint:")


# --- open-fallback (T019) ---


def test_open_fallback_unreadable(batch, tmp_path: Path):
    bad = tmp_path / "corrupt.pdf"
    bad.write_bytes(b"not a pdf")
    order, reason = batch.detect_order_smart(str(bad), even_default="fronts_then_backs")
    assert order == "fronts_then_backs"
    assert reason == "open-fallback"


def test_open_fallback_missing(batch, tmp_path: Path):
    missing = tmp_path / "nope.pdf"
    order, reason = batch.detect_order_smart(str(missing), even_default="interleaved")
    assert order == "interleaved"
    assert reason == "open-fallback"


# --- sampling (T022) ---


def test_sample_page_indices_small_n(batch):
    assert batch.sample_page_indices(10) == list(range(10))
    assert batch.sample_page_indices(40) == list(range(40))


def test_sample_page_indices_large_n(batch):
    idxs = batch.sample_page_indices(100, max_samples=40)
    assert len(idxs) <= 40
    assert idxs[0] == 0
    assert idxs[-1] == 99
    assert idxs == sorted(idxs)
    # Both odd and second-half candidacy remain representable
    assert any(i % 2 == 1 for i in idxs)
    assert any(i >= 50 for i in idxs)


def test_fixture_visual_classifications(batch, fixtures_dir: Path, tmp_path: Path):
    """Use neutral filenames so name-hints do not short-circuit content rules."""

    def _neutral(src_name: str, dest_name: str) -> Path:
        dest = tmp_path / dest_name
        dest.write_bytes((fixtures_dir / src_name).read_bytes())
        return dest

    order, reason = batch.detect_order_smart(
        str(_neutral("sample_interleaved.pdf", "cards_a.pdf")),
        even_default="fronts_then_backs",
    )
    assert order == "interleaved"
    assert reason.startswith("visual:")

    order, reason = batch.detect_order_smart(
        str(_neutral("sample_fronts_then_backs.pdf", "cards_b.pdf")),
        even_default="interleaved",
    )
    assert order == "fronts_then_backs"
    assert reason.startswith("visual:")

    order, reason = batch.detect_order_smart(
        str(_neutral("sample_single.pdf", "one_page.pdf")),
        even_default="interleaved",
    )
    assert order == "single_sided"
    assert reason == "pages:1"

    order, reason = batch.detect_order_smart(
        str(_neutral("sample_odd.pdf", "three_pages.pdf")),
        even_default="interleaved",
    )
    assert order == "last_back"
    assert reason.startswith("pages:odd")

    order, reason = batch.detect_order_smart(
        str(_neutral("sample_ambiguous_even.pdf", "mixed_even.pdf")),
        even_default="fronts_then_backs",
    )
    assert order == "fronts_then_backs"
    assert reason.startswith("visual:tie")
