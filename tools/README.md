# Tools

This directory contains auxiliary and advanced scripts used during the development
and calibration process of *PnP Double-Side Aligner*.

These tools are optional and are not required for normal day-to-day usage.
They are provided for advanced users who want deeper control over calibration,
image-based PnPs, or batch workflows.

**Packaging note**: editable install (`pip install -e .`) exposes only the main
aligner as `pnp-double-align`. Everything under `tools/` stays **script-only**
(invoke with `python tools/<script>.py`); there are no console entry points for
these helpers in v1.

## Included tools

### pnp_calibration_sheet_duplex.py

Generates printable duplex calibration sheets (front/back marks).

### pnp_calibration_solver.py

Helper script to compute printer calibration values from manual measurements.

Features:
- Takes measured offsets (dx, dy) from multiple reference points
- Estimates average X/Y shift and rotation (skew)
- Outputs values suitable for a printer profile JSON

### pnp_double_with_profile_img.py (**experimental**)

Experimental image-based PnP path (PNG/JPG). OpenCV/FPDF extras and a full
rewrite are **out of the first remediation slice** — treat this script as
unsupported/experimental. Prefer the main PDF workflow
(`pnp_double_with_profile_pdf.py`).

### pnp_batch_align.py (**experimental**)

Experimental batch-processing tool for multiple PnP PDFs.

- Processes all PDFs in a directory with the main aligner as worker
- `--auto-detect-smart` is **disabled / unavailable** (incomplete heuristics);
  the flag exits with a clear error instead of crashing
- Manual review of outputs is strongly recommended

## Notes

- These tools were part of the iterative development process
  that led to the final alignment workflow.
- They are provided for transparency and advanced use cases.
- Use these scripts at your own discretion.
