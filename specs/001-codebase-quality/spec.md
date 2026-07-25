# Feature Specification: Codebase Quality Remediation

**Feature Branch**: `001-codebase-quality`

**Created**: 2026-07-25

**Status**: Draft

**Input**: User description: "Analizar la base de código actual para identificar bugs, deuda técnica, código acoplado, áreas de mejora, code smells, problemas de rendimiento y violaciones de mantenibilidad, respetando las reglas definidas en constitution.md. Documentar el comportamiento actual versus el comportamiento deseado."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Restore trustworthy back-page alignment (Priority: P1)

A maker calibrates their printer, saves a profile, and runs the main CLI on a PnP PDF. Back pages receive the documented rotation and X/Y shifts; fronts stay untouched. If the preferred (vector) path cannot complete, the tool falls back to the alternate path with a clear notice and still applies the same correction directions.

**Why this priority**: Without correct, non-silent alignment, the product’s core value (calibrate once, reuse the profile) is broken. Geometric accuracy is a constitution gate.

**Independent Test**: Run the main CLI with a known profile (non-zero rotation and shifts) on a small even-page PDF in preferred mode and in forced alternate mode; visually or via fixture comparison, backs move as documented and fronts do not.

**Acceptance Scenarios**:

1. **Given** a valid profile with non-zero rotation and X/Y shifts and an even-page interleaved PDF, **When** the user runs the main CLI in preferred (vector) mode, **Then** back pages are corrected according to the profile conventions and front pages are unchanged.
2. **Given** the preferred path cannot complete for a recoverable reason, **When** the user runs in automatic mode, **Then** the tool switches to the alternate path, reports that fallback on the error stream, and still applies corrections in the same directions as the preferred path.
3. **Given** a profile that only shifts (no rotation), **When** the user runs the preferred path, **Then** the shift is visibly applied (not a silent copy of the input).

---

### User Story 2 - Predictable profiles and actionable failures (Priority: P1)

A user runs the CLI without a profile, with a missing profile path, with a comment-bearing template mistaken for a runtime profile, or with a missing/corrupt PDF. They get clear messages and non-zero exit status—not raw stack traces as the default experience. Corrections only come from an explicit profile or explicit overrides, not from hidden sample defaults.

**Why this priority**: Calibration-Profile First and CLI-First require an honest profile contract and usable error messages for hobbyists.

**Independent Test**: Invoke the CLI with each failure mode and with no profile; confirm messages, exit codes, and that default corrections are identity unless a profile or override is supplied.

**Acceptance Scenarios**:

1. **Given** no `--profile` and no rotation/shift overrides, **When** the user processes a PDF, **Then** back corrections are identity (zero rotation and zero shifts) unless the user explicitly opts into another documented default policy.
2. **Given** `--profile` points to a missing file, **When** the user runs the CLI, **Then** the tool reports an actionable error on the error stream and exits non-zero (it does not silently substitute sample corrections).
3. **Given** a comment-bearing profile template or invalid JSON is passed as `--profile`, **When** the user runs the CLI, **Then** they see a message explaining that runtime profiles must be valid JSON (and how to obtain one), not an uncaught decode failure as the primary UX.
4. **Given** a missing or unreadable input PDF, **When** the user runs the CLI, **Then** they receive an actionable error and non-zero exit without a default raw traceback.

---

### User Story 3 - Lock behavior before changing it (Priority: P1)

A contributor (human or AI-assisted) needs to fix transforms, profiles, or page-order logic. Before changing those paths, automated characterization checks document today’s intended contract (and fail where today’s code already violates the documented contract). Fixes make those checks pass without introducing silent geometric drift.

**Why this priority**: Constitution requires characterization-first for legacy transform/profile/page-order work; there is currently no test suite.

**Independent Test**: Run the automated check suite alone; critical geometric and profile-contract cases are present and fail on the known broken behaviors until fixed.

**Acceptance Scenarios**:

1. **Given** the repository before transform fixes, **When** characterization checks for rotation, shift, and flip-mode back handling are run, **Then** they fail for the known incorrect behaviors (or clearly assert the documented desired contract).
2. **Given** those checks after remediation, **When** the same suite runs, **Then** all characterization cases for the fixed contract pass.
3. **Given** a change that would invert shift or rotation sign relative to the calibration docs, **When** the suite runs, **Then** at least one check fails.

---

### User Story 4 - Honest page-order and odd-page policies (Priority: P2)

A user processes a PDF with an odd page count in `fronts_then_backs` mode using `--on-odd warn`. They are warned on the error stream. Page classification for all documented order modes matches the help text and calibration docs.

