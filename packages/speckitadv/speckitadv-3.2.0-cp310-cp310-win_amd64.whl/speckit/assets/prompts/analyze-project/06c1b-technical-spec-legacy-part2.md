---
stage: technical_spec_legacy_part2
requires: technical_spec_legacy_part1_complete
condition: state.analysis_scope == "A"
outputs: technical_spec_legacy_part2_complete
version: 3.5.0
---

# Stage 6C1-2: Technical Specification - Legacy System (Part 2)

## Purpose

Generate **Sections 9-16** of the technical specification documenting HOW the LEGACY system is BUILT.

**This is Part 2 of 3** for the legacy technical specification.

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

Verify `{reports_dir}/technical-spec-legacy.md` exists with Sections 1-8.

**IF Part 1 not complete:** STOP - Complete Part 1 first.

---

## Source of Truth

- `{reports_dir}/analysis-report.md`
- `{data_dir}/category-patterns.json`
- `{data_dir}/config-analysis.json`
- Existing technical-spec-legacy.md Sections 1-8

**Output File:** `{reports_dir}/technical-spec-legacy.md` (append)

---

## Sections to Generate (Part 2)

### Section 9: Capabilities by Phase

```markdown
## 9. Capabilities by Phase (Current State)

### Core Capabilities (80%)

| Capability | Component | Coverage | Evidence |
|------------|-----------|----------|----------|
| <<capability>> | <<component>> | <<%>> | <<file:line>> |

### Supporting Capabilities (15%)

<<Same format>>

### Edge Cases (5%)

<<Same format>>
```

---

### Section 10: Component Responsibilities

```markdown
## 10. Component / Service Responsibilities

| Component | Responsibility | Dependencies | Evidence |
|-----------|----------------|--------------|----------|
| <<Controller>> | <<Handle HTTP requests>> | <<Services>> | <<folder>> |
| <<Service>> | <<Business logic>> | <<Repositories>> | <<folder>> |
| <<Repository>> | <<Data access>> | <<Database>> | <<folder>> |
```

---

### Section 11: Interfaces & Contracts

```markdown
## 11. Interfaces & Contracts

### Internal Interfaces

| Interface | Provider | Consumer | Protocol | Evidence |
|-----------|----------|----------|----------|----------|
| <<interface>> | <<component>> | <<component>> | <<method/event>> | <<file:line>> |

### External Contracts

| System | Protocol | Schema | Evidence |
|--------|----------|--------|----------|
| <<system>> | <<REST/SOAP>> | <<schema location>> | <<file:line>> |
```

---

### Section 12: Data & Schema

```markdown
## 12. Data & Schema (Legacy)

### Database Schema

| Table | Columns | Indexes | Relationships | Evidence |
|-------|---------|---------|---------------|----------|
| <<table>> | <<count>> | <<list>> | <<FKs>> | <<migration file>> |

### Schema Diagram

{Mermaid ERD diagram}

**Evidence**: Extracted from migrations/ORM models
```

---

### Section 13: Current Tech Stack

```markdown
## 13. Current Tech Stack

| Category | Technology | Version | Purpose | Evidence |
|----------|------------|---------|---------|----------|
| Language | <<Node/Java>> | <<version>> | <<purpose>> | <<package.json>> |
| Framework | <<Express/Spring>> | <<version>> | <<purpose>> | <<config>> |
| Database | <<PostgreSQL>> | <<version>> | <<purpose>> | <<config>> |
| Cache | <<Redis/None>> | <<version>> | <<purpose>> | <<config>> |

**Evidence**: Extracted from dependency files
```

---

### Section 14: NFR Targets (Current)

```markdown
## 14. NFR Targets (Current Implementation)

### Performance

| Metric | Current Value | Source | Evidence |
|--------|---------------|--------|----------|
| Response time | <<value>> | <<config/code>> | <<file:line>> |
| Throughput | <<value>> | <<config/code>> | <<file:line>> |

### Availability

| Metric | Current | Evidence |
|--------|---------|----------|
| Uptime SLA | <<value>> | <<deployment config>> |
| Recovery time | <<value>> | <<runbook/config>> |
```

---

### Section 15: Operations & SRE

```markdown
## 15. Operations & SRE (Current)

### Monitoring

| Aspect | Tool | Metrics | Evidence |
|--------|------|---------|----------|
| APM | <<tool/none>> | <<metrics>> | <<config>> |
| Logs | <<tool>> | <<format>> | <<config>> |
| Alerts | <<tool/none>> | <<rules>> | <<config>> |

### Runbooks

| Operation | Documentation | Evidence |
|-----------|---------------|----------|
| <<deployment>> | <<location>> | <<file>> |
| <<rollback>> | <<location>> | <<file>> |
```

---

### Section 16: Security & Compliance

```markdown
## 16. Security & Compliance (Current)

### Security Implementation

| Aspect | Implementation | Evidence |
|--------|----------------|----------|
| Authentication | <<method>> | <<file:line>> |
| Authorization | <<method>> | <<file:line>> |
| Encryption | <<method>> | <<file:line>> |
| Input Validation | <<method>> | <<file:line>> |

### Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| <<GDPR/SOX>> | <<compliant/gap>> | <<audit log>> |
```

---

## Writing Instructions

**Step 1**: Read existing file
**Step 2**: Append Sections 9-16
**Step 3**: Display progress

```text
[ok] Part 2/3 complete: Sections 9-16 appended
  - Components documented: [COUNT]
  - Data tables documented: [COUNT]
  - Tech stack items: [COUNT]
  - Lines generated: [COUNT]

```

---

## Verification Gate

- [ ] Sections 9-16 appended
- [ ] Tech stack complete
- [ ] Schema documentation present
- [ ] Security section complete
- [ ] No placeholders

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits Part 3 (Sections 17-23). **Do NOT generate artifacts until you run this command.**
