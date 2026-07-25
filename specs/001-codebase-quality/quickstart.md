# Quickstart: Validate Codebase Quality Remediation

**Feature**: `001-codebase-quality`  
**Purpose**: Runnable checks that prove characterization and (after fixes)
remediation — not a full implementation guide.  
**Contracts**: [cli-contract.md](./contracts/cli-contract.md),
[profile-schema.md](./contracts/profile-schema.md)

## Prerequisites

- Python 3.9+
- Repository root as cwd
- Main stack + dev test runner (added in Phase 1 of implementation):

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Until those files exist, equivalent unpinned install (baseline):

```bash
python -m pip install pymupdf pillow reportlab pytest
```

## Phase 1 — Characterization suite

```bash
python -m pytest tests/ -v
```

**Expected (before Phase 2 fixes)**:
- Suite discovers unit + integration tests
- Cases for already-correct helpers (e.g. `mm_to_pt`, even-page order) **pass**
- Cases encoding desired contract for known bugs **fail** (identity defaults,
  vector shift application, fallback/`FitzError`, raster signs, odd warn,
  missing profile error, invalid JSON UX, batch smart-detect disable)

**Expected (after Phase 2)**: all P1 characterization cases **pass**.

Map failures to [spec.md](./spec.md) Current vs Desired and [plan.md](./plan.md)
Phase 2 fix list.

## Smoke — main CLI (after Phase 2)

Use a tiny even-page fixture PDF under `tests/fixtures/` (or any 2+ page PnP)
and a **valid** JSON profile with non-zero corrections (copy
`profiles/example_printer.json` or a stripped template).

```bash
python pnp_double_with_profile_pdf.py \
  --input tests/fixtures/sample_interleaved.pdf \
  --output /tmp/pnp_out.pdf \
  --profile profiles/example_printer.json \
  --order interleaved \
  --mode auto
```

**Expected**:
- Exit 0
- stdout reports save/finish
- Backs corrected; fronts unchanged (assert via suite; optional visual check)
- If vector fails recoverably: stderr fallback notice + raster output

Identity check (no profile, no overrides):

```bash
python pnp_double_with_profile_pdf.py \
  --input tests/fixtures/sample_interleaved.pdf \
  --output /tmp/pnp_identity.pdf \
  --mode vector
```

**Expected**: reported corrections `0°, (0 mm, 0 mm)`; backs geometrically
identity vs input (suite-enforced).

Failure UX:

```bash
python pnp_double_with_profile_pdf.py \
  --input /no/such.pdf --output /tmp/x.pdf --profile /no/such.json
```

**Expected**: non-zero exit; actionable stderr; not a raw traceback as the only
user-visible result.

Odd warn:

```bash
python pnp_double_with_profile_pdf.py \
  --input tests/fixtures/sample_odd.pdf \
  --output /tmp/pnp_odd.pdf \
  --order fronts_then_backs \
  --on-odd warn
```

**Expected**: warning on stderr; processing continues.

## Tools in scope

Batch smart detect (Phase 2 decision: **disabled**):

```bash
python tools/pnp_batch_align.py --auto-detect-smart ...
```

**Expected**: clear unavailable/experimental error; **not** `NameError` on
`avg_sim_block`.

Image tool remains experimental; not required for this quickstart’s P1 gate.

## Phase 3 regression

After module extraction / typing / docs:

```bash
python -m pytest tests/ -v
```

**Expected**: same green suite as end of Phase 2; no new geometric drift.

## Hygiene

Do not commit personal profiles, secrets, or generated alignment PDFs from
these runs (constitution VIII / FR-020).
