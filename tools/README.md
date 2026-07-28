# Tools

This directory contains auxiliary and advanced scripts used during the development
and calibration process of *PnP Double-Side Aligner*.

These tools are optional and are not required for normal day-to-day usage.
They are provided for advanced users who want deeper control over calibration,
image-based PnPs, or batch workflows.

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

Experimental image-based PnP path (PNG/JPG) with OpenCV crop matching and FPDF
output. **Prefer the main PDF workflow** (`pnp_double_with_profile_pdf.py`) for
production duplex alignment.

Optional dependencies (not part of the main or dev install):

```bash
pip install -r requirements.txt
pip install -r requirements-img.txt
```

Example:

```bash
python tools/pnp_double_with_profile_img.py \
  --profile profiles/example_printer.json \
  --ref-original tests/fixtures/img/ref_original.png \
  --ref-crop tests/fixtures/img/ref_crop.png \
  --front tests/fixtures/img/front0.png \
  --back tests/fixtures/img/back0.png \
  --output /tmp/pnp_img_out.pdf
```

If a `--back` is omitted for an index, the cropped front is duplicated as the
back. Profile rotation/shift/flip apply to **backs only**. See
`specs/003-image-tool-stack/contracts/image-tool-cli.md`.

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
