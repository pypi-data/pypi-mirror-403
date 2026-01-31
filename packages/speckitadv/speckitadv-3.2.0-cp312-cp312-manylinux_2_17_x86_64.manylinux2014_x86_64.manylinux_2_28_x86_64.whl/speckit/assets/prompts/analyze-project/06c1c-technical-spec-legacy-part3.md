---
stage: technical_spec_legacy_part3
requires: technical_spec_legacy_part2_complete
condition: state.analysis_scope == "A"
outputs: technical_spec_legacy_complete
version: 3.5.0
---

# Stage 6C1-3: Technical Specification - Legacy System (Part 3)

## Purpose

Generate **Sections 17-23** of the technical specification documenting HOW the LEGACY system is BUILT.

**This is Part 3 of 3** for the legacy technical specification.

| Part | Sections | Focus |
|------|----------|-------|
| Part 1 | 1-8 | Architecture + Diagrams |
| Part 2 | 9-16 | Components + Data + Tech Stack |
| **Part 3 (this)** | 17-23 | Migration + Risks + ADR |

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

# Recall from ACTUAL cached paths shown in stats output (Migration, Risks, ADR)
# Common examples - use paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/infrastructure")  # if exists in stats
recall_understanding(target="{project_path}/config")          # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check

Verify `{reports_dir}/technical-spec-legacy.md` exists with Sections 1-16.

**IF Parts 1-2 not complete:** STOP - Complete previous parts first.

---

## Source of Truth

- `{reports_dir}/analysis-report.md`
- `{data_dir}/validation-scoring.json`
- Existing technical-spec-legacy.md

**Output File:** `{reports_dir}/technical-spec-legacy.md` (append)

---

## Sections to Generate (Part 3)

### Section 17: Migration / Expansion Paths

```markdown
## 17. Migration / Expansion Paths (Legacy Analysis)

### Current Constraints

| Constraint | Impact | Evidence |
|------------|--------|----------|
| <<constraint>> | <<impact>> | <<file:line>> |

### Potential Migration Paths

| Path | Effort | Risk | Rationale |
|------|--------|------|-----------|
| <<path>> | High/Medium/Low | High/Medium/Low | <<rationale>> |
```

---

### Section 18: Risks & Decisions (RAD)

```markdown
## 18. Risks & Decisions (Technical)

### Technical Risks

| Risk | Severity | Evidence | Mitigation |
|------|----------|----------|------------|
| <<tech debt>> | High/Medium/Low | <<file:line>> | <<suggestion>> |
| <<security gap>> | High/Medium/Low | <<file:line>> | <<suggestion>> |

### Architecture Decisions (Historical)

| Decision | Rationale | Evidence | Impact |
|----------|-----------|----------|--------|
| <<decision>> | <<why made>> | <<file/comment>> | <<current impact>> |
```

---

### Section 19: R->C->T Traceability

```markdown
## 19. Requirements -> Code -> Tests Traceability

| Requirement | Code Location | Test Coverage | Status |
|-------------|---------------|---------------|--------|
| FR-CRIT-001 | <<file:line>> | <<test file>> | Covered/Gap |
| FR-CRIT-002 | <<file:line>> | <<test file>> | Covered/Gap |
```

---

### Section 20: Architecture Decision Records (Historical)

```markdown
## 20. Architecture Decision Records (Legacy)

### ADR-001: <<Decision Title>>

**Status**: Implemented (Legacy)
**Context**: <<Why decision was needed>>
**Decision**: <<What was decided>>
**Consequences**: <<Current impact>>
**Evidence**: <<Where implemented>>

### ADR-002: <<Next Decision>>

<<Repeat for significant architectural decisions>>
```

---

### Section 21: Infrastructure (Current)

```markdown
## 21. Infrastructure (Current State)

### Current Infrastructure

| Component | Technology | Purpose | Evidence |
|-----------|------------|---------|----------|
| <<compute>> | <<type>> | <<purpose>> | <<config>> |
| <<storage>> | <<type>> | <<purpose>> | <<config>> |
| <<network>> | <<type>> | <<purpose>> | <<config>> |

### Infrastructure Diagram

{Mermaid diagram of current infrastructure}
```

---

### Section 22: CI/CD Pipeline (Current)

```markdown
## 22. CI/CD Pipeline (Current)

### Pipeline Stages

| Stage | Tool | Purpose | Evidence |
|-------|------|---------|----------|
| Build | <<tool>> | <<purpose>> | <<config file>> |
| Test | <<tool>> | <<purpose>> | <<config file>> |
| Deploy | <<tool>> | <<purpose>> | <<config file>> |

### Pipeline Diagram

{Mermaid diagram of current pipeline}
```

---

### Section 23: Open Questions & Next Steps

```markdown
## 23. Open Questions & Next Steps

### Open Questions

1. <<Question about architecture>>
2. <<Question about tech debt>>
3. <<Question about migration>>

### Next Steps

1. Review with technical stakeholders
2. Generate technical-spec-target.md
3. Plan migration based on both specs
```

---

## Writing Instructions

**Step 1**: Read existing file
**Step 2**: Append Sections 17-23
**Step 3**: Display completion summary

```text
[ok] Part 3/3 complete: Sections 17-23 appended

===========================================================
  ARTIFACT COMPLETE: technical-spec-legacy.md

  Chain ID: {chain_id}
  Total Sections: 23
  Total Lines: [COUNT]

  This documents HOW the LEGACY system is built.

  NEXT: Generate technical-spec-target.md
===========================================================

ARTIFACT_COMPLETE:TECHNICAL_SPEC_LEGACY
```

---

## Verification Gate

- [ ] All 23 sections present
- [ ] ADRs documented
- [ ] CI/CD pipeline documented
- [ ] Traceability matrix complete
- [ ] No placeholders

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits technical-spec-target Part 1. **Do NOT generate artifacts until you run this command.**
