# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Existing baseline**: Preserve documented CLI/profile/transform contracts
  unless the plan explicitly breaks them; this is an AI-assisted evolution of
  an existing tool, not a greenfield rewrite.
- **Calibration-Profile First**: Corrections live in reusable JSON printer
  profiles (one profile per printer configuration). CLI overrides are for
  experiments; lasting values MUST be profile-backed.
- **CLI-First + clear errors**: User-facing behavior via CLI flags/args;
  errors on stderr; no GUI required; expected failures get actionable
  messages (not raw tracebacks by default).
- **Back-Page Corrections Only**: Transforms apply only to pages classified
  as backs for the chosen page-order mode; fronts stay unmodified.
- **Vector-First**: Prefer vector PDF paths; raster only when forced or as
  documented fallback, with explicit DPI/quality controls.
- **Practical Simplicity**: Python 3.9+ with PyMuPDF / ReportLab / Pillow
  unless justified; no new dependencies without plan approval; prefer
  typed code on new/edited surfaces.
- **Geometric Precision**: Changes to matrices, coordinates, units, or
  transforms MUST NOT regress printed alignment; include characterization
  or equivalent verification when touching that code.
- **Separation of Concerns**: Keep pure geometry independent of I/O; keep
  profile parsing decoupled from the transform engine.
- **Repository hygiene**: No secrets, tokens, personal profiles, or local
  AI/tool scratch in commits; update `.gitignore` when adding tooling.
- **Safe I/O & docs**: Distinct input/output paths; safe temp saves; update
  README / calibration docs when user-visible behavior or profile schema
  changes.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# Default for this repository (flat CLI / scripts)
pnp_double_with_profile_pdf.py   # main entrypoint
tools/                           # optional / advanced helpers
profiles/                        # printer calibration JSON
docs/                            # calibration and operator docs
tests/                           # only when a feature requests tests

# [REMOVE IF UNUSED] Option: packaged layout (if a feature introduces src/)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
