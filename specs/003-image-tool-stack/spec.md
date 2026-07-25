# Feature Specification: Experimental Image Tool Stack

**Feature Branch**: `003-image-tool-stack`

**Created**: 2026-07-25

**Status**: Draft

**Input**: User description: "Tool de imágenes — declarar deps / reescritura OpenCV+FPDF (más experimental, menos impacto en el flujo PDF principal)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install optional image-tool dependencies without touching the main PDF stack (Priority: P1)

A maker or contributor who needs the experimental image-based PnP path can install its extra dependencies from a clearly labeled optional dependency set. Installing or upgrading those extras does not change what the main PDF aligner requires, and someone who only uses the PDF workflow never has to install OpenCV/FPDF-class extras.

**Why this priority**: Today the image tool imports undeclared extras while the main requirements file lists only the PDF constitution stack. Honest packaging is the minimum bar before any rewrite, and it isolates risk from the primary product path.

**Independent Test**: From a clean environment, install only the main dependency set and confirm the main PDF workflow still runs; separately install the optional image-tool set and confirm the image tool’s imports/resolve without adding those packages to the main required set.

**Acceptance Scenarios**:

1. **Given** only the main (PDF) dependency set is installed, **When** a user follows the primary README install path, **Then** they are not required to install image-tool extras to use the main PDF aligner.
2. **Given** the optional image-tool dependency set is installed as documented, **When** a user invokes the experimental image tool (or its documented import check), **Then** missing-module failures for its declared extras no longer occur solely because dependencies were never listed.
3. **Given** documentation for tools, **When** a new contributor reads how to use the image path, **Then** they see which packages are optional/experimental and that the main PDF workflow remains the recommended path.

---

### User Story 2 - Use an honest experimental image→duplex workflow (Priority: P1)

A user with PNG/JPG fronts (and optional backs), a printer profile, and reference crop guidance can run the experimental image tool to produce a duplex-oriented PDF with back-side corrections applied only to backs, without editing hardcoded machine-specific paths as the only supported interface—and without that work changing behavior of the main PDF entrypoint.

**Why this priority**: The deferred rewrite exists so the image path is usable and maintainable for advanced users; impact on the main PDF flow must stay minimal by design.

**Independent Test**: Run the documented image-tool invocation on a small fixture set (reference images + fronts/backs + valid profile); confirm an output PDF is produced, fronts are not incorrectly transformed as backs, and the main PDF CLI characterization checks still pass unchanged.

**Acceptance Scenarios**:

1. **Given** valid inputs (profile, reference crop pair, front/back images) and image-tool extras installed, **When** the user runs the experimental image workflow via its documented interface, **Then** they get an output PDF suitable for duplex printing attempts without relying on undocumented personal hardcoded paths as the sole interface.
2. **Given** the image tool applies printer back corrections from a profile, **When** pages classified as fronts are inspected, **Then** those fronts remain geometrically unmodified relative to the image tool’s own front/back classification rules.
3. **Given** the main PDF aligner’s automated checks, **When** this feature’s image-tool work is complete, **Then** those main-path checks still pass with no intentional contract change required by this feature.

---

### User Story 3 - Keep experimental boundaries clear after rewrite (Priority: P2)

Maintainers and AI-assisted contributors can tell that the image tool is experimental, optional, and out of the critical PDF characterization gate. Failure modes (missing extras, bad paths, bad profile) produce actionable messages rather than unexplained crashes as the default experience.

**Why this priority**: Constitution requires experimental helpers to stay labeled and not silently replace the main workflow; clear errors reduce support burden without elevating the tool to production status.

**Independent Test**: Invoke the image tool without extras installed, with a missing input path, and with an invalid profile; confirm messages and non-zero exits; confirm README/tools docs still mark it experimental.

**Acceptance Scenarios**:

1. **Given** image-tool extras are not installed, **When** the user runs the image tool, **Then** they receive a clear message that optional dependencies are missing and how to install them—not an opaque import failure as the only guidance.
2. **Given** missing image paths or an unusable profile, **When** the user runs the image tool, **Then** they get an actionable error and non-zero exit without a raw traceback as the primary expected-failure UX.
3. **Given** project docs after this feature, **When** a contributor compares primary vs optional scripts, **Then** the image tool remains labeled experimental and is not presented as a replacement for the main PDF aligner.

---

### Edge Cases

