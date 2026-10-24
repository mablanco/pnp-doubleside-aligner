"""Integration/CLI: calibration sheet and margin test page generators."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

import fitz
import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools"
SHEET = TOOLS / "pnp_calibration_sheet_duplex.py"
MARGINS = TOOLS / "pnp_margin_test_page.py"

MM = 72 / 25.4


def run(script: Path, args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args], cwd=str(cwd), capture_output=True, text=True
    )


def page_sizes_mm(path: Path):
    with fitz.open(str(path)) as doc:
        return [(round(p.rect.width / MM, 1), round(p.rect.height / MM, 1)) for p in doc]


@pytest.mark.parametrize(
    "orientation,paper,size",
    [
        ("portrait", "a4", (210.0, 297.0)),
        ("landscape", "a4", (297.0, 210.0)),
        ("portrait", "letter", (215.9, 279.4)),
        ("landscape", "letter", (279.4, 215.9)),
    ],
)
def test_sheet_has_front_and_back_of_the_requested_size(tmp_path: Path, orientation, paper, size):
    proc = run(SHEET, ["--orientation", orientation, "--paper", paper], tmp_path)
    assert proc.returncode == 0, proc.stderr
    out = tmp_path / f"calibration_sheet_{orientation}_{paper}.pdf"
    assert page_sizes_mm(out) == [size, size]


def test_sheet_back_is_mirrored_scales_and_front_has_targets(tmp_path: Path):
    out = tmp_path / "s.pdf"
    assert run(SHEET, ["--output", str(out)], tmp_path).returncode == 0
    with fitz.open(str(out)) as doc:
        front = doc[0].get_text()
        back = doc[1].get_text()
    for label in ("TL", "TR", "BL", "BR"):
        assert label in front
    assert "TOP" in back


def test_sheet_refuses_to_overwrite_without_force(tmp_path: Path):
    out = tmp_path / "s.pdf"
    out.write_text("keep", encoding="utf-8")
    proc = run(SHEET, ["--output", str(out)], tmp_path)
    assert proc.returncode == 1
    assert "--force" in proc.stderr
    assert out.read_text(encoding="utf-8") == "keep"
    assert run(SHEET, ["--output", str(out), "--force"], tmp_path).returncode == 0


@pytest.mark.parametrize("paper,size", [("a4", (210.0, 297.0)), ("letter", (215.9, 279.4))])
def test_margin_page(tmp_path: Path, paper, size):
    proc = run(MARGINS, ["--paper", paper], tmp_path)
    assert proc.returncode == 0, proc.stderr
    out = tmp_path / f"calibration_margins_{paper}.pdf"
    assert page_sizes_mm(out) == [size, size]
    with fitz.open(str(out)) as doc:
        assert "150 mm" in doc[0].get_text()


def test_margin_page_refuses_to_overwrite_without_force(tmp_path: Path):
    out = tmp_path / "m.pdf"
    out.write_text("keep", encoding="utf-8")
    proc = run(MARGINS, ["--output", str(out)], tmp_path)
    assert proc.returncode == 1
    assert out.read_text(encoding="utf-8") == "keep"
