<!--
Sync Impact Report
- Version change: 1.2.0 → 1.2.1 (PATCH: ignore local Cursor skills; drop scratch-file noise)
- Modified principles:
  - VIII. Repository Hygiene & Secrets → .cursor/skills/ MUST stay untracked
- Added sections: none
- Removed sections: none
- Templates / docs requiring updates:
  - .gitignore ✅ updated (.cursor/skills/; removed gemini-code-* pattern)
  - .specify/templates/plan-template.md ✅ hygiene gate clarified
  - README.md ✅ no change required
- Follow-up TODOs: none
-->

# PnP Double-Side Aligner Constitution

## Project Context

This repository began as an existing, human-developed Print-and-Play duplex
alignment tool. Spec Kit, Cursor skills, and other AI-assisted workflows are
being integrated **after** that baseline existed. AI assistance MUST accelerate
documentation, refactors, and features without rewriting project identity,
silently changing geometric behavior, or committing secrets and local machine
state. Human review remains accountable for correctness-critical changes
(transforms, profiles, page-order logic).

## Core Principles

### I. Calibration-Profile First

Printer duplex behavior MUST be captured in reusable JSON calibration
profiles (paper size, orientation, flip mode, back corrections). Features
MUST treat profiles as the primary contract for alignment values. CLI
overrides of rotation/shift are allowed for experimentation, but lasting
corrections MUST be recorded in a profile so they apply across compatible
PnP PDFs. One profile represents one printer configuration (printer + paper
+ duplex settings), not one game or PDF.

**Rationale**: Real duplex misalignment is mechanical and stable; calibrating
once and reusing the profile is the product's core value.

### II. CLI-First Interface

This project is a deterministic CLI tool for geometric duplex alignment and
transformation of Print-and-Play PDFs. User-facing capabilities MUST be
exposed through command-line interfaces (`argparse` or equivalent). Inputs
MUST accept explicit paths and flags; progress and results go to stdout;
errors and warnings go to stderr. Scripts MUST remain runnable without a
GUI. Optional tools under `tools/` MUST document invocation and remain
invocable from the repository root.

On invalid or unusable inputs (corrupt PDFs, malformed profiles, invalid
coordinates or transforms), the CLI MUST report a clear, actionable message
to the user. Raw Python tracebacks MUST NOT be the default end-user error
experience for expected failure modes.

**Rationale**: Hobbyists and makers need predictable, scriptable tooling and
messages they can act on—not stack traces.

### III. Back-Page Corrections Only

Alignment transforms (rotation and X/Y shift) MUST apply only to pages
classified as backs for the selected page-order mode. Front pages MUST
remain geometrically unmodified. Page-order modes
(`interleaved`, `fronts_then_backs`, `last_back`, `single_sided`) and
odd-page policies MUST be explicit and documented. Features MUST NOT
silently rewrite front content to “fix” misalignment.

**Rationale**: Duplex skew is a back-side printer artifact; touching fronts
destroys content that was already correct.

### IV. Vector-First Processing

PDF processing MUST prefer vector-preserving paths. Rasterization MUST be
opt-in or a documented automatic fallback, with explicit controls for DPI
and JPEG quality when raster output is used. Quality-reducing defaults
MUST NOT be introduced without documenting the trade-off in help text or
docs.

**Rationale**: PnP assets are often vector art; unnecessary rasterization
bloats files and softens linework.

### V. Practical Simplicity

Prefer the smallest change that solves a real duplex-alignment problem.
The supported stack is Python 3.9+ with PyMuPDF (`fitz`), ReportLab, and
Pillow unless a feature plan explicitly justifies a change. New external
dependencies MUST NOT be added unless strictly necessary and approved in
the implementation plan (Complexity Tracking when the addition increases
scope or coupling). Do not introduce frameworks, services, or package
layouts without that justification. Mark experimental helpers clearly under
`tools/` and keep the main entrypoint
(`pnp_double_with_profile_pdf.py`) focused on the common path.

New and substantially edited code SHOULD use static typing (`typing` /
annotations) consistent with Python 3.9+.

**Rationale**: This is a focused MIT utility, not a platform; extra
dependencies and untyped churn hurt calibrators and maintainers.

### VI. Geometric Precision (Zero Math Regressions)

Any change to matrix math, coordinate systems, units (mm ↔ points), page
geometry, or image/PDF transforms MUST preserve visual and geometric
accuracy of PDF outputs for equivalent inputs and profiles. Behavior that
affects printed alignment is treated as correctness-critical: silent drift
in rotation, shift, flip handling, or page classification is a defect.

