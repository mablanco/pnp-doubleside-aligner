# Tasks: Installable Package Alongside Scripts

**Input**: Design documents from `/specs/004-package-install/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Packaging smoke required by plan R7 / quickstart (`pnp-double-align --help`).
No geometry characterization changes.

**Organization**: Setup → pyproject foundation → US1 editable install → US2
loose-script dual support → US3 metadata/extras/docs → polish (CI).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Packaging: `pyproject.toml` (new)
- Mirrors: `requirements.txt`, `requirements-dev.txt` (keep; sync pins)
- Optional img: `requirements-img.txt` and/or `[project.optional-dependencies] img` if present from feature `003`
- Main modules: `pnp_double_with_profile_pdf.py`, `geometry.py`, `profiles.py`, `io_pdf.py`
- CI: `.github/workflows/ci.yml`
- Docs: `README.md`
- Tests: `tests/integration/test_packaging_smoke.py` (new)
- Contract: `specs/004-package-install/contracts/packaging-install.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm modules and entrypoint target before writing metadata

- [X] T001 Verify `main()` exists in `pnp_double_with_profile_pdf.py` and root helpers `geometry.py`, `profiles.py`, `io_pdf.py` are importable for setuptools `py-modules`
- [X] T002 [P] Read current pins from `requirements.txt` / `requirements-dev.txt` to copy into `pyproject.toml` dependencies

