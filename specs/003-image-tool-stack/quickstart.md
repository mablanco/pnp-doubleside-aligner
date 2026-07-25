# Quickstart: Validate Experimental Image Tool Stack

**Feature**: `003-image-tool-stack`  
**Purpose**: Prove optional packaging, CLI rewrite, and main-PDF isolation — not
a full implementation guide.  
**Contract**: [image-tool-cli.md](./contracts/image-tool-cli.md)  
**Data model**: [data-model.md](./data-model.md)

## Prerequisites

- Python 3.9+
- Repository root as cwd

## 1 — Main path stays light

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/ -v --ignore=tests/integration/test_img_tool_smoke.py
```

(Adjust ignore/marker if tasks name tests differently; default suite must not
require OpenCV.)

**Expected**: Main PDF characterization/integration tests **pass** without
`requirements-img.txt`.

```bash
grep -iE 'opencv|cv2|fpdf|numpy' requirements.txt requirements-dev.txt || true
```

**Expected**: No image-tool-only packages listed as required in those two files
(NumPy/OpenCV/FPDF belong only in `requirements-img.txt`).

## 2 — Missing extras messaging

With image extras **not** installed (or via unit test of the import guard):

```bash
python tools/pnp_double_with_profile_img.py \
  --profile profiles/example_printer.json \
  --ref-original /nonexistent.png \
  --ref-crop /nonexistent.png \
  --front /nonexistent.png \
  --output /tmp/out.pdf
```

**Expected**: Non-zero exit; stderr mentions missing optional dependencies and
`requirements-img.txt` (or equivalent install hint)—not only a raw
`ModuleNotFoundError` without guidance.

Automated:

```bash
python -m pytest tests/integration/test_img_tool_missing_deps.py -v
```

## 3 — Optional happy path (extras installed)

```bash
python -m pip install -r requirements-img.txt
```

Prepare tiny fixtures under `tests/fixtures/img/` (created during
implementation) or generate minimal PNGs, then:

```bash
python tools/pnp_double_with_profile_img.py \
  --profile profiles/example_printer.json \
  --ref-original tests/fixtures/img/ref_original.png \
  --ref-crop tests/fixtures/img/ref_crop.png \
  --front tests/fixtures/img/front0.png \
  --back tests/fixtures/img/back0.png \
  --output /tmp/pnp_img_out.pdf
```

**Expected**: Exit 0; `/tmp/pnp_img_out.pdf` exists; stdout confirms generation.

```bash
python -m pytest -m img tests/ -v
```

**Expected**: Marked image smoke tests pass when extras present; skip cleanly
when absent (if implemented with skip).

## 4 — Docs check

```bash
grep -n "requirements-img\|experimental\|pnp_double_with_profile_img" tools/README.md README.md
```

**Expected**: Image tool labeled experimental; optional install documented; main
PDF still recommended.

## Map failures

| Symptom | Likely area |
|---------|-------------|
| OpenCV required for default pytest | Extras leaked into dev requirements or unmarked tests |
| No install hint on ImportError | Import guard missing (Phase C) |
| Hardcoded paths still required | CLI rewrite incomplete (FR-004) |
| Main PDF tests fail after changes | Accidental main entrypoint edit (FR-009) |
| Docs still say “out of slice” only | Phase D docs not updated |