**Why this priority**: Misclassified backs/fronts silently corrupt content; “warn” that never warns violates CLI-First.

**Independent Test**: Feed odd- and even-page fixtures through each order mode and odd policy; assert warnings and which indices are treated as backs.

**Acceptance Scenarios**:

1. **Given** an odd-page PDF, `fronts_then_backs`, and `--on-odd warn`, **When** processing runs, **Then** a warning is emitted on the error stream and processing continues under the documented rule.
2. **Given** each documented page-order mode, **When** pages are classified, **Then** back indices match the published rules (fronts unmodified).

---

### User Story 5 - Safer structure without changing the product contract (Priority: P2)

A maintainer can reason about geometry, profile validation, and CLI messaging as separate concerns. Shared rules (units, page classification, profile merge/validation) are not reimplemented inconsistently across the main entrypoint and optional tools. Experimental tools remain labeled, invocable from the repo root, and do not replace the main workflow.

**Why this priority**: Separation of Concerns and Practical Simplicity enable safe refactors; duplication already causes divergent defaults and broken optional paths.

**Independent Test**: After structural cleanup, the same characterization suite still passes; optional tools either share the validated profile/geometry rules or are explicitly deferred/disabled with docs updated.

**Acceptance Scenarios**:

1. **Given** profile validation and unit conversion rules, **When** the main CLI and any in-scope tools apply a profile, **Then** they interpret the same keys and signs the same way.
2. **Given** an experimental batch “smart detect” path that is incomplete, **When** a user invokes it, **Then** they get a clear “unavailable/experimental” error (or a working implementation)—not an undefined-name crash.
3. **Given** documentation for primary vs optional scripts, **When** a new contributor follows README and tools docs, **Then** listed scripts exist, invocation matches reality, and dependency expectations match the constitution stack (or are clearly marked as optional extras).

---

### User Story 6 - Dependable install and I/O hygiene (Priority: P3)

A contributor installs documented dependencies with a pinned/constrained set, and writers use a consistent safe-save policy when input and output paths collide or when writing large outputs.

**Why this priority**: Version drift already breaks transform APIs; inconsistent same-path handling risks partial or surprising outputs.

**Independent Test**: Fresh environment install from the documented dependency file; same-path and distinct-path save scenarios behave as documented for both output modes.

**Acceptance Scenarios**:

1. **Given** a clean environment, **When** a contributor follows the install instructions, **Then** they get a known-good dependency set sufficient to run the main CLI and the characterization suite.
2. **Given** same-path and distinct-path outputs in both preferred and alternate write modes, **When** processing succeeds, **Then** the final file is complete and the policy matches documentation (distinct paths preferred; safe temporary replace when same-path is allowed).

---

### Edge Cases

