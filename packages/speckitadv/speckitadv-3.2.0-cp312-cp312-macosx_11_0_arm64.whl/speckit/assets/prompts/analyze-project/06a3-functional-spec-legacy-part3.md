---
stage: functional_spec_legacy_part3
requires: functional_spec_legacy_part2_complete
condition: state.analysis_scope == "A"
outputs: functional_spec_legacy_complete
version: 3.5.0
---

# Stage 6A-3: Functional Specification - Legacy System (Part 3)

## Purpose

Generate **Sections 18-24 + Appendices** of the functional specification documenting WHAT the LEGACY/EXISTING system CURRENTLY does.

**This is Part 3 of 3** for the legacy functional specification.

| Part | Sections | Focus |
|------|----------|-------|
| Part 1 | 1-8 | Foundation + Use Cases + Business Logic |
| Part 2 | 9-17 | Requirements + Data + Integration |
| **Part 3 (this)** | 18-24 | Quirks + Risks + Checklists |

---

{{include:strict-execution-mode.md}}

{{include:analyze-state-management.md}}

---

## AI Context Cache: Recall Stored Understanding

```text
# FIRST: Discover ALL cached entries (project, modules, files)
get_understanding_stats(limit=50)
# Review output to identify ALL cached targets and their scopes

recall_understanding(target="project")

# Recall modules with gotchas for Quirks & Risks sections
# Use ACTUAL paths from YOUR get_understanding_stats output
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check

1. Verify `{reports_dir}/functional-spec-legacy.md` exists with Sections 1-17

**IF Parts 1-2 not complete:** STOP - Run `speckitadv analyze-project` to complete previous parts first.

---

## Source of Truth

**Extract ALL content from these sources:**

- `{reports_dir}/analysis-report.md` (all phases)
- `{data_dir}/category-patterns.json` (code patterns)
- `{data_dir}/deep-dive-patterns.json` (detailed analysis)
- `{data_dir}/validation-scoring.json` (risks and scores)

**Output File:** `{reports_dir}/functional-spec-legacy.md` (append to existing)

---

## Sections to Generate (Part 3)

Append these sections to `{reports_dir}/functional-spec-legacy.md`:

### Section 18: Known Quirks & Legacy Behaviors

```markdown
## 18. Known Quirks & Legacy Behaviors

### Quirk 1: <<Name>>

- **Description**: <<What happens>>
- **Evidence**: <<file:line>>
- **Root Cause**: <<Why it exists (workaround, bug, limitation)>>
- **Impact**: <<Who is affected, when>>
- **Related State Machine**: SM-<<id>> (if applicable)
- **Related Config**: CFG-<<id>> (if applicable)
- **Decision Needed**: Preserve or fix in modernization?

### Quirk 2: <<Name>>

<<Repeat for each quirk discovered>>
```

---

### Section 19: Risks, Assumptions, Decisions (RAD)

```markdown
## 19. Risks, Assumptions, Decisions (RAD)

### Risks (Identified from Code Analysis)

| Risk | Evidence | Impact | Mitigation |
|------|----------|--------|------------|
| <<Missing input validation>> | <<file:line>> | HIGH | Add validation layer |
| <<Hardcoded credentials>> | <<file:line>> | CRITICAL | Move to secrets manager |
| <<Race condition>> | <<file:line>> | MEDIUM | Add locking mechanism |

### Assumptions (Made During Analysis)

1. <<Assumption 1>>: <<Description>> (Unable to verify from code; needs user confirmation)
2. <<Assumption 2>>: <<Description>>

### Decisions Needed

1. **<<Decision 1>>**: Should we preserve <<legacy quirk X>>?
   - **Options**: A) Preserve, B) Fix
   - **Owner**: User
   - **Deadline**: Before modernization begins

2. **<<Decision 2>>**: <<Question>>
   - **Options**: <<choices>>
   - **Owner**: <<stakeholder>>
```

---

### Section 20: Value / Business Case

```markdown
## 20. Value / Business Case (Legacy System)

