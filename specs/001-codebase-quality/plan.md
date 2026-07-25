# Implementation Plan: Codebase Quality Remediation

**Branch**: `001-codebase-quality` | **Date**: 2026-07-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-codebase-quality/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. Project
overrides live in `.specify/templates/overrides/` (stock templates are restored
locally by `specify init` and are not committed).

## Summary

Remediate the existing PnP duplex aligner so documented calibration behavior is
trustworthy: characterization tests lock the **desired** geometric/profile
contract (failing on known bugs), critical defects in vector transforms,
fallback, signs, profiles, and CLI errors are fixed next, then a minimal
separation-of-concerns refactor plus typing/docs/deps cleanup. Work proceeds in
three consecutive phases; no geometric change without a failing-then-passing
check. Optional image-tool stack rewrite is deferred and labeled experimental.

## Technical Context

**Language/Version**: Python 3.9+

**Primary Dependencies**: PyMuPDF (`fitz`), ReportLab, Pillow (main workflow).
Dev-only: `pytest`. No new runtime dependencies for the main CLI.

**Storage**: N/A (local filesystem: input/output PDFs, JSON calibration profiles)

**Testing**: `pytest` with unit tests (pure geometry/profile/page-order) and
integration/CLI tests (vector/raster paths, stderr, exit codes). Fixtures under
`tests/fixtures/`.

**Target Platform**: Linux/macOS/Windows CLI (hobbyist maker workstations)

**Project Type**: Flat CLI / scripts repository (single main entrypoint + `tools/`)

**Performance Goals**: Prefer vector path; rasterize only on fallback or explicit
`--mode raster`. No deep throughput optimization in this feature.

**Constraints**:
- Zero silent geometric drift (constitution VI)
- Characterization-first before transform/profile/page-order changes
- Identity defaults without profile; actionable stderr for expected failures
- Distinct in/out paths preferred; unified safe temp-replace when same-path allowed
- Python 3.9+ typing on new/substantially edited code

**Scale/Scope**: One main script (~570 LOC) + four tools; remediation covers P1
correctness first, then structure/docs/deps (P2–P3). Image-tool OpenCV/FPDF
rewrite out of first delivery slice.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Existing baseline | PASS | Intentional contract fixes only (identity defaults, signs, errors); called out in spec Current vs Desired |
| Calibration-Profile First | PASS | Profiles remain primary; remove silent sample skew |
| CLI-First + clear errors | PASS | Actionable stderr; no GUI |
| Back-Page Corrections Only | PASS | Characterization + fixes enforce fronts unmodified |
| Vector-First | PASS | Fix preferred path; honest raster fallback |
| Practical Simplicity | PASS | Stay on approved stack; pytest is dev-only |
| Geometric Precision | PASS | Contract tests before/after transform fixes |
| Separation of Concerns | PASS | Deferred to Phase 3 after suite green |
| Repository hygiene | PASS | No secrets/personal profiles/generated PDFs in commits |
| Safe I/O & docs | PASS | Unify safe-save; update README/calibration when behavior changes |

**Post-design re-check**: PASS — design extracts pure modules only after
characterization + bug fixes; contracts encode CLI/profile/geometry without
introducing frameworks or extra runtime deps.

## Incremental Remediation Strategy (mandatory phases)

Work MUST proceed in this order. Later phases MUST NOT start until the prior
phase exit gate is met.

### Phase 1: Characterization Tests (Safety Net)

**Goal**: Executable suite that documents the **desired** documented contract
(`docs/calibration_guide.md` + spec FR/US). Known defects fail today; already-
correct behavior (e.g. `mm_to_pt`, even-page classification) stays green.
Do **not** freeze buggy golden outputs (silent no-op shifts, sample 0.30°/1 mm
defaults). Product logic stays unchanged except minimal harness (`requirements*`,
`tests/` layout).

