# Quickstart: Validate Batch Smart Page-Order Detect

**Feature**: `002-smart-detect`  
**Purpose**: Runnable checks that prove smart detection works end-to-end — not a
full implementation guide.  
**Contract**: [batch-smart-detect.md](./contracts/batch-smart-detect.md)  
**Data model**: [data-model.md](./data-model.md)

## Prerequisites

- Python 3.9+
- Repository root as cwd
- Dependencies (same as main project + pytest):

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
```

## 1 — Automated suite

```bash
python -m pytest tests/unit/test_smart_detect.py tests/integration/test_batch_smart_detect.py -v
```

(Adjust paths if tasks place tests under slightly different module names.)

**Expected (before Phase B implementation)**:
- Enablement / classification tests **fail** (flag still disabled or helper missing)
- New unit cases for decision helpers may fail until implemented

**Expected (after Phase B)**:
- All smart-detect unit + integration tests **pass**
- No assertion that stderr contains `unavailable` / `disabled` for the happy path
- Interleaved and fronts_then_backs gold fixtures are not swapped

Full regression (recommended before calling the feature done):

```bash
python -m pytest tests/ -v
```

## 2 — Smoke: enable smart detect on a fixture folder

Create a temp input dir with copies of fixtures (names matter for hints):

```bash
mkdir -p /tmp/pnp-smart-in /tmp/pnp-smart-out
cp tests/fixtures/sample_interleaved.pdf /tmp/pnp-smart-in/
cp tests/fixtures/sample_fronts_then_backs.pdf /tmp/pnp-smart-in/   # after fixture exists
cp tests/fixtures/sample_odd.pdf /tmp/pnp-smart-in/
cp tests/fixtures/sample_single.pdf /tmp/pnp-smart-in/              # after fixture exists
cp tests/fixtures/sample_interleaved.pdf /tmp/pnp-smart-in/demo_interleaved.pdf
```

```bash
python tools/pnp_batch_align.py \
  --input-dir /tmp/pnp-smart-in \
  --output-dir /tmp/pnp-smart-out \
  --auto-detect-smart \
  --verbose
```

**Expected**:
- Process does **not** exit immediately with “unavailable / experimental disabled”
- Stdout lines show `order='…'` and reasons (`name-hint:…`, `pages:…`, `visual:…`, or tie/fallback)
- `demo_interleaved.pdf` uses name-hint → `interleaved`
- Worker runs per file; review `/tmp/pnp-smart-out`

## 3 — Smoke: inconclusive fallback

```bash
# After sample_ambiguous_even.pdf exists:
mkdir -p /tmp/pnp-smart-amb-in /tmp/pnp-smart-amb-out
cp tests/fixtures/sample_ambiguous_even.pdf /tmp/pnp-smart-amb-in/
python tools/pnp_batch_align.py \
  --input-dir /tmp/pnp-smart-amb-in \
  --output-dir /tmp/pnp-smart-amb-out \
  --auto-detect-smart \
  --even-default fronts_then_backs
```

**Expected**: Status reason indicates tie/fallback; order equals `fronts_then_backs`.

## 4 — Docs check

```bash
grep -n "auto-detect-smart" tools/README.md
```

**Expected**: Describes the flag as available (with limits), not disabled; mentions
precedence name → page-count → content → even-default.

## Map failures

| Symptom | Likely area |
|---------|-------------|
| Immediate unavailable/disabled exit | Disable gate not removed (plan Phase B) |
| `NameError` / `avg_sim_block` | Helper not implemented |
| Interleaved ↔ halves swap | Decision predicate / thresholds (research R1) |
| Name hint ignored | Precedence order in `detect_order_smart` |
| Docs still say disabled | Phase C docs update |
