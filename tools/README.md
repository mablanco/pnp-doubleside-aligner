# Tools

This directory contains auxiliary and advanced scripts used during the development
and calibration process of *PnP Double-Side Aligner*.

These tools are optional and are not required for normal day-to-day usage.
They are provided for advanced users who want deeper control over calibration,
image-based PnPs, or batch workflows.

## Included tools

### pnp_calibration_solver.py

Helper script to compute printer calibration values from manual measurements.

Features:
- Takes measured offsets (dx, dy) from multiple reference points
- Estimates average X/Y shift and rotation (skew)
- Outputs values suitable for a printer profile JSON

Recommended when:
- you want to reduce trial-and-error calibration
- you prefer a more analytical approach to alignment

This tool assumes you understand how and where measurements are taken.

### pnp_double_with_profile_img.py

Processes image-based PnPs (PNG/JPG) instead of PDFs.

Features:
- Works with scanned pages or screenshots
- Uses a reference crop to align all pages consistently
- Applies the same back-side corrections as the PDF workflow
- Outputs an A4 PDF ready for printing

Recommended when:
- the original PnP is not available as a PDF
- working with scans or reconstructed assets
- cleaning up low-quality image sources

This is a more manual workflow compared to the PDF-based script.

### pnp_batch_align.py

Experimental batch-processing tool for multiple PnP PDFs.

Features:
- Processes all PDFs in a directory
- Attempts to detect front/back order automatically
- Applies a single printer profile to all files

Important notes:
- This tool is experimental
- Automatic detection may fail on unusual layouts
- Manual review of the output is strongly recommended

Recommended only for experienced users.

## Notes

- These tools were part of the iterative development process
  that led to the final alignment workflow.
- They are provided for transparency and advanced use cases.
- Use these scripts at your own discretion.
