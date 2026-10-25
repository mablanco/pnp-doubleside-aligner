#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnp_calibration_solver.py

Compute a printer calibration profile from the readings of the direct-read
calibration sheet (tools/pnp_calibration_sheet_duplex.py).

Each reading is DX DY in millimetres, as read on the sheet from the FRONT
side: the offset of the back (dx > 0: right, dy > 0: down). The solver fits a
rotation + shift by least squares and writes the profile corrections; with
--fit-scale it also fits an X/Y scale difference (paper shrinking between the
two passes of a manual duplex, for example) and writes scale_x / scale_y.

Verification / refinement: run the aligner on the calibration sheet with the
profile, print it again, read the residual offsets and pass them with
--refine PROFILE to add the residual correction to that profile.

Example:

    python tools/pnp_calibration_solver.py \\
        --top-left 0.5 0.5 --top-right 1 0 \\
        --bottom-left 1 0.5 --bottom-right 1.5 0 \\
        --center 1 0 \\
        --output profiles/my_printer_A4_portrait.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import calibration as cal  # noqa: E402
from profiles import load_profile  # noqa: E402

DEFAULT_OUTPUT = "profiles/my_calibrated_printer.json"
RESIDUAL_WARNING_MM = 0.75
POINTS = ("top_left", "top_right", "bottom_left", "bottom_right", "center")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Compute a printer calibration profile from the direct-read calibration "
            "sheet. Readings are DX DY in mm, read from the FRONT side "
            "(dx > 0: back is to the right; dy > 0: back is lower)."
        )
    )
    point = dict(nargs=2, type=float, metavar=("DX", "DY"))
    p.add_argument("--top-left", required=True, help="Reading at TL.", **point)
    p.add_argument("--top-right", required=True, help="Reading at TR.", **point)
    p.add_argument("--bottom-left", required=True, help="Reading at BL.", **point)
    p.add_argument("--bottom-right", required=True, help="Reading at BR.", **point)
    p.add_argument("--center", help="Reading at C (optional, improves the fit).", **point)
    p.add_argument("--orientation", choices=cal.ORIENTATIONS, default="portrait",
                   help="Orientation of the sheet that was read (default: portrait).")
    p.add_argument("--paper", choices=sorted(cal.PAPER_SIZES_MM), default="a4",
                   help="Paper of the sheet that was read (default: a4).")
    p.add_argument("--fit-scale", action="store_true",
                   help="Also fit an X/Y scale difference between back and front (e.g. paper "
                        "shrinking between the two passes) and write scale_x/scale_y.")
    p.add_argument("--refine", metavar="PROFILE",
                   help="Treat the readings as residuals of a verification print and "
                        "add their correction to this existing profile.")
    p.add_argument("--name", help="Profile name (default: My_Calibrated_Printer, or the refined profile's).")
    p.add_argument("--output", default=DEFAULT_OUTPUT,
                   help=f"Profile JSON path (default: {DEFAULT_OUTPUT}). Use '-' for stdout.")
    p.add_argument("--force", action="store_true", help="Overwrite the output file if it exists.")
    return p.parse_args(argv)


DECIMALS = {"extra_rot_deg": 3, "shift_x_mm": 2, "shift_y_mm": 2, "scale_x": 4, "scale_y": 4}


def _rounded(bc: Dict[str, float]) -> Dict[str, float]:
    # + 0.0 turns -0.0 into 0.0 in the JSON output
    return {k: round(v, DECIMALS[k]) + 0.0 for k, v in bc.items()}


def _append_note(notes: Any, note: str) -> Any:
    if isinstance(notes, list):
        return [*notes, note]
    if isinstance(notes, str) and notes:
        return f"{notes} | {note}"
    return note


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    w_mm, h_mm = cal.page_size_mm(args.paper, args.orientation)
    readings: Dict[str, Tuple[float, float]] = {}
    for key in POINTS:
        val = getattr(args, key)
        if val is not None:
            readings[key] = (val[0], val[1])
    fit = cal.fit_readings(readings, w_mm, h_mm, fit_scale=args.fit_scale)
    delta = cal.to_back_corrections(fit)
    read_txt = ", ".join(f"{k} {v[0]:g}/{v[1]:g}" for k, v in readings.items())

    if args.refine:
        try:
            base = load_profile(args.refine)
            with open(args.refine, "r", encoding="utf-8") as f:
                raw: Dict[str, Any] = json.load(f)
        except (OSError, ValueError) as exc:
            print(f"Error: cannot use base profile {args.refine}: {exc}", file=sys.stderr)
            return 1
        profile = dict(raw)
        base_bc = dict(base["back_corrections"])
        raw_bc = raw.get("back_corrections") or {}
        for key in ("scale_x", "scale_y"):
            # load_profile fills scales with 1.0; keep them only if really used
            if key not in raw_bc:
                base_bc.pop(key, None)
        profile["back_corrections"] = _rounded(cal.refine_corrections(base_bc, delta))
        if args.name:
            profile["name"] = args.name
        profile["_notes"] = _append_note(
            raw.get("_notes"),
            f"refined with residual readings ({args.paper} {args.orientation}): {read_txt}",
        )
    else:
        profile = {
            "name": args.name or "My_Calibrated_Printer",
            "paper": {"width_mm": w_mm, "height_mm": h_mm, "orientation": args.orientation},
            "margins": {"x_mm": 0, "y_mm": 0},
            # The sheet (like typical PnP files) has backs mirrored in X: they
            # must not be rotated 180°, whatever edge the print dialog flips on.
            "flip_mode": "long",
            "back_corrections": _rounded(delta),
            "_notes": f"Direct-read calibration ({args.paper} {args.orientation}): {read_txt}",
        }

    text = json.dumps(profile, indent=2, ensure_ascii=False)
    if args.output == "-":
        print(text)
    else:
        out = Path(args.output)
        if out.exists() and not args.force:
            print(f"Error: {out} already exists. Use --force to overwrite it or choose another --output.",
                  file=sys.stderr)
            return 1
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"Error: cannot write {out}: {exc}", file=sys.stderr)
            return 1
        print(f"Profile generated: {out}")

    # With --output - stdout carries only the JSON, so the summary goes to stderr
    info = sys.stderr if args.output == "-" else sys.stdout
    bc = profile["back_corrections"]
    print(f"Measured (front view): rotation {fit.rot_deg:+.3f} deg, "
          f"shift X {fit.tx_mm:+.2f} mm, Y {fit.ty_mm:+.2f} mm", file=info)
    if fit.scale_fitted:
        print(f"Measured scale of the back (front view): X {fit.scale_x:.4f}, Y {fit.scale_y:.4f}", file=info)
    print("Profile corrections: " + ", ".join(f"{k}={v}" for k, v in bc.items()), file=info)
    print("Fit residuals (mm): " + ", ".join(f"{k} {v:.2f}" for k, v in fit.residuals_mm.items()), file=info)
    worst = max(fit.residuals_mm, key=fit.residuals_mm.get)
    if fit.residuals_mm[worst] > RESIDUAL_WARNING_MM:
        print(f"Warning: the reading at {worst} does not fit the others "
              f"({fit.residuals_mm[worst]:.2f} mm off). Check it on the sheet.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