- Empty or near-empty PDF pages during preferred-path copy/transform (must not cascade into an unhandled failure that blocks documented fallback).
- Profile present but missing `back_corrections` keys (treat missing keys as identity for those axes; do not resurrect sample non-zero defaults).
- CLI overrides (`--rot`, shift flags) combined with a profile (overrides win; remaining fields come from the profile).
- Odd page counts under `add_blank` vs `drop_last` vs `warn`.
- Short-edge vs long-edge flip mode interaction with the extra 180° back handling.
- Batch or optional tools invoked when the main script is unavailable or returns non-zero (worker failures must surface).
- Comment-bearing templates under `profiles/` used by mistake as runtime profiles.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The main CLI MUST apply documented back-page rotation and X/Y shifts in the preferred (vector-preserving) processing mode using only supported operations for the declared dependency versions.
- **FR-002**: Automatic mode MUST fall back to the alternate (raster) path on recoverable preferred-path failure, emit an explanatory message on the error stream, and MUST NOT fail solely because of references to non-existent error types.
- **FR-003**: Preferred and alternate paths MUST apply the same correction directions as documented in the calibration guide (positive rotation = clockwise; positive Y = downward on the page as printed; positive X per the published convention).
- **FR-004**: Front pages MUST remain geometrically unmodified in all page-order modes.
- **FR-005**: When neither a usable `--profile` nor explicit correction overrides are provided, back corrections MUST be identity (zero rotation and zero shifts).
- **FR-006**: A missing `--profile` path MUST produce an actionable error (or an explicit, documented warning plus identity)—MUST NOT silently merge sample non-zero corrections.
- **FR-007**: Invalid JSON and comment-bearing profile files MUST produce actionable error-stream messages and non-zero exit for expected failure modes; raw tracebacks MUST NOT be the default end-user experience.
- **FR-008**: Missing/unreadable input PDFs and other expected I/O failures MUST be reported with actionable messages and non-zero exit without default raw tracebacks.
- **FR-009**: `--on-odd warn` MUST emit a warning on the error stream when an odd-page PDF is processed under `fronts_then_backs`.
- **FR-010**: Page-order classification (`interleaved`, `fronts_then_backs`, `last_back`, `single_sided`) MUST match published documentation and MUST be covered by automated checks.
- **FR-011**: Before changing transform, profile-merge, or page-order logic, the project MUST add characterization checks that encode the desired geometric/profile contract; those checks MUST fail on currently broken behaviors and pass after fixes.
- **FR-012**: Geometry/unit conversion and profile load/validation MUST be separable from filesystem PDF I/O and from CLI parsing so they can be checked without relying on full end-to-end runs for every case.
- **FR-013**: Incomplete optional features (notably batch smart page-order detection) MUST either be implemented and checked or disabled with a clear user-facing message; they MUST NOT crash with undefined symbols.
- **FR-014**: Same-path vs distinct-path save behavior MUST be consistent across preferred and alternate writers and MUST follow safe temporary-replace patterns where same-path writing is supported.
- **FR-015**: Project docs (README, tools README, calibration guide) MUST match actual CLI behavior, listed scripts, correction sign conventions, and dependency expectations after remediation.
- **FR-016**: A tracked dependency declaration MUST list the supported stack for the main workflow (and clearly separate optional tool extras if any remain).
- **FR-017**: New or substantially edited code introduced by this feature MUST include static type annotations consistent with Python 3.9+.
- **FR-018**: Remediation MUST NOT silently change the published geometric contract; intentional contract changes MUST be called out in docs and characterization checks updated in the same change set.
- **FR-019**: Optional/experimental tools MUST remain labeled as such and MUST NOT replace the main entrypoint workflow.
- **FR-020**: Personal profiles, secrets, generated PDFs, and local tool state MUST remain untracked; remediation MUST NOT commit such artifacts.

### Key Entities

- **Calibration Profile**: Reusable printer configuration (paper, orientation, flip mode, back corrections). Runtime instances are valid JSON without comments; templates with comments are documentation aids only.
- **Back Correction**: Rotation (degrees) and X/Y shifts (mm) applied only to pages classified as backs.
- **Page-Order Mode**: Rule set that classifies each page index as front or back (`interleaved`, `fronts_then_backs`, `last_back`, `single_sided`).
- **Odd-Page Policy**: Behavior when page count is odd under `fronts_then_backs` (`warn`, `add_blank`, `drop_last`).
- **Processing Mode**: Preferred vector-preserving path, alternate raster path, or automatic selection with fallback.
- **Finding Record** (audit artifact): Documented gap between current and desired behavior, used to prioritize remediation (severity, constitution principle, area).

## Current Behavior vs Desired Behavior *(mandatory for this feature)*

Audit baseline date: 2026-07-25. Desired column is governed by constitution v1.3.0 unless noted.

| Area | Current behavior | Desired behavior |
|------|------------------|------------------|
| Preferred-path transforms | Rotation construction uses unsupported matrix construction; page placement ignores caller-supplied matrix arguments, so shifts can silently no-op while reporting success | Back rotation and shifts apply reliably on the preferred path; success means corrections were applied |
| Automatic fallback | Failure handling references a non-existent error type, often blocking fallback and surfacing dual failures/tracebacks | Recoverable preferred-path failures fall back to the alternate path with an error-stream explanation |
| Alternate-path geometry | Y shift and rotation signs disagree with calibration documentation (and with the intended preferred-path semantics) | Both paths honor the same documented sign conventions |
| Default profile | Embedded non-zero sample corrections when no profile is loaded; missing profile path is silently ignored | Identity defaults; missing explicit profile path is an error or an explicit warning—never silent sample skew |
| Expected CLI failures | Missing PDF, invalid JSON, comment-bearing templates → raw tracebacks | Actionable error-stream messages and non-zero exit |
| `--on-odd warn` | No warning emitted; odd `fronts_then_backs` splits can be uneven | Warning on error stream; documented, tested classification |
| Automated checks | No test suite; constitution’s characterization-first rule cannot be followed | Characterization suite for units, page order, profile contract, and transform signs |
| Module boundaries | Single main script mixes CLI, profile I/O, geometry, vector write, and raster write; logic duplicated in tools | Separated pure geometry/profile validation vs I/O vs CLI; shared rules across in-scope tools |
| Batch smart detect | Calls an undefined helper → crash; worker failures can be swallowed | Working implementation or clear disablement; non-zero worker status propagates |
| Optional image workflow | Hardcoded paths; extra undeclared stack beyond the constitution default | Labeled experimental; documented deps/invocation—or deferred out of this feature’s implementation scope with docs saying so |
| Dependencies | Install described only in prose; version drift breaks APIs | Tracked constrained dependency declaration for the main workflow |
| Safe save | Preferred path uses temp replace; alternate path uses different same-path renaming and direct write | Unified, documented safe-save policy for both writers |
| Documentation | README advertises working vector-first alignment; tools README omits some scripts; sign conventions can diverge from code | Docs match runtime behavior and constitution stack |
| Typing | Essentially untyped scripts | Annotations on new/substantially edited code |
| Performance | Full-page rasterization and per-page image encoding when alternate path runs; batch may fingerprint every page then spawn per-file processes | Prefer vector path; rasterize only when needed; avoid redundant work once correctness is restored (no premature optimization beyond that) |
| Repository hygiene | Generally aligned (ignores for personal profiles, venvs, generated PDFs) | Keep ignoring secrets/local state; do not commit calibration outputs from remediation work |

