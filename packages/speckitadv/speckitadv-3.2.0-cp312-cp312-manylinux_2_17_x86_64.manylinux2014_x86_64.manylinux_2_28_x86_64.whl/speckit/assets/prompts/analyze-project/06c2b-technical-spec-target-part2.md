---
stage: technical_spec_target_part2
requires: technical_spec_target_part1_complete
condition: state.analysis_scope == "A"
outputs: technical_spec_target_part2_complete
version: 3.5.0
---

# Stage 6C2-2: Technical Specification - Target System (Part 2)

## Purpose

Generate **Sections 9-16** of the technical specification documenting HOW the MODERNIZED system will be BUILT.

**This is Part 2 of 3** for the target technical specification.

| Part | Sections | Focus |
|------|----------|-------|
| Part 1 | 1-8 | Architecture + Diagrams |
| **Part 2 (this)** | 9-16 | Components + Data + Tech Stack |
| Part 3 | 17-23 | Migration + Risks + ADR |

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

# Recall from ACTUAL cached paths shown in stats output (Components, Data, Tech Stack)
# Common examples - use paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/data")      # if exists in stats
recall_understanding(target="{project_path}/services")  # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check

Verify `{reports_dir}/technical-spec-target.md` exists with Sections 1-8.

**IF Part 1 not complete:** STOP - Complete Part 1 first.

---

## Source of Truth

- `{reports_dir}/technical-spec-legacy.md` Sections 9-16
- `{reports_dir}/analysis-report.md`
- `{data_dir}/validation-scoring.json` (user preferences Q1-Q10)
- Existing technical-spec-target.md Sections 1-8

**Output File:** `{reports_dir}/technical-spec-target.md` (append)

---

## Sections to Generate (Part 2)

### Section 9: Capabilities by Phase

```markdown
## 9. Capabilities by Phase (Target Migration)

### Phase 1: Foundation (MVP)

| Capability | Legacy Component | Target Component | Migration Status |
|------------|------------------|------------------|------------------|
| <<capability>> | <<legacy>> | <<target>> | Phase 1 |

### Phase 2: Core Features

| Capability | Legacy Component | Target Component | Migration Status |
|------------|------------------|------------------|------------------|
| <<capability>> | <<legacy>> | <<target>> | Phase 2 |

### Phase 3: Advanced Features

| Capability | Legacy Component | Target Component | Migration Status |
|------------|------------------|------------------|------------------|
| <<capability>> | <<legacy>> | <<target>> | Phase 3 |

### Migration Timeline

{Mermaid gantt chart showing phased migration}
```

---

### Section 10: Component Responsibilities

```markdown
## 10. Component / Service Responsibilities (Target)

### Legacy vs Target Components

| Legacy Component | Target Component | Responsibility | Change |
|------------------|------------------|----------------|--------|
| <<Controller>> | <<Controller>> | Handle HTTP requests | <<Q1 framework>> |
| <<Service>> | <<Service>> | Business logic | <<modernized>> |
| <<Repository>> | <<Repository>> | Data access | <<Q2 database>> |

### New Components (Target Only)

| Component | Responsibility | Rationale | Q# |
|-----------|----------------|-----------|-----|
| <<MessageHandler>> | Process async messages | Q3: {answer} | Q3 |
| <<CacheService>> | Caching layer | Performance | Q2 |

### Removed Components

| Legacy Component | Reason | Replacement |
|------------------|--------|-------------|
| <<component>> | <<obsolete/consolidated>> | <<target replacement>> |
```

---

### Section 11: Interfaces & Contracts

```markdown
## 11. Interfaces & Contracts (Target)

### Internal Interfaces (Target)

| Interface | Provider | Consumer | Legacy Protocol | Target Protocol |
|-----------|----------|----------|-----------------|-----------------|
| <<interface>> | <<component>> | <<component>> | <<legacy>> | <<target>> |

### External Contracts (Target)

| System | Legacy Protocol | Target Protocol | Migration |
|--------|-----------------|-----------------|-----------|
| <<system>> | <<REST 1.0>> | <<REST 2.0 / GraphQL>> | <<strategy>> |

### API Versioning Strategy

Based on functional-spec-target.md Section 16:

| API | Legacy Version | Target Version | Backward Compat |
|-----|----------------|----------------|-----------------|
| <<api>> | v1 | v2 | <<yes/no/deprecated>> |
```

