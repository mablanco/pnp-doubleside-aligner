"""Integration: distinct-path and same-path safe saves (vector + raster)."""

from __future__ import annotations

import shutil
from pathlib import Path


def test_vector_distinct_path(run_main_cli, sample_interleaved: Path, tmp_output: Path):
    out = tmp_output / "distinct_vec.pdf"
    proc = run_main_cli(
        [
            "--input",
            str(sample_interleaved),
            "--output",
            str(out),
            "--mode",
            "vector",
            "--flip-mode",
            "long",
        ]
    )
    assert proc.returncode == 0, proc.stderr
    assert out.is_file() and out.stat().st_size > 0


def test_vector_same_path(run_main_cli, sample_interleaved: Path, tmp_path: Path):
    work = tmp_path / "same_vec.pdf"
    shutil.copy2(sample_interleaved, work)
    proc = run_main_cli(
        [
            "--input",
            str(work),
            "--output",
            str(work),
            "--mode",
            "vector",
            "--flip-mode",
            "long",
        ]
    )
    assert proc.returncode == 0, proc.stderr
    assert work.is_file() and work.stat().st_size > 0


def test_raster_distinct_and_same_path(run_main_cli, sample_interleaved: Path, tmp_path: Path):
    distinct = tmp_path / "distinct_ras.pdf"
    proc = run_main_cli(
        [
            "--input",
            str(sample_interleaved),
            "--output",
            str(distinct),
            "--mode",
            "raster",
            "--flip-mode",
            "long",
            "--dpi",
            "72",
            "--jpeg-quality",
            "40",
        ]
    )
    assert proc.returncode == 0, proc.stderr
    assert distinct.is_file()

    same = tmp_path / "same_ras.pdf"
    shutil.copy2(sample_interleaved, same)
    proc2 = run_main_cli(
        [
            "--input",
            str(same),
            "--output",
            str(same),
            "--mode",
            "raster",
            "--flip-mode",
            "long",
            "--dpi",
            "72",
            "--jpeg-quality",
            "40",
        ]
    )
    assert proc2.returncode == 0, proc2.stderr
    assert same.is_file() and same.stat().st_size > 0