### Current Value Delivered

Based on code analysis, the legacy system delivers:

- <<Value 1>>: <<Quantify if possible (N users, M transactions/day)>>
- <<Value 2>>: <<Business capability>>
- <<Value 3>>: <<Cost savings/revenue>>

### Modernization Drivers

Why modernize (inferred from code analysis):

1. **Technical Debt**: <<Language version EOL, framework outdated, etc.>>
2. **Performance Issues**: <<Identified bottlenecks from code>>
3. **Security Risks**: <<Vulnerabilities found>>
4. **Scalability Limits**: <<Architecture constraints>>
```

---

### Section 21: Traceability Matrix

```markdown
## 21. Traceability Matrix

### Requirements to Evidence

| Requirement | Use Case | User Story | Business Logic | State Machine | Error Handling | Config | Evidence |
|-------------|----------|------------|----------------|---------------|----------------|--------|----------|
| FR-CRIT-001 | UC-001 | US-CRIT-001 | BL-001 | SM-001 | ERR-001 | CFG-001 | <<file:line>> |
| FR-CRIT-002 | UC-002 | US-CRIT-002 | BL-002 | - | ERR-002 | - | <<file:line>> |
| FR-STD-001 | UC-003 | US-STD-001 | BL-003 | - | - | CFG-002 | <<file:line>> |

### Validation Checklists Cross-Reference

| Checklist | Purpose | When to Use |
|-----------|---------|-------------|
| Section 23 | Business Logic Preservation | Before starting modernization |
| Section 24 | Output Validation | Before stakeholder handoff |
```

---

### Section 22: Next Steps

```markdown
## 22. Next Steps

1. **User Review**: Validate extracted features, use cases, and quirks with stakeholders
2. **Decision Points**: Resolve all "Decision Needed" items in Section 19
3. **Clarifications**: Address assumptions that couldn't be verified from code
4. **State Machine Validation**: Confirm state transitions match expected behavior
5. **Configuration Review**: Verify all config-driven behaviors are documented
6. **Target Spec Generation**: Proceed to functional-spec-target.md
```

---

### Section 23: Business Logic Preservation Checklist

```markdown
## 23. Business Logic Preservation Checklist

[CRITICAL] This checklist ensures ALL business logic is captured before modernization.

### 23.1 Extraction Completeness

| Category | Extracted | Verified | Evidence |
|----------|-----------|----------|----------|
| Validation Rules | [ ] All field validations documented | [ ] Cross-checked with UI | Section 6.5 |
| Calculation Formulas | [ ] All formulas with precision | [ ] Test cases verified | Section 6.3 |
| Decision Trees | [ ] All branching logic mapped | [ ] Edge cases covered | Section 6.2 |
| Business Constants | [ ] All magic numbers documented | [ ] Sources identified | Section 6.4 |
| State Transitions | [ ] All states and transitions | [ ] Invalid paths documented | Section 7 |
| Error Handling | [ ] All exception patterns | [ ] Recovery logic captured | Section 13 |

### 23.2 Critical Business Rules Verification

For each business rule in Section 6, verify:

- [ ] **Rule ID assigned** (BL-XXX format)
- [ ] **Source code reference** (file:line)
- [ ] **Plain English description** (non-technical stakeholder readable)
- [ ] **Pseudocode/algorithm** (developer implementable)
- [ ] **Edge cases documented** (boundary conditions)
- [ ] **Error behavior specified** (what happens on invalid input)

### 23.3 Data Transformation Verification

For each data transformation:

- [ ] **Source format documented** (input structure)
- [ ] **Target format documented** (output structure)
- [ ] **Transformation rules captured** (mapping logic)
- [ ] **Null/empty handling specified**
- [ ] **Type conversions documented**
- [ ] **Precision requirements noted** (decimal places, rounding)

### 23.4 Integration Logic Verification

For each integration point:

