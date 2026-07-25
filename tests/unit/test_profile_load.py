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