**Harness**:
- `requirements.txt` — pinned main stack (PyMuPDF, Pillow, ReportLab)
- `requirements-dev.txt` — `pytest`
- `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- Import from monolito `pnp_double_with_profile_pdf.py` (no premature split)

**Unit targets**: `mm_to_pt`; `is_back_page` / `effective_total` (all orders +
odd policies); `load_profile(None)` → identity; missing/invalid/comment profile
paths; `build_back_matrix` PyMuPDF-compatible construction; raster sign helpers
(+rot clockwise, +Y downward).

**Integration/CLI targets**: vector shift-only backs ≠ identity, fronts identity;
auto fallback + stderr; missing PDF/profile/invalid JSON UX; `--on-odd warn`;
batch `--auto-detect-smart` must not `NameError` (clear disable message).

**Exit gate**: `pytest` runs; failures only map to known audited defects (P1);
correct cases green.

### Phase 2: Critical Bug Fixes

**Goal**: Make P1 acceptance / SC-001–SC-003 pass without structural refactor.

Fix order (severity):
1. Vector transforms — valid PyMuPDF matrix/placement API (no ignored `matrix=`
   on `show_pdf_page`; no `fitz.Matrix(rotation=…)`)
2. Auto fallback — catch real errors (`TypeError`, `RuntimeError`, I/O); remove
   `fitz.FitzError`; stderr notice + `raster_fallback`
3. Raster signs — align PIL rotate and ReportLab Y with calibration guide
4. Profile contract — identity defaults; missing path = error (or explicit
   documented warning); invalid/comment JSON = actionable message
5. Expected I/O failures — missing/unreadable PDF → message + non-zero exit
6. `--on-odd warn` — emit stderr warning for odd `fronts_then_backs`
7. Batch smart detect — **disable with clear message** + propagate worker exits
8. Safe-save — unify raster with vector temp-replace policy

**Out of slice**: rewrite of `tools/pnp_double_with_profile_img.py` OpenCV/FPDF
stack — mark experimental / optional deps; does not replace main entrypoint.

**Exit gate**: characterization suite green for P1; docs signs aligned if needed.

### Phase 3: Refactoring & Technical Debt

**Goal**: Separation of concerns and maintainability **only after** Phase 2 green.

1. Extract pure modules (sibling to entrypoint): e.g. `geometry.py` (units,
   signs, page classification), `profiles.py` (load/validate/merge); keep CLI +
   writers in entrypoint or thin `io_pdf.py`
2. Share rules with in-scope tools or explicitly defer with docs
3. Static typing on new/edited code (Python 3.9+ `typing`)
4. Docs: README Features true; `tools/README.md` lists real scripts; calibration
   guide coherent
5. Tracked dependency install path; img extras separated or deferred
6. Cleanup duplication (`load_profile`), dead paths; no premature optimization
   beyond preferring vector

**Exit gate**: same suite green; SC-005–SC-007; constitution scorecard at Desired.

```text
Audit Current vs Desired
        │
        ▼
 Phase 1 Characterization ──failing contract tests──► Phase 2 Critical bugs
                                                              │
                                                              ▼ suite green P1
                                                     Phase 3 Refactor / debt
                                                              │
                                                              ▼ suite stays green
                                                     Docs / deps / typing / SoC
```

## Project Structure

### Documentation (this feature)

```text
specs/001-codebase-quality/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli-contract.md
│   └── profile-schema.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
pnp_double_with_profile_pdf.py   # main entrypoint (Phase 1–2); thin CLI after Phase 3
geometry.py                      # Phase 3: units, page-order, sign/matrix helpers
profiles.py                      # Phase 3: load / validate / merge profiles
# optional thin writer helper if needed:
# io_pdf.py
tools/                           # optional / experimental helpers
profiles/                        # printer calibration JSON (examples only tracked)
docs/                            # calibration and operator docs
requirements.txt                 # Phase 1 harness: pinned main stack
requirements-dev.txt             # Phase 1 harness: pytest
tests/
├── unit/
├── integration/
└── fixtures/
```

**Structure Decision**: Keep the flat CLI layout. Phase 1–2 work inside the
existing monolith + new `tests/` and dependency files. Phase 3 extracts 2–3
sibling modules (not a `src/` package platform) justified by FR-012 /
Separation of Concerns. Experimental tools remain under `tools/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dev dependency `pytest` (+ `requirements-dev.txt`) | FR-011 / constitution characterization-first; no suite exists today | Manual-only verification cannot gate AI-assisted geometric fixes |
| Sibling module extraction (`geometry.py`, `profiles.py`) in Phase 3 | FR-012; test pure logic without full PDF I/O; stop duplication drift | Keeping forever-monolith blocks unit tests and shared tool rules |
| Defer img-tool stack (cv2/numpy/fpdf) | Practical Simplicity; constitution default stack | Full rewrite expands scope beyond P1 correctness |

## Phase Mapping to Spec

| Plan phase | User stories | Key FRs / SCs |
|------------|--------------|---------------|
| 1 Characterization | US3 (and fixtures for US1–2,4) | FR-011; enables SC-001/SC-004 |
| 2 Critical bugs | US1, US2, US4 (warn), US6 (safe-save) | FR-001–010, FR-013–014; SC-001–SC-003, SC-006 |
| 3 Refactor / debt | US5, US6 (deps), docs/typing | FR-012, FR-015–020; SC-005–SC-007 |
