#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnp_calibration_sheet_duplex.py

Generate a direct-read duplex calibration sheet (2 pages: front and back).

The front has thick crosses at the four corners (TL, TR, BL, BR) and at the
centre (C). The back has, next to each cross, a horizontal (dx) and a vertical
(dy) scale, mirrored so that they read correctly when the printed sheet is
held against a light source and viewed FROM THE FRONT. The number crossed by
the thick line is directly the offset of the back (mm, dx > 0 right, dy > 0
down). Feed the four corner readings to tools/pnp_calibration_solver.py.

Backs are mirrored in X like typical PnP files: print with long-edge flip in
portrait and short-edge flip in landscape. Do NOT run the aligner on this
sheet for the first calibration.
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

RANGE_MM = 6  # scale extent on each side of zero
GAP_MM = 8.0  # cross centre → scale axis (> RANGE_MM so scales never overlap)
ARM_MM = 16  # half length of the cross arms (reaches both scales)
LABELS = {"top_left": "TL", "top_right": "TR", "bottom_left": "BL", "bottom_right": "BR", "center": "C"}
FLIP_HINT = {"portrait": "long edge", "landscape": "short edge"}


class Sheet:
    def __init__(self, paper: str, orientation: str):
        self.paper = paper
        self.orientation = orientation
        self.w_mm, self.h_mm = cal.page_size_mm(paper, orientation)
        self.pw, self.ph = self.w_mm * mm, self.h_mm * mm
        self.targets = cal.targets(self.w_mm, self.h_mm)

    def p(self, x_mm: float, y_mm: float) -> Tuple[float, float]:
        """Front-view mm (Y down) → ReportLab points (Y up)."""
        return x_mm * mm, self.ph - y_mm * mm


def draw_front(c: canvas.Canvas, s: Sheet) -> None:
    c.setLineWidth(1.0)
    for key, (x, y) in s.targets.items():
        c.line(*s.p(x - ARM_MM, y), *s.p(x + ARM_MM, y))
        c.line(*s.p(x, y - ARM_MM), *s.p(x, y + ARM_MM))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(*s.p(x - ARM_MM, y - 3), LABELS[key])

    flip = FLIP_HINT[s.orientation]
    top = 45 if s.orientation == "landscape" else 60  # keep clear of the centre cross
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(
        s.pw / 2, s.ph - top * mm,
        f"DUPLEX CALIBRATION - {s.paper.upper()} {s.orientation.upper()} - FLIP ON {flip.upper()}",
    )
    lines = [
        f"Print double-sided (flip on {flip}) at 100 % (no scaling, no offset). Do not run the aligner on it.",
        "Hold against a light source and look FROM THIS SIDE: two scales of the other side appear by each cross.",
        "If the word TOP of the other side reads upside down, the duplex flip mode is wrong.",
        "dx = number on the horizontal scale crossed by the thick vertical line.",
        "dy = number on the vertical scale crossed by the thick horizontal line.",
        "Write down dx and dy at TL, TR, BL, BR (and C as a check). Halves are fine: 0.5, -1.5...",
    ]
    c.setFont("Helvetica", 9)
    for i, text in enumerate(lines):
        c.drawCentredString(s.pw / 2, s.ph - (top + 10 + i * 5.5) * mm, text)
    c.showPage()


def draw_back(c: canvas.Canvas, s: Sheet) -> None:
    c.saveState()
    # Mirror in X: seen through the paper from the front, everything reads
    # correctly and sits on top of the front targets.
    c.transform(-1, 0, 0, 1, s.pw, 0)
    c.setLineWidth(0.3)
    for key, (x, y) in s.targets.items():
        # dx scale below the cross, ticks pointing at it
        ya = y + GAP_MM
        c.line(*s.p(x - RANGE_MM, ya), *s.p(x + RANGE_MM, ya))
        for k in range(-2 * RANGE_MM, 2 * RANGE_MM + 1):
            u = k / 2
            c.line(*s.p(x + u, ya), *s.p(x + u, ya - (2.5 if k % 2 == 0 else 1.4)))
            if k % 4 == 0:
                # labelled -u: the reading is the displacement of the back
                c.setFont("Helvetica-Bold" if k == 0 else "Helvetica", 4.5)
                c.drawCentredString(*s.p(x + u, ya + 2.2), f"{-u + 0.0:g}")
        # dy scale right of the cross, ticks pointing at it
        xa = x + GAP_MM
        c.line(*s.p(xa, y - RANGE_MM), *s.p(xa, y + RANGE_MM))
        for k in range(-2 * RANGE_MM, 2 * RANGE_MM + 1):
            v = k / 2
            c.line(*s.p(xa, y + v), *s.p(xa - (2.5 if k % 2 == 0 else 1.4), y + v))
            if k % 4 == 0:
                c.setFont("Helvetica-Bold" if k == 0 else "Helvetica", 4.5)
                lx, ly = s.p(xa + 1.2, y + v)
                c.drawString(lx, ly - 1.5, f"{-v + 0.0:g}")
        c.setFont("Helvetica", 6)
        c.drawString(*s.p(x - RANGE_MM, ya + 5.5), f"{LABELS[key]} dx")
        c.drawString(*s.p(xa + 1.2, y - RANGE_MM - 2), f"{LABELS[key]} dy")
    # orientation witness: must read upright through the paper
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(*s.p(s.w_mm / 2, 14), "TOP (if this reads upside down, change the duplex flip mode)")
    c.restoreState()
    c.setFont("Helvetica", 7)
    c.drawCentredString(s.pw / 2, 12 * mm, "Back side: read it against a light source from the front side.")
    c.showPage()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a direct-read duplex calibration sheet (2 pages).")
    p.add_argument("--orientation", choices=cal.ORIENTATIONS, default="portrait")
    p.add_argument("--paper", choices=sorted(cal.PAPER_SIZES_MM), default="a4")
    p.add_argument(
        "--output",
        help="Output PDF (default: calibration_sheet_<orientation>_<paper>.pdf).",
    )
    p.add_argument("--force", action="store_true", help="Overwrite the output file if it exists.")
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    out = Path(args.output or f"calibration_sheet_{args.orientation}_{args.paper}.pdf")
    if out.exists() and not args.force:
        print(f"Error: {out} already exists. Use --force to overwrite it.", file=sys.stderr)
        return 1
    sheet = Sheet(args.paper, args.orientation)
    try:
        c = canvas.Canvas(str(out), pagesize=(sheet.pw, sheet.ph))
        c.setTitle(f"Duplex calibration sheet ({args.paper} {args.orientation})")
        draw_front(c, sheet)
        draw_back(c, sheet)
        c.save()
    except OSError as exc:
        print(f"Error: cannot write {out}: {exc}", file=sys.stderr)
        return 1
    print(f"Calibration sheet generated: {out}")
    print(f"Print it double-sided, flip on the {FLIP_HINT[args.orientation]}, at 100 %.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
