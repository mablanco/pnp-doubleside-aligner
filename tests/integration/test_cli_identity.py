"""Integration/CLI: no profile / no overrides → reported identity corrections."""

from __future__ import annotations

from pathlib import Path


def test_cli_identity_corrections(run_main_cli, sample_interleaved: Path, tmp_output: Path):
    out = tmp_output / "identity.pdf"
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
    assert proc.returncode == 0, proc.stderr + proc.stdout
    combined = (proc.stdout + proc.stderr).lower()
    assert "rotation=0" in combined.replace(" ", "") or "rotation=0.0" in combined.replace(" ", "")
    assert "0 mm" in combined or "(0" in combined
