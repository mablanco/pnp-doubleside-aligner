# Implementation Plan: Back Scale Correction

**Branch**: `006-back-scale-correction` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

## Summary

Add optional `scale_x` / `scale_y` back corrections applied about the page
centre in both processing paths, CLI overrides, and an opt-in scale fit in the
calibration solver.

## Technical Context

**Language/Version**: Python 3.9+ · **Dependencies**: unchanged ·
**Testing**: pytest (unit geometry, raster, profile, calibration round trip,
CLI).

## Transform order and exact mapping

Aligner (back page): `q → Sa·Ra·(q − c) + c` (rotate, then scale), then the
optional 180° turn, then the shift. Printer error seen from the front:
`q → R·S·(q − c) + c + t` (the back is printed at nominal size on a sheet that
shrank). With the back mirrored in X, cancelling both requires `Ra = R⁻¹` (sign
kept, as before), `Sa = S⁻¹` and `s = −(R·S)⁻¹·t` (mirrored in X). Rotating
before scaling in the aligner is what makes `Sa·Ra = (R·S)⁻¹` exact.

Fit: least-squares affine `d = A·v + t`; `B = I + A ≈ R(ψ)·S` decomposed as
`sx = |B·e1|`, `sy = |B·e2|`, `ψ = mean(atan2(b21, b11), atan2(−b12, b22))`.

## Constitution Check

- **Existing baseline**: Additive; without scale keys the output is identical
  (identity skipped in both paths, goldens unchanged).
- **Calibration-Profile First**: Scale lives in the profile; CLI overrides for
  experiments.
- **Back-Page Corrections Only / Vector-First**: Backs only; vector matrix
  extended, raster mirrors it.
- **Geometric Precision**: Characterised by unit tests (centre fixed, order),
  vector vs raster placement, and the calibration round trip through
  `build_back_matrix`.
- **Separation of Concerns**: Math in `geometry.py` / `calibration.py`;
  validation in `profiles.py`.
- **Safe I/O & docs**: Guide, README and template updated.

## Project Structure

```text
geometry.py                     # build_back_matrix(scale_x, scale_y)
profiles.py                     # validate scale, CLI overrides
pnp_double_with_profile_pdf.py  # pass scale (vector + raster), --scalex/--scaley
tools/pnp_batch_align.py        # pass-through overrides
calibration.py                  # fit_scale, exact mapping, refine
tools/pnp_calibration_solver.py # --fit-scale
docs/, README.md, tools/README.md, profiles/base_printer_profile.json
tests/unit/test_vector_matrix.py, test_raster_signs.py, test_profile_load.py,
tests/unit/test_calibration.py, tests/integration/test_calibration_solver_cli.py,
tests/integration/test_scale_cli.py
```

## Complexity Tracking

None.
