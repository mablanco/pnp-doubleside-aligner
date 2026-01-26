#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnp_calibration_solver.py

Helper script to compute a printer calibration profile from measured
front/back misalignment values.
"""

import json
import math
import os

# Fill in your measured offsets (dx, dy in millimeters)
# Back page relative to the front page
measures = {
    "top_left":     {"dx": 0.0, "dy": 2.0},
    "top_right":    {"dx": 0.0, "dy": 0.2},
    "bottom_left":  {"dx": 0.8, "dy": 2.1},
    "bottom_right": {"dx": 1.0, "dy": 0.5},
    "center":       {"dx": 0.5, "dy": 1.5}  # optional
}

# Paper configuration
paper_width_mm  = 297.0
paper_height_mm = 210.0   # A4 landscape
flip_mode       = "long"  # "long" or "short"

# Average shifts
vals = list(measures.values())
avg_dx = sum(v["dx"] for v in vals) / len(vals)
avg_dy = sum(v["dy"] for v in vals) / len(vals)

# Estimate skew (variation of dx from top to bottom)
dx_top    = measures["top_right"]["dx"] - measures["top_left"]["dx"]
dx_bottom = measures["bottom_right"]["dx"] - measures["bottom_left"]["dx"]
avg_slope = (dx_bottom - dx_top) / paper_height_mm
skew_angle_deg = math.degrees(math.atan(avg_slope))

profile = {
    "name": "My_Calibrated_Printer",
    "paper": {
        "width_mm": paper_width_mm,
        "height_mm": paper_height_mm,
        "orientation": "landscape"
    },
    "margins": {"x_mm": 0, "y_mm": 0},
    "flip_mode": flip_mode,
    "back_corrections": {
        "extra_rot_deg": round(skew_angle_deg, 3),
        "shift_x_mm": round(avg_dx, 2),
        "shift_y_mm": round(avg_dy, 2)
    }
}

os.makedirs("profiles", exist_ok=True)
out_path = "profiles/my_calibrated_printer.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(profile, f, indent=2)

print(f"Profile generated: {out_path}")
print(f"Estimated skew angle: {skew_angle_deg:.3f} degrees")
print(f"Average shift: X={avg_dx:.2f} mm, Y={avg_dy:.2f} mm")
