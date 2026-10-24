"""Pure math for direct-read duplex calibration (no I/O).

Readings come from the calibration sheet, seen from the FRONT through the
paper: at each target, (dx, dy) is how far the back is from the front, in mm,
with dx > 0 to the right and dy > 0 downwards.

The printer error is modelled as a rigid motion about the page centre c:

    d(P) = phi * J(P - c) + t,   J(x, y) = (-y, x)

where phi (radians) is a clockwise rotation for Y-down coordinates and t a
shift. The aligner corrects in BACK-page coordinates, which are mirrored in X
with respect to the front view, so the X shift and the rotation keep their
sign as corrections while the Y shift is negated (see to_back_corrections).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Mapping, Tuple

Point = Tuple[float, float]

PAPER_SIZES_MM: Dict[str, Point] = {
    "a4": (210.0, 297.0),
    "letter": (215.9, 279.4),
}
ORIENTATIONS = ("portrait", "landscape")
TARGET_INSET_MM = 25.0
CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")


@dataclass(frozen=True)
class Fit:
    """Rigid motion fitted to the readings (front view, Y down)."""

    rot_deg: float  # clockwise > 0
    tx_mm: float  # right > 0
    ty_mm: float  # down > 0
    residuals_mm: Dict[str, float]  # per reading, distance to the model


def page_size_mm(paper: str, orientation: str) -> Point:
    """Page (width, height) in mm for a paper name and orientation."""
    if paper not in PAPER_SIZES_MM:
        raise ValueError(f"unknown paper {paper!r} (expected one of {sorted(PAPER_SIZES_MM)})")
    if orientation not in ORIENTATIONS:
        raise ValueError(f"unknown orientation {orientation!r} (expected portrait or landscape)")
    short, long_ = PAPER_SIZES_MM[paper]
    return (short, long_) if orientation == "portrait" else (long_, short)


def targets(width_mm: float, height_mm: float, inset_mm: float = TARGET_INSET_MM) -> Dict[str, Point]:
    """Target positions (front view, mm, Y down): four corners and centre."""
    return {
        "top_left": (inset_mm, inset_mm),
        "top_right": (width_mm - inset_mm, inset_mm),
        "bottom_left": (inset_mm, height_mm - inset_mm),
        "bottom_right": (width_mm - inset_mm, height_mm - inset_mm),
        "center": (width_mm / 2, height_mm / 2),
    }


def predicted_offset(
    rot_deg: float, tx_mm: float, ty_mm: float, point: Point, width_mm: float, height_mm: float
) -> Point:
    """Reading predicted by the small-angle model at a point."""
    phi = math.radians(rot_deg)
    vx, vy = point[0] - width_mm / 2, point[1] - height_mm / 2
    return (-phi * vy + tx_mm, phi * vx + ty_mm)


def fit_readings(readings: Mapping[str, Point], width_mm: float, height_mm: float) -> Fit:
    """Least-squares rotation + shift for the given readings (corners required)."""
    missing = [c for c in CORNERS if c not in readings]
    if missing:
        raise ValueError(f"missing readings: {', '.join(missing)}")
    pts = targets(width_mm, height_mm)
    unknown = [k for k in readings if k not in pts]
    if unknown:
        raise ValueError(f"unknown reading names: {', '.join(unknown)}")

    cx, cy = width_mm / 2, height_mm / 2
    n = len(readings)
    # centre the problem so rotation and shift decouple
    mvx = sum(pts[k][0] - cx for k in readings) / n
    mvy = sum(pts[k][1] - cy for k in readings) / n
    mdx = sum(d[0] for d in readings.values()) / n
    mdy = sum(d[1] for d in readings.values()) / n
    num = den = 0.0
    for k, (dx, dy) in readings.items():
        vx, vy = pts[k][0] - cx - mvx, pts[k][1] - cy - mvy
        num += -vy * (dx - mdx) + vx * (dy - mdy)
        den += vx * vx + vy * vy
    phi = num / den
    tx = mdx + phi * mvy
    ty = mdy - phi * mvx
    rot_deg = math.degrees(phi)

    residuals = {}
    for k, (dx, dy) in readings.items():
        px, py = predicted_offset(rot_deg, tx, ty, pts[k], width_mm, height_mm)
        residuals[k] = math.hypot(dx - px, dy - py)
    return Fit(rot_deg=rot_deg, tx_mm=tx, ty_mm=ty, residuals_mm=residuals)


def to_back_corrections(fit: Fit) -> Dict[str, float]:
    """Profile back_corrections that cancel the fitted error.

    In the front view the printer maps back content q to R(q - c) + c + t and
    the aligner (rotation, then shift) to Ra(q - c) + c + s. Cancelling both
    needs Ra = R^-1 and s = -R^-1 t: the printer also rotates the correcting
    shift. The back page is mirrored in X with respect to the front view, so
    the rotation keeps its sign as a back-page correction and the X component
    of the shift is negated.
    """
    phi = math.radians(fit.rot_deg)
    # s = -R(-phi) t, front view (R clockwise for Y down)
    sx = -(fit.tx_mm * math.cos(phi) + fit.ty_mm * math.sin(phi))
    sy = -(-fit.tx_mm * math.sin(phi) + fit.ty_mm * math.cos(phi))
    return {
        "extra_rot_deg": fit.rot_deg,
        "shift_x_mm": -sx,
        "shift_y_mm": sy,
    }


def refine_corrections(base: Mapping[str, float], delta: Mapping[str, float]) -> Dict[str, float]:
    """Add the correction computed from a verification print to a profile's corrections."""
    return {k: float(base.get(k, 0.0)) + float(delta.get(k, 0.0)) for k in ("extra_rot_deg", "shift_x_mm", "shift_y_mm")}
