#!/usr/bin/env python3
"""Generate golden PDF baselines for refactor no-drift checks.

Run from repository root after Phase 2 geometry/profile fixes:

    python tests/fixtures/generate_goldens.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent
GOLDEN = FIXTURES / "golden"
MAIN = REPO / "pnp_double_with_profile_pdf.py"
SAMPLE = FIXTURES / "sample_interleaved.pdf"
PROFILE = FIXTURES / "profile_nonzero.json"


def _run(args: list[str]) -> None:
    cmd = [sys.executable, str(MAIN), *args]
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(
            f"golden generation failed ({proc.returncode}):\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def main() -> None:
    GOLDEN.mkdir(parents=True, exist_ok=True)
    identity = GOLDEN / "out_identity_vector.pdf"
    nonzero = GOLDEN / "out_nonzero_vector.pdf"

    _run(
        [
            "--input",
            str(SAMPLE),
            "--output",
            str(identity),
            "--mode",
            "vector",
            "--flip-mode",
            "long",
            "--order",
            "interleaved",
        ]
    )
    _run(
        [
            "--input",
            str(SAMPLE),
            "--output",
            str(nonzero),
            "--profile",
            str(PROFILE),
            "--mode",
            "vector",
            "--flip-mode",
            "long",
            "--order",
            "interleaved",
        ]
    )
    print(f"Wrote {identity}")
    print(f"Wrote {nonzero}")


if __name__ == "__main__":
    main()
