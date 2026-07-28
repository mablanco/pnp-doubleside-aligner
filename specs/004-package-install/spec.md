# Feature Specification: Installable Package Alongside Scripts

**Feature Branch**: `004-package-install`

**Created**: 2026-07-25

**Status**: Draft

**Input**: User description: "pyproject.toml / packaging — instalar como paquete (pip install -e .) además de scripts sueltos"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install the project as an editable package (Priority: P1)

A contributor clones the repository, creates a virtual environment, and installs the project in editable mode with a single documented package-install command. After that, the main duplex aligner is available as a normal installed command-line tool (not only by typing a path to a script file), and its runtime dependencies are pulled in by that install.

**Why this priority**: Today install is “pip install requirements then run loose scripts.” Editable packaging is the requested install path for contributors who expect a standard Python project layout while developing.

**Independent Test**: In a clean virtual environment, follow the documented editable install; confirm the main aligner command is on PATH (or equivalently invocable as an installed module CLI) and runs `--help` / a trivial supported invocation successfully.

**Acceptance Scenarios**:

1. **Given** a clean virtual environment and a clone of the repo, **When** the user runs the documented editable package install, **Then** the install completes successfully and the main aligner’s runtime dependencies are available in that environment without a separate undocumented manual dependency hunt.
2. **Given** a successful editable install, **When** the user invokes the documented installed main aligner command with `--help` (or equivalent), **Then** they see the tool’s help and a zero exit status.
3. **Given** documentation for installation, **When** a new contributor reads the README install section, **Then** both the editable package install and the existing requirements/script workflow are described (package install is not the only mentioned path unless docs intentionally retire the old one later).

---

### User Story 2 - Keep loose scripts working (Priority: P1)

A user who prefers the historic workflow—install dependencies from the requirements files and run scripts from the repository root—can still do so. Packaging MUST NOT force every user to use only the installed console command, and MUST NOT break the documented script invocations for the main aligner.

**Why this priority**: The request is package install *in addition to* loose scripts, not a breaking replacement of the current hobbyist workflow.

**Independent Test**: Without relying on the editable install’s console script (or after only installing requirements as today), run the main aligner script from the repo root as documented; confirm behavior matches the existing supported script path.

**Acceptance Scenarios**:

1. **Given** dependencies installed via the documented requirements-based path (without requiring editable install), **When** the user runs the main aligner as a script from the repository root per docs, **Then** the tool still starts and exposes the same primary duplex-alignment capability.
2. **Given** an editable install is also present, **When** the user runs the loose main script from the repo root, **Then** the script still runs (no hard requirement that only the installed command works).
3. **Given** the automated main-path test suite, **When** packaging changes land, **Then** existing characterization/regression checks for the main aligner still pass.

---

### User Story 3 - Clear package metadata and optional extras for contributors (Priority: P2)

A maintainer can see project name, version, license, and dependency groups in one packaging metadata place. Development/test dependencies and any experimental optional stacks (e.g. image-tool extras) are expressible as optional install extras or equivalently documented companion install paths so contributors know what to install for which workflow.

**Why this priority**: Packaging value includes reproducible metadata and optional groups; experimental tools must not become mandatory for every install.

**Independent Test**: Inspect documented packaging metadata / extras; install “main” only and confirm experimental image extras are not forced; install documented optional extra(s) when present and confirm they resolve.

**Acceptance Scenarios**:

1. **Given** packaging metadata for the project, **When** a contributor inspects it, **Then** they can identify project identity (name, version, license consistent with the MIT project) and the main runtime dependency set.
2. **Given** a main-only package install (no optional extras), **When** the environment is inspected, **Then** experimental image-tool-only dependencies are not required for that main install.
3. **Given** docs after this feature, **When** a contributor wants tests, **Then** they have a documented way to install development/test dependencies (via packaging extra and/or existing requirements-dev path).

---

### Edge Cases

