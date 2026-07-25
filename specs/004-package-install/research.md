# Research: Installable Package Alongside Scripts

**Feature**: `004-package-install`  
**Date**: 2026-07-25  
**Related**: [spec.md](./spec.md), [plan.md](./plan.md)

## R1 — Layout: flat py-modules vs src/ package

**Decision**: Keep the current flat repository layout. Use setuptools
`py-modules` to ship `pnp_double_with_profile_pdf`, `geometry`, `profiles`, and
`io_pdf`. Do not migrate to `src/pnp_doubleside_aligner/` in this feature.

**Rationale**: Spec Assumptions prefer the smallest packaging change; constitution
Practical Simplicity and feature `001` already rejected a package platform for
remediation. Flat modules preserve `python pnp_double_with_profile_pdf.py` from
repo root without shim files.

**Alternatives considered**:
- `src/` layout with moved modules — cleaner long-term imports, but larger
  churn and risk to tests/`PYTHONPATH=.`; deferred.
- Namespace package wrapping without moving files — extra indirection for little
  gain while scripts stay at root.

## R2 — Build backend and entry point

**Decision**:
- Build system: `setuptools>=61` + `wheel` (PEP 517/`pyproject.toml` only; no
  `setup.py` required).
- Distribution name: `pnp-doubleside-aligner` (matches repo).
- Import/module names: unchanged underscore modules.
- Console script: `pnp-double-align = pnp_double_with_profile_pdf:main`
- Also document `python -m pnp_double_with_profile_pdf` after install (module
  remains executable via existing `if __name__ == "__main__"`).

**Rationale**: FR-002; `main()` already exists; one clear command name for PATH.

**Alternatives considered**:
- Hatchling/poetry — fine tools, but setuptools is ubiquitous and enough here.
- Multiple console scripts for every `tools/` helper — out of scope (spec:
  tools may stay script-only in v1).

## R3 — Dual dependency sources (pyproject vs requirements*.txt)

**Decision**:
- **`pyproject.toml` `[project].dependencies`** is authoritative for
  **package / editable** installs.
- **`requirements.txt`** remains a **pinned convenience mirror** of those main
  deps (same versions), with a header comment: keep in sync with pyproject.
- **`requirements-dev.txt`** keeps `-r requirements.txt` + pytest pin; mirror
  `[project.optional-dependencies] dev`.
- CI: prefer `python -m pip install -e ".[dev]"` so editable install is
  continuously exercised; keep `cache-dependency-path` including
  `pyproject.toml` and requirements files. Alternatively CI may install
  requirements-dev **and** `pip install -e .` without deps if needed—choose
  single path: **`-e ".[dev]"`** as primary.

**Rationale**: FR-003, FR-010; hobbyists can still `pip install -r`; packagers
get metadata.

**Alternatives considered**:
- Delete requirements files — breaks FR-003 / existing docs muscle memory.
- Dynamic reading of requirements from pyproject only — nicer later; mirror
  comments are enough for MVP.

## R4 — Optional extras

**Decision**:
- `dev = ["pytest==7.4.4"]` (match current pin).
- `img`: if `requirements-img.txt` exists from feature `003`, declare the same
  pins under `[project.optional-dependencies] img` and document
  `pip install -e ".[img]"`. If `003` is not implemented yet, omit `img` extra
  and point docs at `requirements-img.txt` when it appears—do not invent
  unpinned OpenCV deps here.
- Default install NEVER includes image extras.

**Rationale**: FR-005; coordinate with `003` without blocking `004`.

**Alternatives considered**:
- Force img into main dependencies — rejected by spec.

## R5 — What not to package

**Decision**: Exclude from the wheel/editable install payload: `tests/`,
`specs/`, `.specify/`, `.venv/`, personal/generated PDFs, and do not ship
`profiles/my_*.json` or non-example profiles as package data. Example profiles
may remain in the git tree for scripts; they need not be installed as package
data for CLI to work (user passes `--profile` paths).

**Rationale**: Repository hygiene; CLI takes explicit paths.

**Alternatives considered**:
- Install `profiles/example_printer.json` as package data — optional nicety;
  skip for MVP to avoid path complexity.

## R6 — Versioning

**Decision**: Start packaged version at `0.1.0` in `pyproject.toml` (first
installable distribution). Single source of version for packaging; scripts need
not print version unless already supported.

**Rationale**: Clear first packaged release without claiming 1.0 API stability.

**Alternatives considered**:
- `1.0.0` immediately — fine later; 0.1.0 signals “newly packaged.”

## R7 — Tests

**Decision**: Add a small smoke that assumes the package is installed in the
active env (CI after `-e ".[dev]"`): run `pnp-double-align --help` via
subprocess and expect exit 0. Loose-script path remains covered by existing
tests invoking `pnp_double_with_profile_pdf.py`. No geometry golden changes.

**Rationale**: SC-001/SC-002; packaging must not break characterization.

## Resolved clarifications

No Technical Context `NEEDS CLARIFICATION` items remain.
