# Feature Specification: Direct-Read Duplex Calibration

**Feature Branch**: `005-direct-read-calibration`

**Created**: 2026-10-24

**Status**: Draft

**Input**: User description: "La herramienta de calibración que hemos usado (hoja de lectura directa + solver) no está en el repo, así que los usuarios no pueden generar sus perfiles. Sustituir la hoja y el solver actuales."

## Context

A real calibration session (A4, colour laser, KDE/Okular) exposed that the tracked
calibration tooling cannot produce a correct profile:

- `tools/pnp_calibration_sheet_duplex.py` only produces landscape sheets with
  registration crosses that must be measured with a ruler, and the sign of each
  measurement (viewpoint, axis direction) is ambiguous.
- `tools/pnp_calibration_solver.py` estimates skew as
  `(dx_br − dx_bl) − (dx_tr − dx_tl)`, which is **zero for a pure rotation**.
- Nothing explains that the measurement viewpoint (front) differs from the
  correction space (back page, mirrored in X), which flips the sign of X and of
  the rotation but not of Y.
- Driver scaling modes can silently scale or offset the page (e.g. "no scaling"
  offset the page by the 4.23 mm declared margin), invalidating any
  calibration. There is no tool to detect it.

A direct-read sheet plus a matching solver produced a verified profile in two
prints (calibration + verification) for both orientations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Calibrate a printer without measuring with a ruler (Priority: P1)

A user generates a calibration sheet for their paper size and orientation,
prints it double-sided without alignment, holds it against a light source from
the front side and reads, at each corner, the number on the back-side scale
crossed by the thick front line. Those numbers are the back offsets (dx, dy) in
millimetres as seen from the front. The solver turns the four readings into a
valid profile.

**Why this priority**: Without it, users cannot create correct profiles.

**Independent Test**: Simulate a printer error (rotation + shift), compute the
readings the sheet would show, run the solver, apply the profile with the
aligner geometry and check the residual offsets are ~0.

**Acceptance Scenarios**:

1. **Given** `--orientation portrait|landscape` and `--paper a4|letter`, **When**
   the user generates a sheet, **Then** a 2-page PDF (front crosses, mirrored
   back scales) of that size is written, and existing files are not
   overwritten without `--force`.
2. **Given** four corner readings, **When** the solver runs, **Then** it writes a
   valid profile (no comments) whose corrections cancel the measured error,
   with `flip_mode: "long"` and the paper size/orientation of the sheet.
3. **Given** the duplex flip mode chosen in the print dialog is wrong, **When**
   the user looks through the sheet, **Then** an orientation witness on the
   back reads upside down.

### User Story 2 - Refine an existing profile with a verification print (Priority: P1)

The user runs the aligner on the calibration sheet with their profile, prints
it, and reads the residual offsets. The solver adds the residual correction to
the existing profile.

**Independent Test**: Base profile + residual readings → new corrections equal
base + residual correction; other profile fields preserved.

**Acceptance Scenarios**:

1. **Given** `--refine PROFILE` and residual readings, **When** the solver runs,
   **Then** the output profile keeps the base profile fields and adds the
   residual rotation and shifts.

### User Story 3 - Detect driver scaling/offset before calibrating (Priority: P2)

The user prints a margin test page (rulers starting at each paper edge, plus
reference lines of known length) to find the scaling mode that prints at 100 %
with no offset, and the real non-printable margin of each edge.

**Acceptance Scenarios**:

1. **Given** `--paper a4|letter`, **When** the user generates the page, **Then**
   a 2-page PDF with edge rulers and 150/200 mm reference lines is written.

### Edge Cases

- Readings inconsistent with a rigid motion (reading mistakes): the solver
  reports per-point fit residuals and warns when the largest exceeds 0.75 mm.
- Optional centre reading: used in the fit and in the residual report.
- Invalid or missing base profile for `--refine`: clear error, exit 1, no
  traceback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `tools/pnp_calibration_sheet_duplex.py` MUST generate a direct-read
  sheet for portrait and landscape, A4 and Letter (replaces the old sheets).
- **FR-002**: Back scales MUST be mirrored in X so they read correctly from the
  front through the paper, and labelled so the reading equals the back offset
  (dx > 0 right, dy > 0 down, mm, front view).
- **FR-003**: `tools/pnp_calibration_solver.py` MUST fit rotation + translation
  by least squares to the readings and map them to back-page corrections
  (`extra_rot_deg = φ`, `shift_x_mm = tx`, `shift_y_mm = −ty`).
- **FR-004**: The solver MUST support `--refine PROFILE` (additive residual).
- **FR-005**: `tools/pnp_margin_test_page.py` MUST generate the margin test page.
- **FR-006**: Calibration math MUST live in a pure module without I/O.
- **FR-007**: `docs/calibration_guide.md`, `README.md` and `tools/README.md` MUST
  describe the new procedure (margins → calibration → verification/refine).

### Contract break (intentional)

- The old three-file output of the sheet tool (`PnP_Calibration_Front.pdf`,
  `..._Back_long.pdf`, `..._Back_short.pdf`) is removed.
- Solver readings are now defined as **seen from the front** (as read on the
  new sheet) and the skew estimate changes (the old formula was wrong). The
  `--top-left/--top-right/--bottom-left/--bottom-right/--center`, `--name`,
  `--output`, `--force` flags are kept; `--paper-width/--paper-height/
  --flip-mode` are replaced by `--paper` and `--orientation`.

## Success Criteria *(mandatory)*

- **SC-001**: For any simulated error within ±1° and ±5 mm, sheet readings →
  solver → aligner geometry leaves a residual below 0.01 mm at every target.
- **SC-002**: A user can produce a verified profile with two prints
  (calibration + verification) following only the documentation.
