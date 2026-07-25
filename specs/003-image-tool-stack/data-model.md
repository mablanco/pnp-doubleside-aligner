# Data Model: Experimental Image Tool Stack

**Feature**: `003-image-tool-stack`  
**Date**: 2026-07-25  
**Related**: [spec.md](./spec.md), [contracts/image-tool-cli.md](./contracts/image-tool-cli.md)

Logical entities only. No database. Calibration profile field semantics align
with feature `001` / main aligner where consumed.

## Optional Image-Tool Dependency Set

Declared packages required only to run the experimental image tool.

| Package role | Purpose |
|--------------|---------|
| OpenCV (headless) | Read images, edge detect, template match for relative crop |
| NumPy | Array ops used with OpenCV |
| FPDF (`fpdf2`) | Emit multi-page PDF from raster pages |
| Pillow | Rotation / PIL bridge (also on main stack) |

**Rules**:
- Listed in `requirements-img.txt` with pins (FR-011).
- Not required by `requirements.txt` or `requirements-dev.txt` (FR-002).
- Missing set → tool refuses with install hint (FR-005).

## Image Workflow Inputs

| Field | Required | Rules |
|-------|----------|-------|
| `profile` | yes | Valid runtime JSON printer profile path |
| `ref_original` | yes | Readable image; full reference screenshot |
| `ref_crop` | yes | Readable image; crop patch within original |
| `fronts` | yes | ≥1 readable image paths |
| `backs` | no | Index-aligned with fronts; missing → duplicate front (documented) |
| `output` | yes | Destination PDF path (distinct from inputs) |

## Relative Crop Box

Fractions `(left, top, right, bottom)` of image width/height derived from
template match of `ref_crop` within `ref_original`.

**Validation**: If match fails or images unreadable → actionable error; do not
silently invent a full-frame crop without notice (edge case).

## Page Pair (front, back)

For each index `i` in `fronts`:

| Side | Source | Corrections applied |
|------|--------|---------------------|
| Front | Cropped `fronts[i]` | None (identity placement aside from fit-to-page) |
| Back | Cropped `backs[i]` if present else copy of front | Profile `extra_rot_deg`, `shift_x_mm`, `shift_y_mm`, flip-mode 180° when short-edge |

**Invariant**: Back corrections MUST NOT be applied to front pages (FR-007).

## Calibration Profile (consumed subset)

Same logical profile as main tool; image tool reads at least:

| Field | Use |
|-------|-----|
| `paper.width_mm` / `height_mm` | Page size for PDF |
| `paper.orientation` | Landscape swap if needed |
| `margins.x_mm` / `y_mm` | Fit margins |
| `flip_mode` | `short` → 180° on back placement; `long` → no extra 180 |
| `back_corrections.*` | Rotation and shifts on backs only |

**Validation**: Invalid JSON / comment-bearing template → actionable error ≠0.

## Output Artifact

Single multi-page PDF: interleaved front/back pairs in order
`(F0, B0, F1, B1, …)`.

## State transitions

```text
[start]
  → extras missing? → error(install hint) → exit ≠0
  → parse CLI / validate paths
  → load profile (fail → error)
  → compute relative crop (fail → error)
  → for each front: emit front page; emit corrected back page
  → write output PDF → success
```
