"""Unit tests for profile load: identity defaults and error paths (desired contract)."""

import json
from pathlib import Path

import pytest

from profiles import load_profile


def _corrections(prof):
    bc = prof["back_corrections"]
    return (
        float(bc["extra_rot_deg"]),
        float(bc["shift_x_mm"]),
        float(bc["shift_y_mm"]),
    )


def test_load_profile_none_is_identity():
    """No profile path → identity corrections (not sample 0.30/1/1)."""
    assert _corrections(load_profile(None)) == (0.0, 0.0, 0.0)


def test_load_profile_missing_keys_are_identity(tmp_path: Path):
    path = tmp_path / "partial.json"
    path.write_text(
        json.dumps({"flip_mode": "long", "back_corrections": {"shift_x_mm": 2.5}}),
        encoding="utf-8",
    )
    rot, sx, sy = _corrections(load_profile(str(path)))
    assert rot == 0.0
    assert sx == 2.5
    assert sy == 0.0


def test_load_profile_missing_path_raises(tmp_path: Path):
    missing = tmp_path / "no_such_profile.json"
    with pytest.raises((FileNotFoundError, OSError, ValueError)):
        load_profile(str(missing))


def test_load_profile_invalid_json_raises(fixtures_dir: Path):
    with pytest.raises((json.JSONDecodeError, ValueError, TypeError)):
        load_profile(str(fixtures_dir / "profile_invalid.json"))


def test_load_profile_comments_raise(fixtures_dir: Path):
    with pytest.raises((json.JSONDecodeError, ValueError)):
        load_profile(str(fixtures_dir / "profile_with_comments.json"))


def test_load_profile_nonzero_fixture(fixtures_dir: Path):
    rot, sx, sy = _corrections(load_profile(str(fixtures_dir / "profile_nonzero.json")))
    assert (rot, sx, sy) == (2.0, 3.0, 4.0)


def test_load_profile_scale_defaults_to_one(tmp_path: Path):
    path = tmp_path / "p.json"
    path.write_text(json.dumps({"back_corrections": {"shift_x_mm": 1}}), encoding="utf-8")
    bc = load_profile(str(path))["back_corrections"]
    assert (bc["scale_x"], bc["scale_y"]) == (1.0, 1.0)
    assert load_profile(None)["back_corrections"]["scale_x"] == 1.0


@pytest.mark.parametrize("value", ["big", 0.5, 1.2, 0])
def test_load_profile_invalid_scale_raises(tmp_path: Path, value):
    path = tmp_path / "p.json"
    path.write_text(json.dumps({"back_corrections": {"scale_x": value}}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_profile(str(path))


def test_cli_overrides_scale():
    from profiles import apply_cli_overrides

    prof = apply_cli_overrides(load_profile(None), scalex=0.996, scaley=1.001)
    assert prof["back_corrections"]["scale_x"] == 0.996
    assert prof["back_corrections"]["scale_y"] == 1.001
