"""Regression tests for the security-hardening pass (profiles, CLI, tools/)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import fitz
import pytest

import pnp_double_with_profile_pdf as main_cli
from profiles import load_profile

TOOLS = Path(__file__).resolve().parents[2] / "tools"


def _load_tool(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ----------------------------- profiles / main CLI -----------------------------


@pytest.mark.parametrize("key", ["extra_rot_deg", "shift_x_mm", "shift_y_mm"])
@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_load_profile_rejects_non_finite_corrections(tmp_path: Path, key: str, value: str):
    path = tmp_path / "p.json"
    path.write_text('{"back_corrections": {"%s": %s}}' % (key, value), encoding="utf-8")
    with pytest.raises(ValueError, match="finite"):
        load_profile(str(path))


@pytest.mark.parametrize(
    "flag,value",
    [("--rot", "nan"), ("--shiftx", "inf"), ("--shifty", "-inf"), ("--dpi", "0"), ("--dpi", "100000")],
)
def test_cli_rejects_non_finite_corrections_and_out_of_range_dpi(
    run_main_cli, sample_interleaved: Path, tmp_output: Path, flag: str, value: str
):
    out = tmp_output / "out.pdf"
    proc = run_main_cli(["--input", str(sample_interleaved), "--output", str(out), flag, value])
    assert proc.returncode == 2
    assert flag in proc.stderr
    assert not out.exists()


def test_raster_same_file_failure_leaves_no_temp(tmp_path: Path, sample_interleaved: Path, monkeypatch):
    pdf = tmp_path / "deck.pdf"
    pdf.write_bytes(sample_interleaved.read_bytes())
    original = pdf.read_bytes()

    def boom(*_a, **_k):
        raise RuntimeError("render failed")

    monkeypatch.setattr(main_cli, "render_page_image", boom)
    with pytest.raises(RuntimeError):
        main_cli.raster_fallback(str(pdf), str(pdf), load_profile(None), "interleaved", "warn", dpi=72)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["deck.pdf"]
    assert pdf.read_bytes() == original


# --------------------------------- batch tool ----------------------------------


def test_batch_ignores_decoy_worker_in_cwd(run_batch, sample_interleaved: Path, tmp_path: Path):
    """A same-named script in the current directory must never be executed."""
    cwd = tmp_path / "downloaded"
    in_dir = cwd / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir(parents=True)
    (in_dir / "deck.pdf").write_bytes(sample_interleaved.read_bytes())
    marker = tmp_path / "decoy-ran"
    (cwd / "pnp_double_with_profile_pdf.py").write_text(
        f"open({str(marker)!r}, 'w').close()\n", encoding="utf-8"
    )

    proc = run_batch(["--input-dir", str(in_dir), "--output-dir", str(out_dir)], cwd=cwd)

    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert not marker.exists()
    assert len(list(out_dir.glob("*.pdf"))) == 1


def test_batch_continues_after_unreadable_pdf(run_batch, sample_interleaved: Path, tmp_path: Path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    (in_dir / "a_broken.pdf").write_bytes(b"not a pdf at all")
    (in_dir / "b_good.pdf").write_bytes(sample_interleaved.read_bytes())

    proc = run_batch(["--input-dir", str(in_dir), "--output-dir", str(out_dir)])

    assert proc.returncode == 1
    assert "Cannot open a_broken.pdf" in proc.stderr
    assert [p.name for p in out_dir.glob("*.pdf")] == ["b_good_interleaved_aligned.pdf"]


def test_batch_input_dir_with_glob_metacharacters(run_batch, sample_interleaved: Path, tmp_path: Path):
    in_dir = tmp_path / "decks [2026]"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    (in_dir / "deck.pdf").write_bytes(sample_interleaved.read_bytes())

    proc = run_batch(["--input-dir", str(in_dir), "--output-dir", str(out_dir)])

    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert len(list(out_dir.glob("*.pdf"))) == 1


def test_page_fingerprint_caps_render_size(monkeypatch):
    batch = _load_tool("pnp_batch_align")
    doc = fitz.open()
    doc.new_page(width=14400, height=7200)  # maximum PDF page size

    sizes = []
    real = fitz.Page.get_pixmap

    def spy(self, *args, **kwargs):
        pix = real(self, *args, **kwargs)
        sizes.append((pix.width, pix.height))
        return pix

    monkeypatch.setattr(fitz.Page, "get_pixmap", spy)
    vec = batch.page_fingerprint(doc, 0)

    assert len(vec) == 32 * 32
    assert max(sizes[0]) <= batch.MAX_FINGERPRINT_PX


# ---------------------------------- image tool ----------------------------------


@pytest.mark.parametrize(
    "profile",
    [
        {"back_corrections": {"extra_rot_deg": float("nan")}},
        {"back_corrections": {"shift_x_mm": float("inf")}},
        {"paper": {"width_mm": 0}},
        {"paper": {"height_mm": -210}},
        {"margins": {"x_mm": -1}},
        {"paper": "A4"},
    ],
)
def test_img_tool_profile_validation(tmp_path: Path, profile: dict):
    img_tool = _load_tool("pnp_double_with_profile_img")
    path = tmp_path / "p.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(ValueError):
        img_tool.load_profile(str(path))


def test_img_tool_profile_defaults_unchanged(tmp_path: Path):
    img_tool = _load_tool("pnp_double_with_profile_img")
    path = tmp_path / "p.json"
    path.write_text("{}", encoding="utf-8")
    prof = img_tool.load_profile(str(path))
    assert (prof["paper_w"], prof["paper_h"], prof["orientation"]) == (297.0, 210.0, "landscape")
