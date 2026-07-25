"""Integration: --mode auto recoverable vector failure → stderr fallback + raster output."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pnp_double_with_profile_pdf as mod


def test_auto_fallback_stderr_and_raster_output(
    run_main_cli,
    sample_interleaved: Path,
    profile_shift_only: Path,
    tmp_output: Path,
    monkeypatch,
):
    """Force preferred-path failure; auto must explain on stderr and write raster PDF."""
    out = tmp_output / "auto_fallback.pdf"

    def boom(*args, **kwargs):
        raise TypeError("forced vector failure for characterization")

    monkeypatch.setattr(mod, "process_pdf_vector", boom)

    # Invoke via importable main path so monkeypatch applies
    import sys

    argv = [
        "pnp_double_with_profile_pdf.py",
        "--input",
        str(sample_interleaved),
        "--output",
        str(out),
        "--profile",
        str(profile_shift_only),
        "--mode",
        "auto",
        "--flip-mode",
        "long",
        "--dpi",
        "72",
        "--jpeg-quality",
        "50",
    ]
    monkeypatch.setattr(sys, "argv", argv)

    # Capture stderr from main
    from io import StringIO
    import contextlib

    err = StringIO()
    with contextlib.redirect_stderr(err):
        try:
            mod.main()
            code = 0
        except SystemExit as e:
            code = int(e.code or 0)

    assert code == 0
    assert out.is_file() and out.stat().st_size > 0
    stderr = err.getvalue().lower()
    assert "raster" in stderr or "fallback" in stderr or "vector" in stderr
