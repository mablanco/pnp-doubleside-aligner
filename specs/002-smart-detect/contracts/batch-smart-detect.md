# Contract: Batch Smart Page-Order Detect (`tools/pnp_batch_align.py`)

**Feature**: `002-smart-detect`  
**Interface type**: Command-line (argparse)  
**Related**: [data-model.md](../data-model.md), [spec.md](../spec.md)

## Invocation

```bash
python tools/pnp_batch_align.py \
  --input-dir <dir> \
  --output-dir <dir> \
  --auto-detect-smart \
  [--even-default interleaved|fronts_then_backs] \
  [--profile <profile.json>] \
  [--on-odd warn|add_blank|drop_last] \
  [--flip-mode long|short] \
  [--rot <deg>] [--shiftx <mm>] [--shifty <mm>] \
  [--dpi <int>] \
  [--script <path-to-worker>] \
  [--verbose]
```

Without `--auto-detect-smart`, existing non-smart order selection remains
(page-count + even-default only; no content-based path).

Progress / per-file decision lines → **stdout**.  
Errors and worker failures → **stderr**.

## Exit status

| Condition | Exit | Notes |
|-----------|------|-------|
| Smart detect enabled and runs (no longer refused as unavailable) | — | Must not exit solely because the flag is set |
| Success (all workers exit 0; PDFs found) | 0 | |
| No PDFs in input dir | 0 | Clear stdout message (existing empty-dir behavior) |
| One or more workers non-zero | 1 | Failure count; detect itself succeeded |
| Uncaught programming error on detect path | forbidden | Must not NameError / missing helper |

## Behavioral contract (detection)

1. **Precedence**: name hint → page-count (`single_sided` / `last_back`) →
   content-based common-back rule → `--even-default` on tie / open-fallback.
2. **Modes**: Only emit documented aligner modes:
   `interleaved`, `fronts_then_backs`, `last_back`, `single_sided`.
3. **Status line**: For each PDF, stdout includes chosen `order` and a short
   `reason` (see [data-model.md](../data-model.md) reason taxonomy).
4. **Verbose**: `--verbose` may print similarity scores used for the content path.
5. **No transforms**: Detection does not rotate/shift pages; worker applies
   profile/overrides with chosen `--order`.
6. **Main CLI unchanged**: This contract does not add auto-detect to
   `pnp_double_with_profile_pdf.py`.
7. **Sampling**: For large page counts, fingerprint sampling per research R3 is
   allowed; must not change precedence rules.

## Characterization mapping

| Acceptance / FR | Suggested check |
|-----------------|-----------------|
| US1 / FR-001 | Integration: `--auto-detect-smart` does not print unavailable/disabled refusal |
| US1 / FR-002–005 | Fixtures: interleaved, fronts_then_backs, single, odd→last_back classified correctly |
| US2 / FR-006–007 | Name-hint wins; ambiguous even → even-default + tie reason |
| US2 / FR-008 | Open/corrupt path → open-fallback or clear error; no NameError |
| US3 / FR-009–011 | Status reason present; tools README describes available smart detect |
| SC-005 | Gold interleaved vs fronts_then_backs never swapped on confident path |

## Non-goals (this contract)

- Auto-detect on the main single-file CLI
- Guaranteeing perfect classification of every arbitrary PDF in the wild
- Changing profile schema or worker geometry
- Requiring high-DPI renders or new ML dependencies
