# Test fixtures

Deterministic inputs used by the characterization suite and golden PDF net.

## Sample PDFs

| File | Pages | Purpose |
|------|-------|---------|
| `sample_interleaved.pdf` | 4 (F,B,F,B) with shared back | Even interleaved / vector geometry / goldens / smart-detect |
| `sample_fronts_then_backs.pdf` | 4 (F,F,B,B) with shared backs | Smart-detect fronts_then_backs |
| `sample_single.pdf` | 1 | Smart-detect `single_sided` |
| `sample_ambiguous_even.pdf` | 4 unique pages | Smart-detect inconclusive → `--even-default` |
| `sample_odd.pdf` | 3 | Odd → `last_back`; also `fronts_then_backs` + `--on-odd` |

Smart-detect fixtures use full-page color fills and patterns so low-DPI
fingerprints distinguish shared backs from unique fronts. Geometry/golden
tests still use `sample_interleaved.pdf` (regenerate goldens after changing it).

Generated with PyMuPDF: fixed 200×200 pt pages. Regenerate only if intentional
fixture change is required (will invalidate goldens).

## Profiles

| File | Role |
|------|------|
| `profile_nonzero.json` | Non-zero rot+shift, `flip_mode: long` |
| `profile_shift_only.json` | Shift-X only (vector ≠ identity) |
| `profile_invalid.json` | Valid JSON syntax but bad types / unusable corrections |
| `profile_with_comments.json` | Comment-bearing (must fail at runtime) |

## Image-tool fixtures (`img/`)

Small PNGs for the optional experimental image tool smoke tests. See
`img/README.md`. Default CI does **not** require OpenCV; use
`pytest -m img` when `requirements-img.txt` is installed.

## Golden outputs

Baselines live under `golden/`. Capture **desired-contract** outputs only
(never silent no-ops or sample 0.30°/1 mm defaults).

Regenerate after Phase 2 geometry/profile fixes:

```bash
python tests/fixtures/generate_goldens.py
```

Writes at least:

- `golden/out_identity_vector.pdf`
- `golden/out_nonzero_vector.pdf`

## Hygiene (FR-020)

Do **not** commit personal printer profiles, secrets, or ad-hoc alignment PDFs
outside `tests/fixtures/` (and `tests/fixtures/golden/`). Local CLI smoke
outputs belong in `/tmp` or gitignored dirs.
