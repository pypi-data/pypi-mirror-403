---
stage: functional_spec_target_part2
requires: functional_spec_target_part1_complete
condition: state.analysis_scope == "A"
outputs: functional_spec_target_part2_complete
version: 3.5.0
---

# Stage 6B-2: Functional Specification - Target System (Part 2)

## Purpose

Generate **Sections 9-17** of the functional specification documenting WHAT the MODERNIZED system WILL do.

**This is Part 2 of 3** for the target functional specification.

| Part | Sections | Focus |
|------|----------|-------|
| Part 1 | 1-8 | Foundation + Use Cases + Business Logic |
| **Part 2 (this)** | 9-17 | Requirements + Data + Integration |
| Part 3 | 18-24 | Modernization Decisions + Checklists |

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

# Recall relevant modules for sections 9-17 (Requirements, Data, Integration)
# Use ACTUAL paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/data")  # if exists in stats
recall_understanding(target="{project_path}/api")   # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check

1. Verify `{reports_dir}/functional-spec-target.md` exists with Sections 1-8

**IF Part 1 not complete:** STOP - Complete Part 1 first.

---

## Source of Truth

**Primary Sources:**

- `{reports_dir}/functional-spec-legacy.md` Sections 9-17 (base content)
- `{reports_dir}/functional-spec-target.md` Sections 1-8 (for consistency)
- `{data_dir}/validation-scoring.json` (user preferences Q1-Q10)

**Output File:** `{reports_dir}/functional-spec-target.md` (append to existing)

---

## Sections to Generate (Part 2)

Append these sections to `{reports_dir}/functional-spec-target.md`:

### Section 9: Scope / Out-of-Scope

```markdown
## 9. Scope / Out-of-Scope (Target System)

### In Scope (Target Features)

| Feature/Capability | Legacy Status | Target Status | Migration |
|--------------------|---------------|---------------|-----------|
| <<Feature 1>> | Existing | PRESERVE | As-is |
| <<Feature 2>> | Existing | ENHANCE | Add <<improvement>> |
| <<Feature 3>> | NEW | NEW | Implement for <<reason>> |

### Out of Scope (Target System)

| Capability | Legacy Status | Reason for Exclusion |
|------------|---------------|---------------------|
| <<Feature X>> | Deprecated | No longer needed |
| <<Feature Y>> | Quirk | Being removed (see Section 18) |
```

---

### Section 10: Functional Requirements

```markdown
## 10. Functional Requirements (Target System)

### CRITICAL Features (Preserved from Legacy)

#### FR-CRIT-001: <<Feature Name>>

**Legacy Reference**: FR-CRIT-001 (functional-spec-legacy.md)
**Preservation Status**: EXACT | MODERNIZED

- **As a** <<persona>>, **the system provides** <<capability>>,
  **so that** <<business value>>.
- **Target Implementation**:
  - Language: Q1 ({answer})
  - Database: Q2 ({answer})
- **Changes from Legacy**:
  - <<Change 1>>
  - <<Change 2>>
- **Acceptance Criteria (Target)**:
  - AC-1: <<Measurable condition>>
  - AC-2: <<Second condition>>

---

### STANDARD Features (Modernized)

#### FR-STD-001: <<Feature Name>>

**Legacy Reference**: FR-STD-001
**Modernization**: <<What's improved>>

- **As a** <<persona>>, **the system provides** <<capability>>, **so that** <<value>>.
- **Target Implementation**: <<Summary with Q1-Q10 preferences>>
- **Acceptance Criteria (Target)**:
  - AC-1: <<Condition>>

---

### NEW Features (Target Only)

#### FR-NEW-001: <<New Feature Name>>

**Status**: NEW (no legacy equivalent)
**Rationale**: <<Why needed in target system>>
**Related User Preference**: Q<<N>>

- **As a** <<persona>>, **the system provides** <<capability>>, **so that** <<value>>.
- **Acceptance Criteria**:
  - AC-1: <<Condition>>
```

