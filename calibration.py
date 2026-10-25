"""Pure math for direct-read duplex calibration (no I/O).

Readings come from the calibration sheet, seen from the FRONT through the
paper: at each target, (dx, dy) is how far the back is from the front, in mm,
with dx > 0 to the right and dy > 0 downwards.

The printer error is modelled as a rigid motion about the page centre c:

    d(P) = phi * J(P - c) + t,   J(x, y) = (-y, x)

where phi (radians) is a clockwise rotation for Y-down coordinates and t a
shift (optionally also axis scales S, see fit_readings). The aligner
corrects in BACK-page coordinates, which are mirrored in X
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
    scale_x: float = 1.0  # back size / front size along X (front view)
    scale_y: float = 1.0
    scale_fitted: bool = False


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


def fit_readings(
    readings: Mapping[str, Point], width_mm: float, height_mm: float, fit_scale: bool = False
) -> Fit:
    """Least-squares rotation + shift (+ axis scales) for the readings (corners required).

    With fit_scale the back is modelled as R(phi)·S(sx, sy) about the centre
    plus a shift: an affine fit decomposed into rotation and axis scales.
    """
    missing = [c for c in CORNERS if c not in readings]
    if missing:
        raise ValueError(f"missing readings: {', '.join(missing)}")
    pts = targets(width_mm, height_mm)
    unknown = [k for k in readings if k not in pts]
    if unknown:
        raise ValueError(f"unknown reading names: {', '.join(unknown)}")

    if fit_scale:
        return _fit_affine(readings, pts, width_mm / 2, height_mm / 2)

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


def _fit_affine(readings: Mapping[str, Point], pts: Mapping[str, Point], cx: float, cy: float) -> Fit:
    n = len(readings)
    vs = {k: (pts[k][0] - cx, pts[k][1] - cy) for k in readings}
    mvx = sum(v[0] for v in vs.values()) / n
    mvy = sum(v[1] for v in vs.values()) / n
    mdx = sum(d[0] for d in readings.values()) / n
    mdy = sum(d[1] for d in readings.values()) / n
    # A = (sum d v^T)(sum v v^T)^-1 with centred data
    sxx = sxy = syy = 0.0
    dxx = dxy = dyx = dyy = 0.0
    for k, (dx, dy) in readings.items():
        vx, vy = vs[k][0] - mvx, vs[k][1] - mvy
        ex, ey = dx - mdx, dy - mdy
        sxx += vx * vx
        sxy += vx * vy
        syy += vy * vy
        dxx += ex * vx
        dxy += ex * vy
        dyx += ey * vx
        dyy += ey * vy
    det = sxx * syy - sxy * sxy
    i11, i12, i22 = syy / det, -sxy / det, sxx / det
    a11 = dxx * i11 + dxy * i12
    a12 = dxx * i12 + dxy * i22
    a21 = dyx * i11 + dyy * i12
    a22 = dyx * i12 + dyy * i22
    tx = mdx - (a11 * mvx + a12 * mvy)
    ty = mdy - (a21 * mvx + a22 * mvy)
    # B = I + A ≈ R(phi)·S: columns are the scaled, rotated axes
    b11, b12, b21, b22 = 1 + a11, a12, a21, 1 + a22
    sx = math.hypot(b11, b21)
    sy = math.hypot(b12, b22)
    phi = (math.atan2(b21, b11) + math.atan2(-b12, b22)) / 2

    c, s_ = math.cos(phi), math.sin(phi)
    residuals = {}
    for k, (dx, dy) in readings.items():
        vx, vy = vs[k]
        px = c * sx * vx - s_ * sy * vy - vx + tx
        py = s_ * sx * vx + c * sy * vy - vy + ty
        residuals[k] = math.hypot(dx - px, dy - py)
    return Fit(
        rot_deg=math.degrees(phi), tx_mm=tx, ty_mm=ty, residuals_mm=residuals,
        scale_x=sx, scale_y=sy, scale_fitted=True,
    )


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
    # s = -(R·S)^-1 t = -S^-1 R(-phi) t, front view (R clockwise for Y down)
    sx = -(fit.tx_mm * math.cos(phi) + fit.ty_mm * math.sin(phi)) / fit.scale_x
    sy = -(-fit.tx_mm * math.sin(phi) + fit.ty_mm * math.cos(phi)) / fit.scale_y
    out = {
        "extra_rot_deg": fit.rot_deg,
        "shift_x_mm": -sx,
        "shift_y_mm": sy,
    }
    if fit.scale_fitted:
        # mirroring in X does not change an axis scale
        out["scale_x"] = 1 / fit.scale_x
        out["scale_y"] = 1 / fit.scale_y
    return out


def refine_corrections(base: Mapping[str, float], delta: Mapping[str, float]) -> Dict[str, float]:
    """Combine a profile's corrections with those from a verification print.

    Rotations and shifts add up; scales multiply. Scale keys are only present
    when either side has them.
    """
    out = {
        k: float(base.get(k, 0.0)) + float(delta.get(k, 0.0))
        for k in ("extra_rot_deg", "shift_x_mm", "shift_y_mm")
    }
    for k in ("scale_x", "scale_y"):
        if k in base or k in delta:
            out[k] = float(base.get(k, 1.0)) * float(delta.get(k, 1.0))
    return out
