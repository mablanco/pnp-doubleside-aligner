# Tasks: Direct-Read Duplex Calibration

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/calibration-cli.md](contracts/calibration-cli.md)

## Phase 1: Tests first (must fail before implementation)

- [x] T001 [US1] `tests/unit/test_calibration.py`: targets per orientation/paper,
      fit recovers a synthetic rotation + shift, per-point residuals, mapping to
      profile fields, refine is additive.
- [x] T002 [US1] Geometric round-trip in `tests/unit/test_calibration.py`: simulated
      printer error → readings → solver → `build_back_matrix` → residual < 0.01 mm
      (portrait and landscape).
- [x] T003 [US1][US2] `tests/integration/test_calibration_solver_cli.py`: help,
      required readings, output/`-`/`--force`, `--refine`, missing base profile,
      residual warning.
- [x] T004 [US1][US3] `tests/integration/test_calibration_sheets_cli.py`: sheet and
      margin page sizes/page counts, default names, `--force`.
- [x] T005 Remove `tests/unit/test_calibration_solver.py` (characterised the old,
      wrong skew formula).

## Phase 2: Implementation

- [x] T006 [US1] `calibration.py` pure module; add to `pyproject.toml` py-modules.
- [x] T007 [US1] Rewrite `tools/pnp_calibration_sheet_duplex.py`.
- [x] T008 [US1][US2] Rewrite `tools/pnp_calibration_solver.py`.
- [x] T009 [US3] Add `tools/pnp_margin_test_page.py`.

## Phase 3: Documentation

- [x] T010 Rewrite `docs/calibration_guide.md` (margins → calibration → verify/refine,
      print dialog settings, flip mode per orientation).
- [x] T011 Update `README.md` calibration section and `tools/README.md`.
- [x] T012 Clarify `flip_mode` in `profiles/base_printer_profile.json` comments.