- User installs main deps only and accidentally runs the image tool → clear missing-extras guidance.
- User installs image extras but points at a comment-bearing profile template → same honest JSON/profile rules as the rest of the project (actionable error).
- Empty fronts list or mismatched front/back counts → clear error or documented pairing rule; no silent nonsense PDF.
- Reference crop matching fails or is ambiguous → clear failure; do not invent a crop silently without notice.
- Image extras versions conflict with main stack pins → docs state supported optional pins; main PDF pins remain authoritative for the primary path.
- Contributor proposes moving image extras into the main required install → out of scope / rejected by this feature’s boundary assumptions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST publish a clearly labeled optional dependency set for the experimental image tool, separate from the main PDF workflow’s required dependencies.
- **FR-002**: The main PDF workflow’s required dependency set MUST NOT gain image-tool-only packages as mandatory installs for ordinary PDF users.
- **FR-003**: Documentation MUST state how to install image-tool extras, that the tool is experimental, and that the main PDF aligner remains the recommended production path.
- **FR-004**: The experimental image tool MUST provide a documented, reproducible way to supply inputs (profile, reference images, front/back image lists, output path) without requiring the user to edit personal hardcoded paths in the script as the only supported method.
- **FR-005**: When image-tool extras are missing, the tool MUST fail with an actionable install hint and non-zero exit.
- **FR-006**: When inputs are missing, unreadable, or the profile is invalid for runtime use, the tool MUST report an actionable error and non-zero exit (no raw traceback as the default expected-failure experience).
- **FR-007**: Back-side corrections from the profile MUST apply only to pages/images classified as backs by the image tool’s documented pairing rules; fronts MUST remain unmodified by those corrections.
- **FR-008**: Any rewrite of the OpenCV/FPDF-based implementation (keeping that stack with declared pins, or replacing it with another approved approach for this experimental tool) MUST preserve the user-visible goals of crop-guided image assembly plus profile-based back corrections into an output PDF, unless docs explicitly retire a capability.
- **FR-009**: Changes under this feature MUST NOT alter the main PDF aligner’s documented geometric/profile CLI contract; main-path automated checks MUST remain passing without requiring intentional main-contract breaks for this feature.
- **FR-010**: The image tool MUST remain labeled experimental in script documentation and tools docs after delivery.
- **FR-011**: If the rewrite retains heavy optional libraries, they MUST be pinned or otherwise constrained in the optional dependency set so contributors can reproduce a known-good extras environment.
- **FR-012**: Minimal automated checks for the image tool (at least: missing-extras messaging and one happy-path or fixture smoke when extras are available) MUST exist or be explicitly documented as optional/skipped when extras are absent in CI—without making image extras mandatory for the main test gate.

### Key Entities

- **Optional image-tool dependency set**: Declared packages needed only for the experimental image path; not part of the main required install.
- **Experimental image workflow**: Crop-guided assembly of PNG/JPG fronts/backs into a duplex-oriented PDF using a printer calibration profile for back corrections.
- **Image workflow inputs**: Profile path, reference original, reference crop, front image list, back image list (or documented duplicate-fronts rule), output path.
- **Main PDF workflow**: Primary aligner path and its required dependencies; intentionally out of change scope for this feature except for shared docs that clarify boundaries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user following the main install docs can run the primary PDF aligner without installing image-tool extras (0 mandatory image-only packages on the main path).
- **SC-002**: With optional extras installed per docs, a documented image-tool run on a small fixture set completes successfully (produces an output PDF) in under 5 minutes of operator setup+run time for that fixture.
- **SC-003**: 100% of main PDF automated characterization/regression checks that passed before this feature still pass after it, with no intentional main-contract change required by this work.
- **SC-004**: In a clean environment without image extras, running the image tool yields a clear missing-dependency message in under 10 seconds and a non-zero exit (not an unexplained failure).
- **SC-005**: After delivery, tools documentation mentions the image tool as experimental and describes optional install steps; reviewers can confirm the main README does not present the image path as the default recommended workflow.

## Assumptions

- Scope is the experimental image tool and its packaging/docs; the main PDF aligner is a non-goal for behavioral change (boundary inherited from feature `001` deferral).
- “Declare deps” is mandatory; “rewrite” means bring the experimental tool to a maintainable, documented, invocable state—either by properly packaging the existing OpenCV/FPDF approach or by replacing that stack inside the experimental tool only. Planning chooses the technical approach; this spec requires the user outcomes above.
- Image-tool extras may increase optional complexity; that is acceptable because the feature is explicitly lower impact and more experimental than the main PDF flow (constitution Complexity Tracking belongs in the plan if extras stay).
- Shared profile JSON semantics (valid runtime JSON, back corrections signs/units) should stay aligned with the rest of the project where the image tool consumes profiles.
- CI for the repository may continue to gate on the main PDF suite without requiring OpenCV/FPDF in the default job; image-tool checks can be optional or conditional.
- Hardcoded personal paths in the current script are technical debt to remove from the supported interface, not a feature to preserve.
- No requirement to match the main PDF aligner’s vector-first quality bar; the image path is inherently raster/image-based and remains experimental.
