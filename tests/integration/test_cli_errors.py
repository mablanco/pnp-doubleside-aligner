"""Integration/CLI: missing PDF/profile and invalid JSON → stderr + non-zero exit."""

from __future__ import annotations

from pathlib import Path


def test_missing_input_pdf(run_main_cli, tmp_output: Path, tmp_path: Path):
    proc = run_main_cli(
        [
            "--input",
            str(tmp_path / "missing.pdf"),
            "--output",
            str(tmp_output / "x.pdf"),
        ]
    )
    assert proc.returncode != 0
    assert proc.stderr.strip()
    assert "Traceback" not in proc.stderr.splitlines()[0]


def test_missing_profile_path(run_main_cli, sample_interleaved: Path, tmp_output: Path, tmp_path: Path):
    proc = run_main_cli(
        [
            "--input",
            str(sample_interleaved),
            "--output",
            str(tmp_output / "x.pdf"),
            "--profile",
            str(tmp_path / "no_profile.json"),
        ]
    )
    assert proc.returncode != 0
    assert proc.stderr.strip()
    assert "profile" in proc.stderr.lower() or "not found" in proc.stderr.lower()


def test_comment_profile_errors(run_main_cli, sample_interleaved: Path, fixtures_dir: Path, tmp_output: Path):
    proc = run_main_cli(
        [
            "--input",
            str(sample_interleaved),
            "--output",
            str(tmp_output / "x.pdf"),
            "--profile",
            str(fixtures_dir / "profile_with_comments.json"),
        ]
    )
    assert proc.returncode != 0
    assert proc.stderr.strip()
    assert "json" in proc.stderr.lower() or "comment" in proc.stderr.lower() or "valid" in proc.stderr.lower()


def test_invalid_profile_errors(run_main_cli, sample_interleaved: Path, fixtures_dir: Path, tmp_output: Path):
    proc = run_main_cli(
        [
            "--input",
            str(sample_interleaved),
            "--output",
            str(tmp_output / "x.pdf"),
            "--profile",
            str(fixtures_dir / "profile_invalid.json"),
        ]
    )
    assert proc.returncode != 0
    assert proc.stderr.strip()
