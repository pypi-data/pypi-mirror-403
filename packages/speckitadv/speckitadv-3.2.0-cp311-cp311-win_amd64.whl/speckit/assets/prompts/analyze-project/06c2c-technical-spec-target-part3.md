---
stage: technical_spec_target_part3
requires: technical_spec_target_part2_complete
condition: state.analysis_scope == "A"
outputs: technical_spec_target_complete
version: 3.5.0
---

# Stage 6C2-3: Technical Specification - Target System (Part 3)

## Purpose

Generate **Sections 17-23** of the technical specification documenting HOW the MODERNIZED system will be BUILT.

**This is Part 3 of 3** for the target technical specification.

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

Verify `{reports_dir}/technical-spec-target.md` exists with Sections 1-16.

**IF Parts 1-2 not complete:** STOP - Complete previous parts first.

---

## Source of Truth

- `{reports_dir}/technical-spec-legacy.md` Sections 17-23
- `{data_dir}/validation-scoring.json`
- Existing technical-spec-target.md

**Output File:** `{reports_dir}/technical-spec-target.md` (append)

---

## Sections to Generate (Part 3)

### Section 17: Migration / Expansion Paths

```markdown
## 17. Migration / Expansion Paths (Target System)

### Migration Strategy

Based on user preferences and legacy analysis:

| Migration Aspect | Approach | Rationale | Q# |
|------------------|----------|-----------|-----|
| Data Migration | <<approach>> | <<why>> | Q2 |
| Code Migration | <<approach>> | <<why>> | Q1 |
| Infrastructure Migration | <<approach>> | <<why>> | Q5, Q6, Q7 |

### Migration Phases

{Mermaid gantt chart showing migration phases}

### Phase 1: Foundation

| Task | Legacy State | Target State | Dependencies |
|------|--------------|--------------|--------------|
| <<task>> | <<current>> | <<target>> | <<deps>> |

### Phase 2: Data Migration

| Data Set | Volume | Strategy | Downtime Required |
|----------|--------|----------|-------------------|
| <<dataset>> | <<size>> | <<ETL/CDC/etc>> | <<yes/no/minimal>> |

### Phase 3: Cutover

| Component | Cutover Strategy | Rollback Plan | Success Criteria |
|-----------|------------------|---------------|------------------|
| <<component>> | <<blue-green/canary>> | <<rollback steps>> | <<metrics>> |

### Expansion Paths (Post-Migration)

| Expansion | Enabled By | Effort | Business Value |
|-----------|------------|--------|----------------|
| <<feature>> | <<Q1/Q2/Q5 choice>> | Low/Medium/High | <<value>> |
```

---

### Section 18: Risks & Decisions (RAD)

```markdown
## 18. Risks & Decisions (Migration Technical)

### Migration Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Data loss during migration | Medium | Critical | <<mitigation>> | Data Team |
| Performance degradation | Medium | High | <<mitigation>> | Platform Team |
| Integration failures | Low | High | <<mitigation>> | Integration Team |
| Skill gap (Q1 language) | <<based on Q1>> | Medium | Training plan | Engineering |

### Technical Decisions Made

Based on user preferences (Q1-Q10):

| Decision | Options Considered | Chosen (Q#) | Rationale |
|----------|-------------------|-------------|-----------|
| Runtime | <<options>> | Q1: {answer} | <<why>> |
| Database | <<options>> | Q2: {answer} | <<why>> |
| Message Bus | <<options>> | Q3: {answer} | <<why>> |
| Package Manager | <<options>> | Q4: {answer} | <<why>> |
| Deployment | <<options>> | Q5: {answer} | <<why>> |
| IaC | <<options>> | Q6: {answer} | <<why>> |
| Container | <<options>> | Q7: {answer} | <<why>> |
| Observability | <<options>> | Q8: {answer} | <<why>> |
| Security | <<options>> | Q9: {answer} | <<why>> |
| Testing | <<options>> | Q10: {answer} | <<why>> |

### Open Technical Decisions

| Decision | Options | Recommendation | Deadline |
|----------|---------|----------------|----------|
| <<decision>> | <<options>> | <<recommendation>> | <<when>> |
```

---

### Section 19: R->C->T Traceability

