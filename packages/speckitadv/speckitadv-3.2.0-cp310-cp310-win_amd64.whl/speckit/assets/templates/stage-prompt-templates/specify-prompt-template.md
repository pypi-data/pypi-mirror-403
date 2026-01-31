# Specify Stage Prompt (from Legacy Analysis)

**Input Source**: `.analysis/{project}/reports/functional-spec-target.md`
**Project**: <<PROJECT_NAME>>

---

## Instructions

This stage maps legacy functionality to modern requirements.
Use `functional-spec-target.md` from the `.analysis/{project}/reports/` directory
as the source of truth for WHAT the target system should do.

---

## Ready-to-Paste Prompt

```text
SPECIFY requirements for modernization of <<PROJECT_NAME>>.

BASE REQUIREMENTS: Use .analysis/{project}/reports/functional-spec-target.md

PHASING (50/30/15/5):
- Phase 1 (50%): <<List FR-CRIT-* features>>
- Phase 2 (30%): <<List FR-STD-* features>>
- Phase 3 (15%): <<List enhanced features>>
- Phase 4 (5%): <<List optional features>>

CRITICAL FEATURES (must preserve exactly):
<<FOR_EACH FR-CRIT-* from functional-spec-legacy.md>>
- <<FEATURE_NAME>>
  Evidence: <<file:line>>
  Acceptance Criteria: <<from functional-spec-legacy.md>>
<<END_FOR_EACH>>

STANDARD FEATURES (can modernize):
<<FOR_EACH FR-STD-* from functional-spec-legacy.md>>
- <<FEATURE_NAME>>
  Current: <<implementation>>
  Opportunity: <<modernization approach>>
<<END_FOR_EACH>>

LEGACY QUIRKS (decide preserve vs. fix):
<<FOR_EACH FR-QUIRK-* from functional-spec-legacy.md>>
- <<QUIRK_NAME>>
  Issue: <<description>>
  Decision: <<preserve | fix>>
<<END_FOR_EACH>>

DATA MODELS: See functional-spec-legacy.md Section 8
API CONTRACTS: See functional-spec-legacy.md Section 10

For detailed functional requirements, see .analysis/{project}/reports/functional-spec-target.md.
```
