# Tasks: Reliable Batch Smart Page-Order Detect

**Input**: Design documents from `/specs/002-smart-detect/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by FR-010 / plan Phase A (characterization-first). Write failing
tests before re-enabling `--auto-detect-smart`.

**Organization**: Phases follow plan order — Setup → fixtures/foundation →
US1 enablement → US2 confidence/fallbacks → US3 docs/tests polish → polish.
Do not remove the disable gate until characterization fixtures and failing
enablement tests exist.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Batch tool: `tools/pnp_batch_align.py`
- Docs: `tools/README.md`, `README.md` (only if it mentions smart-detect disable)
- Tests: `tests/unit/`, `tests/integration/`, `tests/fixtures/`, `tests/conftest.py`
- Contract: `specs/002-smart-detect/contracts/batch-smart-detect.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm workspace ready for smart-detect work (no new deps)

- [ ] T001 Verify existing stack (`requirements.txt`, `requirements-dev.txt`) already provides PyMuPDF, Pillow, pytest; note no new runtime deps for this feature in `specs/002-smart-detect/plan.md` checklist comment or skip if already true
- [ ] T002 [P] Skim `tools/pnp_batch_align.py` disable gate and incomplete `avg_sim_block` references; list touch points in a short note under `specs/002-smart-detect/` only if needed for implementers (optional; otherwise proceed to fixtures)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fixtures and conftest helpers required before enablement work

**⚠️ CRITICAL**: Do not remove the `--auto-detect-smart` disable gate until this phase’s fixtures exist and failing enablement tests are written (Phase 3)

- [ ] T003 [P] Create and commit even-page fronts-then-backs fixture PDF at `tests/fixtures/sample_fronts_then_backs.pdf` (distinct shared-back second half vs interleaved sample)
- [ ] T004 [P] Create and commit single-page fixture PDF at `tests/fixtures/sample_single.pdf`
- [ ] T005 [P] Create and commit ambiguous/inconclusive even-page fixture at `tests/fixtures/sample_ambiguous_even.pdf` (both cluster scores weak or tied under thresholds)
- [ ] T006 [P] Extend `tests/fixtures/README.md` with provenance for the new smart-detect fixtures
- [ ] T007 Add pytest fixtures in `tests/conftest.py` for `sample_fronts_then_backs`, `sample_single`, and `sample_ambiguous_even`

**Checkpoint**: New fixtures committed; `pytest` still discovers existing suite; disable gate still present

---

## Phase 3: User Story 1 - Enable working smart page-order detection (Priority: P1) 🎯 MVP

**Goal**: `--auto-detect-smart` runs end-to-end and classifies interleaved /
fronts_then_backs / single / last_back correctly on gold fixtures

**Independent Test**: Batch CLI with `--auto-detect-smart` on a fixture folder;
no “unavailable/disabled” refusal; expected orders for interleaved +
fronts_then_backs + single + odd; see `specs/002-smart-detect/quickstart.md`

### Tests for User Story 1 (write first; expect fail while disabled / incomplete)

- [ ] T008 [P] [US1] Unit tests for `name_hint_to_order` and `detect_order_by_page_count` in `tests/unit/test_smart_detect.py`
- [ ] T009 [P] [US1] Unit tests for `avg_sim_block` (synthetic fingerprint lists) in `tests/unit/test_smart_detect.py`
- [ ] T010 [P] [US1] Unit tests for common-back cluster decision (odd-cluster vs second-half; thresholds T=0.80, M=0.03) in `tests/unit/test_smart_detect.py`
- [ ] T011 [US1] Replace disable-oriented assertions in `tests/integration/test_batch_smart_detect.py` with enablement tests: `--auto-detect-smart` must not print unavailable/disabled; classify `sample_interleaved` → interleaved and `sample_fronts_then_backs` → fronts_then_backs; single → `single_sided`; odd → `last_back`

### Implementation for User Story 1

- [ ] T012 [US1] Implement missing `avg_sim_block` helper in `tools/pnp_batch_align.py`
- [ ] T013 [US1] Replace pair-vs-halves `decide_by_visual_similarity` with common-back cluster rule per `specs/002-smart-detect/research.md` R1 in `tools/pnp_batch_align.py`
- [ ] T014 [US1] Wire `detect_order_smart` to use new decision path + existing fingerprints/cosine in `tools/pnp_batch_align.py`
- [ ] T015 [US1] Remove early `SystemExit` disable gate for `--auto-detect-smart` and restore argparse help text as available (experimental batch) in `tools/pnp_batch_align.py`
- [ ] T016 [US1] Confirm `tests/unit/test_smart_detect.py` and enablement cases in `tests/integration/test_batch_smart_detect.py` pass for US1 fixtures

**Checkpoint**: Smart detect flag usable; gold interleaved vs halves not swapped (SC-005)

---

## Phase 4: User Story 2 - Honest confidence and safe fallbacks (Priority: P1)

