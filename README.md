# PnP Double-Side Aligner

A practical tool to correct duplex misalignment when printing Print-and-Play (PnP) PDFs.

This project compensates for mechanical skew and offset introduced by real printers
when printing double-sided, producing accurately aligned fronts and backs.

The workflow is based on printer calibration: you measure once, create a profile,
and reuse it for all compatible PnPs.

## Project status

This started as a hand-written utility. Spec Kit / Cursor AI workflows are being
added on top of that existing codebase to help with specs, refactors, and
documentation—not to replace the original duplex-alignment behavior.

If you contribute (human or AI-assisted):

- Keep geometric transforms and printer-profile contracts stable unless a change
  is intentional and documented
- Do not commit secrets, tokens, `.env` files, personal printer profiles, or
  local tool config (see `.gitignore`)
- Prefer characterization tests before refactoring transform or profile logic

Project principles live in `.specify/memory/constitution.md`.

### Spec Kit tooling after clone

Git tracks project state (constitution, Spec Kit config, template overrides).
Regenerable `specify init` assets (scripts, stock templates, skills, extension
payloads, workflows) are gitignored. After cloning, restore local tooling, for
example:

```bash
specify init --here --force --integration cursor-agent
```

Use the same integration options you normally use for this repo. Project
template customizations live under `.specify/templates/overrides/`.

## Features

- Corrects rotation (skew) and X/Y shift on back pages only
- Uses printer calibration profiles (JSON)
- Supports multiple PnP page orders
- Vector-first processing with automatic raster fallback
- Controlled raster output with JPEG compression
- Designed for real-world duplex printers

## Requirements

- Python 3.9+

It is strongly recommended to use a **virtual environment (venv)** to avoid interfering
with system-wide Python packages.

### Using a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pymupdf pillow reportlab
```

To deactivate the environment:

```bash
deactivate
```

### System packages (preferred when available)

Whenever possible, prefer installing the required libraries using your operating
system or Linux distribution packages (apt, dnf, pacman, etc.), especially on Linux.

This usually provides better integration, stability and easier updates.

## Basic Usage

```bash
python pnp_double_with_profile_pdf.py \
  --input game.pdf \
  --output game_aligned.pdf
```

## Printer Profile

This tool uses a printer calibration profile to compensate for duplex misalignment.

Profiles describe:
- paper size and orientation
- duplex flip mode
- rotation and X/Y shifts applied to back pages

Profiles are reusable across all compatible PnP PDFs.

## Using the base printer profile

A base template is provided at:

profiles/base_printer_profile.json

Use this file as a starting point to calibrate a new printer or paper type.

1. Copy and rename the file (for example: my_printer_EPSON_A4_200g.json)
2. Edit the values after calibration
3. Remove all comments so the file becomes valid JSON
4. Use the profile with the main script

Personal profiles under `profiles/` (anything other than the tracked examples)
are gitignored on purpose so local calibration data is not published.

## Calibration

Calibration is performed using a dedicated script that generates printable
calibration sheets on demand.

### Generate calibration sheets

Run the following script from the repository root:

```bash
python tools/pnp_calibration_sheet_duplex.py
```

This script generates FRONT and BACK calibration pages with clear visual markers
to reveal duplex misalignment and rotation.

### Follow the calibration guide

A complete, step-by-step calibration guide is provided here:

```bash
docs/calibration_guide.md
```

Calibration is required only once per printer configuration.

## Page Order Modes

Supported page order modes:

- interleaved – Front / Back alternating
- fronts_then_backs – All fronts first, then all backs
- last_back – All fronts, last page is the back
- single_sided – No backs

Odd-page PDFs in fronts_then_backs mode can be handled by:
- warning only
- dropping the last page
- adding a blank page

## Advanced Options

Force raster output:

```bash
--mode raster --dpi 300 --jpeg-quality 85
```

Override profile values from the command line:

```bash
--rot 0.28 --shiftx 0.8 --shifty 1.2
```

## Tools

Additional helper scripts are available in the tools/ directory.

These scripts are optional and intended for advanced or specialized workflows,
such as assisted calibration, image-based PnPs, or batch processing.

See tools/README.md for details.

## FAQ

### Do I need one profile per printer or per PnP?

You need one profile per printer configuration, not per PnP.

A profile represents the physical behavior of your printer when printing double-sided:
paper feed, duplex mechanism, skew and consistent offsets.

The same profile can be reused for all compatible PnP PDFs.

### Does this script work with any PnP PDF?

No.

This tool assumes that PnP PDFs are properly centered on the page:
- left and right margins are equal
- top and bottom margins are equal
- front and back pages share the same page geometry

Poorly centered PDFs must be fixed before using this tool.

## Best Practices

- Always use different input and output filenames
- Close PDF viewers before processing files
- Recalibrate if you change printer, paper, or duplex settings
- Keep API keys, Sonar tokens, and `.env` files out of git

## Contributing

This project is released under the MIT License.

If you modify or improve this tool (bug fixes, new features or documentation),
please consider contributing your changes back.

Even small improvements or documentation updates are welcome.

## License

MIT License.
