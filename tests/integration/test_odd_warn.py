"""Integration/CLI: --on-odd warn emits stderr for odd fronts_then_backs."""

from __future__ import annotations

from pathlib import Path


def test_odd_warn_stderr(run_main_cli, sample_odd: Path, tmp_output: Path):
    out = tmp_output / "odd.pdf"
    proc = run_main_cli(
        [
            "--input",
            str(sample_odd),
            "--output",
            str(out),
            "--order",
            "fronts_then_backs",
            "--on-odd",
            "warn",
            "--mode",
            "vector",
            "--flip-mode",
            "long",
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert proc.stderr.strip(), "expected odd-page warning on stderr"
    assert "odd" in proc.stderr.lower()
