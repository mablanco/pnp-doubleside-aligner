# Contract: Runtime Calibration Profile (JSON)

**Feature**: `001-codebase-quality`  
**Interface type**: JSON file consumed by `--profile`  
**Related**: [data-model.md](../data-model.md), [cli-contract.md](./cli-contract.md)

## Media type

- UTF-8 JSON object
- **No comments** (`//` or `/* */`) in runtime profiles
- Templates with comments MUST be copied and stripped before use

## Schema (informal)

```json
{
  "paper": {
    "width_mm": 210.0,
    "height_mm": 297.0,
    "orientation": "portrait"
  },
  "margins": {
    "x_mm": 0.0,
    "y_mm": 0.0
  },
  "flip_mode": "short",
  "back_corrections": {
    "extra_rot_deg": 0.0,
    "shift_x_mm": 0.0,
    "shift_y_mm": 0.0
  }
}
```

Optional documentation field (ignored by engine): `"_notes": ["…"]`.

## Field rules

| Path | Required | Notes |
|------|----------|-------|
| `paper.*` | recommended | Structural; A4-like defaults OK if absent |
| `flip_mode` | recommended | `short` ⇒ extra 180° back handling; `long` ⇒ no extra 180° |
| `back_corrections.extra_rot_deg` | optional | Missing → `0.0` |
| `back_corrections.shift_x_mm` | optional | Missing → `0.0` |
| `back_corrections.shift_y_mm` | optional | Missing → `0.0` |

## Sign conventions (normative)

Same as calibration guide:

- `extra_rot_deg` > 0 → clockwise
- `shift_x_mm` > 0 → move back content right
- `shift_y_mm` > 0 → move back content downward

## Load semantics

| Input | Result |
|-------|--------|
| No `--profile` | Identity corrections (zeros); not sample non-zero skew |
| Path does not exist | Error (stderr + non-zero exit) |
| Invalid JSON / comments | Error with guidance to use valid JSON |
| Valid JSON, partial `back_corrections` | Merge; missing axes = 0 |
| Valid JSON + CLI `--rot` / shifts | CLI wins for supplied axes |

## Canonical files

| File | Role |
|------|------|
| `profiles/base_printer_profile.json` | Comment-bearing **template** (not runtime) |
| `profiles/example_printer.json` | Valid example (may contain sample non-zero corrections for illustration) |

Personal printer profiles MUST stay untracked (constitution VIII).

## Compatibility

- Python 3.9+ `json` module
- No JSON5 / comment-preserving parsers in the main workflow
