# Feature Specification: Reliable Batch Smart Page-Order Detect

**Feature Branch**: `002-smart-detect`

**Created**: 2026-07-25

**Status**: Draft

**Input**: User description: "para smart-detect \"-auto-detect-smart — hoy está deshabilitado a propósito; completar heurística o sustituirla por algo fiable\""

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enable working smart page-order detection (Priority: P1)

A maker batch-aligns a folder of PnP PDFs whose page orders differ (interleaved, fronts-then-backs, last-back, single-sided). They turn on smart page-order detection. For each PDF, the batch tool chooses a page-order mode that matches the document’s real structure closely enough that backs receive corrections and fronts stay unmodified—without the feature being blocked as unavailable.

**Why this priority**: The flag exists and is documented as the path for mixed folders, but it is intentionally disabled after incomplete heuristics caused crashes. Without a working detector, users must guess order per file or rename files.

**Independent Test**: Run the batch tool with smart detection on a fixture folder containing at least one PDF per supported order pattern; confirm each file is assigned the expected order (or an explicitly documented safe fallback) and that alignment proceeds with non-zero exit only on real failures—not on “feature disabled.”

**Acceptance Scenarios**:

1. **Given** a directory of PDFs with known page-order layouts and smart detection enabled, **When** the user runs the batch aligner, **Then** the tool does not refuse with an “unavailable / experimental disabled” error solely because the flag is set.
2. **Given** an even-page interleaved fixture and an even-page fronts-then-backs fixture, **When** smart detection runs, **Then** each is classified as the matching order mode (not swapped).
3. **Given** a single-page PDF and an odd-page PDF that should use last-back style handling, **When** smart detection runs, **Then** they are classified as `single_sided` and `last_back` respectively (or the documented equivalents for those counts).

---

### User Story 2 - Honest confidence and safe fallbacks (Priority: P1)

When the detector cannot decide with acceptable confidence, the user sees why and gets a predictable fallback—never a silent wrong classification presented as certain, and never an undefined-name or similar crash.

**Why this priority**: Misclassifying page order silently corrupts fronts or leaves backs uncorrected; CLI-First and Geometric Precision demand honest messaging.

**Independent Test**: Feed ambiguous or unreadable PDFs through smart detection; assert reported reason strings, fallback order, and exit behavior match the documented policy.

**Acceptance Scenarios**:

1. **Given** an even-page PDF whose structure does not clearly match interleaved vs fronts-then-backs under the reliability rules, **When** smart detection runs, **Then** the tool applies the user’s configured even-page default and reports a clear reason that it fell back (not a claim of high-confidence visual match).
2. **Given** a PDF that cannot be opened or analyzed, **When** smart detection is attempted, **Then** the tool reports a clear failure or fallback reason on the error or status stream and does not crash with an uncaught programming error.
3. **Given** a filename that clearly encodes a page-order hint (e.g. interleaved / halves / last_back / single), **When** smart detection runs, **Then** that hint takes precedence over weaker visual cues, and the status line records that the decision came from the name hint.

---

### User Story 3 - Documented, testable behavior for contributors (Priority: P2)

A contributor can verify smart detection against fixed fixtures and understand when results are confident vs fallback. Tools docs state that the flag works, what it decides, and that the batch tool remains optional/experimental relative to the main single-PDF workflow.

**Why this priority**: Characterization-first and Practical Simplicity require locked behavior before iterating on heuristics; docs must match reality after re-enablement.

**Independent Test**: Run the automated checks for smart detection alone; follow tools documentation and reproduce the documented invocation without hitting a disable message.

**Acceptance Scenarios**:

1. **Given** the repository after this feature, **When** automated checks for known order fixtures run, **Then** confident classifications match expected orders and fallback cases assert the documented default-plus-reason behavior.
2. **Given** tools documentation for the batch aligner, **When** a new user reads it, **Then** `--auto-detect-smart` is described as available (with limits/confidence notes), not as disabled/unavailable.
3. **Given** smart detection is used in the batch tool, **When** processing completes for a PDF, **Then** the user-visible status includes the chosen order and a short reason suitable for auditing misclassifications.

---

### Edge Cases

