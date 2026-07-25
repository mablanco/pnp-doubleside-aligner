"""Integration/CLI: batch --auto-detect-smart must not NameError; clear disable message."""

from __future__ import annotations

from pathlib import Path


def test_batch_smart_detect_disabled(run_batch, sample_interleaved: Path, tmp_path: Path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    # Copy/symlink not required — point at fixtures dir parent file by copying bytes
    target = in_dir / "sample.pdf"
    target.write_bytes(sample_interleaved.read_bytes())

    proc = run_batch(
        [
            "--input-dir",
            str(in_dir),
            "--output-dir",
            str(out_dir),
            "--auto-detect-smart",
        ]
    )
    assert proc.returncode != 0
    combined = (proc.stdout + proc.stderr).lower()
    assert "nameerror" not in combined
    assert "avg_sim_block" not in combined
    assert (
        "unavailable" in combined
        or "experimental" in combined
        or "disabled" in combined
        or "not available" in combined
    )
