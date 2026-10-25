"""Integration/CLI: back scale correction in vector and raster paths."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _probe(path: Path) -> None:
    """Two A4 pages with a small square 200 pt right of the page centre."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for _ in range(2):
        c.rect(A4[0] / 2 + 200 - 5, A4[1] / 2 - 5, 10, 10, stroke=0, fill=1)
        c.showPage()
    c.save()


def _square_center_x(path: Path, page: int) -> float:
    """X (pt) of the square's centre, rendering only a strip around it."""
    cx, cy = A4[0] / 2, A4[1] / 2  # the square sits on the horizontal centre line
    clip = fitz.Rect(cx, cy - 20, A4[0], cy + 20)
    with fitz.open(str(path)) as doc:
        pix = doc[page].get_pixmap(dpi=144, colorspace=fitz.csGRAY, clip=clip)
    xs = [
        x
        for y in range(pix.height)
        for x in range(pix.width)
        if pix.samples[y * pix.stride + x] < 128
    ]
    return cx + sum(xs) / len(xs) / 2  # pixels at 144 dpi → points


@pytest.mark.parametrize("mode", ["vector", "raster"])
def test_scalex_shrinks_back_about_page_center(run_main_cli, tmp_path: Path, mode):
    src = tmp_path / "probe.pdf"
    out = tmp_path / f"out_{mode}.pdf"
    _probe(src)
    proc = run_main_cli(
        ["--input", str(src), "--output", str(out), "--mode", mode,
         "--order", "interleaved", "--flip-mode", "long", "--scalex", "0.9"]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "scale=(0.9, 1.0)" in proc.stdout
    front = _square_center_x(out, 0)
    back = _square_center_x(out, 1)
    assert front == pytest.approx(A4[0] / 2 + 200, abs=1.0)
    assert back == pytest.approx(A4[0] / 2 + 180, abs=1.0)