---

### Section 12: Data & Schema

```markdown
## 12. Data & Schema (Target)

### Target Database

Based on Q2 ({answer}):

### Schema Migration

| Legacy Table | Target Table | Schema Changes | Migration Strategy |
|--------------|--------------|----------------|-------------------|
| <<table>> | <<table>> | <<changes>> | <<ETL/incremental>> |

### Target Schema Diagram

{Mermaid ERD diagram for TARGET schema}

### Data Type Mappings

| Legacy Type | Target Type | Conversion | Notes |
|-------------|-------------|------------|-------|
| <<legacy type>> | <<Q2 type>> | <<conversion>> | <<edge cases>> |

### Index Strategy (Target)

| Table | Legacy Indexes | Target Indexes | Rationale |
|-------|----------------|----------------|-----------|
| <<table>> | <<legacy>> | <<target>> | <<Q2 optimization>> |
```

---

### Section 13: Current Tech Stack -> Target Tech Stack

**[!] IMPORTANT: Validate Target Dependencies Against Artifactory**

{{include:artifactory-validation.md}}

For each target dependency identified below, run:

```bash
speckitadv search-lib <package-name>
```

Document results in the "Artifactory Status" column.

```markdown
## 13. Technology Stack (Target)

### Stack Comparison

| Category | Legacy | Target | Q# | Rationale |
|----------|--------|--------|-----|-----------|
| Language | <<legacy>> | {Q1 answer} | Q1 | <<why>> |
| Framework | <<legacy>> | <<based on Q1>> | Q1 | <<why>> |
| Database | <<legacy>> | {Q2 answer} | Q2 | <<why>> |
| Message Bus | <<legacy/none>> | {Q3 answer} | Q3 | <<why>> |
| Package Manager | <<legacy>> | {Q4 answer} | Q4 | <<why>> |
| Container | <<legacy/none>> | {Q7 answer} | Q7 | <<why>> |

### Target Dependencies

**Run `speckitadv search-lib <package>` for each dependency:**

| Package | Version | Purpose | Artifactory Status |
|---------|---------|---------|-------------------|
| `<package>` | `<version>` | `<purpose>` | `[VERIFIED]` / `[NOT FOUND - needs approval]` / `[SKIPPED - not configured]` |

**Blocked Dependencies** (NOT FOUND in Artifactory):

| Package | Proposed Alternative | Status |
|---------|---------------------|--------|
| `<blocked>` | `<alternative>` | `<verified/pending approval>` |

### Version Requirements

| Component | Minimum Version | Target Version | EOL Date |
|-----------|-----------------|----------------|----------|
| <<Q1 runtime>> | <<min>> | <<target>> | <<EOL>> |
| <<Q2 database>> | <<min>> | <<target>> | <<EOL>> |
```

---

### Section 14: NFR Targets

```markdown
## 14. NFR Targets (Target System)

### Performance Targets

| Metric | Legacy Value | Target Value | Improvement | Method |
|--------|--------------|--------------|-------------|--------|
| Response time (p95) | <<legacy>> | <<target>> | <<% better>> | <<Q1, Q2>> |
| Throughput | <<legacy>> | <<target>> | <<% better>> | <<Q5, Q7>> |
| Cold start | <<legacy>> | <<target>> | <<% better>> | <<Q7>> |

### Availability Targets

| Metric | Legacy | Target | Method |
|--------|--------|--------|--------|
| Uptime SLA | <<legacy>> | <<target>> | <<Q5 approach>> |
| Recovery time (RTO) | <<legacy>> | <<target>> | <<Q5, Q7>> |
| Recovery point (RPO) | <<legacy>> | <<target>> | <<Q2 backup>> |

### Scalability Targets

| Metric | Legacy Limit | Target Capacity | Method |
|--------|--------------|-----------------|--------|
| Concurrent users | <<legacy>> | <<target>> | <<Q5, Q7>> |
| Data volume | <<legacy>> | <<target>> | <<Q2>> |
| Request rate | <<legacy>> | <<target>> | <<Q5>> |
```

---

### Section 15: Operations & SRE