### Constitution principle scorecard (baseline)

| Principle | Baseline | Desired after this feature |
|-----------|----------|----------------------------|
| I. Calibration-Profile First | Partial (profiles exist; silent sample defaults undermine trust) | Explicit profile contract; identity without profile |
| II. CLI-First + clear errors | Partial (main has CLI; tools uneven; tracebacks common) | Actionable errors; tools CLI or clearly edit-run experimental |
| III. Back-Page Corrections Only | Intent present; undermined by non-applied / mis-signed transforms | Enforced and checked |
| IV. Vector-First | Failing on common installs | Working preferred path + honest fallback |
| V. Practical Simplicity | Mostly; optional tool pulls extra stack | Stay on approved stack unless plan justifies extras |
| VI. Geometric Precision | Failing; no regression net | Characterization net + matching signs |
| VII. Separation of Concerns | Failing (monolith + duplication) | Separated and shareable core rules |
| VIII. Repository Hygiene | Mostly OK | Preserve; no secret/profile leaks in remediation |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of characterization cases for rotation, X/Y shift, and flip-mode back handling pass on both preferred and alternate paths after remediation (suite is empty or failing before fixes for known defects).
- **SC-002**: In a scripted pass of expected failure modes (missing PDF, missing profile path, invalid JSON profile, comment-bearing template), 100% produce actionable error-stream messages and non-zero exit without relying on a raw traceback as the primary user-visible result.
- **SC-003**: With no profile and no correction overrides, measured back corrections are exactly identity (0° rotation, 0 mm shifts) on a fixture run.
- **SC-004**: A reviewer can map each P1 acceptance scenario to at least one automated check or a short documented manual verification step recorded in the feature plan/tasks.
- **SC-005**: After remediation, README “Features” claims (back-only correction, vector-first with fallback, profile reuse) are true for the main CLI on the declared dependency set—verified by the characterization suite plus one documented smoke command.
- **SC-006**: Incomplete optional entry points in scope either pass a smoke check or refuse with a clear message; zero undefined-symbol crashes on documented flags.
- **SC-007**: No personal printer profiles, secrets, or generated alignment PDFs are added to version control by this feature’s changes.

## Assumptions

- This feature’s outcome is **remediation guided by the audit**, not an audit-only document left without follow-up tasks; the Current vs Desired table is the contract for planning (`/speckit-plan`) and task breakdown (`/speckit-tasks`).
- Scope priority is **correctness and safety first** (P1 stories), then structure/docs/deps (P2–P3). Large optional rewrites (e.g. replacing the experimental image tool’s extra stack) may be deferred if docs clearly mark them experimental and out of the first delivery slice.
- The published calibration sign conventions in `docs/calibration_guide.md` are the source of truth for “desired” geometry unless a later intentional contract change is approved.
- Input PnPs remain centered with shared front/back geometry (constitution geometry assumption).
- Python 3.9+ remains the compatibility floor.
- Characterization checks may start by asserting the **desired** documented contract (failing on today’s bugs) rather than freezing incorrect silent no-ops as golden behavior.
- Performance work is limited to avoiding unnecessary rasterization and obvious redundant work once transforms are correct; deep throughput optimization is out of scope.
- No new GUI; CLI-first remains mandatory.
- No new external dependencies for the main workflow beyond the constitution stack unless a later plan’s Complexity Tracking justifies them.
