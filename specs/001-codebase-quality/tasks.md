# Tasks: Codebase Quality Remediation

**Input**: Design documents from `/specs/001-codebase-quality/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by FR-011 / User Story 3 (characterization-first). Write failing
contract tests before transform/profile/page-order fixes.

**Organization**: Phases follow the plan’s mandatory order — Setup → Foundation →
characterization (US3) → critical fixes (US1, US2, US4, US6 safe-save) →
structure/docs (US5, US6 deps) → polish. Do not start a later plan gate until
the prior exit gate is met.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Main entrypoint: `pnp_double_with_profile_pdf.py`
- Phase 3 modules: `geometry.py`, `profiles.py` (optional `io_pdf.py`)
- Tools: `tools/`
- Profiles: `profiles/`
- Docs: `docs/`, `README.md`, `tools/README.md`
- Tests: `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- Golden outputs (refactor no-drift): `tests/fixtures/golden/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Test harness and dependency pins so characterization can run

- [ ] T001 Create `tests/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`, and `tests/fixtures/golden/` directories with empty `__init__.py` where needed for imports
- [ ] T002 [P] Add pinned main-stack `requirements.txt` (PyMuPDF, Pillow, ReportLab) at repository root
- [ ] T003 [P] Add `requirements-dev.txt` with `pytest` at repository root
- [ ] T004 [P] Ensure `.gitignore` keeps personal profiles, secrets, venvs, and *ad-hoc* generated alignment PDFs untracked, while allowing committed fixtures under `tests/fixtures/` and `tests/fixtures/golden/` (FR-020)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared fixtures and pytest helpers required by all characterization stories

**⚠️ CRITICAL**: No user-story implementation/fixes until this phase is complete

- [ ] T005 Add `tests/conftest.py` with shared helpers (repo-root path, CLI runner via `subprocess` or importable `main`, temp output dirs)
- [ ] T006 [P] Create and **commit** even-page interleaved sample PDF at `tests/fixtures/sample_interleaved.pdf` (minimum 2 pages; deterministic content suitable for golden diffs)
- [ ] T007 [P] Create and **commit** odd-page sample PDF at `tests/fixtures/sample_odd.pdf` for `fronts_then_backs` / `--on-odd` cases
- [ ] T008 [P] Create valid non-zero correction profile fixture at `tests/fixtures/profile_nonzero.json` (and shift-only variant `tests/fixtures/profile_shift_only.json`)
- [ ] T009 [P] Create invalid/comment-bearing profile fixtures at `tests/fixtures/profile_invalid.json` and `tests/fixtures/profile_with_comments.json`
- [ ] T010 Document fixture provenance, golden regeneration steps, and “do not commit personal/ad-hoc PDFs outside `tests/fixtures/`” in `tests/fixtures/README.md`

**Checkpoint**: `python -m pip install -r requirements.txt -r requirements-dev.txt` works; `pytest` discovers an empty/minimal suite; two sample input PDFs are saved under `tests/fixtures/`

---

## Phase 3: User Story 3 - Lock behavior before changing it (Priority: P1)

**Goal**: Executable characterization suite encoding the **desired** geometric/profile
contract; known defects fail; already-correct helpers stay green. Also install the
**golden PDF net** so post-refactor outputs can be proven byte-identical to the
pre-refactor (post-fix) baselines.

**Independent Test**: `python -m pytest tests/ -v` discovers unit + integration
tests; failures map only to audited defects; correct cases (e.g. `mm_to_pt`,
even-page classification) pass; golden compare harness exists for ≥2 sample
outputs

### Characterization tests (write first; expect failures on known bugs)

- [ ] T011 [P] [US3] Unit tests for `mm_to_pt` in `tests/unit/test_units.py` importing from `pnp_double_with_profile_pdf.py`
- [ ] T012 [P] [US3] Unit tests for `is_back_page` / effective totals for all page-order modes and odd policies in `tests/unit/test_page_order.py`
- [ ] T013 [P] [US3] Unit tests for `load_profile(None)` → identity and missing-key axes → 0 in `tests/unit/test_profile_load.py` (assert desired contract; expect fail on sample defaults)
- [ ] T014 [P] [US3] Unit tests for missing/invalid/comment profile path errors in `tests/unit/test_profile_load.py` (desired: actionable failure, not silent sample merge)
- [ ] T015 [P] [US3] Unit tests for `build_back_matrix` / vector matrix construction (no `fitz.Matrix(rotation=…)`) in `tests/unit/test_vector_matrix.py`
- [ ] T016 [P] [US3] Unit tests for raster sign helpers (+rot clockwise via PIL negate; +Y downward → ReportLab placement) in `tests/unit/test_raster_signs.py`
- [ ] T017 [P] [US3] Integration test: vector mode with non-zero profile — backs move, fronts identity — in `tests/integration/test_vector_geometry.py`
- [ ] T018 [P] [US3] Integration test: shift-only profile — vector backs ≠ identity copy — in `tests/integration/test_vector_geometry.py`
- [ ] T019 [P] [US3] Integration test: `--mode auto` recoverable vector failure → stderr fallback + raster output in `tests/integration/test_auto_fallback.py`
- [ ] T020 [P] [US3] Integration/CLI tests: missing PDF, missing `--profile` path, invalid/comment JSON → stderr + non-zero exit in `tests/integration/test_cli_errors.py`
- [ ] T021 [P] [US3] Integration/CLI test: no profile / no overrides → reported identity corrections in `tests/integration/test_cli_identity.py`
- [ ] T022 [P] [US3] Integration/CLI test: `--on-odd warn` emits stderr for odd `fronts_then_backs` in `tests/integration/test_odd_warn.py`
- [ ] T023 [P] [US3] Integration/CLI test: batch `--auto-detect-smart` must not `NameError` (clear disable message) in `tests/integration/test_batch_smart_detect.py`

### Golden sample outputs (refactor no-drift net)

> Capture **desired-contract** baselines only — never freeze pre-fix buggy
> silent no-ops as goldens. Initial files may be placeholders; **regenerate and
> commit** after plan Phase 2 fixes (see T046) before structural refactor.

- [ ] T024 [US3] Add PDF compare helper (byte-identical file compare, or deterministic content-stream/hash if metadata timestamps differ) in `tests/helpers/pdf_compare.py` and wire via `tests/conftest.py`
- [ ] T025 [US3] Add golden generation script `tests/fixtures/generate_goldens.py` that runs the main CLI on the two sample inputs and writes baselines under `tests/fixtures/golden/` (at minimum: identity vector on `sample_interleaved.pdf`, and non-zero profile vector on the same input)
- [ ] T026 [US3] Run generator (or document deferred regen) and **save** at least two golden output PDFs: `tests/fixtures/golden/out_identity_vector.pdf` and `tests/fixtures/golden/out_nonzero_vector.pdf`
- [ ] T027 [US3] Integration test: live CLI output for those same two scenarios must be **identical** to the saved goldens in `tests/integration/test_golden_outputs.py` (gate for US5 refactor; may stay skipped/xfail until T046 regenerates post-fix goldens)

**Checkpoint**: Suite runs; green only for already-correct behavior; red cases map to plan Phase 2 fix list; golden harness + ≥2 sample output paths exist under `tests/fixtures/golden/`

---

## Phase 4: User Story 1 - Restore trustworthy back-page alignment (Priority: P1) 🎯 MVP

**Goal**: Preferred-path transforms apply; auto fallback works; raster signs match
calibration guide; fronts stay unmodified

**Independent Test**: CLI with non-zero profile on even-page fixture in `vector`
and `raster`/`auto`; characterization geometry/fallback tests from US3 pass

### Implementation

- [ ] T028 [US1] Fix vector rotation construction to positional `fitz.Matrix(degrees)` (remove `rotation=`) in `pnp_double_with_profile_pdf.py` (`build_back_matrix` / related helpers)
- [ ] T029 [US1] Apply back rotation+shift via a PyMuPDF placement API that actually transforms content (do not rely on ignored `matrix=` on `show_pdf_page`) in `pnp_double_with_profile_pdf.py`
- [ ] T030 [US1] Replace non-existent `fitz.FitzError` handling with recoverable `(TypeError, RuntimeError, OSError, ValueError)` and stderr fallback notice + `raster_fallback` in `pnp_double_with_profile_pdf.py`
- [ ] T031 [US1] Align raster rotation sign with calibration guide (negate angle for PIL clockwise contract) in `pnp_double_with_profile_pdf.py`
- [ ] T032 [US1] Align raster Y placement with +Y-downward contract (ReportLab canvas conversion) in `pnp_double_with_profile_pdf.py`
- [ ] T033 [US1] Re-run and confirm `tests/unit/test_vector_matrix.py`, `tests/unit/test_raster_signs.py`, `tests/integration/test_vector_geometry.py`, and `tests/integration/test_auto_fallback.py` pass

**Checkpoint**: US1 acceptance scenarios / SC-001 geometry cases green; fronts unmodified

---

## Phase 5: User Story 2 - Predictable profiles and actionable failures (Priority: P1)

**Goal**: Identity defaults; missing/invalid profiles and PDFs yield actionable
stderr + non-zero exit — never silent sample skew or raw traceback UX

**Independent Test**: Invoke CLI with no profile, missing profile, comment/invalid
JSON, missing PDF; confirm messages, exit codes, identity corrections

### Implementation

- [ ] T034 [US2] Change default `back_corrections` to identity (0, 0, 0) when no `--profile` and no CLI overrides in `pnp_double_with_profile_pdf.py`
- [ ] T035 [US2] Error on missing `--profile` path (stderr + non-zero exit; no silent sample merge) in `pnp_double_with_profile_pdf.py`
- [ ] T036 [US2] Map invalid JSON / comment-bearing profiles to actionable stderr messages + non-zero exit in `pnp_double_with_profile_pdf.py`
- [ ] T037 [US2] Map missing/unreadable input PDFs to actionable stderr + non-zero exit (no default raw traceback UX) in `pnp_double_with_profile_pdf.py`
- [ ] T038 [US2] Ensure CLI overrides (`--rot` / `--shiftx` / `--shifty`) win over profile axes; missing profile keys remain identity in `pnp_double_with_profile_pdf.py`
- [ ] T039 [US2] Re-run and confirm `tests/unit/test_profile_load.py`, `tests/integration/test_cli_errors.py`, and `tests/integration/test_cli_identity.py` pass

**Checkpoint**: US2 / SC-002 / SC-003 satisfied

---

## Phase 6: User Story 4 - Honest page-order and odd-page policies (Priority: P2)

**Goal**: `--on-odd warn` actually warns; page classification matches docs for all modes

**Independent Test**: Odd/even fixtures through each order mode and odd policy;
stderr warning for warn; back indices match published rules

### Implementation

- [ ] T040 [US4] Emit stderr warning when `order=fronts_then_backs`, page count odd, and `--on-odd warn` in `pnp_double_with_profile_pdf.py`
- [ ] T041 [US4] Verify/fix page classification for `interleaved`, `fronts_then_backs`, `last_back`, `single_sided` against help/docs in `pnp_double_with_profile_pdf.py`
- [ ] T042 [US4] Re-run and confirm `tests/unit/test_page_order.py` and `tests/integration/test_odd_warn.py` pass

**Checkpoint**: US4 / FR-009–FR-010 green

---

## Phase 7: User Story 6 - Dependable install and I/O hygiene (Priority: P3) — safe-save + install path

**Goal**: Unified safe-save across writers; documented install from tracked deps
(safe-save is a plan Phase 2 gate; finish before structural refactor)

**Independent Test**: Same-path and distinct-path saves for vector and raster;
fresh env install from `requirements*.txt` runs main CLI + pytest

### Implementation

- [ ] T043 [US6] Unify raster same-path save to temp-file + `os.replace` (with copy fallback) matching vector `safe_save` in `pnp_double_with_profile_pdf.py`
- [ ] T044 [P] [US6] Add integration coverage for distinct-path and same-path saves in both modes in `tests/integration/test_safe_save.py`
- [ ] T045 [US6] Point README install instructions at `requirements.txt` / `requirements-dev.txt` in `README.md`
- [ ] T046 [US6] Regenerate and **commit** post-fix golden PDFs via `tests/fixtures/generate_goldens.py` into `tests/fixtures/golden/`; enable `tests/integration/test_golden_outputs.py` so both sample scenarios pass identical-output asserts (pre-refactor baseline)
- [ ] T047 [US6] Confirm install + suite smoke per `specs/001-codebase-quality/quickstart.md` (no personal/ad-hoc PDFs outside fixtures committed)

**Checkpoint**: Plan Phase 2 exit gate — P1 suite green including safe-save **and** golden identity tests; ready for refactor

---

## Phase 8: User Story 5 - Safer structure without changing the product contract (Priority: P2)

**Goal**: Extract pure geometry/profile modules; disable incomplete batch smart
detect honestly; keep experimental tools labeled; suite stays green with
**identical** CLI PDF output vs pre-refactor goldens

**Independent Test**: Same characterization suite still passes after extraction;
`tests/integration/test_golden_outputs.py` proves refactored output is identical
to saved goldens for both sample scenarios; `--auto-detect-smart` returns clear
unavailable error; tools docs match reality

### Implementation

- [ ] T048 [US5] Extract units, page-order, and sign/matrix helpers into `geometry.py`; update imports in `pnp_double_with_profile_pdf.py`
- [ ] T049 [US5] Extract load/validate/merge profile logic into `profiles.py`; update imports in `pnp_double_with_profile_pdf.py`
- [ ] T050 [P] [US5] Optionally extract shared safe-save / thin writer helpers into `io_pdf.py` if it reduces duplication without API churn
- [ ] T051 [US5] Disable `tools/pnp_batch_align.py` `--auto-detect-smart` with clear unavailable/experimental stderr + non-zero exit; propagate worker non-zero exits
- [ ] T052 [US5] Update unit/integration imports to use `geometry.py` / `profiles.py` where tests target pure logic (`tests/unit/`)
- [ ] T053 [P] [US5] Label `tools/pnp_double_with_profile_img.py` experimental and document deferred OpenCV/FPDF extras (or “out of slice”) in `tools/README.md` and script docstring
- [ ] T054 [P] [US5] Align `tools/README.md` listed scripts with files that actually exist under `tools/`
- [ ] T055 [US5] Re-run full `tests/` suite including `tests/integration/test_golden_outputs.py`; confirm refactored outputs are **identical** to `tests/fixtures/golden/*.pdf` (no geometric drift)

**Checkpoint**: FR-012 / FR-013 / FR-019; Separation of Concerns improved; suite green; golden identity holds

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Typing, docs coherence, hygiene, final validation

- [ ] T056 [P] Add Python 3.9+ type annotations on new/substantially edited code in `geometry.py`, `profiles.py`, and edited sections of `pnp_double_with_profile_pdf.py`
- [ ] T057 [P] Update `README.md` Features so vector-first, back-only correction, and profile reuse claims match runtime + suite
- [ ] T058 [P] Align `docs/calibration_guide.md` sign conventions and odd/profile notes with implemented behavior (call out intentional contract fixes)
- [ ] T059 Remove duplicated dead `load_profile` / unused paths after extraction in `pnp_double_with_profile_pdf.py` and in-scope tools
- [ ] T060 Run full quickstart validation from `specs/001-codebase-quality/quickstart.md` (pytest + smoke CLI + failure UX + odd warn + batch smart-detect + golden identity)
- [ ] T061 Final hygiene check: `git status` shows no personal profiles, secrets, or ad-hoc generated alignment PDFs staged outside `tests/fixtures/` (FR-020 / SC-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US3 (Phase 3)**: Depends on Foundational — **blocks all fix/refactor stories** (FR-011); includes golden harness + ≥2 sample output paths
- **US1 (Phase 4)**: Depends on US3 characterization existing (failing tests for geometry)
- **US2 (Phase 5)**: Depends on US3; can proceed after or parallel to US1 if different areas, but same file (`pnp_double_with_profile_pdf.py`) → prefer sequential after US1
- **US4 (Phase 6)**: Depends on US3; prefer after US1/US2 (same monolith file)
- **US6 safe-save/install (Phase 7)**: Depends on US1 writers existing; regenerates post-fix goldens (T046); completes plan Phase 2 gate before US5
- **US5 (Phase 8)**: Depends on plan Phase 2 exit + committed goldens; refactored output must stay identical (T055)
- **Polish (Phase 9)**: Depends on US5 (and desired stories complete)

### User Story Dependencies

- **User Story 3 (P1)**: First story after foundation — characterization net only
- **User Story 1 (P1)**: After US3 — geometry/fallback/signs MVP
- **User Story 2 (P1)**: After US3 (prefer after US1 to reduce merge conflict on monolith)
- **User Story 4 (P2)**: After US3; prefer after US1/US2
- **User Story 6 (P3)**: Safe-save before US5; docs/install can finish in Phase 7/9
- **User Story 5 (P2)**: Only after Phase 2 exit gate (suite green for P1 fixes)

### Within Each User Story

- Characterization tests (US3) MUST exist and fail on known bugs before fixes
- Fixes make the corresponding US3 tests pass
- Regenerate committed goldens (T046) only after desired-contract suite is green
- Extract modules only after suite green **and** golden baselines committed
- After refactor, `test_golden_outputs.py` MUST still pass (identical vs goldens)
- Story complete before moving to next plan gate

### Parallel Opportunities

- T002–T004 (Setup) in parallel
- T006–T009 (fixtures) in parallel after T005
- T011–T023 (US3 characterization test files) largely in parallel once fixtures exist
- T024–T027 (golden harness) after sample inputs exist; sequential among themselves
- US1 vs US2 implementation: **not** parallel on the same monolith without coordination
- T053–T054 and T056–T058 (docs/typing) in parallel during later phases

---

## Parallel Example: User Story 3

```bash
# Launch characterization unit tests together after fixtures exist:
Task: "Unit tests for mm_to_pt in tests/unit/test_units.py"
Task: "Unit tests for page-order in tests/unit/test_page_order.py"
Task: "Unit tests for profile load in tests/unit/test_profile_load.py"
Task: "Unit tests for vector matrix in tests/unit/test_vector_matrix.py"
Task: "Unit tests for raster signs in tests/unit/test_raster_signs.py"

# Launch integration/CLI characterization together:
Task: "Integration vector geometry in tests/integration/test_vector_geometry.py"
Task: "Integration auto fallback in tests/integration/test_auto_fallback.py"
Task: "CLI errors in tests/integration/test_cli_errors.py"
Task: "CLI identity in tests/integration/test_cli_identity.py"
Task: "Odd warn in tests/integration/test_odd_warn.py"
Task: "Batch smart detect in tests/integration/test_batch_smart_detect.py"

# Golden net (after sample PDFs exist; sequential):
Task: "PDF compare helper in tests/helpers/pdf_compare.py"
Task: "Golden generator tests/fixtures/generate_goldens.py"
Task: "Save out_identity_vector.pdf + out_nonzero_vector.pdf under tests/fixtures/golden/"
Task: "Identical-output asserts in tests/integration/test_golden_outputs.py"
```

## Parallel Example: User Story 5 (after suite green + goldens committed)

```bash
# Docs/labeling can run while extraction is reviewed:
Task: "Label img tool experimental in tools/README.md"
Task: "Align tools/README.md script list with tools/"

# After extract: must prove identical outputs
Task: "Re-run tests/integration/test_golden_outputs.py vs tests/fixtures/golden/"
```

---

## Implementation Strategy

### MVP First (Characterization + User Story 1)

1. Complete Phase 1: Setup (incl. `tests/fixtures/golden/`)
2. Complete Phase 2: Foundational — **commit two sample input PDFs**
3. Complete Phase 3: US3 characterization + golden harness (≥2 output baselines)
4. Complete Phase 4: US1 geometry/fallback/signs
5. **STOP and VALIDATE**: US1 independent test + related US3 cases green
6. Demo trustworthy back-page alignment on fixture PDF

### Incremental Delivery

1. Setup + Foundational → harness + sample inputs ready
2. US3 → failing contract suite + golden compare infrastructure
3. US1 → vector/raster geometry MVP
4. US2 → honest profiles and CLI errors
5. US4 → odd warn + page-order honesty
6. US6 safe-save/install → **regenerate post-fix goldens** → plan Phase 2 exit gate
7. US5 → module extraction; **golden identity must still hold**
8. Polish → typing, README/calibration, quickstart, hygiene

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (sample PDFs committed)
2. Split US3 characterization test files across authors (different paths); one owner for golden harness
3. Serialize US1 → US2 → US4 → US6 (incl. golden regen) on the monolith
4. After green suite + committed goldens: one author extracts `geometry.py`/`profiles.py`; another updates tools docs; both verify `test_golden_outputs.py`

---

## Notes

- [P] tasks = different files, no dependencies on incomplete work
- [Story] label maps task to US1–US6 for traceability
- Do **not** freeze *buggy* golden outputs (silent no-ops, sample 0.30°/1 mm defaults) as the desired geometric contract
- **Do** commit ≥2 post-fix sample output PDFs under `tests/fixtures/golden/` and require refactored CLI output to be identical (T027 / T046 / T055)
- Image-tool OpenCV/FPDF rewrite is out of first delivery slice (R11)
- Prefer vector path; no deep performance work beyond avoiding unnecessary rasterization
- Commit after each task or logical group; stop at checkpoints to validate independently
