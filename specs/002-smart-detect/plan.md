# Implementation Plan: Reliable Batch Smart Page-Order Detect

**Branch**: `002-smart-detect` | **Date**: 2026-07-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-smart-detect/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. Project
overrides live in `.specify/templates/overrides/` (stock templates are restored
locally by `specify init` and are not committed).

## Summary

Re-enable `tools/pnp_batch_align.py --auto-detect-smart` so mixed PnP folders
get a reliable per-file page-order decision (name hint → page-count →
content-based → even-default fallback) instead of the intentional “unavailable”
exit from feature `001`. Complete the unfinished visual pipeline by implementing
the missing block-similarity helper, **replace** the old pair-vs-halves decision
predicate with a PnP-oriented common-back cluster rule (still using existing
low-res fingerprints + cosine similarity, no new dependencies), add fixture
coverage for all modes, flip the disable-oriented integration test to an
enablement contract, and update `tools/README.md`. Detection only chooses
`--order` for the existing worker; it does not transform pages.

## Technical Context

**Language/Version**: Python 3.9+

**Primary Dependencies**: Existing batch stack only — PyMuPDF (`fitz`), Pillow.
No new runtime dependencies. Dev: `pytest` (already present).

**Storage**: N/A (local PDFs under `--input-dir` / `--output-dir`; fixtures under
`tests/fixtures/`)

**Testing**: `pytest` unit tests for pure decision helpers (name hint, page-count,
similarity decision, `avg_sim_block`) and integration/CLI tests for
`--auto-detect-smart` on a fixture folder (stdout order+reason, no disable
refusal, worker still invoked with chosen `--order`).

**Target Platform**: Linux/macOS/Windows CLI (hobbyist maker workstations)

**Project Type**: Flat CLI / scripts repository (optional tool under `tools/`)

**Performance Goals**: Content-based detection under 30s per ≤100-page PDF on a
typical desktop; use low-DPI thumbnails and a documented page-sampling cap when
page count is large (see research R3).

**Constraints**:
- Batch/optional tool only — do not change main CLI `--order` contract (FR-013)
- Detection MUST NOT apply alignment transforms (FR-012); worker remains source of truth
- Zero new deps; Practical Simplicity
- Honest reasons: confident vs fallback/tie vs open-fallback (FR-007–009)
- Characterization-first: fixtures + tests before declaring heuristics “done”
- Keep experimental labeling of the batch tool; flag becomes *available* within it

**Scale/Scope**: One optional script (`tools/pnp_batch_align.py`) + docs + tests;
small fixture PDFs for interleaved, fronts_then_backs, odd/last_back, single-page,
name-hint, and inconclusive even cases.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Existing baseline | PASS | Intentional re-enable of previously disabled flag; main CLI unchanged |
| Calibration-Profile First | PASS | Profiles unchanged; detect only chooses page-order for worker |
| CLI-First + clear errors | PASS | Flag + per-file reason on stdout; open/analysis failures have defined messaging |
| Back-Page Corrections Only | PASS | Order choice feeds worker; fronts still unmodified by aligner |
| Vector-First | PASS | Thumb rasterization is detection-only; worker still prefers vector |
| Practical Simplicity | PASS | Complete/reuse fingerprint path; no new libraries |
| Geometric Precision | PASS | No matrix/transform changes; order misclassification covered by fixtures |
| Separation of Concerns | PASS | Prefer pure helpers for similarity/decision; CLI/batch loop stays thin |
| Repository hygiene | PASS | Fixtures only under `tests/fixtures/`; no personal profiles |
| Safe I/O & docs | PASS | Update `tools/README.md` when flag becomes available |

**Post-design re-check**: PASS — contracts document CLI surface and decision
precedence; sampling and confidence rules stay in-process with existing stack;
main aligner contract untouched.

## Incremental Delivery Strategy

Work MUST proceed in this order.

### Phase A: Characterization & fixtures (Safety Net)

**Goal**: Executable checks that encode the desired smart-detect contract
(including cases that fail while the feature is still disabled).

**Includes**:
- Fixture PDFs: interleaved (reuse), fronts_then_backs, single-page, odd/last_back
  (reuse/adapt), name-hinted copy, inconclusive/ambiguous even PDF
- Unit tests for name hint, page-count rules, `avg_sim_block`, decision thresholds
- Replace `test_batch_smart_detect_disabled` with enablement + classification
  expectations (or add sibling tests and retire disable assertion)

**Exit gate**: Suite fails on current disable-early-exit / missing helper; fixtures
exist for FR-010 cases.

### Phase B: Implement & re-enable

**Goal**: Working `--auto-detect-smart` path meeting SC-001/SC-005 on fixtures.

**Includes**:
- Implement `avg_sim_block`
- Replace pair-vs-halves decision with common-back cluster rule (research R1)
- Remove early `SystemExit` disable gate; restore help text for available flag
- Page-sampling policy for large N (research R3)
- Keep open-fallback / even-default tie behavior with distinct reason strings

**Exit gate**: Smart-detect unit + integration tests pass; disable message gone.

### Phase C: Docs & smoke

**Goal**: Operator-facing docs match reality; quickstart smoke passes.

**Includes**: Update `tools/README.md` (and README tools blurb if it claims disabled);
run [quickstart.md](./quickstart.md).

**Exit gate**: Docs describe available smart detect + precedence; quickstart green.

## Project Structure

### Documentation (this feature)

```text
specs/002-smart-detect/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── batch-smart-detect.md
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
tools/pnp_batch_align.py          # re-enable + complete/replace detect logic
tools/README.md                   # document available smart detect
pnp_double_with_profile_pdf.py    # unchanged worker (order consumer only)
tests/fixtures/                   # add order-layout PDFs for detection
tests/unit/                       # pure detect helpers
tests/integration/                # CLI --auto-detect-smart enablement
tests/conftest.py                 # fixture path helpers as needed
```

**Structure Decision**: Stay on the flat CLI / `tools/` layout. No new package
tree. Pure decision helpers may remain in `pnp_batch_align.py` or move to a
small shared module only if duplication with the main CLI appears—default is
keep in the batch tool to avoid scope creep (Practical Simplicity).

## Complexity Tracking

> No constitution violations requiring justification. Optional note:

| Item | Why Needed | Simpler Alternative Rejected Because |
|------|------------|--------------------------------------|
| Replace decision predicate (not only add `avg_sim_block`) | Old pair-avg ≥ 0.80 → interleaved mismatches typical PnP F/B pairs | Completing only the missing helper would re-enable an unreliable rule and fail SC-005 |
