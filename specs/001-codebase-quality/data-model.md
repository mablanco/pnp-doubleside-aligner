# Data Model: Codebase Quality Remediation

**Feature**: `001-codebase-quality`  
**Date**: 2026-07-25  
**Related**: [spec.md](./spec.md), [contracts/profile-schema.md](./contracts/profile-schema.md)

Entities below are logical (in-memory / JSON / CLI). No database.

## Calibration Profile

Reusable printer configuration: one profile = one printer configuration
(printer + paper + duplex settings), not one game/PDF.

| Field | Type | Rules |
|-------|------|-------|
| `paper.width_mm` | float | > 0 |
| `paper.height_mm` | float | > 0 |
| `paper.orientation` | string | `portrait` \| `landscape` |
| `margins.x_mm` | float | default 0 |
| `margins.y_mm` | float | default 0 |
| `flip_mode` | string | `short` \| `long` |
| `back_corrections` | BackCorrection | required object; missing axes → identity |
| `_notes` | list[string] (optional) | documentation only; ignored by engine |

**Validation**:
- Runtime file MUST be valid JSON (no comments).
- Comment-bearing templates (`profiles/base_printer_profile.json`) are docs aids;
  using them as `--profile` is an expected failure with actionable message.
- Canonical tracked examples: `profiles/base_printer_profile.json` (template),
  `profiles/example_printer.json` (valid JSON example).

**Defaults when no profile and no CLI overrides**: identity BackCorrection
(all zeros). Paper/margins/flip may use A4 portrait / short as structural
defaults without applying non-zero corrections.

## Back Correction

Rotation and shifts applied **only** to pages classified as backs.

| Field | Type | Unit | Sign convention |
|-------|------|------|-----------------|
| `extra_rot_deg` | float | degrees | positive = clockwise |
| `shift_x_mm` | float | mm | positive = move back right |
| `shift_y_mm` | float | mm | positive = move back downward |

**CLI overrides** (`--rot`, `--shiftx`, `--shifty`): when present, override the
corresponding field; remaining fields come from the loaded profile (or identity).

**Relationships**: owned by Calibration Profile; consumed by Processing Mode
writers (vector and raster) with identical signs.

## Page-Order Mode

Rule set classifying each 0-based page index as front or back.

| Value | Back indices (summary) |
|-------|-------------------------|
| `interleaved` | odd indices (1, 3, 5, …) for even-style duplex pairing |
| `fronts_then_backs` | second half of effective page count |
| `last_back` | only the last page |
| `single_sided` | none (no backs) |

Exact classification MUST match published help/docs and be covered by
characterization tests (FR-010). Fronts MUST remain geometrically unmodified.

## Odd-Page Policy

Applies when page count is odd under `fronts_then_backs`.

| Value | Behavior |
|-------|----------|
| `warn` | Emit stderr warning; continue without changing page count |
| `add_blank` | Effective total = N + 1 (blank trailing page) |
| `drop_last` | Effective total = N − 1 |

## Processing Mode

| Value | Behavior |
|-------|----------|
| `vector` | Preferred vector-preserving path only |
| `raster` | Alternate raster path only |
| `auto` | Try vector; on recoverable failure → stderr notice + raster |

Shared inputs: input/output paths, profile, page-order, odd policy, optional
flip override, DPI / JPEG quality (raster).

## Finding Record (audit artifact)

Used in the spec’s Current vs Desired table to prioritize remediation; not a
runtime object.

| Field | Description |
|-------|-------------|
| Area | Transform, profile, CLI, tools, docs, deps, … |
| Current behavior | Observed baseline (audit date 2026-07-25) |
| Desired behavior | Constitution-governed target |
| Severity / phase | Phase 1 test, Phase 2 fix, Phase 3 debt |

## State transitions

### Profile load

```text
[no --profile] → identity corrections
[--profile missing] → error (non-zero exit)
[--profile invalid JSON / comments] → error (non-zero exit)
[--profile valid] → merge into structural defaults; missing correction keys → 0
[+ CLI overrides] → override listed axes
```

### Processing (auto)

```text
start → try vector
  → success → done (vector output)
  → recoverable failure → stderr fallback message → raster
  → raster success → done
  → raster / I/O failure → actionable error, non-zero exit
```

### Characterization suite (feature delivery)

```text
Phase 1: contract tests added (many fail on known bugs)
Phase 2: fixes → P1 tests pass
Phase 3: refactor → same tests still pass
```
