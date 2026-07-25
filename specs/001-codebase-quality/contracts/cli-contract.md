# Contract: Main CLI (`pnp_double_with_profile_pdf.py`)

**Feature**: `001-codebase-quality`  
**Interface type**: Command-line (argparse)  
**Related**: [profile-schema.md](./profile-schema.md), [data-model.md](../data-model.md)

## Invocation

```bash
python pnp_double_with_profile_pdf.py \
  --input <in.pdf> \
  --output <out.pdf> \
  [--profile <profile.json>] \
  [--order interleaved|fronts_then_backs|single_sided|last_back] \
  [--on-odd warn|add_blank|drop_last] \
  [--flip-mode long|short] \
  [--rot <deg>] [--shiftx <mm>] [--shifty <mm>] \
  [--mode auto|vector|raster] \
  [--dpi <int>] [--jpeg-quality <1-95>]
```

Progress and success summaries → **stdout**.  
Errors, warnings, and fallback notices → **stderr**.

## Exit status

| Condition | Exit | stderr |
|-----------|------|--------|
| Success | 0 | optional fallback notice if auto→raster |
| Missing/unreadable input PDF | ≠ 0 | actionable message (no raw traceback as primary UX) |
| `--profile` path missing | ≠ 0 | actionable message (must not silently apply sample skew) |
| Invalid JSON / comment-bearing profile | ≠ 0 | explain valid JSON / copy-strip template |
| Vector-only mode hard failure | ≠ 0 | clear failure; no silent partial success claim |
| Unexpected internal error | ≠ 0 | may include traceback only for unexpected faults |

## Behavioral contract (geometric)

1. **Backs only**: Transforms apply only to indices classified as backs for
   `--order`; fronts are geometrically unmodified.
2. **Signs**: Positive rotation = clockwise; +X right; +Y downward
   (`docs/calibration_guide.md`). Vector and raster MUST agree.
3. **Identity default**: No `--profile` and no `--rot`/`--shiftx`/`--shifty` →
   corrections are exactly `0, 0, 0`.
4. **Overrides**: Explicit CLI correction flags win over profile values for
   those axes.
5. **Auto fallback**: Recoverable preferred-path failure → stderr explanation →
   raster path with same correction directions.
6. **Odd warn**: `fronts_then_backs` + odd N + `--on-odd warn` → warning on
   stderr; processing continues under documented classification.
7. **Safe save**: Distinct paths preferred; same-path uses temp + replace
   consistently for vector and raster writers.

## Characterization mapping

| Acceptance / FR | Suggested check |
|-----------------|-----------------|
| US1 / FR-001–004 | Integration: profile with non-zero rot/shift; fronts identity; backs moved |
| US1 / FR-002 | Force preferred failure or auto path; stderr fallback + raster output |
| US2 / FR-005–008 | CLI: no profile → identity; missing/invalid profile/PDF → stderr + ≠0 |
| US4 / FR-009–010 | Unit: page-order table; CLI: odd warn |
| US3 / FR-011 | Suite exists; fails pre-fix; passes post-fix |

## Non-goals (this contract)

- GUI
- Guaranteeing pixel-identical raster vs vector (only sign/direction parity)
- Implementing batch smart page-order detection (see tools contract note in
  quickstart: disabled with clear error)
