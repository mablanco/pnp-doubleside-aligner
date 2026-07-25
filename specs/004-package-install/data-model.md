# Data Model: Installable Package Alongside Scripts

**Feature**: `004-package-install`  
**Date**: 2026-07-25  
**Related**: [spec.md](./spec.md), [contracts/packaging-install.md](./contracts/packaging-install.md)

Logical packaging entities (metadata / install artifacts). No database.
Duplex geometry entities are unchanged from prior features.

## Distribution

Installable Python project representing this repository.

| Field | Rules |
|-------|-------|
| `name` | `pnp-doubleside-aligner` |
| `version` | SemVer starting at `0.1.0` for first packaged form |
| `description` | Short summary of duplex PnP alignment purpose |
| `license` | MIT (consistent with `LICENSE`) |
| `requires-python` | `>=3.9` |
| `dependencies` | Main PDF runtime set (PyMuPDF, Pillow, reportlab) pinned |

**Relationships**: Provides one primary **CLI Entry**; may declare **Optional
Extras**.

## CLI Entry

| Field | Value / rules |
|-------|----------------|
| `command` | `pnp-double-align` |
| `target` | `pnp_double_with_profile_pdf:main` |
| `behavior` | Same argparse/geometry contract as loose script |

Alternate invoke after install: `python -m pnp_double_with_profile_pdf`.

## Optional Extra

| Extra name | Purpose | Mandatory on default install? |
|------------|---------|-------------------------------|
| `dev` | Test runner (pytest) | No |
| `img` | Experimental image-tool stack (only if declared) | No |

## Convenience Requirement Sets

| Artifact | Role |
|----------|------|
| `requirements.txt` | Mirror of main `dependencies` for non-editable installs |
| `requirements-dev.txt` | Mirror of main + `dev` extra |
| `requirements-img.txt` | Mirror of `img` extra when that stack exists |

**Validation (process)**: Pins in mirrors MUST match `pyproject.toml` for the
same logical set (FR-010).

## Packaged Modules

Modules included in the distribution (flat):

| Module | Role |
|--------|------|
| `pnp_double_with_profile_pdf` | Main CLI + entry point target |
| `geometry` | Shared geometry helpers |
| `profiles` | Profile load/validation helpers |
| `io_pdf` | PDF I/O helpers |

**Not packaged as console scripts (v1)**: `tools/*` (script-only).

## Install Modes (state)

```text
[clone]
  → pip install -r requirements.txt          → script workflow only
  → pip install -e .                         → package + pnp-double-align + main deps
  → pip install -e ".[dev]"                  → package + tests
  → pip install -e ".[img]"                  → package + image extras (if defined)
```

Editable and requirements workflows MAY coexist in one venv.
