#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnp_calibration_solver.py

Helper script to compute a printer calibration profile from measured
front/back misalignment values.

Measurements are offsets (dx, dy) in millimeters of the back page relative
to the front page, taken at the four corner reference marks (and optionally
the center mark) of the calibration sheet.

Example:

    python tools/pnp_calibration_solver.py \\
        --top-left 0.0 2.0 --top-right 0.0 0.2 \\
        --bottom-left 0.8 2.1 --bottom-right 1.0 0.5 \\
        --center 0.5 1.5 \\
        --output profiles/my_printer_A4_200g.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

DEFAULT_OUTPUT = "profiles/my_calibrated_printer.json"

Measures = Dict[str, Dict[str, float]]


def solve(measures: Measures, paper_height_mm: float) -> Dict[str, float]:
    """Estimate skew angle and average shift from measured offsets."""
    vals = list(measures.values())
    avg_dx = sum(v["dx"] for v in vals) / len(vals)
    avg_dy = sum(v["dy"] for v in vals) / len(vals)

    # Estimate skew (variation of dx from top to bottom)
    dx_top = measures["top_right"]["dx"] - measures["top_left"]["dx"]
    dx_bottom = measures["bottom_right"]["dx"] - measures["bottom_left"]["dx"]
    avg_slope = (dx_bottom - dx_top) / paper_height_mm
    skew_angle_deg = math.degrees(math.atan(avg_slope))

    return {"rot_deg": skew_angle_deg, "shift_x_mm": avg_dx, "shift_y_mm": avg_dy}


def build_profile(
    solution: Dict[str, float],
    *,
    name: str,
    paper_width_mm: float,
    paper_height_mm: float,
    orientation: str,
    flip_mode: str,
) -> dict:
    return {
        "name": name,
        "paper": {
            "width_mm": paper_width_mm,
            "height_mm": paper_height_mm,
            "orientation": orientation,
        },
        "margins": {"x_mm": 0, "y_mm": 0},
        "flip_mode": flip_mode,
        "back_corrections": {
            "extra_rot_deg": round(solution["rot_deg"], 3),
            "shift_x_mm": round(solution["shift_x_mm"], 2),
            "shift_y_mm": round(solution["shift_y_mm"], 2),
        },
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Compute a printer calibration profile from front/back offsets "
            "measured on the duplex calibration sheet. Offsets are dx dy in mm "
            "of the back relative to the front (dx > 0: back is to the right; "
            "dy > 0: back is lower)."
        )
    )
    point = dict(nargs=2, type=float, metavar=("DX", "DY"))
    p.add_argument("--top-left", required=True, help="Offset at top-left mark.", **point)
    p.add_argument("--top-right", required=True, help="Offset at top-right mark.", **point)
    p.add_argument("--bottom-left", required=True, help="Offset at bottom-left mark.", **point)
    p.add_argument("--bottom-right", required=True, help="Offset at bottom-right mark.", **point)
    p.add_argument("--center", help="Offset at center mark (optional).", **point)
    p.add_argument("--paper-width", type=float, default=297.0, help="Paper width in mm (default: 297, A4 landscape).")
    p.add_argument("--paper-height", type=float, default=210.0, help="Paper height in mm (default: 210, A4 landscape).")
    p.add_argument("--orientation", choices=["landscape", "portrait"], default="landscape")
    p.add_argument("--flip-mode", choices=["long", "short"], default="long")
    p.add_argument("--name", default="My_Calibrated_Printer", help="Profile name.")
    p.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Profile JSON path (default: {DEFAULT_OUTPUT}). Use '-' to print to stdout.",
    )
    p.add_argument("--force", action="store_true", help="Overwrite the output file if it exists.")
    args = p.parse_args(argv)
    if args.paper_width <= 0 or args.paper_height <= 0:
        p.error("paper dimensions must be positive")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    measures: Measures = {}
    for key in ("top_left", "top_right", "bottom_left", "bottom_right", "center"):
        val: Optional[List[float]] = getattr(args, key)
        if val is not None:
            measures[key] = {"dx": val[0], "dy": val[1]}

    solution = solve(measures, args.paper_height)
    profile = build_profile(
        solution,
        name=args.name,
        paper_width_mm=args.paper_width,
        paper_height_mm=args.paper_height,
        orientation=args.orientation,
        flip_mode=args.flip_mode,
    )
    text = json.dumps(profile, indent=2)

    if args.output == "-":
        print(text)
    else:
        out_path = Path(args.output)
        if out_path.exists() and not args.force:
            print(
                f"Error: {out_path} already exists. Use --force to overwrite it "
                "or choose another --output.",
                file=sys.stderr,
            )
            return 1
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
        except OSError as exc:
            print(f"Error: cannot write {out_path}: {exc}", file=sys.stderr)
            return 1
        print(f"Profile generated: {out_path}")

    # With --output - stdout carries only the JSON, so the summary goes to stderr
    info = sys.stderr if args.output == "-" else sys.stdout
    print(f"Estimated skew angle: {solution['rot_deg']:.3f} degrees", file=info)
    print(
        f"Average shift: X={solution['shift_x_mm']:.2f} mm, Y={solution['shift_y_mm']:.2f} mm",
        file=info,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
