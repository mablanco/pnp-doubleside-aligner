"""Packaging smoke: installed console script / module entry after editable install."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_pyproject_text() -> str:
    return (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_pnp_double_align_help_via_console_script_or_module() -> None:
    """SC-001: pnp-double-align --help (or module form) exits 0 when packaged."""
    cmd = shutil.which("pnp-double-align")
    if cmd:
        result = subprocess.run(
            [cmd, "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        # Editable install not on PATH (e.g. some local runs): try module form.
        result = subprocess.run(
            [sys.executable, "-m", "pnp_double_with_profile_pdf", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip(
                "pnp-double-align not on PATH and python -m entry failed; "
                "install with: pip install -e '.[dev]'"
            )

    assert result.returncode == 0, result.stderr or result.stdout
    combined = (result.stdout or "") + (result.stderr or "")
    assert "--input" in combined or "input" in combined.lower()


def test_default_dependencies_exclude_image_extras() -> None:
    """SC-004 / FR-005: default deps must not require opencv or fpdf."""
    text = _load_pyproject_text().lower()
    # Locate [project] dependencies block roughly; fail if opencv/fpdf appear
    # as required (not merely mentioned in comments under optional-deps).
    # Split on optional-dependencies so comments there are allowed.
    main_part = text.split("[project.optional-dependencies]", 1)[0]
    assert "opencv" not in main_part
    assert "fpdf" not in main_part
    # Optional img extra may be absent until feature 003; if present it is ok.
    if "[project.optional-dependencies]" in text:
        # Ensure opencv is not in the unscoped dependencies list lines.
        for line in main_part.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert "opencv" not in stripped
            assert "fpdf" not in stripped
