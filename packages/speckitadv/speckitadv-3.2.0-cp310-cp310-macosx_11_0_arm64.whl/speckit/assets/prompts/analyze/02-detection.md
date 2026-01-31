---
description: Cross-artifact consistency analysis - Stage 2: Detection passes
stage: 2
total_stages: 3
version: 1.1.0
---

{{include:verification-rules.md}}

## Build Semantic Models

Create internal representations (do not output raw artifacts):

- **Requirements inventory**: Each requirement with stable key (e.g., "User can upload file" -> `user-can-upload-file`)
- **User story/action inventory**: Discrete user actions with acceptance criteria
- **Task coverage mapping**: Map each task to requirements (by keyword/explicit reference)
- **Constitution rule set**: Extract principle names and MUST/SHOULD normative statements

## Detection Passes

Focus on high-signal findings. Limit to 50 findings total.

### A. Duplication Detection

- Identify near-duplicate requirements
- Mark lower-quality phrasing for consolidation

### B. Ambiguity Detection

- Flag vague adjectives (fast, scalable, secure, intuitive) lacking measurable criteria
- Flag unresolved placeholders (TODO, TKTK, ???, `<placeholder>`)

### C. Underspecification

- Requirements with verbs but missing object or measurable outcome
- User stories missing acceptance criteria alignment
- Tasks referencing files/components not defined in spec/plan

### D. Constitution Alignment

- Any requirement or plan element conflicting with a MUST principle
- Missing mandated sections or quality gates from constitution

### E. Coverage Gaps

- Requirements with zero associated tasks
- Tasks with no mapped requirement/story
- Non-functional requirements not reflected in tasks

### F. Inconsistency

- Terminology drift (same concept named differently across files)
- Data entities in plan but absent in spec (or vice versa)
- Task ordering contradictions
- Conflicting requirements (e.g., one requires Next.js while other specifies Vue)

### G. Guideline Compliance (if guidelines loaded)

Report violations as:

- **CRITICAL**: Banned library specified in plan
- **HIGH**: Mandatory corporate library not specified
- **MEDIUM**: Architecture pattern deviates from guidelines
- **LOW**: Minor style/convention deviations

## Severity Assignment

- **CRITICAL**: Violates constitution MUST, missing core artifact, or requirement blocking baseline functionality
- **HIGH**: Duplicate/conflicting requirement, ambiguous security/performance attribute
- **MEDIUM**: Terminology drift, missing non-functional task coverage
- **LOW**: Style/wording improvements, minor redundancy

---

**Next:** `speckitadv analyze --stage=3`
