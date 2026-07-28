# Research: Reliable Batch Smart Page-Order Detect

**Feature**: `002-smart-detect`  
**Date**: 2026-07-25  
**Related**: [spec.md](./spec.md), [plan.md](./plan.md)

## R1 — Complete heuristic vs replace decision rule

**Decision**: Reuse the existing low-resolution page fingerprint + cosine
similarity infrastructure, **implement the missing `avg_sim_block` helper**, and
**replace** `decide_by_visual_similarity`’s pair-avg vs halves-avg predicate with
a **common-back cluster** rule tailored to PnP layouts.

**Common-back cluster (even page count)**:

1. Score **interleaved candidacy**: average similarity among **odd-index** pages
   (typical shared card backs in F,B,F,B…).
2. Score **fronts_then_backs candidacy**: average similarity among **second-half**
   pages (typical shared backs when all fronts precede all backs).
3. If one score is ≥ absolute threshold **and** ≥ the other by a margin → choose
   that mode with a confident `visual:…` reason.
4. Otherwise → `--even-default` with an explicit tie/fallback reason.

Initial constants (tunable only if fixtures demand it; document in code/comments):
absolute threshold **0.80**, margin **0.03** (same numeric spirit as the prior
helper so behavior stays interpretable).

**Rationale**: Feature `001` disabled the flag because `avg_sim_block` was
undefined (crash). Completing that helper alone does not meet “fiable”: the old
rule rewarded high consecutive-pair similarity for `interleaved`, which fights
typical front/back card pairs. Spec FR-005 explicitly allows completion **or**
replacement if reliability criteria hold. Common-back clustering matches the
domain and needs no new dependencies.

**Alternatives considered**:
- Only implement `avg_sim_block` and keep old `decide_by_visual_similarity` —
  rejected as likely to fail SC-005 on gold interleaved vs halves fixtures.
- ML / embedding models / OpenCV — rejected (Practical Simplicity, new deps).
- Filename-only detection — rejected; insufficient for mixed folders without
  naming discipline (spec requires content-based path for even pages).

## R2 — Precedence and fallbacks

**Decision**: Keep the existing precedence already sketched in
`detect_order_smart`:

1. Filename hint (`NAME_HINTS`) → win + `name-hint:…` reason  
2. Page-count: `total <= 1` → `single_sided`; odd `total` → `last_back`  
3. Even: content-based common-back rule  
4. Inconclusive → `args.even_default` + tie/fallback reason  
5. Unreadable/unopenable PDF → `even_default` + `open-fallback` (no crash)

Name hints that conflict with strong visual evidence still win; users rename to
force visual-only (spec edge case).

**Rationale**: Matches FR-003–007 and Assumptions; minimizes user surprise vs the
pre-disable design.

**Alternatives considered**:
- Abort file or whole batch on low confidence — rejected; Assumptions prefer
  even-default continuation.
- Prefer visual over filename — rejected; explicit names are user intent.

## R3 — Performance / large PDFs

**Decision**: Fingerprints remain low-DPI thumbnails (existing ~72 DPI, small
thumb size). If page count **N > 40**, compute fingerprints only for an
evenly spaced sample of up to **40** page indices (always including enough
indices to evaluate both odd-set and second-half candidacy when N is even).
Document the cap in tools README. Target: detection &lt; 30s for ≤100 pages
(SC-002).

**Rationale**: Spec allows a sampling policy; full render of every page at even
low DPI can be slow for large hobbyist exports.

**Alternatives considered**:
- Always fingerprint all pages — simpler but risks SC-002 on large N.
- Raise DPI for accuracy — costlier; fixtures should pass at low DPI first.

## R4 — Re-enable CLI surface

**Decision**: Remove the early `SystemExit(2)` “unavailable” gate when
`--auto-detect-smart` is set. Restore argparse help to describe working smart
detection (experimental batch tool). Keep batch tool labeled experimental in
docs; “available” means the flag runs the detector.

**Rationale**: FR-001, SC-002, SC-004; supersedes `001` R7 disable decision for
this feature.

**Alternatives considered**:
- New flag name (`--auto-detect-v2`) — unnecessary churn; same flag is fine.
- Silent ignore of the flag — dishonest; rejected in `001` already.

## R5 — Testing strategy

**Decision**:

| Layer | Coverage |
|-------|----------|
| Unit | `name_hint_to_order`, `detect_order_by_page_count`, `avg_sim_block`, common-back decision (synthetic fingerprint vectors), sampling index selection |
| Integration | Batch CLI with `--auto-detect-smart` on fixture dir; assert per-file `order='…'` / reason prefixes; no disable wording; exit 0 when worker succeeds (identity/no profile OK) |
| Fixtures | Reuse `sample_interleaved.pdf`, `sample_odd.pdf`; add `sample_fronts_then_backs.pdf`, `sample_single.pdf`, `sample_ambiguous_even.pdf`; name-hint via copy named e.g. `game_interleaved.pdf` |

Replace disable-oriented `test_batch_smart_detect_disabled` with enablement
assertions (or delete and add new tests in the same module).

**Rationale**: FR-010, SC-001/SC-003/SC-005; characterization-first.

**Alternatives considered**:
- Integration-only — weaker for pure math/decision regressions.
- Live printer validation — out of scope per Assumptions.

## R6 — Separation / code location

**Decision**: Keep detection helpers in `tools/pnp_batch_align.py` for this
feature. Extract to a shared module only if a follow-up needs the same detector
in the main CLI (explicitly out of scope per FR-013).

**Rationale**: Practical Simplicity; avoid drive-by package layout.

**Alternatives considered**:
- New `tools/page_order_detect.py` — optional cleanup later; not required for MVP.
- Wire into main CLI `--order auto` — out of scope (FR-013).

## R7 — Documentation touchpoints

**Decision**: Update `tools/README.md` (smart detect available, precedence,
confidence/fallback, sampling note, experimental batch label). Update root
`README.md` only if it still claims the flag is disabled. No calibration-guide
or profile-schema changes (profiles untouched).

**Rationale**: FR-011, Safe I/O & docs gate; constitution requires docs when
user-visible tool behavior changes.

## Resolved clarifications

No Technical Context `NEEDS CLARIFICATION` items remained after research; all
algorithm, fallback, performance, and scope choices are decided above.
