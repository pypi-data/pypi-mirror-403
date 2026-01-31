---
stage: functional_spec_target_part3
requires: functional_spec_target_part2_complete
condition: state.analysis_scope == "A"
outputs: functional_spec_target_complete
version: 3.5.0
---

# Stage 6B-3: Functional Specification - Target System (Part 3)

## Purpose

Generate **Sections 18-24 + Appendices** of the functional specification documenting WHAT the MODERNIZED system WILL do.

**This is Part 3 of 3** for the target functional specification.

| Part | Sections | Focus |
|------|----------|-------|
| Part 1 | 1-8 | Foundation + Use Cases + Business Logic |
| Part 2 | 9-17 | Requirements + Data + Integration |
| **Part 3 (this)** | 18-24 | Modernization Decisions + Checklists |

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

# Recall relevant modules for sections 18-24 (Quirks, Decisions, Risks)
# Use ACTUAL paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/config")  # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check

1. Verify `{reports_dir}/functional-spec-target.md` exists with Sections 1-17

**IF Parts 1-2 not complete:** STOP - Complete previous parts first.

---

## Source of Truth

**Primary Sources:**

- `{reports_dir}/functional-spec-legacy.md` Sections 18-24 (base content)
- `{reports_dir}/functional-spec-target.md` Sections 1-17 (for consistency)
- `{data_dir}/validation-scoring.json` (user preferences Q1-Q10)

**Output File:** `{reports_dir}/functional-spec-target.md` (append to existing)

---

## Sections to Generate (Part 3)

Append these sections to `{reports_dir}/functional-spec-target.md`:

### Section 18: Known Quirks - Modernization Decisions

```markdown
## 18. Known Quirks - Modernization Decisions

For each quirk from legacy Section 18, document the modernization decision:

### Quirk 1: <<Name>>

**Legacy Reference**: Quirk 1 (functional-spec-legacy.md Section 18)
**Decision**: PRESERVE | FIX | REMOVE

| Aspect | Legacy | Target Decision |
|--------|--------|-----------------|
| **Behavior** | <<legacy behavior>> | <<target behavior>> |
| **Root Cause** | <<why it existed>> | <<addressed/preserved>> |
| **Decision** | N/A | PRESERVE / FIX / REMOVE |
| **Rationale** | N/A | <<why this decision>> |
| **Migration Impact** | N/A | <<what changes>> |

**IF PRESERVE**: Document why backward compatibility is needed.
**IF FIX**: Document the correct behavior and migration plan.
**IF REMOVE**: Document deprecation timeline and user communication.

### Quirk 2: <<Name>>

<<Repeat for each legacy quirk>>

### Quirks Summary

| Quirk | Legacy ID | Decision | Migration Effort |
|-------|-----------|----------|------------------|
| <<name>> | Quirk-001 | PRESERVE | None |
| <<name>> | Quirk-002 | FIX | Medium |
| <<name>> | Quirk-003 | REMOVE | Low |
```

---

### Section 19: Risks, Assumptions, Decisions (RAD)

```markdown
## 19. Risks, Assumptions, Decisions (Target System)

### Migration Risks

| Risk | Legacy Risk | Target Mitigation | Owner |
|------|-------------|-------------------|-------|
| <<data loss>> | Section 19 | <<migration testing plan>> | <<team>> |
| <<downtime>> | Section 19 | <<zero-downtime deployment>> | <<team>> |
| <<compatibility>> | NEW | <<backward compatibility layer>> | <<team>> |

### Assumptions (Target System)

1. <<Assumption 1>>: <<Description>> (Inherited from legacy / NEW assumption)
2. <<Assumption 2>>: <<Description>>

### Key Decisions Made

| Decision | Options Considered | Chosen Option | Rationale |
|----------|-------------------|---------------|-----------|
| Language | <<options>> | Q1: {answer} | <<why>> |
| Database | <<options>> | Q2: {answer} | <<why>> |
| Deployment | <<options>> | Q5: {answer} | <<why>> |
| Security | <<options>> | Q9: {answer} | <<why>> |

### Open Decisions (User Input Needed)

| Decision | Options | Recommendation | Deadline |
|----------|---------|----------------|----------|
| <<decision>> | A, B, C | <<recommendation>> | <<date>> |
```

---

### Section 20: Value / Business Case

```markdown
## 20. Value / Business Case (Target System)

### Expected Value from Modernization

| Value Area | Legacy State | Target State | Business Impact |
|------------|--------------|--------------|-----------------|
| Performance | <<legacy>> | <<target>> | <<quantified improvement>> |
| Scalability | <<legacy>> | <<target>> | <<capacity increase>> |
| Maintainability | <<legacy>> | <<target>> | <<reduced effort>> |
| Security | <<legacy>> | <<target>> | <<risk reduction>> |

### ROI Analysis

- **Investment**: <<modernization effort>>
- **Expected Return**: <<benefits>>
- **Timeline**: <<when benefits realized>>

### Success Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| <<metric>> | <<current>> | <<target>> | <<how to measure>> |
```

---

### Section 21: Traceability Matrix

