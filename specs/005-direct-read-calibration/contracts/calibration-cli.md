# Contract: calibration CLIs

All three scripts run from the repository root, write to stdout on success,
to stderr on error, and never overwrite an existing output without `--force`.
Paper: `a4` (210 × 297 mm) or `letter` (215.9 × 279.4 mm).

## tools/pnp_margin_test_page.py

```
python tools/pnp_margin_test_page.py [--paper a4|letter] [--output PATH] [--force]
```

- Default output: `calibration_margins_<paper>.pdf`.
- 2 identical portrait pages: three rulers per edge starting at the paper edge
  (0 mm, ticks every mm up to 20 mm), a 150 mm horizontal and a 200 mm vertical
  reference line.
- Exit 0 on success; 1 if the output exists without `--force` or cannot be
  written.

## tools/pnp_calibration_sheet_duplex.py

```
python tools/pnp_calibration_sheet_duplex.py [--orientation portrait|landscape]
    [--paper a4|letter] [--output PATH] [--force]
```

- Default: `portrait`, `a4`, output `calibration_sheet_<orientation>_<paper>.pdf`.
- Page 1 (front): crosses `TL`, `TR`, `BL`, `BR` at 25 mm from the edges and
  `C` at the centre, plus instructions.
- Page 2 (back): per target a horizontal (dx) and a vertical (dy) scale,
  mirrored in X; orientation witness "TOP".
- Exit codes as above.

## tools/pnp_calibration_solver.py

```
python tools/pnp_calibration_solver.py
    --top-left DX DY --top-right DX DY --bottom-left DX DY --bottom-right DX DY
    [--center DX DY]
    [--orientation portrait|landscape] [--paper a4|letter]
    [--refine PROFILE] [--name NAME]
    [--output PATH | --output -] [--force]
```

- Readings: back offset seen from the front, in mm (dx > 0 right, dy > 0 down),
  exactly as read on the sheet.
- Default output: `profiles/my_calibrated_printer.json`; `-` prints JSON to
  stdout (summary to stderr).
- Without `--refine`: new profile with `paper` (size + orientation),
  `margins` 0, `flip_mode: "long"`, `back_corrections`, `_notes` with the
  readings.
- With `--refine PROFILE`: base profile fields are kept; `back_corrections`
  become base + correction from the (residual) readings; `_notes` is appended.
- Summary: rotation and shifts, per-point fit residuals; warning on stderr if
  the largest residual exceeds 0.75 mm.
- Exit 0 on success; 2 on argument errors (argparse); 1 if the output exists
  without `--force`, the base profile is missing/invalid, or the output cannot
  be written.

## Profile mapping

| Front-view fit | Profile field |
|---|---|
| rotation φ (clockwise > 0) | `extra_rot_deg = φ` |
| tx (right > 0) | `shift_x_mm = tx` |
| ty (down > 0) | `shift_y_mm = −ty` |

Shifts are counter-rotated by φ first (`s = −R(−φ)·t`), exact for any skew.
