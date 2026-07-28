# Tasks: Experimental Image Tool Stack

**Input**: Design documents from `/specs/003-image-tool-stack/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by FR-012 (missing-extras always; happy-path optional/skipped
when extras absent). Write missing-deps test before relying on import guard.

**Organization**: Plan phases A→D mapped to Setup → Foundation → US1 deps →
US2 CLI rewrite → US3 boundaries → polish. Do not put OpenCV/FPDF into
`requirements.txt` or `requirements-dev.txt`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Image tool: `tools/pnp_double_with_profile_img.py`
- Optional deps: `requirements-img.txt` (new)
- Main deps: `requirements.txt`, `requirements-dev.txt` (unchanged for img extras)
- Docs: `tools/README.md`, `README.md`
- Fixtures: `tests/fixtures/img/`
- Tests: `tests/integration/test_img_tool_*.py`, optional `tests/unit/`
- Contract: `specs/003-image-tool-stack/contracts/image-tool-cli.md`
- Main PDF entrypoint: `pnp_double_with_profile_pdf.py` — **do not change** for this feature

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Optional dependency file and directory placeholders

- [X] T001 Create pinned optional extras file `requirements-img.txt` at repo root (`opencv-python-headless`, `numpy`, `fpdf2` with versions per `specs/003-image-tool-stack/research.md` R2; do not `-r` into main requirements)
- [X] T002 [P] Create `tests/fixtures/img/` directory and document intended assets in `tests/fixtures/img/README.md`
- [X] T003 [P] Confirm `requirements.txt` and `requirements-dev.txt` contain no OpenCV/FPDF/numpy-as-required image extras (grep/review)

**Checkpoint**: `requirements-img.txt` exists; main install path still PDF-only

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Tiny image fixtures and pytest markers/helpers for img tests

**⚠️ CRITICAL**: CLI rewrite and happy-path smoke need fixtures; missing-deps test can start once T001 exists

- [X] T004 [P] Create minimal deterministic PNGs: `tests/fixtures/img/ref_original.png`, `tests/fixtures/img/ref_crop.png`, `tests/fixtures/img/front0.png`, `tests/fixtures/img/back0.png` (crop patch must be matchable inside original)
- [X] T005 Register optional `img` pytest marker in `tests/conftest.py` (or `pytest.ini` / `pyproject.toml` markers section if present) and document skip-when-no-cv2 policy
- [X] T006 [P] Add `run_img_tool` helper (subprocess to `tools/pnp_double_with_profile_img.py`) in `tests/conftest.py`

**Checkpoint**: Fixtures readable; marker documented; main pytest still green without img extras

---

## Phase 3: User Story 1 - Install optional image-tool dependencies (Priority: P1) 🎯 MVP

**Goal**: Documented optional install; main PDF path untouched; extras resolve imports

**Independent Test**: Main `pip install -r requirements.txt` has no img packages;
`pip install -r requirements-img.txt` satisfies tool imports; docs explain both

### Tests for User Story 1

- [X] T007 [P] [US1] Add static/docs-oriented check or test comment in `tests/integration/test_img_tool_missing_deps.py` module docstring mapping to FR-001/002 (optional assert that parsing `requirements.txt` excludes opencv/fpdf)

### Implementation for User Story 1

- [X] T008 [US1] Document optional install (`pip install -r requirements-img.txt`) and “prefer main PDF” in `tools/README.md` under `pnp_double_with_profile_img.py`
- [X] T009 [P] [US1] Add short pointer in root `README.md` optional-tools section to `requirements-img.txt` without making it mandatory
- [X] T010 [US1] Update module docstring in `tools/pnp_double_with_profile_img.py` to reference `requirements-img.txt` and experimental status (replace “out of first remediation slice only” with current packaging guidance)

**Checkpoint**: SC-001/SC-005 packaging/docs boundary clear for deps

---

## Phase 4: User Story 2 - Honest experimental image→duplex workflow (Priority: P1)

**Goal**: argparse CLI (no hardcoded-only UX); crop + profile backs; output PDF;
paper size from profile

**Independent Test**: Documented CLI on `tests/fixtures/img/` + example profile
produces output PDF; fronts without back corrections; main pytest unchanged

### Tests for User Story 2

- [X] T011 [P] [US2] Add `@pytest.mark.img` smoke test in `tests/integration/test_img_tool_smoke.py`: run CLI with fixtures → output PDF exists; skip if OpenCV/FPDF missing
- [X] T012 [P] [US2] Add test that front pages do not receive back rot/shift (inspect or behavioral assertion) in `tests/integration/test_img_tool_smoke.py` or unit helper tests

### Implementation for User Story 2

- [X] T013 [US2] Replace hardcoded `PROFILE_PATH` / `REF_*` / `FRONTS` / `BACKS` / fixed output with argparse CLI per `specs/003-image-tool-stack/contracts/image-tool-cli.md` in `tools/pnp_double_with_profile_img.py`
- [X] T014 [US2] Use profile paper width/height for FPDF page format (fix silent always-A4 mismatch) in `tools/pnp_double_with_profile_img.py`
- [X] T015 [US2] Keep OpenCV crop template-matching + FPDF emit; apply profile rot/shift/flip only to backs; document missing-back → duplicate front in help text in `tools/pnp_double_with_profile_img.py`
- [X] T016 [US2] Align profile JSON error messaging with project norms (invalid/comment-bearing → actionable stderr + ≠0) in `tools/pnp_double_with_profile_img.py`
- [X] T017 [US2] Confirm marked img smoke passes when extras installed; ensure `pnp_double_with_profile_pdf.py` untouched

**Checkpoint**: FR-004/FR-007/FR-008 satisfied for happy path

---

## Phase 5: User Story 3 - Keep experimental boundaries clear (Priority: P2)

**Goal**: Missing extras / bad paths → actionable errors; experimental labeling
everywhere; main suite never requires img extras

**Independent Test**: Run tool without extras → install hint; missing path →
clear error; docs still say experimental

### Tests for User Story 3

- [X] T018 [US3] Integration/unit test: missing extras → stderr mentions `requirements-img.txt` (or install hint) + ≠0 in `tests/integration/test_img_tool_missing_deps.py` (test import guard directly if cv2 present in env)
- [X] T019 [P] [US3] Integration test: missing input path / bad profile → actionable stderr + ≠0 (with extras installed or mocked) in `tests/integration/test_img_tool_errors.py`

### Implementation for User Story 3

- [X] T020 [US3] Add guarded/lazy imports for cv2/numpy/fpdf with stderr install hint in `tools/pnp_double_with_profile_img.py` (prefer `--help` without heavy imports when practical)
- [X] T021 [US3] Ensure expected-failure paths avoid raw traceback as primary UX in `tools/pnp_double_with_profile_img.py`
- [X] T022 [US3] Finalize experimental banners in `tools/pnp_double_with_profile_img.py`, `tools/README.md`, and README pointer (FR-010)

**Checkpoint**: SC-004 missing-deps UX; FR-005/FR-006 done

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T023 Run main suite without img extras: `python -m pytest tests/ -v -m "not img"` (or equivalent ignore) and confirm green (FR-009 / SC-003)
- [X] T024 Run steps from `specs/003-image-tool-stack/quickstart.md` and fix gaps
- [X] T025 [P] Complexity Tracking already in plan — no new main-stack deps; double-check `requirements-img.txt` pins are reproducible

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup**: Immediate (T001 critical for US1)
- **Foundational**: Fixtures/markers before US2 smoke
- **US1**: Can proceed after T001 (docs + pins)
- **US2**: After foundational fixtures; CLI rewrite on same file as US3 guards — sequence US2 then US3 or combine carefully
- **US3**: Import guard should land with or right after CLI rewrite
- **Polish**: After stories

### User Story Dependencies

- **US1 (P1)**: Packaging/docs MVP — independent of full CLI once T001 exists
- **US2 (P1)**: Needs fixtures + CLI rewrite
- **US3 (P2)**: Needs import guard + error UX on rewritten CLI

### Parallel Opportunities

- T002–T003, T004 fixture assets, T008–T009 docs
- T011–T012 tests in parallel before/during implementation
- T018–T019 error tests in parallel

---

## Parallel Example: User Story 2

```bash
# Fixtures already done in Phase 2
Task: "Img smoke test in tests/integration/test_img_tool_smoke.py"
Task: "Fronts-unmodified assertion in tests/integration/test_img_tool_smoke.py"

# Implementation sequential on tools/pnp_double_with_profile_img.py:
Task: "Add argparse CLI"
Task: "Fix paper size from profile"
Task: "Backs-only corrections + help text"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. `requirements-img.txt` + docs pointers
2. Validate main requirements stay clean
3. **STOP**: Optional deps story done even before CLI rewrite

### Incremental Delivery

1. US1 → honest optional deps
2. US2 → usable CLI + smoke
3. US3 → missing-deps/errors + labels
4. Polish → quickstart + main suite gate

---

## Notes

- Keep OpenCV/FPDF stack (research R1); rewrite is CLI/UX not Pillow port
- Never add image extras to `requirements-dev.txt`
- Do not modify main PDF aligner behavior in this feature
