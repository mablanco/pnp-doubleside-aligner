# Contract: Packaging & Install UX

**Feature**: `004-package-install`  
**Interface type**: Python packaging / CLI entry points  
**Related**: [data-model.md](../data-model.md), [spec.md](../spec.md)

## Editable package install

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e .
# with tests:
python -m pip install -e ".[dev]"
```

**Expected**: Install succeeds; main runtime deps present; console script
`pnp-double-align` available on PATH.

## Installed main CLI

```bash
pnp-double-align --help
# equivalent module form:
python -m pnp_double_with_profile_pdf --help
```

**Expected**: Exit 0; help text for the main duplex aligner (same flags as the
loose script contract from feature `001`).

Functional PDF alignment (unchanged contract):

```bash
pnp-double-align --input game.pdf --output game_aligned.pdf [--profile profile.json] ...
```

## Loose-script workflow (still supported)

```bash
python -m pip install -r requirements.txt
python pnp_double_with_profile_pdf.py --input game.pdf --output game_aligned.pdf
```

**Expected**: Remains documented and working without requiring editable install.

## Optional extras

| Extra | Install | Notes |
|-------|---------|-------|
| `dev` | `pip install -e ".[dev]"` | pytest for contributors/CI |
| `img` | `pip install -e ".[img]"` | Only if declared; else use `requirements-img.txt` when present |

Default `pip install -e .` MUST NOT pull experimental image-only deps.

## Authority & sync

| Concern | Authority |
|---------|-----------|
| Package metadata, extras, console scripts | `pyproject.toml` |
| Convenience non-editable pins | `requirements*.txt` (mirrors; keep versions aligned) |

## CI expectations

- Install path exercises editable install with `dev` extra (recommended):
  `pip install -e ".[dev]"`.
- Main test suite: `python -m pytest tests/ -v` (with repo checkout; editable
  install removes need for `PYTHONPATH=.` for packaged modules).
- Cache keys include `pyproject.toml` and requirements files.

## Non-goals

- Publishing to PyPI / TestPyPI in this feature
- Converting all `tools/` scripts into console entry points
- Changing geometric/profile behavior of the main aligner
- Requiring users to abandon the loose-script workflow
