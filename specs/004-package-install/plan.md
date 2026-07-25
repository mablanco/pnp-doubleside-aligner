# Implementation Plan: Installable Package Alongside Scripts

**Branch**: `004-package-install` | **Date**: 2026-07-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-package-install/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. Project
overrides live in `.specify/templates/overrides/` (stock templates are restored
locally by `specify init` and are not committed).

## Summary

Add `pyproject.toml` so contributors can `pip install -e .` (and
`pip install -e ".[dev]"`) while **keeping** the existing requirements files and
root/script workflows. Package the current flat root modules
(`pnp_double_with_profile_pdf`, `geometry`, `profiles`, `io_pdf`) via setuptools
`py-modules`—no `src/` migration. Expose one console script,
`pnp-double-align`, pointing at `pnp_double_with_profile_pdf:main`. Optional
extras: `dev` (pytest), and `img` only if/when image extras pins exist (else
document `requirements-img.txt`). Update README + CI cache paths; do not change
duplex geometry/profile behavior.

## Technical Context

**Language/Version**: Python 3.9+ (`requires-python = ">=3.9"`)

**Primary Dependencies**: Same pins as today — PyMuPDF==1.23.7, Pillow==10.2.0,
reportlab==4.1.0 (declared in `[project].dependencies`). Build backend:
`setuptools` + `wheel` (PEP 517).

**Storage**: N/A

**Testing**: Existing `pytest` suite; add a thin packaging smoke (editable
install + `pnp-double-align --help` and/or `python -m pnp_double_with_profile_pdf
--help`). CI may switch to `pip install -e ".[dev]"` or keep requirements-dev
with documented sync (research R3).

**Target Platform**: Linux/macOS/Windows developer workstations + GitHub Actions

**Project Type**: Flat CLI / scripts + installable distribution metadata

**Performance Goals**: N/A (packaging only)

**Constraints**:
- Dual support: editable package **and** loose scripts (FR-003)
- No intentional main aligner geometry/profile contract changes (FR-008)
- Image extras not on default install (FR-005)
- Practical Simplicity: no unjustified `src/` package platform
- Local/editable install only; PyPI publish out of scope (spec Assumptions)

**Scale/Scope**: `pyproject.toml` (+ maybe `MANIFEST.in` if needed), README/CI
doc tweaks, minimal smoke test; optional thin `__main__` only if required for
`python -m` ergonomics (module already runnable).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Existing baseline | PASS | Packaging additive; scripts remain |
| Calibration-Profile First | PASS | No profile schema/behavior change |
| CLI-First + clear errors | PASS | New installed CLI name documents same argparse surface |
| Back-Page Corrections Only | PASS | Untouched |
| Vector-First | PASS | Untouched |
| Practical Simplicity | PASS | Flat `py-modules`; no frameworks; setuptools only as packaging means |
| Geometric Precision | PASS | No transform code changes required |
| Separation of Concerns | PASS | Packaging metadata separate from geometry modules |
| Repository hygiene | PASS | Do not package personal profiles/venvs; exclude via setuptools config |
| Safe I/O & docs | PASS | README install dual-path update |

**Post-design re-check**: PASS — contracts define install UX and entry point;
requirements remain convenience mirrors; Complexity Tracking empty (no
constitution violation).

## Incremental Delivery Strategy

### Phase A — Packaging metadata

Add `pyproject.toml` (project metadata, dependencies, optional-dependencies,
scripts, setuptools py-modules / package discovery exclusions). Ensure
`pip install -e .` works from clone root.

### Phase B — Docs + dependency sync policy

README: editable install + `pnp-double-align`; keep requirements/script path.
Comment headers on `requirements*.txt` stating sync with `pyproject.toml`.
Document script-only tools under `tools/`.

### Phase C — CI + smoke

Update CI install and `cache-dependency-path` to include `pyproject.toml`.
Add packaging smoke test or quickstart step. Confirm full `pytest` green and
loose-script invocation still documented/working.

## Project Structure

### Documentation (this feature)

```text
specs/004-package-install/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── packaging-install.md
└── tasks.md             # /speckit-tasks — not created here
```

### Source Code (repository root)

```text
pyproject.toml                 # NEW — packaging metadata + entry point
requirements.txt               # KEEP — convenience mirror of main deps
requirements-dev.txt           # KEEP — convenience (-r requirements + pytest)
requirements-img.txt           # optional / owned by 003 if present
pnp_double_with_profile_pdf.py # unchanged behavior; console script target
geometry.py / profiles.py / io_pdf.py  # packaged as py-modules
tools/                         # script-only (not console_scripts in v1)
README.md                      # dual install docs
.github/workflows/ci.yml       # install/cache may use editable+[dev]
tests/                         # optional packaging smoke
```

**Structure Decision**: Remain flat at repo root. Do **not** introduce a `src/`
layout or rename the main script in this feature. setuptools `py-modules`
lists the four root modules needed for the main aligner.

## Complexity Tracking

> No constitution violations requiring justification. Packaging via
> `pyproject.toml` is explicitly requested and uses the smallest viable layout.