```markdown
## 19. Requirements -> Code -> Tests Traceability (Target)

### Traceability Matrix

| Requirement | Legacy Location | Target Location | Test Coverage |
|-------------|-----------------|-----------------|---------------|
| FR-CRIT-001 | <<legacy file>> | <<target module>> | <<test file>> |
| FR-CRIT-002 | <<legacy file>> | <<target module>> | <<test file>> |

### Migration Verification

| Requirement | Legacy Test | Target Test | Parity Verified |
|-------------|-------------|-------------|-----------------|
| FR-CRIT-001 | <<legacy test>> | <<target test>> | [ ] |

### Test Migration Strategy

Based on Q10 ({answer}):

| Test Type | Legacy Coverage | Target Coverage | Migration Approach |
|-----------|-----------------|-----------------|-------------------|
| Unit | <<legacy %>> | <<target %>> | <<rewrite/convert>> |
| Integration | <<legacy %>> | <<target %>> | <<rewrite/convert>> |
| E2E | <<legacy %>> | <<target %>> | <<rewrite/convert>> |
```

---

### Section 20: Architecture Decision Records (Target)

```markdown
## 20. Architecture Decision Records (Target)

### ADR-001: Target Language Selection

**Status**: Approved
**Context**: Modernization requires selecting target language/runtime
**Decision**: Q1: {answer}
**Consequences**:
- Positive: <<benefits>>
- Negative: <<trade-offs>>
- Neutral: <<considerations>>
**Evidence**: User preference Q1 in validation-scoring.json

### ADR-002: Database Selection

**Status**: Approved
**Context**: Data layer modernization
**Decision**: Q2: {answer}
**Consequences**:
- Positive: <<benefits>>
- Negative: <<migration effort>>
**Evidence**: User preference Q2

### ADR-003: Deployment Strategy

**Status**: Approved
**Context**: Infrastructure modernization
**Decision**: Q5: {answer} with Q7: {answer} containers
**Consequences**:
- Positive: <<scalability, reliability>>
- Negative: <<complexity, learning curve>>
**Evidence**: User preferences Q5, Q7

### ADR-004: Observability Stack

**Status**: Approved
**Context**: Operations and monitoring
**Decision**: Q8: {answer}
**Consequences**:
- Positive: <<visibility, debugging>>
- Negative: <<cost, setup>>
**Evidence**: User preference Q8

### ADR-005: Security Architecture

**Status**: Approved
**Context**: Authentication and authorization
**Decision**: Q9: {answer}
**Consequences**:
- Positive: <<security posture>>
- Negative: <<implementation effort>>
**Evidence**: User preference Q9
```

---

### Section 21: Infrastructure (Target)

```markdown
## 21. Infrastructure (Target State)

### Target Infrastructure

Based on Q5 ({answer}), Q6 ({answer}), Q7 ({answer}):

| Component | Legacy | Target | IaC Resource |
|-----------|--------|--------|--------------|
| Compute | <<legacy>> | <<Q5/Q7 based>> | <<Q6 resource>> |
| Storage | <<legacy>> | <<Q2/Q5 based>> | <<Q6 resource>> |
| Network | <<legacy>> | <<Q5 based>> | <<Q6 resource>> |
| Load Balancer | <<legacy>> | <<Q5 based>> | <<Q6 resource>> |
| CDN | <<legacy/none>> | <<if needed>> | <<Q6 resource>> |

### Infrastructure Diagram (Target)

{Mermaid diagram of target infrastructure}

### IaC Structure

Based on Q6 ({answer}):

```text
infrastructure/
+-- {Q6_format}/
    +-- modules/
    |   +-- compute/
    |   +-- database/
    |   +-- network/
    |   +-- monitoring/
    +-- environments/
    |   +-- dev/
    |   +-- staging/
    |   +-- prod/
    +-- main.{Q6_ext}
```

### Cost Comparison

| Component | Legacy Cost | Target Cost | Change |
|-----------|-------------|-------------|--------|
| Compute | <<legacy>> | <<target>> | <<+/->> |
| Database | <<legacy>> | <<target>> | <<+/->> |
| Network | <<legacy>> | <<target>> | <<+/->> |
| **Total** | <<legacy>> | <<target>> | <<+/->> |

---

### Section 22: CI/CD Pipeline (Target)

```markdown
## 22. CI/CD Pipeline (Target)

### Pipeline Overview

Based on Q5 ({answer}), Q10 ({answer}):

{Mermaid diagram of target CI/CD pipeline}

### Pipeline Stages

| Stage | Tool | Purpose | Quality Gate |
|-------|------|---------|--------------|
| Build | <<Q1 build tool>> | Compile/package | Build success |
| Test | <<Q10 framework>> | Automated testing | Coverage threshold |
| Security | <<SAST tool>> | Security scan | No critical findings |
| Package | <<Q7 tool>> | Container image | Image scan pass |
| Deploy | <<Q5/Q6 tool>> | Deployment | Health checks |

### Environment Promotion