- Empty input directory: no PDFs → clear message; no crash; exit success or documented empty-input status.
- Mixed folder: some PDFs name-hinted, some visual-only, some odd/single → each file decided independently.
- Very short even PDFs (2 pages): detector still chooses interleaved vs fronts-then-backs (or fallback) without crashing.
- Very large page counts: detection completes in reasonable wall time for hobbyist batch sizes, or documents a page-cap / sampling policy if full-document analysis is too costly.
- Filename hints that conflict with strong visual evidence: name hint wins (documented); user can rename to force visual-only.
- Worker alignment failure after a correct order choice: batch still propagates non-zero worker status (existing batch contract); smart detect does not hide worker failures.
- Same even-default configured as both “tie fallback” and user’s preference: status still distinguishes fallback-from-tie vs confident match when possible.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The batch aligner’s smart page-order detection option MUST be usable end-to-end: when enabled, it MUST select a documented page-order mode per input PDF and continue the batch workflow (subject to other errors), not exit solely because the feature is disabled.
- **FR-002**: Smart detection MUST support deciding among the documented order modes needed for duplex alignment: at least `interleaved`, `fronts_then_backs`, `last_back`, and `single_sided`.
- **FR-003**: For single-page inputs, smart detection MUST select `single_sided` (or equivalent documented single-page handling).
- **FR-004**: For odd page counts (greater than one), smart detection MUST select `last_back` unless a stronger documented rule (e.g. filename hint) overrides.
- **FR-005**: For even page counts, smart detection MUST distinguish `interleaved` vs `fronts_then_backs` using a completed and validated decision procedure—either a finished/fixed form of the existing visual-similarity approach or a replacement method that meets the same reliability success criteria. Incomplete helpers or undefined steps MUST NOT remain on the enabled path.
- **FR-006**: Filename-based order hints MUST be honored when present and MUST be reported in the decision reason.
- **FR-007**: When even-page visual (or replacement) evidence is inconclusive under documented confidence rules, the tool MUST use the user-configured even-page default and MUST report that the decision was a fallback/tie, not a confident detection.
- **FR-008**: Smart detection MUST NOT crash with programming errors (e.g. missing helpers) on valid PDFs or on expected open/analysis failures; failures MUST surface as clear messages and defined fallback or non-zero exit behavior.
- **FR-009**: Per-PDF status output MUST include the chosen order and a brief human-readable reason (hint, page-count rule, confident visual/replacement match, or fallback).
- **FR-010**: Automated characterization or fixture-based checks MUST cover at least: interleaved even, fronts-then-backs even, odd/`last_back`, single-page, name-hint override, and inconclusive even-page fallback.
- **FR-011**: User-facing tools documentation MUST state that smart detection is available, describe precedence (name hint → page-count rules → content-based decision → even default), and note remaining limits (e.g. experimental batch tool, confidence/fallback behavior).
- **FR-012**: Smart detection MUST NOT apply alignment transforms itself; it only chooses page-order for the existing aligner worker so that back-only corrections remain the alignment contract.
- **FR-013**: Enabling smart detection MUST NOT change the main single-file aligner contract; the feature lives in the optional batch workflow unless a later spec explicitly expands scope.

### Key Entities

- **Page-order decision**: Chosen mode (`interleaved`, `fronts_then_backs`, `last_back`, `single_sided`) plus reason code/text and whether the decision was confident or a fallback.
- **Input PDF (batch item)**: One file in the batch folder; independently ordered, then passed to the aligner worker with that order.
- **Even-page default**: User-configured preference used only when content-based evidence is inconclusive for even-page PDFs.
- **Filename hint**: Pattern in the base filename that maps to a page-order mode and outranks weaker content-based cues.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a fixed fixture set with known orders (at least one PDF per mode in FR-002, plus a name-hint case), smart detection assigns the expected order for ≥95% of confident-path cases; remaining cases are only those explicitly marked as inconclusive fixtures and MUST use the documented fallback—not a wrong “confident” label.
- **SC-002**: With smart detection enabled on the fixture folder, the batch command completes the detect-and-dispatch path without a “feature unavailable/disabled” refusal; wall time for detection alone stays under 30 seconds per typical hobbyist PDF (≤100 pages) on a standard desktop, or documents and enforces a sampling strategy that meets that bound.
- **SC-003**: 100% of automated smart-detection checks for the documented fixtures pass before the feature is considered done; zero checks allow an uncaught programming error on the enabled path.
- **SC-004**: A new user following tools documentation can enable smart detection and interpret the per-file order+reason line without consulting source code; documentation no longer describes the flag as disabled.
- **SC-005**: Misclassification rate on confident decisions for the gold interleaved vs fronts-then-backs fixtures is 0% (they must not be swapped); any residual ambiguity is handled only via the fallback path with an explicit reason.

## Assumptions

- Scope is the optional batch aligner workflow and its smart-detection option; the main single-PDF CLI continues to require explicit `--order` (or its existing defaults) unless a future feature expands auto-detect there.
- Completing the existing visual-similarity heuristic is acceptable if it becomes reliable under SC-001/SC-005; replacing it with another content-based method is also acceptable if it meets the same user-visible contract (modes, precedence, fallbacks, messaging). Planning chooses the approach; this spec requires reliability, not a particular algorithm.
- Filename-hint precedence over visual/content cues remains desirable and is kept.
- Even-page ties continue to use the user-configured even-page default rather than aborting the whole batch for that file.
- The batch tool remains labeled experimental/optional relative to the main aligner; “available” means the flag works as documented, not that it becomes the primary product path.
- Reliability is proven with repository fixtures and checks, not by requiring live printer runs for every change.
- No new user-facing page-order modes beyond those already documented for the aligner.
- Prior disablement in the quality-remediation work was intentional and is superseded by this feature once checks pass.