**Checkpoint**: Ready to author `pyproject.toml` without moving to `src/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create installable metadata (blocks console script and CI switch)

**⚠️ CRITICAL**: User-story validation needs a working `pip install -e .`

- [X] T003 Create `pyproject.toml` at repo root with `[build-system]` setuptools/wheel, `[project]` name `pnp-doubleside-aligner`, version `0.1.0`, MIT license, `requires-python = ">=3.9"`, and pinned main dependencies matching `requirements.txt`
- [X] T004 Configure setuptools flat `py-modules` for `pnp_double_with_profile_pdf`, `geometry`, `profiles`, `io_pdf` in `pyproject.toml` (exclude `tests`, `specs`, `.specify`, tools from package discovery as needed)
- [X] T005 Add `[project.scripts]` entry `pnp-double-align = "pnp_double_with_profile_pdf:main"` in `pyproject.toml`
- [X] T006 Add `[project.optional-dependencies]` `dev = ["pytest==7.4.4"]` (match `requirements-dev.txt`) in `pyproject.toml`
- [X] T007 Validate locally: `python -m pip install -e ".[dev]"` from repo root succeeds

**Checkpoint**: Editable install works; `pnp-double-align` on PATH

---

## Phase 3: User Story 1 - Install as editable package (Priority: P1) 🎯 MVP

**Goal**: Documented `pip install -e .` pulls main deps; installed CLI `--help` works

**Independent Test**: Fresh venv → `pip install -e .` → `pnp-double-align --help` exit 0; see `specs/004-package-install/quickstart.md`

### Tests for User Story 1

- [X] T008 [US1] Add packaging smoke test in `tests/integration/test_packaging_smoke.py`: subprocess `pnp-double-align --help` and/or `python -m pnp_double_with_profile_pdf --help` expect exit 0 (assumes editable install in CI/dev env; skip with clear reason if entry point missing)

### Implementation for User Story 1

- [X] T009 [US1] Document editable install and `pnp-double-align` in `README.md` Requirements/Usage sections per `specs/004-package-install/contracts/packaging-install.md`
- [X] T010 [US1] Confirm `python -m pnp_double_with_profile_pdf --help` works after editable install (no code change if already true; fix `__main__` only if required)
- [X] T011 [US1] Run smoke test / manual help check and fix `pyproject.toml` if entry point fails

**Checkpoint**: SC-001 package-install path usable

---

## Phase 4: User Story 2 - Keep loose scripts working (Priority: P1)

**Goal**: Requirements + `python pnp_double_with_profile_pdf.py` still documented and working; full suite green

**Independent Test**: `pip install -r requirements.txt` (no `-e`) → script `--help`; existing `pytest` suite passes under editable or requirements workflow

### Tests for User Story 2

- [X] T012 [US2] Ensure existing CLI integration tests still invoke loose script path successfully (run `python -m pytest tests/ -v`); fix only packaging-related import breakages without geometry changes

### Implementation for User Story 2

- [X] T013 [US2] Keep loose-script usage examples in `README.md` alongside editable install (dual workflow; FR-003)
- [X] T014 [US2] Add sync headers to `requirements.txt` and `requirements-dev.txt` stating pins must match `pyproject.toml` (FR-010)
- [X] T015 [US2] Verify versions in `requirements.txt` equal `[project].dependencies` in `pyproject.toml`

**Checkpoint**: SC-002/SC-003 dual support verified

---

## Phase 5: User Story 3 - Package metadata and optional extras (Priority: P2)

**Goal**: Clear metadata; `dev` extra; `img` extra only if 003 pins exist; default install excludes image extras

**Independent Test**: Inspect `pyproject.toml` for name/version/license/deps; `pip install -e .` does not install OpenCV; `pip install -e ".[dev]"` provides pytest

### Tests for User Story 3

- [X] T016 [P] [US3] Add assertion or doc-test note in `tests/integration/test_packaging_smoke.py` that default metadata/optional-deps do not list opencv/fpdf as required dependencies (parse `pyproject.toml` or skip if tomllib unavailable on 3.9—use a small parser or install `tomli` only in test if needed; prefer stdlib `tomllib` on 3.11+ with fallback)

### Implementation for User Story 3

- [X] T017 [US3] Complete `[project]` metadata (description, authors/urls if desired, `readme = "README.md"`, license files) in `pyproject.toml`
- [X] T018 [US3] If `requirements-img.txt` exists, add matching `[project.optional-dependencies] img` in `pyproject.toml` and document `pip install -e ".[img]"` in `README.md`; otherwise document `requirements-img.txt` when added by feature `003`
- [X] T019 [US3] Document which CLIs are installed (`pnp-double-align`) vs script-only (`tools/*`) in `README.md` and/or `tools/README.md`
- [X] T020 [US3] Document `pip install -e ".[dev]"` as the preferred contributor/test install in `README.md`

**Checkpoint**: FR-005–007, SC-004/SC-005 satisfied

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T021 Update `.github/workflows/ci.yml` to `pip install -e ".[dev]"` (or install requirements-dev then `pip install -e .`) and add `pyproject.toml` to `cache-dependency-path`
- [X] T022 [P] Remove obsolete `PYTHONPATH=.` from README/CI if editable install makes it unnecessary; keep if still required for any un-packaged imports
- [X] T023 Run `specs/004-package-install/quickstart.md` validation end-to-end
- [X] T024 [P] Confirm no intentional changes to duplex geometry/profile behavior (`git diff` on transform modules empty or docs-only)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup → Foundational**: `pyproject.toml` must exist before US1 smoke
- **US1**: After T007 editable install works
- **US2**: Parallelizable with US1 docs once install works; suite run after packaging
- **US3**: Metadata/extras after core `[project]` exists
- **Polish**: CI after extras/docs decided

### User Story Dependencies

- **US1 (P1)**: MVP editable install + console script
- **US2 (P1)**: Dual loose-script support (mostly docs + suite proof)
- **US3 (P2)**: Metadata polish + optional extras + docs clarity

### Parallel Opportunities

- T009 docs vs T008 smoke (after T007)
- T013–T015 requirements sync vs US3 metadata
- T018–T020 docs tasks in parallel

---

## Parallel Example: User Story 1

```bash
# After pyproject foundation:
Task: "Packaging smoke in tests/integration/test_packaging_smoke.py"
Task: "Document editable install in README.md"
Task: "Verify python -m pnp_double_with_profile_pdf --help"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. `pyproject.toml` + scripts entry
2. `pip install -e ".[dev]"` + `--help` smoke
3. README editable section
4. **STOP**: Package install usable

### Incremental Delivery

1. US1 → editable + PATH command
2. US2 → dual workflow + sync headers + full pytest
3. US3 → metadata/extras/docs
4. Polish → CI uses `-e ".[dev]"`

---

## Notes

- No `src/` migration in this feature (research R1)
- PyPI publish out of scope
- Coordinate `img` extra with feature `003` without blocking `004`
- Do not break existing characterization tests
