# Contract: Experimental Image Tool CLI (`tools/pnp_double_with_profile_img.py`)

**Feature**: `003-image-tool-stack`  
**Interface type**: Command-line (argparse)  
**Related**: [data-model.md](../data-model.md), [spec.md](../spec.md)

## Status

**Experimental / optional.** Prefer `pnp_double_with_profile_pdf.py` for
production duplex alignment. This tool does not replace the main entrypoint.

## Dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-img.txt
```

Main PDF users install **only** `requirements.txt` (and optionally
`requirements-dev.txt`). Image extras are never mandatory for the main path.

## Invocation

```bash
python tools/pnp_double_with_profile_img.py \
  --profile <profile.json> \
  --ref-original <ref_full.png> \
  --ref-crop <ref_crop.png> \
  --front <front0.png> [--front <front1.png> ...] \
  [--back <back0.png>] [--back <back1.png> ...] \
  --output <out.pdf> \
  [--verbose]
```

Progress / success → **stdout**.  
Errors and install hints → **stderr**.

## Exit status

| Condition | Exit | stderr |
|-----------|------|--------|
| Success | 0 | optional |
| Missing optional extras (OpenCV/FPDF/…) | ≠ 0 | Install hint pointing at `requirements-img.txt` |
| Missing/unreadable input image or profile | ≠ 0 | Actionable path/profile message |
| Invalid / comment-bearing profile JSON | ≠ 0 | Valid runtime JSON guidance |
| Empty fronts list / no fronts provided | ≠ 0 | Clear message |
| Crop match failure (documented) | ≠ 0 | Clear failure; no silent bogus crop |
| Unexpected internal error | ≠ 0 | May include traceback only for unexpected faults |

## Behavioral contract

1. **Backs only**: Profile rotation, shifts, and flip-mode 180° apply only to
   back pages; front pages are not given those corrections.
2. **Pairing**: For each front index, emit front then back; missing back →
   duplicate cropped front (documented).
3. **Crop**: Relative box from `--ref-original` / `--ref-crop` applied to all
   pages consistently.
4. **Paper**: Page size follows profile paper dimensions (not a silent ignore
   of profile size).
5. **No main-PDF contract change**: This feature MUST NOT alter
   `pnp_double_with_profile_pdf.py` geometric/CLI behavior.
6. **Help**: `--help` describes experimental status and required extras at a
   high level.

## Characterization mapping

| Acceptance / FR | Suggested check |
|-----------------|-----------------|
| US1 / FR-001–003 | `requirements-img.txt` exists; main requirements lack cv2/fpdf; docs mention extras |
| US1 / FR-005 | CLI without extras → install hint + ≠0 |
| US2 / FR-004, FR-007–008 | CLI smoke with fixtures → PDF; fronts unmodified vs backs |
| US2 / FR-009 | Full main `pytest` without img extras still passes |
| US3 / FR-006, FR-010 | Bad path/profile messaging; experimental labeling in docs |

## Non-goals

- Becoming the recommended default workflow
- Vector-preserving PDF editing
- Requiring OpenCV in default CI / `requirements-dev.txt`
- Batch smart-detect or main CLI auto-order
