# Feature Specification: Back Scale Correction

**Feature Branch**: `006-back-scale-correction`

**Created**: 2026-10-25

**Status**: Draft

**Input**: User description: "Tras calibrar giro y desplazamiento, en una hoja de contornos el borde izquierdo coincide pero el desfase crece hacia la derecha hasta 0,5–1 mm: la trasera sale ~0,4 % más ancha. Añadir corrección de escala al aligner."

## Context

With manual duplex on a laser printer, the paper goes through the fuser for
the front, loses moisture and shrinks slightly (mostly across the grain). The
back is printed at nominal size on the shrunk sheet, so relative to the front
it comes out slightly larger. A rigid correction (rotation + shift) can only
spread that error: on an A4 card grid a 0.4 % horizontal scale difference
leaves ~0.8 mm between the leftmost and rightmost columns.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct a back that prints larger or smaller (Priority: P1)

A user adds `scale_x` / `scale_y` factors to the profile `back_corrections`;
the aligner scales the backs about the page centre (vector and raster paths)
so that front and back match across the whole sheet.

**Independent Test**: A back with `scale_x = 0.996` keeps the page centre fixed
and brings points 100 mm from the centre 0.4 mm closer; vector and raster
place content at the same position.

**Acceptance Scenarios**:

1. **Given** a profile without scale keys, **When** the aligner runs, **Then**
   the output is identical to before this feature (goldens unchanged).
2. **Given** `scale_x`/`scale_y` in the profile (or `--scalex/--scaley` on the
   CLI), **When** the aligner runs, **Then** backs are scaled about the page
   centre, after the rotation and before the 180° turn and the shift.
3. **Given** a non-numeric or out-of-range scale (outside 0.9–1.1), **When** the
   profile is loaded, **Then** a clear error is reported.

### User Story 2 - Measure the scale during calibration (Priority: P1)

The solver can fit the scale together with rotation and shift from the sheet
readings (`--fit-scale`), and refine an existing profile's scale.

**Independent Test**: Simulated printer error with rotation, shift and
anisotropic scale → readings → solver with `--fit-scale` → aligner geometry →
residual < 0.01 mm.

**Acceptance Scenarios**:

1. **Given** readings and `--fit-scale`, **When** the solver runs, **Then** the
   profile includes `scale_x`/`scale_y` that cancel the measured scale.
2. **Given** `--refine` with `--fit-scale`, **When** the solver runs, **Then**
   scales are multiplied and other corrections added.
3. **Given** no `--fit-scale`, **When** the solver runs, **Then** its output is
   unchanged (rigid fit, no scale keys).

## Requirements *(mandatory)*

- **FR-001**: `back_corrections.scale_x` / `scale_y` (optional, default 1.0,
  valid range 0.9–1.1) in the profile schema.
- **FR-002**: Vector and raster paths apply the same transform order:
  rotation → scale → optional 180° → shift, all about the page centre.
- **FR-003**: `--scalex` / `--scaley` CLI overrides in the main aligner and the
  batch tool.
- **FR-004**: `calibration.fit_readings(..., fit_scale=True)` fits an affine
  model and decomposes it into rotation and axis scales; the mapping to back
  corrections is exact for the rotation·scale·shift printer model.
- **FR-005**: Docs (calibration guide, README, base profile template) describe
  the scale correction and when to use it.
- **FR-006**: The experimental image tool ignores scale (documented).

## Success Criteria *(mandatory)*

- **SC-001**: Round trip with up to ±1°, ±5 mm and ±1 % scale per axis leaves a
  residual < 0.01 mm at every target.
- **SC-002**: Existing goldens and tests pass unchanged.
