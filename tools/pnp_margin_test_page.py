#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnp_margin_test_page.py

Generate a margin test page (2 identical portrait pages, print double-sided).

Each edge carries three millimetre rulers that start exactly at the paper edge
(0 mm). The first visible tick on each ruler is how many millimetres that edge
does not print. Two reference lines (150 mm and 200 mm) check that nothing is
scaled. Use it to find the print-dialog scaling mode that prints at 100 % with
no offset before calibrating: unequal losses on opposite edges mean the page
is shifted, wrong reference lengths mean it is scaled.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import calibration as cal  # noqa: E402

RULER_MM = 20  # ruler length from the edge


def ruler(
    c: canvas.Canvas,
    origin: Tuple[float, float],
    inward: Tuple[float, float],
    along: Tuple[float, float],
) -> None:
    """Ruler perpendicular to an edge, starting at `origin` (on the edge)."""
    ox, oy = origin
    dx, dy = inward
    ax, ay = along
    # grey band to see where ink starts
    half = 1.2 * mm
    c.setFillGray(0.8)
    path = c.beginPath()
    path.moveTo(ox - ax * half, oy - ay * half)
    path.lineTo(ox + ax * half, oy + ay * half)
    path.lineTo(ox + ax * half + dx * RULER_MM * mm, oy + ay * half + dy * RULER_MM * mm)
    path.lineTo(ox - ax * half + dx * RULER_MM * mm, oy - ay * half + dy * RULER_MM * mm)
    path.close()
    c.drawPath(path, stroke=0, fill=1)
    c.setFillGray(0)
    c.setLineWidth(0.25)
    for i in range(RULER_MM + 1):
        tick = 2.6 if i % 5 == 0 else 2.0 if i % 2 == 0 else 1.4
        x, y = ox + dx * i * mm, oy + dy * i * mm
        c.line(x, y, x + ax * tick * mm, y + ay * tick * mm)
        if i % 2 == 0 and i:
            # labels on two staggered rows so they never overlap
            off = 6.0 if i % 4 == 0 else 3.6
            c.setFont("Helvetica-Bold" if i % 10 == 0 else "Helvetica", 5.5)
            c.drawCentredString(x + ax * off * mm, y + ay * off * mm - 1.9, str(i))


def draw_page(c: canvas.Canvas, w_mm: float, h_mm: float, side: int) -> None:
    pw, ph = w_mm * mm, h_mm * mm
    for x in (30, w_mm / 2, w_mm - 30):
        ruler(c, (x * mm, ph), (0, -1), (1, 0))  # top
        ruler(c, (x * mm, 0), (0, 1), (1, 0))  # bottom
    for y in (30, h_mm / 2, h_mm - 30):
        ruler(c, (0, y * mm), (1, 0), (0, 1))  # left
        ruler(c, (pw, y * mm), (-1, 0), (0, 1))  # right

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(pw / 2, ph - 32 * mm, "TOP")
    # text block left of the vertical reference line (it reaches high on Letter)
    tx = pw / 2 - 30 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(tx, ph - 45 * mm, f"MARGIN TEST - SIDE {side}")
    c.setFont("Helvetica", 8)
    for i, text in enumerate(
        [
            "Print double-sided at 100 % (no scaling).",
            "On each ruler, write down the first visible tick:",
            "it is how many mm that edge does not print",
            "(0 = prints up to the edge).",
            "Unequal losses on opposite edges: the page",
            "is shifted by the print dialog.",
            "Check with a ruler that the reference lines",
            "measure 150 mm and 200 mm.",
        ]
    ):
        c.drawCentredString(tx, ph - (53 + i * 4) * mm, text)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(26 * mm, ph / 2 + 20 * mm, "LEFT")
    c.drawRightString(pw - 26 * mm, ph / 2 + 20 * mm, "RIGHT")

    c.setLineWidth(0.4)
    c.setFont("Helvetica", 8)
    y = 95 * mm
    x0 = (pw - 150 * mm) / 2
    c.line(x0, y, x0 + 150 * mm, y)
    for x in (x0, x0 + 150 * mm):
        c.line(x, y - 3 * mm, x, y + 3 * mm)
    c.drawCentredString(pw / 2, y + 2 * mm, "must measure 150 mm")
    x = pw / 2 + 40 * mm
    y0 = 25 * mm
    c.line(x, y0, x, y0 + 200 * mm)
    for yy in (y0, y0 + 200 * mm):
        c.line(x - 3 * mm, yy, x + 3 * mm, yy)
    c.saveState()
    c.translate(x - 2 * mm, y0 + 140 * mm)
    c.rotate(90)
    c.drawCentredString(0, 0, "must measure 200 mm")
    c.restoreState()
    c.showPage()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a printer margin / scaling test page (2 pages).")
    p.add_argument("--paper", choices=sorted(cal.PAPER_SIZES_MM), default="a4")
    p.add_argument("--output", help="Output PDF (default: calibration_margins_<paper>.pdf).")
    p.add_argument("--force", action="store_true", help="Overwrite the output file if it exists.")
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    out = Path(args.output or f"calibration_margins_{args.paper}.pdf")
    if out.exists() and not args.force:
        print(f"Error: {out} already exists. Use --force to overwrite it.", file=sys.stderr)
        return 1
    w_mm, h_mm = cal.page_size_mm(args.paper, "portrait")
    try:
        c = canvas.Canvas(str(out), pagesize=(w_mm * mm, h_mm * mm))
        c.setTitle(f"Margin test ({args.paper})")
        draw_page(c, w_mm, h_mm, 1)
        draw_page(c, w_mm, h_mm, 2)
        c.save()
    except OSError as exc:
        print(f"Error: cannot write {out}: {exc}", file=sys.stderr)
        return 1
    print(f"Margin test page generated: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
