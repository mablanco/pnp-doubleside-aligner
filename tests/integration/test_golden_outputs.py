"""Integration: live CLI output must match committed golden baselines."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.pdf_compare import pdfs_equivalent


@pytest.mark.parametrize(
    "golden_name,extra_args",
    [
        ("out_identity_vector.pdf", []),
        (
            "out_nonzero_vector.pdf",
            ["--profile", "PROFILE_NONZERO"],
        ),
    ],
)
def test_golden_outputs_match(
    run_main_cli,
    sample_interleaved: Path,
    profile_nonzero: Path,
    fixtures_dir: Path,
    tmp_output: Path,
    golden_name: str,
    extra_args: list,
):
    golden = fixtures_dir / "golden" / golden_name
    if not golden.is_file() or golden.stat().st_size == 0:
        pytest.skip(f"golden missing or empty: {golden} (run generate_goldens.py after fixes)")

    args = list(extra_args)
    args = [
        profile_nonzero if a == "PROFILE_NONZERO" else a for a in args
    ]
    # stringify paths
    args = [str(a) if isinstance(a, Path) else a for a in args]

    out = tmp_output / golden_name
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
            "--order",
            "interleaved",
            *args,
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert pdfs_equivalent(out, golden), f"output differs from golden {golden_name}"
