# Implementation Plan: Direct-Read Duplex Calibration

**Branch**: `005-direct-read-calibration` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-direct-read-calibration/spec.md`

## Summary

Replace the calibration sheet and solver with a direct-read sheet (portrait and
landscape, A4 and Letter), a least-squares solver that maps front-view readings
to back-page corrections (with `--refine` for verification prints), and add a
margin test page. The math lives in a new pure module `calibration.py`.

## Technical Context

**Language/Version**: Python 3.9+

**Primary Dependencies**: ReportLab (sheets), PyMuPDF only in tests (aligner
geometry); no new dependencies.

**Storage**: JSON profiles, PDF sheets (generated, gitignored).

**Testing**: pytest (unit for the math, CLI integration for the three tools,
geometric round-trip through `geometry.build_back_matrix`).

**Target Platform**: any OS with Python; print dialogs documented generically.

**Project Type**: CLI scripts.

**Constraints**: black-only output; content ≥ 25 mm from the edges on sheets.

## Constitution Check

- **Existing baseline**: Intentional contract break for the two calibration
  tools, documented in the spec. The main aligner, profile schema and
  transforms are unchanged.
- **Calibration-Profile First**: The solver writes reusable profiles; `--refine`
  keeps one profile per printer configuration.
- **CLI-First + clear errors**: argparse, stderr messages, exit codes in the
  contract; no tracebacks for expected failures.
- **Back-Page Corrections Only / Vector-First**: Untouched.
- **Practical Simplicity**: No new dependencies; one new pure module.
- **Geometric Precision**: Not changing transforms. The new solver is verified
  against the real `build_back_matrix` with a geometric round-trip test.
- **Separation of Concerns**: `calibration.py` has no I/O; tools only parse
  arguments, draw PDFs and read/write files.
- **Repository hygiene**: Default outputs match ignored patterns
  (`calibration_*.pdf`, `profiles/*`).
- **Safe I/O & docs**: No overwrite without `--force`; guide and READMEs updated.

## Project Structure

```text
calibration.py                         # NEW pure math (targets, fit, mapping, refine)
tools/pnp_calibration_sheet_duplex.py  # REWRITTEN direct-read sheet
tools/pnp_calibration_solver.py        # REWRITTEN solver (+ --refine)
tools/pnp_margin_test_page.py          # NEW margin test page
docs/calibration_guide.md              # REWRITTEN procedure
README.md, tools/README.md             # updated
pyproject.toml                         # py-modules += calibration
tests/unit/test_calibration.py         # NEW math + geometric round-trip
tests/unit/test_calibration_solver.py  # REPLACED (old formula characterisation)
tests/integration/test_calibration_solver_cli.py  # REWRITTEN
tests/integration/test_calibration_sheets_cli.py  # NEW sheet + margin page CLIs
```

## Complexity Tracking

None.