```markdown
## 15. Operations & SRE (Target)

### Observability Stack

Based on Q8 ({answer}):

| Aspect | Legacy Tool | Target Tool | Q8 Component |
|--------|-------------|-------------|--------------|
| Metrics | <<legacy>> | <<Q8 metrics>> | Metrics |
| Logging | <<legacy>> | <<Q8 logging>> | Logging |
| Tracing | <<legacy/none>> | <<Q8 tracing>> | Tracing |
| Alerting | <<legacy>> | <<Q8 alerting>> | Alerting |

### Key Metrics (Target)

| Metric | Type | Alert Threshold | Dashboard |
|--------|------|-----------------|-----------|
| <<metric>> | <<gauge/counter>> | <<threshold>> | <<dashboard>> |

### Runbook Updates

| Operation | Legacy Runbook | Target Runbook | Changes |
|-----------|----------------|----------------|---------|
| Deployment | <<legacy>> | <<target>> | <<Q5, Q6, Q7>> |
| Rollback | <<legacy>> | <<target>> | <<Q5, Q7>> |
| Scaling | <<legacy/manual>> | <<target/auto>> | <<Q5, Q7>> |

### On-Call Considerations

| Aspect | Legacy | Target | Training Needed |
|--------|--------|--------|-----------------|
| Alert volume | <<high/medium/low>> | <<expected>> | <<yes/no>> |
| Complexity | <<legacy>> | <<target>> | <<skills>> |
```

---

### Section 16: Security & Compliance

```markdown
## 16. Security & Compliance (Target)

### Security Architecture

Based on Q9 ({answer}):

| Aspect | Legacy | Target | Q9 Applied |
|--------|--------|--------|------------|
| Authentication | <<legacy>> | <<Q9 auth>> | Yes |
| Authorization | <<legacy>> | <<Q9 authz>> | Yes |
| Encryption at rest | <<legacy>> | <<Q9/Q2 based>> | Yes |
| Encryption in transit | <<legacy>> | <<TLS 1.3>> | Standard |
| Secrets management | <<legacy>> | <<Q9 approach>> | Yes |

### Security Controls (Target)

| Control | Implementation | Evidence |
|---------|----------------|----------|
| OWASP Top 10 | <<mitigations>> | <<tests/tools>> |
| Input validation | <<Q1 framework validation>> | <<schema validation>> |
| Output encoding | <<Q1 framework encoding>> | <<template engine>> |
| Rate limiting | <<Q5 infrastructure based>> | <<config>> |
| WAF | <<based on Q5>> | <<config>> |

### Compliance Mapping

| Requirement | Legacy Status | Target Status | Changes |
|-------------|---------------|---------------|---------|
| <<GDPR/SOX/HIPAA>> | <<status>> | <<target status>> | <<what changes>> |

### Security Testing (Target)

Based on Q10 ({answer}):

| Test Type | Tool | Frequency | CI/CD Integration |
|-----------|------|-----------|-------------------|
| SAST | <<tool>> | Per commit | Yes |
| DAST | <<tool>> | Per deploy | Yes |
| Dependency scan | <<Q4 based>> | Daily | Yes |
| Penetration | <<manual/automated>> | <<frequency>> | No |
```

---

## Writing Instructions

**Step 1**: Read existing files

- Read `{reports_dir}/technical-spec-legacy.md` Sections 9-16
- Read `{reports_dir}/technical-spec-target.md` Sections 1-8

**Step 2**: Append to file using Edit tool

- Append Sections 9-16 to technical-spec-target.md

**Step 3**: Display progress

```text
[ok] Part 2/3 complete: Sections 9-16 appended
  - Components mapped: [COUNT] (legacy -> target)
  - Data tables migrated: [COUNT]
  - Tech stack items: [COUNT]
  - User preferences applied: Q1, Q2, Q3, Q4, Q7, Q8, Q9, Q10
  - Lines generated: [COUNT]

```

---

## Verification Gate

- [ ] Sections 9-16 appended
- [ ] Tech stack shows Legacy -> Target with Q1-Q10 applied
- [ ] Schema migration plan complete
- [ ] Security section applies Q9
- [ ] Observability applies Q8
- [ ] No placeholders

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits Part 3 (Sections 17-23). **Do NOT generate artifacts until you run this command.**