- [ ] **Protocol documented** (REST, SOAP, file, queue)
- [ ] **Message format captured** (request/response schemas)
- [ ] **Error handling documented** (retry, timeout, fallback)
- [ ] **Authentication method noted**
- [ ] **Rate limits/throttling documented**
```

---

### Section 24: Output Validation Checklist

```markdown
## 24. Output Validation Checklist

Use this checklist to validate specification completeness before handoff.

### 24.1 Document Quality

| Check | Status | Notes |
|-------|--------|-------|
| All sections complete (no TODO/TBD) | [ ] | |
| All placeholders replaced with actual content | [ ] | |
| All cross-references valid | [ ] | |
| All code references verified (file:line exists) | [ ] | |
| All tables properly formatted | [ ] | |
| All diagrams render correctly | [ ] | |

### 24.2 Content Completeness

| Section | Min Items | Actual | Verified |
|---------|-----------|--------|----------|
| Use Cases (Section 4) | 5+ | <<N>> | [ ] |
| User Stories (Section 5) | 10+ | <<N>> | [ ] |
| Business Logic Rules (Section 6) | 10+ | <<N>> | [ ] |
| State Machines (Section 7) | 1+ | <<N>> | [ ] |
| Configuration Behaviors (Section 8) | 5+ | <<N>> | [ ] |
| Functional Requirements (Section 10) | 10+ | <<N>> | [ ] |
| Error Handling Patterns (Section 13) | 5+ | <<N>> | [ ] |
| Integration Points (Section 17) | 1+ | <<N>> | [ ] |

### 24.3 Traceability Validation

- [ ] Every feature has at least one use case
- [ ] Every use case has at least one user story
- [ ] Every business rule has source code evidence
- [ ] Every state machine has transition evidence
- [ ] Traceability matrix (Section 21) is complete

### 24.4 Stakeholder Readiness

- [ ] Executive Summary readable by non-technical stakeholders
- [ ] Business rules understandable by domain experts
- [ ] Technical details sufficient for developers
- [ ] Edge cases documented for QA team
- [ ] Assumptions documented for product owner review
```

---

### Appendices

```markdown
## Appendix A: Glossary

| Term | Definition | Evidence |
|------|------------|----------|
| <<Term>> | <<Definition from code comments/docs>> | <<file:line>> |

## Appendix B: File Reference Index

| File Path | Purpose | Key Sections |
|-----------|---------|--------------|
| <<path>> | <<purpose>> | <<which spec sections use this>> |

## Appendix C: Change Log

| Date | Author | Change |
|------|--------|--------|
| <<date>> | AI Agent | Initial extraction from legacy code |
```

---

## Writing Instructions

**Step 1**: Read existing file

- Read `{reports_dir}/functional-spec-legacy.md`
- Confirm Sections 1-17 exist

**Step 2**: Append to file using Edit tool

- Append Sections 18-24 and Appendices to the existing file

**Step 3**: Display completion summary

```text
[ok] Part 3/3 complete: Sections 18-24 + Appendices
  - Quirks documented: [COUNT]
  - Risks identified: [COUNT]
  - Decisions needed: [COUNT]
  - Lines generated: [COUNT]

===========================================================
  ARTIFACT COMPLETE: functional-spec-legacy.md

  Chain ID: {chain_id}
  Total Sections: 24 + 3 Appendices
  Total Lines: [COUNT]

  This documents the LEGACY system (what exists today).

  NEXT: Generate functional-spec-target.md (what will be built)
===========================================================

ARTIFACT_COMPLETE:FUNCTIONAL_SPEC_LEGACY
```

---

## Verification Gate

Before proceeding, verify:

- [ ] All 24 sections present
- [ ] 3 Appendices present
- [ ] Section 23 (Preservation Checklist) complete
- [ ] Section 24 (Validation Checklist) complete
- [ ] Traceability matrix links all artifacts
- [ ] No placeholders (TODO, TBD, etc.)

**IF verification fails**: Fix missing content before proceeding.

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits functional-spec-target Part 1. **Do NOT generate artifacts until you run this command.**
