# Data Model: Reliable Batch Smart Page-Order Detect

**Feature**: `002-smart-detect`  
**Date**: 2026-07-25  
**Related**: [spec.md](./spec.md), [contracts/batch-smart-detect.md](./contracts/batch-smart-detect.md)

Entities are logical (in-memory / CLI). No database. Alignment transforms and
calibration profiles are unchanged from `001`; this feature only produces a
page-order decision for the existing worker.

## Page-Order Decision

Result of smart detection for one batch input PDF.

| Field | Type | Rules |
|-------|------|-------|
| `order` | PageOrderMode | One of `interleaved`, `fronts_then_backs`, `last_back`, `single_sided` |
| `reason` | string | Short audit string (see Reason taxonomy) |
| `confident` | bool (logical) | True when content-based or hint/page-count rule chose without tie fallback; false for tie / open-fallback |

**Relationships**: Consumed by the batch loop to pass `--order` to the worker.
Does not contain rotation/shift values.

## PageOrderMode

Same modes as the main aligner (see `001` data model). Smart detect MUST only
emit these values.

| Value | Typical smart-detect trigger |
|-------|------------------------------|
| `single_sided` | `total <= 1` (unless name hint overrides) |
| `last_back` | Odd `total > 1` (unless name hint overrides) |
| `interleaved` | Name hint, or confident common-back (odd-index cluster) |
| `fronts_then_backs` | Name hint, or confident common-back (second-half cluster) |

## Reason taxonomy

Stable prefixes for stdout auditing (exact wording may include metrics):

| Prefix / pattern | Meaning |
|------------------|---------|
| `name-hint:<mode>` | Filename pattern won |
| `pages:1` | Single-page rule |
| `pages:odd(N)` | Odd page-count → `last_back` |
| `visual:…` | Confident content-based choice (include scores when verbose) |
| `visual:tie(…)-> <even_default>` | Inconclusive even-page content → even default |
| `open-fallback` | PDF could not be opened/analyzed → even default |

## Filename Hint

Mapping from base filename regex → `PageOrderMode`.

| Pattern intent (examples) | Mode |
|---------------------------|------|
| fronts/halves style names | `fronts_then_backs` |
| last_back style | `last_back` |
| single / single_sided | `single_sided` |
| interleaved | `interleaved` |

**Validation**: First matching hint wins; if none match, proceed to page-count /
content rules.

## Even-Page Default

User CLI preference (`--even-default`) used only when even-page content evidence
is inconclusive or open fails.

| Field | Allowed values |
|-------|----------------|
| `even_default` | `interleaved` \| `fronts_then_backs` |

Default when flag omitted: `interleaved` (existing batch argparse default).

## Content Scores (internal)

Used only for even-page confident vs tie decisions; not persisted.

| Score | Meaning |
|-------|---------|
| `sim_odd_cluster` | Avg similarity among odd-index (sampled) pages — interleaved candidacy |
| `sim_second_half_cluster` | Avg similarity among second-half (sampled) pages — fronts_then_backs candidacy |

**Validation / decision**:
- Confident interleaved if `sim_odd_cluster >= T` and `sim_odd_cluster >= sim_second_half_cluster + M`
- Confident fronts_then_backs if `sim_second_half_cluster >= T` and `sim_second_half_cluster >= sim_odd_cluster + M`
- Else tie → even default  
- Constants: `T = 0.80`, `M = 0.03` unless fixture-driven retune is documented in research follow-up

## Page Sample Plan

When `N > 40`, detection uses up to 40 evenly spaced indices (see research R3).
Sample plan is ephemeral; must still allow both cluster scores to be computed
for even N.

## Batch Item

One input PDF in `--input-dir`.

| Field | Notes |
|-------|-------|
| `path` | `*.pdf` under input dir |
| `decision` | Page-Order Decision |
| `worker_exit` | Propagated; non-zero increments batch failure count |

## State transitions (per PDF)

```text
[start]
   → name hint? yes → Decision(confident)
   → else page-count single/odd? yes → Decision(confident)
   → else open fail? yes → Decision(open-fallback, even_default)
   → else content scores → confident mode OR tie(even_default)
   → worker(order) → success | worker_failure
```

No transition applies transforms; worker owns geometry.