| Stage | Environment | Trigger | Approval |
|-------|-------------|---------|----------|
| Dev | development | Push to feature branch | Auto |
| Staging | staging | PR merge to main | Auto |
| Prod | production | Release tag | Manual |

### Rollback Strategy

| Scenario | Detection | Action | Recovery Time |
|----------|-----------|--------|---------------|
| Deployment failure | Health check | Auto rollback | < 5 min |
| Performance degradation | Metrics alert | Manual decision | < 15 min |
| Data corruption | Integrity check | Restore from backup | < 1 hour |

### Pipeline Configuration

Based on Q5 ({answer}):

```yaml
# Example pipeline structure
pipeline:
  stages:
    - build
    - test
    - security
    - package
    - deploy

  build:
    runtime: {Q1_answer}
    package_manager: {Q4_answer}

  test:
    framework: {Q10_answer}
    coverage_threshold: 80%

  package:
    container: {Q7_answer}
    registry: <<registry>>

  deploy:
    platform: {Q5_answer}
    iac: {Q6_answer}
```

---

### Section 23: Open Questions & Next Steps

```markdown
## 23. Open Questions & Next Steps

### Open Technical Questions

1. **Performance Baseline**: What are the exact legacy performance metrics for comparison?
2. **Data Migration Window**: What is the acceptable downtime for data migration?
3. **Feature Parity**: Are there legacy features that should NOT be migrated?
4. **Integration Partners**: Do external systems need to be notified of API changes?

### Resolved Questions

| Question | Resolution | Evidence |
|----------|------------|----------|
| Target language | Q1: {answer} | User preference |
| Database technology | Q2: {answer} | User preference |
| Deployment platform | Q5: {answer} | User preference |

### Next Steps

1. **Review Technical Spec** with engineering team
2. **Resolve Open Questions** in this section
3. **Create Migration Runbook** based on Section 17
4. **Set Up Infrastructure** using Section 21 IaC
5. **Implement CI/CD Pipeline** per Section 22
6. **Begin Phase 1 Migration** per Section 17

### Migration Readiness Checklist

- [ ] All ADRs approved by stakeholders
- [ ] Infrastructure provisioned in dev environment
- [ ] CI/CD pipeline operational
- [ ] Security controls implemented
- [ ] Observability stack configured
- [ ] Rollback procedures tested
- [ ] Team trained on target stack (Q1, Q2)
```

---

## Writing Instructions

**Step 1**: Read existing file
**Step 2**: Append Sections 17-23
**Step 3**: Display completion summary

```text
[ok] Part 3/3 complete: Sections 17-23 appended

===========================================================
  ARTIFACT COMPLETE: technical-spec-target.md

  Chain ID: {chain_id}
  Total Sections: 23
  Total Lines: [COUNT]

  This documents HOW the TARGET system will be built.

  User Preferences Applied (Q1-Q10):
    Q1 Language: {answer}
    Q2 Database: {answer}
    Q3 Message Bus: {answer}
    Q4 Package Manager: {answer}
    Q5 Deployment: {answer}
    Q6 IaC: {answer}
    Q7 Container: {answer}
    Q8 Observability: {answer}
    Q9 Security: {answer}
    Q10 Testing: {answer}

  NEXT: Generate stage-prompts.md
===========================================================

ARTIFACT_COMPLETE:TECHNICAL_SPEC_TARGET
```

---

## Verification Gate

- [ ] All 23 sections present
- [ ] ADRs document all Q1-Q10 decisions
- [ ] CI/CD pipeline documented with Q5, Q10 applied
- [ ] Infrastructure documented with Q5, Q6, Q7 applied
- [ ] Migration phases defined
- [ ] Traceability matrix complete
- [ ] No placeholders

---

## Both Technical Specs Complete

```text
===========================================================
  BOTH TECHNICAL SPECS COMPLETE

  1. technical-spec-legacy.md - LEGACY system (how it's built today)
  2. technical-spec-target.md - TARGET system (how it will be built)

  Chain ID: {chain_id}

  User Preferences Applied:
    Q1 Language: {answer}
    Q2 Database: {answer}
    Q3 Message Bus: {answer}
    Q4 Package Manager: {answer}
    Q5 Deployment: {answer}
    Q6 IaC: {answer}
    Q7 Container: {answer}
    Q8 Observability: {answer}
    Q9 Security: {answer}
    Q10 Testing: {answer}

  Now proceeding to stage-prompts...
===========================================================

ARTIFACT_COMPLETE:TECHNICAL_SPEC_TARGET
```

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits the next prompt (stage-prompts). **Do NOT generate artifacts until you run this command.**