---

### Section 11: Non-Negotiables

```markdown
## 11. Non-Negotiables (Target System)

These constraints from legacy MUST be preserved:

1. **<<Non-Negotiable 1>>** (from legacy Section 11)
   - **Legacy Implementation**: <<how it was done>>
   - **Target Implementation**: <<how it will be done>>
   - **Verification**: <<how to confirm preservation>>

2. **<<Non-Negotiable 2>>** (e.g., PII Encryption)
   - **Legacy**: AES-256-CBC
   - **Target**: AES-256-GCM (upgraded, backward compatible)
   - **Migration**: <<encryption key migration plan>>

3. **<<Non-Negotiable 3>>** (e.g., Audit Logging)
   - **Legacy**: Custom audit table
   - **Target**: Structured logging to Q8 ({answer}) stack
   - **Data Migration**: <<how to preserve audit history>>
```

---

### Section 12: Non-Functional Requirements

```markdown
## 12. Non-Functional Requirements (Target System)

### Performance (Target)

Based on Q5 ({deployment}), Q7 ({container}):

| Metric | Legacy | Target | Improvement |
|--------|--------|--------|-------------|
| Response time | <<legacy>> | p95 < <<target>>ms | <<X%>> better |
| Throughput | <<legacy>> | <<target>> req/min | <<X%>> better |
| Batch size | <<legacy>> | <<target>> records | <<X%>> better |

### Availability & Reliability (Target)

| Metric | Legacy | Target | Implementation |
|--------|--------|--------|----------------|
| Uptime | <<legacy>> | <<target>>% | Using Q5: {answer} |
| Retry logic | <<legacy>> | <<target>> | Improved backoff |
| Circuit breaker | <<legacy>> | <<target>> | Modern patterns |

### Security (Target)

Based on Q9 ({security}):

| Aspect | Legacy | Target | Migration |
|--------|--------|--------|-----------|
| Authentication | <<legacy>> | Q9: {answer} | <<migration plan>> |
| Authorization | <<legacy>> | <<target>> | <<migration plan>> |
| Encryption | <<legacy>> | <<target>> | <<migration plan>> |

### Observability (Target)

Based on Q8 ({observability}):

| Aspect | Legacy | Target | Implementation |
|--------|--------|--------|----------------|
| Metrics | <<legacy>> | Q8: {answer} | <<details>> |
| Logging | <<legacy>> | Structured | <<format>> |
| Tracing | <<legacy or none>> | <<target>> | <<implementation>> |
```

---

### Section 13: Error Handling & Recovery

```markdown
## 13. Error Handling & Recovery (Target System)

### 13.1 Exception Handling Strategy (Target)

Based on Q1 ({language}) idioms:

| Exception Type | Legacy Handling | Target Handling | Rationale |
|----------------|-----------------|-----------------|-----------|
| <<type>> | <<legacy>> | <<target>> | <<why changed>> |

### 13.2 Error Recovery (Target)

**Target Pattern**: <<Modern error handling pattern for Q1 language>>

- Retry with exponential backoff
- Circuit breaker (threshold: <<N>>)
- Fallback strategies
- Graceful degradation

### 13.3 Error Codes (Target)

| Error Code | Legacy | Target | Migration |
|------------|--------|--------|-----------|
| <<ERR_001>> | <<legacy>> | <<target>> | <<backward compatible?>> |
```

---

### Section 14: Data Models

