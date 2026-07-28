"""Error-path tests for the experimental image tool CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("fpdf")


@pytest.mark.img
def test_missing_input_path(
    run_img_cli,
    img_fixtures_dir: Path,
    repo_root: Path,
    tmp_output: Path,
    tmp_path: Path,
):
    proc = run_img_cli(
        [
            "--profile",
            str(repo_root / "profiles" / "example_printer.json"),
            "--ref-original",
            str(tmp_path / "missing_ref.png"),
            "--ref-crop",
            str(img_fixtures_dir / "ref_crop.png"),
            "--front",
            str(img_fixtures_dir / "front0.png"),
            "--output",
            str(tmp_output / "out.pdf"),
        ]
    )
    assert proc.returncode != 0
    assert proc.stderr.strip()
    assert "Traceback" not in proc.stderr.splitlines()[0]
    assert "missing" in proc.stderr.lower() or "ref-original" in proc.stderr.lower()


@pytest.mark.img
def test_missing_profile_path(
    run_img_cli,
    img_fixtures_dir: Path,
    tmp_output: Path,
    tmp_path: Path,
):
    proc = run_img_cli(
        [
            "--profile",
            str(tmp_path / "no_profile.json"),
            "--ref-original",
            str(img_fixtures_dir / "ref_original.png"),
            "--ref-crop",
            str(img_fixtures_dir / "ref_crop.png"),
            "--front",
            str(img_fixtures_dir / "front0.png"),
            "--output",
            str(tmp_output / "out.pdf"),
        ]
    )
    assert proc.returncode != 0
    assert proc.stderr.strip()
    assert "profile" in proc.stderr.lower() or "missing" in proc.stderr.lower()
    assert "Traceback" not in proc.stderr.splitlines()[0]


@pytest.mark.img
def test_comment_profile_errors(
    run_img_cli,
    img_fixtures_dir: Path,
    fixtures_dir: Path,
    tmp_output: Path,
):
    proc = run_img_cli(
        [
            "--profile",
            str(fixtures_dir / "profile_with_comments.json"),
            "--ref-original",
            str(img_fixtures_dir / "ref_original.png"),
            "--ref-crop",
            str(img_fixtures_dir / "ref_crop.png"),
            "--front",
            str(img_fixtures_dir / "front0.png"),
            "--output",
            str(tmp_output / "out.pdf"),
        ]
    )
    assert proc.returncode != 0
    assert proc.stderr.strip()
    low = proc.stderr.lower()
    assert "json" in low or "comment" in low or "valid" in low
    assert "Traceback" not in proc.stderr.splitlines()[0]