**Goal**: Name hints win; ties/open failures report clear reasons and use
`--even-default`; no programming crashes

**Independent Test**: Name-hinted copy → `name-hint:…`; ambiguous fixture →
tie/fallback + even-default; unreadable PDF → `open-fallback` without NameError

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit/integration cases for name-hint precedence over visual cues in `tests/unit/test_smart_detect.py` and/or `tests/integration/test_batch_smart_detect.py`
- [ ] T018 [P] [US2] Integration test: `sample_ambiguous_even.pdf` + `--even-default fronts_then_backs` yields fallback reason and that order in `tests/integration/test_batch_smart_detect.py`
- [ ] T019 [P] [US2] Test open/unreadable path returns `open-fallback` (or clear error) without `NameError`/`avg_sim_block` crash in `tests/unit/test_smart_detect.py` or `tests/integration/test_batch_smart_detect.py`

### Implementation for User Story 2

- [ ] T020 [US2] Ensure reason taxonomy prefixes (`name-hint:`, `pages:`, `visual:`, `visual:tie`, `open-fallback`) match `specs/002-smart-detect/data-model.md` in `tools/pnp_batch_align.py`
- [ ] T021 [US2] Implement page-sampling plan for N>40 (evenly spaced ≤40 indices) in `tools/pnp_batch_align.py` per research R3
- [ ] T022 [US2] Add unit coverage for sampling index selection in `tests/unit/test_smart_detect.py`
- [ ] T023 [US2] Confirm US2 tests pass; worker non-zero exits still propagate from batch loop in `tools/pnp_batch_align.py`

**Checkpoint**: Fallbacks honest; no crash on open failure; sampling documented in code comments

---

## Phase 5: User Story 3 - Documented, testable behavior (Priority: P2)

**Goal**: Docs describe available smart detect + precedence; status lines
auditable; suite is the source of truth

**Independent Test**: `grep` docs; run `tests/unit/test_smart_detect.py` +
`tests/integration/test_batch_smart_detect.py`; per-file stdout has order+reason

### Tests / docs for User Story 3

- [ ] T024 [P] [US3] Assert status stdout includes `order=` and reason for each PDF in `tests/integration/test_batch_smart_detect.py`
- [ ] T025 [US3] Update `tools/README.md`: `--auto-detect-smart` available, precedence (name → page-count → content → even-default), sampling note, experimental batch label
- [ ] T026 [P] [US3] Update root `README.md` only if it still claims smart-detect is disabled
- [ ] T027 [US3] Update argparse description/help in `tools/pnp_batch_align.py` to match docs (available, experimental)

**Checkpoint**: Docs no longer say disabled; FR-011 satisfied

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T028 [P] Ensure main PDF suite still passes without depending on smart-detect changes: `python -m pytest tests/ -v`
- [ ] T029 Run validation steps from `specs/002-smart-detect/quickstart.md` and fix any gaps
- [ ] T030 [P] Confirm `pnp_double_with_profile_pdf.py` was not behaviorally changed for this feature (diff review)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Immediate
- **Foundational (Phase 2)**: After Setup — BLOCKS enablement implementation
- **US1 (Phase 3)**: After Foundational; tests before implementation
- **US2 (Phase 4)**: After US1 core re-enable (shares `tools/pnp_batch_align.py`)
- **US3 (Phase 5)**: After US1 (docs reflect working flag); can overlap late US2
- **Polish**: After desired stories complete

### User Story Dependencies

- **US1 (P1)**: MVP — re-enable + correct gold classifications
- **US2 (P1)**: Builds on US1 detect path for fallbacks/sampling/reasons
- **US3 (P2)**: Docs + status assertions; depends on US1 behavior being real

### Parallel Opportunities

- T003–T005 fixture creation in parallel
- T008–T010 unit tests in parallel before T011
- T017–T019 tests in parallel
- T025–T026 docs in parallel

---

## Parallel Example: User Story 1

```bash
# Tests first (expect fail):
Task: "Unit tests name/page-count in tests/unit/test_smart_detect.py"
Task: "Unit tests avg_sim_block in tests/unit/test_smart_detect.py"
Task: "Unit tests common-back decision in tests/unit/test_smart_detect.py"

# Then implement in tools/pnp_batch_align.py (sequential on same file):
Task: "Implement avg_sim_block"
Task: "Replace decision predicate"
Task: "Remove disable gate"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1–2 fixtures
2. Failing enablement/unit tests
3. Implement detect + remove disable gate
4. **STOP**: Validate gold classifications

### Incremental Delivery

1. US1 → flag works on clear fixtures
2. US2 → ties, hints, sampling, open-fallback
3. US3 → docs + audit reasons
4. Polish → full pytest + quickstart

---

## Notes

- [P] = different files / no incomplete-task dependency
- Do not change main aligner `--order` contract
- Detection only chooses order for the worker
- Commit after each logical group; keep fixtures deterministic
