"""Shared pytest helpers for the PnP doubleside aligner suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = REPO_ROOT / "pnp_double_with_profile_pdf.py"
BATCH_SCRIPT = REPO_ROOT / "tools" / "pnp_batch_align.py"
IMG_SCRIPT = REPO_ROOT / "tools" / "pnp_double_with_profile_img.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def pytest_configure(config: pytest.Config) -> None:
    """Register optional markers (img extras are not required for default CI)."""
    config.addinivalue_line(
        "markers",
        "img: needs optional image-tool extras (opencv/fpdf); "
        "skip when cv2 is not importable",
    )


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def sample_interleaved(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_interleaved.pdf"


@pytest.fixture
def sample_odd(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_odd.pdf"


@pytest.fixture
def profile_nonzero(fixtures_dir: Path) -> Path:
    return fixtures_dir / "profile_nonzero.json"


@pytest.fixture
def profile_shift_only(fixtures_dir: Path) -> Path:
    return fixtures_dir / "profile_shift_only.json"


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Directory for CLI outputs (isolated per test)."""
    out = tmp_path / "out"
    out.mkdir()
    return out


def run_cli(
    args: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    check: bool = False,
) -> subprocess.CompletedProcess:
    """Run the main aligner CLI via subprocess."""
    cmd: List[str] = [sys.executable, str(MAIN_SCRIPT), *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        check=check,
    )


def run_batch_cli(
    args: Sequence[str],
    *,
    cwd: Optional[Path] = None,
) -> subprocess.CompletedProcess:
    """Run the batch aligner CLI via subprocess."""
    cmd: List[str] = [sys.executable, str(BATCH_SCRIPT), *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
    )


def run_img_tool(
    args: Sequence[str],
    *,
    cwd: Optional[Path] = None,
) -> subprocess.CompletedProcess:
    """Run the experimental image tool CLI via subprocess."""
    cmd: List[str] = [sys.executable, str(IMG_SCRIPT), *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
    )


@pytest.fixture
def run_main_cli():
    return run_cli


@pytest.fixture
def run_batch():
    return run_batch_cli


@pytest.fixture
def run_img_cli():
    return run_img_tool


@pytest.fixture
def img_fixtures_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "img"


# Wire PDF compare helper for golden tests (T024)
from tests.helpers.pdf_compare import pdfs_equivalent  # noqa: E402

__all__ = ["pdfs_equivalent", "run_cli", "run_batch_cli", "run_img_tool"]