- Editable install in an environment that already used requirements.txt → still works; no conflicting duplicate “two sources of truth” without docs explaining how they relate.
- User runs installed command from a different working directory → paths for inputs/outputs remain user-supplied; tool does not assume cwd is the repo root for reading PDFs.
- Optional tools under `tools/` may remain script-invoked in v1 if not exposed as console commands; docs MUST say which commands are installed vs script-only.
- Version bump process: single obvious place for version in packaging metadata (docs note if scripts also print a version later).
- CI: continuous integration can use either editable install or requirements install, but MUST remain able to run the main test suite.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST provide standard installable packaging metadata so users can perform an editable install of the project from the clone root with the documented command equivalent to installing the local project in editable mode.
- **FR-002**: After editable install, users MUST be able to invoke the main duplex aligner via a documented installed command-line entry (console command and/or `python -m …` module form), without needing to type the historical script filename as the only supported method.
- **FR-003**: The historic workflow—install dependencies from documented requirements files and run the main aligner as a loose script from the repository root—MUST remain supported and documented alongside the package install.
- **FR-004**: Packaging MUST declare the main runtime dependencies needed for the primary PDF duplex aligner so editable install pulls them in.
- **FR-005**: Packaging MUST NOT make experimental image-tool-only dependencies mandatory for a default/main install.
- **FR-006**: Project packaging metadata MUST include name, version, description, and license information consistent with this MIT-licensed project.
- **FR-007**: Documentation (README and any install section) MUST describe both editable package install and the loose-script/requirements workflow, and MUST list which CLIs are provided as installed entry points versus script-only tools.
- **FR-008**: Introducing packaging MUST NOT intentionally change the main aligner’s duplex geometric/profile behavior; existing main-path automated checks MUST still pass.
- **FR-009**: Development/test dependencies MUST remain installable for contributors (packaging optional “dev” extra and/or `requirements-dev.txt`), and CI MUST retain a documented path to run the main test suite.
- **FR-010**: If both packaging metadata and requirements files list dependencies, docs MUST state which is authoritative for what (or that they are kept in sync), so contributors are not left guessing.

### Key Entities

- **Installable project package**: The repository represented as an installable Python distribution (editable from a clone).
- **Installed main CLI entry**: Documented command users run after package install to reach the primary duplex aligner.
- **Loose script workflow**: Running scripts directly from the repo with dependencies from requirements files.
- **Optional dependency group**: Non-mandatory install set (e.g. dev/test, experimental image tool) distinct from the main runtime set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new contributor following README package-install steps completes editable install and successfully runs the installed main aligner help command in under 10 minutes on a typical developer machine (excluding slow network variance).
- **SC-002**: 100% of existing main-path automated characterization/regression tests that passed before packaging still pass after packaging lands.
- **SC-003**: A user following only the requirements + loose-script docs (no editable install) can still run the main aligner script successfully for a documented smoke invocation.
- **SC-004**: A default/main package install does not require experimental image-tool-only packages (0 such packages mandatory on the main install path).
- **SC-005**: After delivery, README install docs mention editable package install and loose scripts; a reviewer can identify the installed main command name from docs without reading source.

## Assumptions

- Goal is local/editable install from a git clone for contributors and advanced users; publishing a release to a public package index is out of scope unless a later feature explicitly adds release publishing.
- “In addition to loose scripts” means dual support: packaging does not remove or break the script-based workflow in this feature.
- The primary installed entry point is the main PDF duplex aligner; optional/experimental tools may stay script-only in this feature to limit scope (docs must say so).
- Existing `requirements.txt` / `requirements-dev.txt` (and any image extras file) may remain as convenience installs; planning will decide sync strategy with packaging metadata (FR-010).
- Package layout may stay minimal (Practical Simplicity): justify any move to a deeper `src/` layout in the plan’s Complexity Tracking if chosen; default preference is the smallest packaging change that enables editable install + entry point.
- Geometric behavior and profile contracts remain owned by existing specs; this feature is install/UX packaging only.
