# Research: Codebase Quality Remediation

**Feature**: `001-codebase-quality`  
**Date**: 2026-07-25  
**Inputs**: [spec.md](./spec.md), [constitution.md](../../.specify/memory/constitution.md), code audit of `pnp_double_with_profile_pdf.py` / `tools/`

## R1 — Preferred-path (vector) transform application

**Decision**: Build rotation with positional `fitz.Matrix(degrees)` (not
`fitz.Matrix(rotation=…)`). Do **not** rely on `Page.show_pdf_page(..., matrix=)`
to move content — that kwarg is not part of the documented apply path and does
not shift/rotate placement on verified PyMuPDF 1.23.x. Apply corrections via an
API that actually transforms page content (e.g. insert with explicit morph /
transform of the source page into the destination rect, or equivalent
documented MuPDF placement that honors translation + rotation about page
center). Characterization must assert shift-only backs differ from identity.

**Rationale**: Current `build_back_matrix` raises `TypeError` on keyword
`rotation=`; shift-only builds a matrix that is then ignored → silent success
with identity output. Constitution VI + FR-001/FR-003 require real application.

**Alternatives considered**:
- Pin an older PyMuPDF that accepted `rotation=` — fragile; still leaves
  ignored `matrix=` on `show_pdf_page`.
- Always force raster — violates Vector-First (constitution IV).
- Freeze silent no-op as golden — rejected by spec assumption (assert desired
  contract).

## R2 — Automatic fallback exception types

**Decision**: Catch `(TypeError, RuntimeError, OSError, ValueError)` (and any
library-specific errors that actually exist on the pinned PyMuPDF). Remove
references to non-existent `fitz.FitzError`. On recoverable preferred-path
failure in `--mode auto`, print an explanatory message on **stderr** and call
`raster_fallback`.

**Rationale**: Evaluating `except (fitz.FitzError, …)` raises `AttributeError`
before the handler can run, blocking fallback. `TypeError` from Matrix is not
caught today.

**Alternatives considered**:
- Broad bare `except Exception` — works but hides programmer errors; prefer
  explicit recoverable set plus re-raise unexpected after logging if needed.
- Fail closed (no fallback) — worse UX; product already documents auto mode.

## R3 — Sign conventions (vector vs raster vs docs)

**Decision**: Single contract from `docs/calibration_guide.md`:
- positive rotation = **clockwise**
- positive X = move back **right**
- positive Y = move back **downward** (as printed)

Raster path: negate angle for PIL `Image.rotate` (PIL is counter-clockwise).
ReportLab placement: convert +Y-down into canvas coordinates (origin
bottom-left) by placing at `y = -shift_y_pt` (or equivalent). Vector path must
use the same semantic signs. Both paths covered by characterization.

**Rationale**: Audit shows PIL and ReportLab disagree with the published
contract and with each other relative to intent.

**Alternatives considered**:
- Change the calibration guide to match current PIL/ReportLab — breaks
  existing profile documentation and user mental model; rejected.
- Only fix vector and leave raster — FR-003 requires both paths.

## R4 — Profile defaults and missing path

**Decision**: When no `--profile` and no CLI correction overrides are supplied,
`back_corrections` MUST be identity (`extra_rot_deg=0`, `shift_x_mm=0`,
`shift_y_mm=0`). If `--profile` is set to a path that does not exist → actionable
error on stderr and non-zero exit (no silent sample merge). Missing keys inside
a valid profile → identity for those axes only.

**Rationale**: Embedded sample `0.30` / `1.0` undermines Calibration-Profile
First and FR-005/FR-006.

**Alternatives considered**:
- Keep sample defaults with a loud warning — still surprising; identity is
  clearer.
- Warning-only on missing path — allowed by FR-006 wording, but **error** is
  chosen for honesty (user asked for a profile and did not get it).

## R5 — Expected CLI failure UX

**Decision**: Wrap profile JSON load and PDF open in handlers that map
`JSONDecodeError`, comment-bearing / invalid JSON, and missing/unreadable PDFs
to stderr messages + non-zero exit. Raw tracebacks MUST NOT be the default
primary UX for these expected modes. Mention that runtime profiles must be
valid JSON and that comment templates must be copied/stripped.

**Rationale**: Constitution II + FR-007/FR-008.

**Alternatives considered**:
- Depend on argparse alone — does not cover JSON/PDF open failures.

## R6 — `--on-odd warn`

**Decision**: When `order=fronts_then_backs` and page count is odd and
`--on-odd warn`, emit a warning on stderr and continue with the documented
classification rule (same effective total as today for `warn`: no add/drop).
Document uneven half-split behavior in tests.

**Rationale**: Flag exists but is a no-op; FR-009.

**Alternatives considered**:
- Make `warn` imply `drop_last` — would change behavior beyond emitting a
  warning; out of scope unless docs change intentionally.

## R7 — Batch `--auto-detect-smart`

**Decision**: **Disable** with a clear user-facing error (stderr + non-zero
exit) stating the feature is unavailable/experimental. Do not implement
`avg_sim_block` in the first delivery slice. Propagate non-zero worker
subprocess exits to the batch process exit status.

**Rationale**: Undefined `avg_sim_block` crashes (FR-013). Implementing visual
similarity is larger scope than P1 correctness; Practical Simplicity favors
honest disablement.

**Alternatives considered**:
- Implement smart detect fully — deferred; can be a later feature.
- Silent skip of the flag — less honest than an explicit error.

## R8 — Safe-save policy

**Decision**: Both vector and raster writers use the same policy: prefer
distinct input/output paths; when same-path is allowed, write via temporary
file then `os.replace` (with copy fallback if replace fails), matching current
vector `safe_save`. Remove raster’s rename-to-`*_aligned.pdf` + direct write
divergence unless docs intentionally keep a different user-visible name — unify
to documented behavior.

**Rationale**: FR-014; inconsistent writers risk partial outputs.

**Alternatives considered**:
- Document two policies — harder for users; rejected for this remediation.

## R9 — Testing stack

**Decision**: Add `pytest` as a **dev-only** dependency (`requirements-dev.txt`).
Pin main runtime stack in `requirements.txt`. Characterization asserts the
**desired** contract (failing on known bugs), not buggy goldens.

**Rationale**: No suite exists; constitution Development Workflow requires
characterization before transform refactors; FR-011.

**Alternatives considered**:
- unittest stdlib only — viable but pytest is simpler for fixtures/parametrize
  and is a one-line approved Complexity Tracking exception.
- Snapshot entire PDFs as goldens before fixes — would lock defects; rejected.

## R10 — Module extraction timing

**Decision**: Phase 1–2 keep the monolito importable for tests. Phase 3 extracts
sibling modules `geometry.py` and `profiles.py` (optional thin I/O helper). No
`src/` package platform.

**Rationale**: Characterization-first; Separation of Concerns without violating
Practical Simplicity.

**Alternatives considered**:
- Extract modules before any tests — higher regression risk.
- Full package layout — unjustified for this utility.

## R11 — Optional image workflow

**Decision**: Leave `tools/pnp_double_with_profile_img.py` experimental; document
extra deps or mark out of first delivery. Must not replace
`pnp_double_with_profile_pdf.py`.

**Rationale**: Undeclared cv2/numpy/fpdf stack conflicts with constitution V;
spec Assumptions allow deferral.

**Alternatives considered**:
- Port image tool to constitution stack in this feature — expands scope.

## Resolved clarifications

All Technical Context items are resolved; no remaining NEEDS CLARIFICATION
markers for this plan.