```markdown
## 21. Traceability Matrix (Legacy -> Target)

### Requirements Mapping

| Legacy Req | Target Req | Status | Migration Notes |
|------------|------------|--------|-----------------|
| FR-CRIT-001 | FR-CRIT-001 | PRESERVED | As-is |
| FR-CRIT-002 | FR-CRIT-002 | MODERNIZED | Updated tech stack |
| FR-STD-001 | FR-STD-001 | ENHANCED | Added features |
| N/A | FR-NEW-001 | NEW | Target only |

### Use Case Mapping

| Legacy UC | Target UC | Status | Changes |
|-----------|-----------|--------|---------|
| UC-001 | UC-001 | EXACT | None |
| UC-002 | UC-002 | ENHANCED | <<changes>> |

### Business Logic Mapping

| Legacy BL | Target BL | Preservation | Verification |
|-----------|-----------|--------------|--------------|
| BL-001 | BL-001 | EXACT | Unit tests |
| BL-002 | BL-002 | MODERNIZED | Integration tests |
```

---

### Section 22: Next Steps

```markdown
## 22. Next Steps

### Immediate Actions

1. **Review this specification** with stakeholders
2. **Resolve open decisions** in Section 19
3. **Approve quirk decisions** in Section 18
4. **Proceed to technical specs**

### Technical Specification

After approval:
- Generate `technical-spec-legacy.md` (document HOW legacy is built)
- Generate `technical-spec-target.md` (document HOW target will be built)

### Migration Planning

1. Data migration strategy (from Section 14)
2. API versioning rollout (from Section 16)
3. Integration updates (from Section 17)
```

---

### Section 24: Output Validation Checklist

```markdown
## 24. Output Validation Checklist (Target System)

**Note**: Section 23 (Business Logic Preservation Checklist) is legacy-only.
For target, verify implementation of preserved logic during development.

### 24.1 Document Quality

| Check | Status | Notes |
|-------|--------|-------|
| All sections complete (no TODO/TBD) | [ ] | |
| All Legacy -> Target mappings complete | [ ] | |
| User preferences (Q1-Q10) consistently applied | [ ] | |
| All cross-references valid | [ ] | |
| All tables properly formatted | [ ] | |

### 24.2 Content Completeness

| Section | Legacy Items | Target Items | Mapping Complete |
|---------|--------------|--------------|------------------|
| Use Cases | <<N>> | <<N>> | [ ] |
| User Stories | <<N>> | <<N>> | [ ] |
| Business Logic | <<N>> | <<N>> | [ ] |
| Requirements | <<N>> | <<N>> | [ ] |
| Data Models | <<N>> | <<N>> | [ ] |

### 24.3 Modernization Verification

- [ ] All legacy quirks have PRESERVE/FIX/REMOVE decision
- [ ] All user preferences (Q1-Q10) applied consistently
- [ ] Migration plans documented for all data changes
- [ ] API versioning strategy defined
- [ ] Backward compatibility addressed where needed

### 24.4 Stakeholder Readiness

- [ ] Executive Summary reflects modernization goals
- [ ] Business value clearly articulated
- [ ] Technical decisions justified
- [ ] Migration risks documented with mitigations
- [ ] Open decisions identified for resolution
```

---

### Appendices

```markdown
## Appendix A: Glossary

| Term | Legacy Definition | Target Definition | Change |
|------|-------------------|-------------------|--------|
| <<Term>> | <<legacy>> | <<target>> | <<if changed>> |

## Appendix B: User Preference Summary

| Q# | Topic | User's Choice | Applied In |
|----|-------|---------------|------------|
| Q1 | Language | {answer} | Sections 5, 6, 10, 13 |
| Q2 | Database | {answer} | Sections 12, 14 |
| Q3 | Message Bus | {answer} | Sections 13, 17 |
| Q4 | Package Manager | {answer} | Section 15 |
| Q5 | Deployment | {answer} | Sections 12, 15 |
| Q6 | IaC | {answer} | Section 15 |
| Q7 | Container | {answer} | Section 12 |
| Q8 | Observability | {answer} | Section 12 |
| Q9 | Security | {answer} | Sections 11, 12 |
| Q10 | Testing | {answer} | Section 24 |

## Appendix C: Change Log

| Date | Author | Change |
|------|--------|--------|
| <<date>> | AI Agent | Target specification generated from legacy |
```

---

## Writing Instructions

**Step 1**: Read legacy spec Sections 18-24

- Read `{reports_dir}/functional-spec-legacy.md` Sections 18-24
- Extract quirks, risks, decisions to transform

**Step 2**: Append to file using Edit tool

- Append Sections 18-24 (skip 23) and Appendices

**Step 3**: Display completion summary

```text
[ok] Part 3/3 complete: Sections 18-24 + Appendices
  - Quirk decisions: [COUNT] (PRESERVE: N, FIX: N, REMOVE: N)
  - Open decisions: [COUNT]
  - Lines generated: [COUNT]

===========================================================
  BOTH FUNCTIONAL SPECS COMPLETE

  1. functional-spec-legacy.md - LEGACY system (what exists today)
  2. functional-spec-target.md - TARGET system (what will be built)

  Chain ID: {chain_id}

  User Preferences Applied (Q1-Q10):
    Q1 Language: {answer}
    Q2 Database: {answer}
    Q3 Message Bus: {answer}
    ...

  NEXT: Generate technical specs (legacy + target)
===========================================================

ARTIFACT_COMPLETE:FUNCTIONAL_SPEC_TARGET
```

---

## Verification Gate

Before proceeding, verify:

- [ ] All sections present (18-22, 24, Appendices)
- [ ] Section 23 skipped (legacy only)
- [ ] All quirks have PRESERVE/FIX/REMOVE decision
- [ ] Traceability matrix complete
- [ ] User preferences summary in Appendix B
- [ ] No placeholders (TODO, TBD, etc.)

**IF verification fails**: Fix missing content before proceeding.

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits technical-spec-legacy Part 1. **Do NOT generate artifacts until you run this command.**
