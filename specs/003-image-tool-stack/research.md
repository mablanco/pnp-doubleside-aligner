# Research: Experimental Image Tool Stack

**Feature**: `003-image-tool-stack`  
**Date**: 2026-07-25  
**Related**: [spec.md](./spec.md), [plan.md](./plan.md)

## R1 — Keep OpenCV/FPDF vs port to constitution stack

**Decision**: **Keep** OpenCV + NumPy + FPDF for the experimental image tool,
declared and pinned in an **optional** requirements file. “Rewrite” means
CLI, error UX, I/O, profile handling, and removal of hardcoded-only
configuration—not replacing the computer-vision crop stack in this feature.

**Rationale**: The tool’s distinctive capability is reference-based relative
crop via edge template matching. That path already uses `cv2`; a Pillow-only
port would weaken or drop it. Spec FR-008 allows retaining the stack with
declared pins. User intent emphasizes experimental + low impact on the main
PDF flow—optional heavy deps achieve that better than forcing a full CV
reimplementation or polluting main requirements.

**Alternatives considered**:
- Port entirely to Pillow + ReportLab — aligns with constitution default stack
  but loses robust template matching without substantial new design; deferred.
- Delete the image tool — rejects user request to declare deps / rewrite.
- Move OpenCV into `requirements.txt` — violates FR-002 and “menos impacto”.

## R2 — Optional dependency file shape

**Decision**: Add `requirements-img.txt` at repo root with pinned:
- `opencv-python-headless` (prefer headless over full GUI OpenCV for CLI/CI)
- `numpy` (compatible pin with chosen OpenCV)
- `fpdf2` (modern PyPI name providing `fpdf` / FPDF API used by the script)
- Pillow already in main requirements; image file may `-r requirements.txt`
  or document “install main + img”. Prefer **img file includes only extras**
  and docs say: install `requirements.txt` then `requirements-img.txt`.

`requirements-dev.txt` continues to `-r requirements.txt` only—**does not**
include image extras so default test installs stay light.

**Rationale**: FR-001–002; clear separation; headless OpenCV avoids GUI deps.

**Alternatives considered**:
- extras in `pyproject.toml` optional-dependencies — repo today uses
  requirements files; stay consistent unless a later packaging feature lands.
- Unpinned “latest” extras — hurts reproducibility (FR-011).

## R3 — CLI surface

**Decision**: Replace hardcoded `PROFILE_PATH` / `REF_*` / `FRONTS` / `BACKS` /
fixed output name with `argparse`:

| Flag | Purpose |
|------|---------|
| `--profile` | Runtime JSON profile (required) |
| `--ref-original` | Reference full screenshot |
| `--ref-crop` | Reference crop patch |
| `--front` | Repeatable front image path (required ≥1) |
| `--back` | Repeatable back image path (optional; index-aligned) |
| `--output` | Output PDF path (required) |
| `--verbose` | Optional progress |

Documented pairing: if back missing for index `i`, duplicate cropped front
(existing behavior) and mention in help/docs. Empty `--front` → error.

**Rationale**: FR-004; CLI-First; removes personal path debt from supported UX.

**Alternatives considered**:
- JSON manifest of images — nicer later; argparse is enough for MVP.
- Keep edit-script config as primary — fails FR-004.

## R4 — Missing extras UX

**Decision**: Guard OpenCV/FPDF imports behind a helper that catches
`ImportError` and prints stderr instructions:

```text
pip install -r requirements-img.txt
```

Exit non-zero. Do not require extras to collect `--help` if practical
(parse args before heavy imports, or catch at start of `main`).

**Rationale**: FR-005, SC-004.

**Alternatives considered**:
- Let raw `ModuleNotFoundError` surface — poorer UX; rejected.

## R5 — Profile & paper handling

**Decision**: Load profile as valid JSON only; on failure, actionable message
(align with main tool messaging style). Use profile paper width/height for
FPDF page format (custom mm size), not a silent always-A4 if profile differs.
Orientation swap when landscape requested and width &lt; height (keep current
intent). Sign conventions for rot/shift: match `docs/calibration_guide.md`
(same as main tool).

**Rationale**: FR-006–007; current script hardcodes `format="A4"` while reading
profile paper sizes—inconsistent.

**Alternatives considered**:
- Force A4 only — simpler but ignores profile paper fields.

## R6 — Testing / CI

**Decision**:
- Default CI / `requirements-dev.txt`: **no** image extras.
- Always-run test: invoke tool (or import guard entry) without cv2 installed
  in that environment → assert install hint + ≠0. Implement via subprocess
  with scrubbed `PYTHONPATH` / documenting that the test mocks ImportError
  if cv2 is present in the developer venv—prefer testing the guard function
  unit-style + one subprocess CLI test.
- Optional: `@pytest.mark.img` happy-path creating minimal PNGs, skipped
  unless `opencv` importable.
- Never make main PDF tests depend on image extras.

**Rationale**: FR-012; SC-003.

**Alternatives considered**:
- Always install OpenCV in CI — heavier, conflicts with “menos impacto”.

## R7 — Docs touchpoints

**Decision**: Update `tools/README.md` (install extras, CLI example,
experimental warning, prefer main PDF). Short pointer in root `README.md`
under optional tools. Script module docstring: experimental + extras file.
No change to calibration guide beyond optional cross-link if signs are cited.

**Rationale**: FR-003, FR-010, SC-005.

## R8 — Out of scope

**Decision**: Do not modify `pnp_double_with_profile_pdf.py` geometry/CLI for
this feature. Do not implement smart-detect or batch changes. Do not promote
image tool to recommended default.

**Rationale**: Spec Assumptions / FR-009; user “menos impacto”.

## Resolved clarifications

No Technical Context `NEEDS CLARIFICATION` items remain; stack, packaging,
CLI, and test strategy are decided above.