Before changing transform algorithms, contributors MUST establish a way to
detect regressions (characterization tests, golden fixtures, or an
equivalent documented verification step in the feature plan).

**Rationale**: A tool that “almost” aligns duplex pages is worse than no
tool; mathematical regressions destroy trust in calibration profiles.

### VII. Separation of Concerns

Pure mathematical and geometric logic MUST remain independent of filesystem
I/O. JSON profile parsing/validation MUST stay decoupled from the transform
engine that applies corrections to pages. CLI argument parsing and user
messaging MUST NOT embed core geometry algorithms.

Refactors that improve this separation are encouraged when they do not
violate Geometric Precision or Practical Simplicity.

**Rationale**: Decoupling lets us test transforms without PDFs on disk and
swap I/O or profile formats without rewriting the math.

### VIII. Repository Hygiene & Secrets

The working tree MUST stay safe to share and to open in AI coding tools.
Secrets, tokens, private host configuration, personal printer profiles,
virtualenvs, caches, generated PDFs, and local AI scratch notes MUST NOT be
committed. `.gitignore` is part of project governance: when adding tooling
(Sonar, agents, cloud CLIs, MCP, etc.), ignore patterns MUST be updated in
the same change set. Never place API keys, Sonar tokens, or `.env` values in
tracked files, specs, or agent prompts that will be committed.

Tracked Spec Kit assets under `.specify/` and shared Cursor rules under
`.cursor/rules/` are allowed when they contain no secrets. Local Cursor
skills under `.cursor/skills/` MUST remain gitignored (regenerated or
machine-local tooling, not project source).

**Rationale**: AI-assisted workflows increase the chance of accidental leaks;
ignore rules and review habits are the first control.

## Additional Constraints

- **Geometry assumption**: Input PnPs are expected to be centered (equal
  margins; shared front/back page geometry). Features that relax this MUST
  document the new contract and failure modes.
- **Safe I/O**: Input and output paths MUST be distinct for normal use.
  Writers MUST use safe temporary save patterns to avoid OS locks and
  partial chunk files.
- **Profile validity**: Runtime profiles MUST be valid JSON (no comments).
  Comment-bearing templates (e.g. `profiles/base_printer_profile.json`)
  are documentation aids and MUST be copied/stripped before use. Only
  `profiles/base_printer_profile.json` and `profiles/example_printer.json`
  are the canonical tracked examples unless a plan adds more intentionally.
- **Compatibility**: Target Python 3.9+ unless a constitution amendment
  raises the floor.
- **Licensing**: Contributions remain under the MIT License; keep copyright
  and license notices intact.

## Development Workflow

- Feature work follows Spec Kit flow: specify → plan → tasks → implement,
  with this constitution as a non-negotiable gate in every plan.
- **Existing baseline first**: Treat current scripts, profile schema, and
  documented CLI behavior as the contract. AI-proposed changes MUST call out
  intentional contract breaks; accidental rewrites of working legacy paths
  are defects.
- **Characterization-First for legacy refactors**: Before refactoring an
  existing block that affects transforms, profiles, or page-order logic,
  add unit or integration tests (`pytest`) that lock current behavior, then
  refactor. Specs that request tests MUST have those tests written and
  failing before new behavior is implemented.
- Calibration or profile-schema changes MUST update `docs/calibration_guide.md`
  and profile examples when user-visible behavior changes.
- README and `tools/README.md` MUST stay accurate for primary vs optional
  scripts, including notes about AI-assisted development when that process
  changes how contributors work in the repo.
- Automated tests are not mandatory for every cosmetic or docs-only change;
  they ARE mandatory when changing geometric/transform behavior or when a
  feature spec requests them.
- Experimental tools MUST be labeled as such and MUST NOT silently replace
  the main PDF workflow.
- Before committing, verify no secrets, personal profiles, or local tool
  config slipped into the staging area.

## Governance

This constitution supersedes conflicting informal practices in the
repository. Amendments MUST update `.specify/memory/constitution.md`, bump
the version using semantic versioning (MAJOR for removals or incompatible
redefinitions, MINOR for new/expanded principles, PATCH for clarifications),
set **Last Amended** to the amendment date, and sync dependent Spec Kit
templates when gates or mandatory sections change. Pull requests and reviews
MUST verify compliance with Core Principles; complexity that violates
simplicity MUST be recorded in the plan's Complexity Tracking table with
justification. Runtime guidance for operators lives in `README.md` and
`docs/calibration_guide.md`; this file governs how the project evolves.

**Version**: 1.2.1 | **Ratified**: 2026-07-25 | **Last Amended**: 2026-07-25