```markdown
## 14. Data Models (Target System)

Based on Q2 ({database}):

### Core Entities (Target)

#### Entity: <<EntityName>>

**Legacy Reference**: Section 14 (functional-spec-legacy.md)
**Migration Status**: EXACT | MODIFIED

| Field | Legacy Type | Target Type | Migration |
|-------|-------------|-------------|-----------|
| id | UUID | UUID | As-is |
| email | VARCHAR(255) | VARCHAR(255) | As-is |
| <<new_field>> | N/A | <<type>> | NEW |

**Schema Changes**:
- <<Change 1>>
- <<Change 2>>

**Migration Plan**:
1. <<Migration step 1>>
2. <<Migration step 2>>

---

### 14.2 Field Mappings (Legacy -> Target)

| Legacy Field | Legacy Type | Target Field | Target Type | Transformation |
|--------------|-------------|--------------|-------------|----------------|
| <<field>> | <<type>> | <<field>> | <<type>> | <<conversion>> |

### 14.3 Data Validation Rules (Target)

| Entity | Field | Legacy Rule | Target Rule | Change |
|--------|-------|-------------|-------------|--------|
| <<Entity>> | <<field>> | <<legacy>> | <<target>> | <<change>> |
```

---

### Section 15: Configuration Mapping

```markdown
## 15. Configuration Mapping (Target System)

Based on Q5 ({deployment}), Q6 ({iac}):

| Legacy Config | Target Config | Migration Strategy |
|---------------|---------------|-------------------|
| `.env.example` | Environment secrets | Use <<secret manager>> |
| `config/app.js` | `config/app.yaml` | Convert to YAML |
| `config/database.yml` | Connection string | Use environment variable |

### Target Configuration Structure

| Config Key | Source | Default | Override |
|------------|--------|---------|----------|
| <<key>> | Environment | <<default>> | <<profile>> |
```

---

### Section 16: API Contracts

```markdown
## 16. API Contracts (Target System)

### REST Endpoints (Target)

| Method | Legacy Path | Target Path | Changes |
|--------|-------------|-------------|---------|
| GET | `/api/users` | `/api/v2/users` | Versioned, pagination |
| POST | `/api/users` | `/api/v2/users` | Validation improved |

### API Versioning Strategy

- **Legacy**: Unversioned
- **Target**: `/api/v2/*`
- **Migration**: Support both during transition

### Request/Response Schemas (Target)

<<Target API schemas with modern patterns>>
```

---

### Section 17: Integration Points

```markdown
## 17. Integration Points (Target System)

Based on Q3 ({message_bus}):

| External System | Legacy Protocol | Target Protocol | Migration |
|-----------------|-----------------|-----------------|-----------|
| <<Payment>> | REST API | REST API | Update SDK |
| <<Email>> | SMTP | Q3: {answer} | Async messaging |
| <<Analytics>> | HTTP POST | Q3: {answer} | Event streaming |

### 17.1 Message Formats (Target)

| Message Type | Legacy Format | Target Format | Migration |
|--------------|---------------|---------------|-----------|
| <<type>> | JSON | JSON | Schema evolution |

### Target Integration Architecture

{Mermaid diagram showing target integration patterns}
```

---

## Writing Instructions

**Step 1**: Read legacy spec Sections 9-17

- Read `{reports_dir}/functional-spec-legacy.md` Sections 9-17
- Extract content to transform for target

**Step 2**: Append to file using Edit tool

- Append Sections 9-17 to `{reports_dir}/functional-spec-target.md`

**Step 3**: Display progress

```text
[ok] Part 2/3 complete: Sections 9-17 appended
  - Requirements mapped: [COUNT]
  - Data entities mapped: [COUNT]
  - API endpoints mapped: [COUNT]
  - Integration points mapped: [COUNT]
  - Lines generated: [COUNT]

```

---

## Verification Gate

Before proceeding, verify:

- [ ] Sections 9-17 all appended
- [ ] Legacy -> Target mapping for all requirements
- [ ] User preferences (Q1-Q10) applied
- [ ] Data migration plans documented
- [ ] API versioning strategy defined
- [ ] No placeholders (TODO, TBD, etc.)

**IF verification fails**: Fix missing content before proceeding.

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits Part 3 (Sections 18-24). **Do NOT generate artifacts until you run this command.**
