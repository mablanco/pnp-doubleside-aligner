# Implementation Plan: Experimental Image Tool Stack

**Branch**: `003-image-tool-stack` | **Date**: 2026-07-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-image-tool-stack/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. Project
overrides live in `.specify/templates/overrides/` (stock templates are restored
locally by `specify init` and are not committed).

## Summary

Make the experimental image PnP tool (`tools/pnp_double_with_profile_img.py`)
honestly installable and invocable without touching the main PDF aligner
contract. Publish a **separate optional dependency file** pinning OpenCV,
NumPy, and FPDF; **keep that stack** for crop template-matching (research R1);
rewrite the script into a CLI-first experimental tool (no hardcoded personal
paths as the only interface), with actionable missing-deps / I/O / profile
errors, backs-only corrections, and docs that keep the tool labeled
experimental. Main `requirements.txt` and PDF characterization suite stay the
gate for ordinary users.

## Technical Context

**Language/Version**: Python 3.9+

**Primary Dependencies (main / unchanged)**: PyMuPDF, ReportLab, Pillow via
`requirements.txt`.

**Optional Dependencies (image tool only)**: OpenCV (`opencv-python-headless`
preferred), NumPy, `fpdf2` (FPDF), listed in a new optional requirements file
(e.g. `requirements-img.txt`). Not pulled in by `requirements.txt` or
`requirements-dev.txt`.

**Storage**: N/A (local PNG/JPG inputs, JSON profile, output PDF)

**Testing**: `pytest` — (1) missing-extras messaging without installing OpenCV
in default CI; (2) optional/skipped happy-path smoke when extras present
(`pytest.importorskip` or marker); main `tests/` PDF suite must stay green
without image extras.

**Target Platform**: Linux/macOS/Windows CLI (hobbyist workstations)

**Project Type**: Flat CLI / scripts (`tools/` experimental helper)

**Performance Goals**: Small fixture image→PDF run under a few minutes
operator time (SC-002); no throughput optimization.

**Constraints**:
- Zero intentional change to main PDF CLI/geometry contract (FR-009)
- Image extras MUST NOT become mandatory on the main install path (FR-001–002)
- Experimental label retained (FR-010)
- Constitution Complexity Tracking for optional OpenCV/FPDF (justified below)
- Profile runtime JSON rules aligned with project (no comment-bearing templates)

**Scale/Scope**: One experimental script + optional requirements file + docs +
minimal tests/fixtures under `tests/fixtures/img/` (or similar). No main
entrypoint rewrite.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Existing baseline | PASS | Image tool already experimental; main PDF baseline preserved |
| Calibration-Profile First | PASS | Tool continues to consume JSON printer profiles for back corrections |
| CLI-First + clear errors | PASS | Plan adds argparse CLI + actionable stderr for expected failures |
| Back-Page Corrections Only | PASS | Fronts unmodified; backs get rot/shift/flip from profile |
| Vector-First | N/A → PASS | Image path is inherently raster; does not change PDF vector preference |
| Practical Simplicity | PASS w/ tracking | Optional OpenCV/FPDF only for this tool; not main stack (see Complexity Tracking) |
| Geometric Precision | PASS | No changes to main PDF transforms; image-tool signs should match calibration docs |
| Separation of Concerns | PASS | Keep load/validate profile, crop math, and PDF emit separable where cheap |
| Repository hygiene | PASS | No personal paths in tracked defaults; fixtures only under tests |
| Safe I/O & docs | PASS | Distinct output path via CLI; update tools/README (+ README pointer) |

**Post-design re-check**: PASS — optional deps file + CLI contract isolate extras;
main requirements and PDF tests remain authoritative; Complexity Tracking
records why OpenCV/FPDF stay for this experimental tool only.

## Incremental Delivery Strategy

### Phase A — Packaging & docs boundary

**Goal**: Optional deps exist; main install path unchanged; docs describe extras.

**Includes**: `requirements-img.txt` (pinned); README / `tools/README.md` install
notes; assert `requirements.txt` / `requirements-dev.txt` do not include
cv2/fpdf/numpy as required.

**Exit gate**: Doc + file review; main `pip install -r requirements.txt` still
sufficient for PDF workflow.

### Phase B — Characterization / failure UX tests

**Goal**: Tests encode missing-extras and (when available) smoke expectations.

**Includes**: Test that running the tool without extras yields install hint +
≠0; optional marked test for happy path; tiny fixtures (or generate in test).

**Exit gate**: Missing-extras test fails until import guard exists; PDF suite
still passes without img extras.

### Phase C — Script rewrite (CLI + errors + keep OpenCV/FPDF)

**Goal**: Documented CLI; remove hardcoded-only UX; preserve crop + profile
backs behavior; safe/explicit output path.

**Includes**: argparse for profile, ref original/crop, fronts, backs, output;
lazy/guarded imports with install hint; profile JSON validation messages;
pairing rules (backs optional → duplicate front, documented); paper size from
profile (fix A4-hardcode mismatch if profile differs); keep experimental banner.

**Exit gate**: CLI smoke with extras; missing-extras test passes; main pytest
green without extras.

### Phase D — Docs polish

**Goal**: SC-004/SC-005; tools docs list flags, extras install, experimental
warning, “prefer main PDF”.

**Exit gate**: [quickstart.md](./quickstart.md) passes.

## Project Structure

### Documentation (this feature)

```text
specs/003-image-tool-stack/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── image-tool-cli.md
└── tasks.md             # /speckit-tasks — not created here
```

### Source Code (repository root)

```text
requirements.txt                 # unchanged main PDF stack
requirements-dev.txt             # unchanged; does NOT pull image extras
requirements-img.txt             # NEW: optional OpenCV/NumPy/fpdf2 pins
tools/pnp_double_with_profile_img.py   # CLI rewrite; experimental
tools/README.md                  # install + invocation
README.md                        # pointer: optional image extras
tests/fixtures/img/              # small PNG fixtures for smoke (optional CI)
tests/integration/test_img_tool_*.py
# pnp_double_with_profile_pdf.py — DO NOT change for this feature
```

**Structure Decision**: Stay flat CLI/`tools/`. No new package layout. Optional
deps file at repo root next to existing requirements files.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Optional OpenCV + NumPy + FPDF outside constitution default stack | Crop uses edge template matching (`matchTemplate` / Canny); current tool’s core value depends on it | Porting crop to Pillow-only loses reliable template matching without a larger R&D slice; dropping crop removes the tool’s reason to exist; putting OpenCV in `requirements.txt` would force every PDF user to install heavy extras (violates FR-002 / “menos impacto”) |
