"""Calibration profile load / validate / merge."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, MutableMapping, Optional


IDENTITY_BACK_CORRECTIONS: Dict[str, float] = {
    "extra_rot_deg": 0.0,
    "shift_x_mm": 0.0,
    "shift_y_mm": 0.0,
}


def default_profile() -> Dict[str, Any]:
    """Identity defaults (no sample skew)."""
    return {
        "paper": {"width_mm": 210.0, "height_mm": 297.0, "orientation": "portrait"},
        "margins": {"x_mm": 0.0, "y_mm": 0.0},
        "flip_mode": "short",
        "back_corrections": dict(IDENTITY_BACK_CORRECTIONS),
    }


def _validate_back_corrections(bc: MutableMapping[str, Any]) -> Dict[str, float]:
    """Ensure correction axes are present and numeric; missing → 0."""
    out: Dict[str, float] = {}
    for key in ("extra_rot_deg", "shift_x_mm", "shift_y_mm"):
        if key not in bc:
            out[key] = 0.0
            continue
        try:
            out[key] = float(bc[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid back_corrections.{key}={bc[key]!r}; expected a number."
            ) from exc
    return out


def load_profile(path: Optional[str]) -> Dict[str, Any]:
    """
    Load a printer calibration profile.

    - path is None → identity corrections
    - path missing → FileNotFoundError
    - invalid / comment-bearing JSON → json.JSONDecodeError (or ValueError)
    - partial back_corrections → missing axes are 0
    """
    prof = default_profile()

    if path is None:
        return prof

    if not os.path.exists(path):
        raise FileNotFoundError(f"Profile not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise json.JSONDecodeError(
                f"Invalid JSON profile (comments are not allowed): {exc.msg}",
                exc.doc,
                exc.pos,
            ) from exc

    if not isinstance(data, dict):
        raise ValueError("Profile root must be a JSON object.")

    for k, v in data.items():
        if k == "back_corrections":
            continue
        if isinstance(v, dict) and isinstance(prof.get(k), dict):
            prof[k].update(v)
        else:
            prof[k] = v

    if "back_corrections" in data:
        bc = data["back_corrections"]
        if not isinstance(bc, dict):
            raise ValueError("back_corrections must be a JSON object.")
        # Start from identity, then overlay provided keys (validated)
        merged = dict(IDENTITY_BACK_CORRECTIONS)
        merged.update(bc)
        prof["back_corrections"] = _validate_back_corrections(merged)
    else:
        prof["back_corrections"] = dict(IDENTITY_BACK_CORRECTIONS)

    return prof


def apply_cli_overrides(
    profile: Dict[str, Any],
    *,
    rot: Optional[float] = None,
    shiftx: Optional[float] = None,
    shifty: Optional[float] = None,
) -> Dict[str, Any]:
    """CLI correction flags win over profile axes when provided."""
    bc = profile.setdefault("back_corrections", dict(IDENTITY_BACK_CORRECTIONS))
    if rot is not None:
        bc["extra_rot_deg"] = float(rot)
    if shiftx is not None:
        bc["shift_x_mm"] = float(shiftx)
    if shifty is not None:
        bc["shift_y_mm"] = float(shifty)
    return profile
