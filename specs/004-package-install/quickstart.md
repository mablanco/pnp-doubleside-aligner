# Quickstart: Validate Package Install

**Feature**: `004-package-install`  
**Purpose**: Prove editable install, console entry, and dual script support.  
**Contract**: [packaging-install.md](./contracts/packaging-install.md)

## Prerequisites

- Python 3.9+
- Repository root as cwd
- Clean or disposable virtualenv recommended

## 1 — Editable install + help

```bash
python3 -m venv /tmp/pnp-pkg-venv
source /tmp/pnp-pkg-venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
pnp-double-align --help
python -m pnp_double_with_profile_pdf --help
```

**Expected**: Both help commands exit 0; usage mentions input/output/profile
style flags consistent with the main aligner.

## 2 — Main test suite under editable install

```bash
python -m pytest tests/ -v
```

**Expected**: Existing main-path tests pass (SC-002). Packaging smoke (if added)
passes.

## 3 — Loose script still works

In the same venv (deps already present) or a requirements-only venv:

```bash
python pnp_double_with_profile_pdf.py --help
```

**Expected**: Exit 0; script path remains usable (FR-003).

Requirements-only path (optional second venv):

```bash
python3 -m venv /tmp/pnp-req-venv
source /tmp/pnp-req-venv/bin/activate
python -m pip install -r requirements.txt
python pnp_double_with_profile_pdf.py --help
```

## 4 — Default install excludes image extras

```bash
python -m pip show opencv-python-headless fpdf2 2>/dev/null || true
# after only: pip install -e .
```

**Expected**: Those packages are absent unless `.[img]` or `requirements-img.txt`
was installed (SC-004).

## 5 — Docs check

```bash
grep -n "pip install -e\|pnp-double-align\|requirements.txt" README.md
```

**Expected**: README documents editable install, console command name, and
loose-script/requirements workflow.

## Map failures

| Symptom | Likely area |
|---------|-------------|
| `pnp-double-align` not found | `[project.scripts]` missing/wrong |
| Import errors after `-e .` | `py-modules` incomplete (geometry/profiles/io_pdf) |
| Tests need `PYTHONPATH=.` after `-e .` | Modules not packaged / editable misconfigured |
| OpenCV pulled by default | `img` mistakenly in main dependencies |
| Requirements pins drift | Sync policy not applied (FR-010) |
