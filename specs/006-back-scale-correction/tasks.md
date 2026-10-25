# Tasks: Back Scale Correction

## Phase 1: Tests first

- [x] T001 [US1] Vector matrix: scale keeps the centre fixed, scales distances,
      default 1.0 is identity, rotation is applied before scale.
- [x] T002 [US1] Raster: scale keeps a centred mark centred and fills white.
- [x] T003 [US1] Profile: scale defaults to 1.0, invalid / out-of-range raises,
      CLI overrides.
- [x] T004 [US1] CLI: vector and raster outputs place a scaled back at the same
      position; `--scalex` override reported in the summary.
- [x] T005 [US2] Calibration: affine fit recovers rotation, scale and shift;
      round trip with scale < 0.01 mm; refine multiplies scales; solver
      `--fit-scale` writes scale keys and omits them otherwise.

## Phase 2: Implementation

- [x] T006 [US1] `geometry.build_back_matrix(..., scale_x, scale_y)`.
- [x] T007 [US1] `profiles.py` validation and overrides.
- [x] T008 [US1] Main CLI (vector + raster) and batch pass-through.
- [x] T009 [US2] `calibration.py` fit/mapping/refine with scale; solver flag.

## Phase 3: Documentation

- [x] T010 Calibration guide (paper shrink, contour check, `--fit-scale`),
      README, tools/README, base profile template.
