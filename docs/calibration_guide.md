# Printer Calibration Guide

This guide explains how to calibrate your printer so that front and back pages
align correctly when printing Print-and-Play (PnP) PDFs.

Calibration is based on measuring the physical behavior of your printer
and encoding the correction into a reusable printer profile.

## Overview

Real printers introduce small but consistent errors when printing double-sided:
- rotation (skew)
- horizontal shift (X)
- vertical shift (Y)

These errors are mechanical and repeatable.
Once measured, they can be compensated automatically for all compatible PnPs.

## Step 1: Generate calibration sheets

Calibration sheets are generated using the following script:

```bash
tools/pnp_calibration_sheet_duplex.py
```

Run the script from the root of the repository:
```bash
python tools/pnp_calibration_sheet_duplex.py
```

The script generates printable PDF files containing:
- a FRONT calibration page
- one or more BACK calibration pages
- clear reference marks near the page edges
- explicit TOP and feed-edge indicators

These sheets are designed to make duplex misalignment and rotation visible.

## Step 2: Print the calibration sheets

Print the generated PDFs using exactly the same settings you plan to use
for your PnP projects:

- same printer
- same paper type and weight
- same paper tray
- same duplex mode (long edge or short edge)
- same orientation (portrait or landscape)
- no scaling (100% size)

Do not rotate or resize the PDF when printing.

## Step 3: Measure the misalignment

After printing, hold the sheet against a light source.

Compare the FRONT and BACK reference marks and measure:
- horizontal offset (X) in millimeters
- vertical offset (Y) in millimeters
- any visible rotation between front and back

Take measurements at multiple reference points if possible.

## Step 4: Create a printer profile

Create a new printer profile based on the template:

```bash
profiles/base_printer_profile.json
```

Copy and rename it, for example:

```bash
my_printer_A4_200g.json
```

Edit the file and fill in the measured values under back_corrections.

Positive values mean:
- rotation: clockwise
- X shift: move the back to the right
- Y shift: move the back downward

Negative values move in the opposite direction.

These sign conventions apply to **both** the preferred (vector) path and the
raster fallback. Without `--profile` and without CLI overrides, corrections are
identity (`0°, 0 mm, 0 mm`) — not sample skew.

Important: remove all comments before using the profile.
The final file must be valid JSON. Templates under `profiles/` that contain
comments must be copied and stripped before use with `--profile`.

For `fronts_then_backs` with an odd page count, `--on-odd warn` prints a warning
on stderr and continues; use `add_blank` or `drop_last` to change effective length.

## Step 5: Iterate if needed

Calibration is usually an iterative process.

1. Apply the profile using pnp_double_with_profile_pdf.py
2. Print a test page
3. Check alignment
4. Adjust values in small steps

Repeat until alignment is satisfactory.

## Optional: Assisted calibration

For advanced users, the following helper script is available:

```bash
tools/pnp_calibration_solver.py
```

This script can compute suggested correction values from measured offsets.

## Reusing the profile

Once calibrated, the same profile can be reused for all compatible PnP PDFs.

Recalibration is only required if you change:
- printer
- paper type or weight
- paper tray
- duplex mode
- page orientation

## Notes and limitations

- This calibration assumes that PnP PDFs are properly centered on the page.
- The script corrects printer errors, not layout errors.
- Poorly centered PDFs must be fixed before calibration.

Calibration may take some time, but it only needs to be done once.
After that, duplex-aligned PnP printing becomes repeatable and reliable.
