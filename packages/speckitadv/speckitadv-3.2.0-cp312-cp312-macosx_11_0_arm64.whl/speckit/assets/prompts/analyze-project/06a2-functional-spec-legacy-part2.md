---
stage: functional_spec_legacy_part2
requires: functional_spec_legacy_part1_complete
condition: state.analysis_scope == "A"
outputs: functional_spec_legacy_part2_complete
version: 3.5.0
---

# Stage 6A-2: Functional Specification - Legacy System (Part 2)

## Purpose

Generate **Sections 9-17** of the functional specification documenting WHAT the LEGACY/EXISTING system CURRENTLY does.

**This is Part 2 of 3** for the legacy functional specification.

| Part | Sections | Focus |
|------|----------|-------|
| Part 1 | 1-8 | Foundation + Use Cases + Business Logic |
| **Part 2 (this)** | 9-17 | Requirements + Data + Integration |
| Part 3 | 18-24 | Quirks + Risks + Checklists |

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

1. Verify `{reports_dir}/functional-spec-legacy.md` exists with Sections 1-8

**IF Part 1 not complete:** STOP - Run `speckitadv analyze-project` to complete Part 1 first.

---

## Source of Truth

**Extract ALL content from these sources:**

- `{reports_dir}/analysis-report.md` Phase 2-3 (Features, Patterns)
- `{data_dir}/category-patterns.json` (code patterns)
- `{data_dir}/deep-dive-patterns.json` (detailed analysis)
- `{data_dir}/config-analysis.json` (configuration)

**Output File:** `{reports_dir}/functional-spec-legacy.md` (append to existing)

---

## Content Rules

**EXTRACTION FOCUS** (Legacy = document what EXISTS):

- Extract from **actual code**, not imagination
- Every finding must include **Evidence** (file:line references)
- Document existing behaviors exactly as implemented
- NO forward-looking statements or recommendations

---

## Sections to Generate (Part 2)

Append these sections to `{reports_dir}/functional-spec-legacy.md`:

### Section 9: Scope / Out-of-Scope

```markdown
## 9. Scope / Out-of-Scope

### In Scope (Features Found in Legacy Code)

| Feature/Capability | Evidence (file:line) | Criticality |
|--------------------|----------------------|-------------|
| <<Feature 1>> | <<path/to/file:123>> | CRITICAL |
| <<Feature 2>> | <<path/to/file:456>> | STANDARD |
| <<Feature 3>> | <<path/to/file:789>> | STANDARD |

### Out of Scope (Not Found in Legacy Code)

| Capability | Rationale |
|------------|-----------|
| <<Feature X>> | No evidence in codebase; may be external/deprecated |
| <<Feature Y>> | Only mentioned in comments, no implementation |
```

---

### Section 10: Functional Requirements

```markdown
## 10. Functional Requirements (Extracted from Legacy Code)

### CRITICAL Features (Must Preserve Exactly)

#### FR-CRIT-001: <<Feature Name>>

- **As a** <<persona>>, **the system provides** <<capability>>,
  **so that** <<business value>>.
- **Evidence**: <<controller/service/file:line-range>>
- **Current Implementation**:
  - <<Key code logic summary>>
  - <<Important config/constants>>
- **Related Use Case**: UC-<<id>>
- **Related User Story**: US-CRIT-<<id>>
- **Business Logic**: BL-<<id>>
- **Acceptance Criteria** (derived from code/tests):
  - AC-1: <<Measurable condition>>
  - AC-2: <<Second condition>>
- **CRITICAL**: This behavior MUST be preserved exactly.

---

### STANDARD Features (Can Modernize Implementation)

#### FR-STD-001: <<Feature Name>>

- **As a** <<persona>>, **the system provides** <<capability>>, **so that** <<value>>.
- **Evidence**: <<file:line>>
- **Current Implementation**: <<Summary>>
- **Related Use Case**: UC-<<id>>
- **Modernization Opportunity**: <<How this could be improved>>
- **Acceptance Criteria**:
  - AC-1: <<Condition>>

---

### LEGACY QUIRKS (Decide: Preserve or Fix)

#### FR-QUIRK-001: <<Quirk Name>>

- **Current Behavior**: <<Description of unexpected behavior>>
- **Evidence**: <<file:line>>
- **Issue**: <<Why this is a quirk>>
- **Decision Needed**:
  - **Option A**: Preserve (for backward compatibility)
  - **Option B**: Fix/modernize (with migration plan)
- **Impact Analysis**: <<What breaks if changed>>
```

---

### Section 11: Non-Negotiables

```markdown
## 11. Non-Negotiables (Extracted from Code Analysis)

These constraints are derived from code evidence and must be preserved:

1. **<<Non-Negotiable 1>>**
   - **Rationale**: <<Why mandatory>>
   - **Evidence**: <<file:line>>
   - **Example**: <<Actual code snippet or config value>>

2. **<<Non-Negotiable 2>>** (e.g., PII Encryption)
   - **Rationale**: All PII must be encrypted at rest
   - **Evidence**: <<encryption-middleware.js:45-78>>
   - **Example**: Uses AES-256-CBC with custom key derivation

3. **<<Non-Negotiable 3>>** (e.g., Audit Logging)
   - **Rationale**: Regulatory compliance (GDPR, SOX)
   - **Evidence**: <<audit-logger.js:12-34>>
```

---

### Section 12: Non-Functional Requirements

```markdown
## 12. Non-Functional Requirements (Legacy System)

### Performance (Extracted from Config/Code)

| Metric | Current Target | Evidence | Notes |
|--------|----------------|----------|-------|
| Response time | p95 < <<X>>ms | <<config.js:23>> | Hardcoded timeout |
| Throughput | <<Y>> req/min | <<rate-limiter.js:45>> | Per-user limit |
| Batch size | <<Z>> records | <<batch-processor.js:67>> | Max batch |

### Availability & Reliability

| Metric | Current Implementation | Evidence |
|--------|------------------------|----------|
| Uptime | <<SLA/config>> | <<deploy/config.yaml:12>> |
| Retry logic | <<3 attempts, exp backoff>> | <<http-client.js:89-102>> |
| Circuit breaker | <<Threshold: 5 failures>> | <<circuit-breaker.js:34>> |

### Security (Current Implementation)

| Aspect | Implementation | Evidence |
|--------|----------------|----------|
| Authentication | <<Session-based, 30min timeout>> | <<auth/session.js:45>> |
| Authorization | <<Role-based (admin/user/guest)>> | <<auth/rbac.js:23-67>> |
| Encryption | <<AES-256-CBC for PII>> | <<crypto/encrypt.js:12>> |
| Input validation | <<Schema-based (Joi)>> | <<validators/input.js:34>> |

### Accessibility, Privacy, Localization

| Aspect | Current State | Evidence |
|--------|---------------|----------|
| A11y | <<WCAG level/none>> | <<frontend analysis>> |
| Privacy | <<PII masking in logs>> | <<logger.js:56>> |
| I18n | <<EN only / multi-lang>> | <<i18n/locales/>> |
```

---

### Section 13: Error Handling & Recovery

```markdown
## 13. Error Handling & Recovery

### 13.1 Exception Handling Patterns

| Exception Type | Handling Strategy | Retry Logic | Fallback Action | Evidence |
|----------------|-------------------|-------------|-----------------|----------|
| <<ExceptionClass>> | <<Log/Rethrow/Handle>> | <<retry count>> | <<alternative>> | <<file:line>> |

### 13.2 Error Recovery Algorithms

ALGORITHM: HandleError[<<ErrorType>>]
INPUT: <<error object, context>>
OUTPUT: <<recovery result or escalation>>

STEP 1: Error Classification
  <<Determine error severity and type>>

STEP 2: Retry Strategy
  IF <<retriable error>>:
    FOR attempt = 1 to <<max_retries>>:
      <<Wait with exponential backoff>>
      <<Retry operation>>

STEP 3: Fallback Mechanism
  IF <<retry failed>>:
    <<Execute fallback logic>>

STEP 4: Escalation
  IF <<critical error>>:
    <<Notify monitoring system>>

### 13.3 Validation Error Handling

| Validation Failure | Error Code | Error Message | User Action | Evidence |
|--------------------|------------|---------------|-------------|----------|
| <<type>> | <<code>> | <<message>> | <<action>> | <<file:line>> |

### 13.4 Error Codes Catalog

| Error Code | Category | Description | Severity | Recovery |
|------------|----------|-------------|----------|----------|
| <<ERR_001>> | <<category>> | <<description>> | <<level>> | <<auto/manual>> |
```

---

### Section 14: Data Models

```markdown
## 14. Data Models (Extracted from DB Schemas)

### Core Entities

#### Entity: <<EntityName>> (e.g., User)

**Evidence**: <<migrations/001_create_users.sql>> or <<models/User.js>>

| Field | Type | Constraints | PII | Notes |
|-------|------|-------------|-----|-------|
| id | UUID | PRIMARY KEY | No | Auto-generated |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Yes | Encrypted |
| password_hash | VARCHAR(255) | NOT NULL | Yes | bcrypt |
| role | ENUM | admin/user/guest | No | Default: user |
| created_at | TIMESTAMP | NOT NULL | No | Auto |

**Relationships**:
- Has many: <<RelatedEntity>> (<<foreign_key_field>>)
- Belongs to: <<ParentEntity>> (<<foreign_key_field>>)

---

### 14.2 Field Mappings

| Source Field | Source Type | Target Field | Target Type | Transformation | Evidence |
|--------------|-------------|--------------|-------------|----------------|----------|
| <<input>> | <<type>> | <<output>> | <<type>> | <<logic>> | <<file:line>> |

### 14.3 Data Validation Rules

| Entity | Field | Validation Type | Rule | Error Message | Evidence |
|--------|-------|-----------------|------|---------------|----------|
| <<Entity>> | <<field>> | <<type>> | <<constraint>> | <<message>> | <<file:line>> |
```

---

### Section 15: Configuration Mapping

```markdown
## 15. Configuration Mapping (All Config Files)

| Config File | Purpose | Key Settings | Migration Strategy |
|-------------|---------|--------------|-------------------|
| `.env.example` | Env var template | DB_URL, API_KEY | Keep, update keys |
| `config/app.js` | App settings | PORT, LOG_LEVEL | Migrate to env vars |
| `config/database.yml` | DB connection | host, port, credentials | Use connection string |
| `logging.conf` | Log settings | Format, level, output | Structured logging |

**Evidence**: Analysis of <<N>> config files
```

---

### Section 16: API Contracts

```markdown
## 16. API Contracts (Extracted from Code)

### REST Endpoints

| Method | Path | Purpose | Auth Required | Request | Response | Evidence |
|--------|------|---------|---------------|---------|----------|----------|
| GET | `/api/users` | List users | Yes (admin) | Query params | User[] | <<routes/users.js:23>> |
| POST | `/api/users` | Create user | Yes (admin) | UserInput | User | <<routes/users.js:45>> |
| GET | `/api/users/:id` | Get user | Yes | - | User | <<routes/users.js:67>> |
| PUT | `/api/users/:id` | Update user | Yes (self/admin) | UserInput | User | <<routes/users.js:89>> |
| DELETE | `/api/users/:id` | Delete user | Yes (admin) | - | 204 | <<routes/users.js:112>> |

### Request/Response Schemas

<<Paste actual schemas found in code>>
```

---

### Section 17: Integration Points

```markdown
## 17. Integration Points (External Systems)

| External System | Purpose | Protocol | Auth Method | Evidence |
|-----------------|---------|----------|-------------|----------|
| <<Payment Gateway>> | Process payments | REST API | API Key | <<services/payment.js:34>> |
| <<Email Service>> | Send notifications | SMTP | Username/Password | <<services/email.js:56>> |
| <<Analytics>> | Track events | HTTP POST | Bearer token | <<services/analytics.js:78>> |

### 17.1 Message Formats

| Message Type | Format | Schema | Routing Key | Exchange/Topic | Evidence |
|--------------|--------|--------|-------------|----------------|----------|
| <<type>> | <<JSON/XML>> | <<schema>> | <<key>> | <<exchange>> | <<file:line>> |

### Database Operations

| Operation | Query Type | Tables | Indexes Used | Performance Notes | Evidence |
|-----------|------------|--------|--------------|-------------------|----------|
| <<operation>> | <<SELECT/INSERT>> | <<tables>> | <<indexes>> | <<notes>> | <<file:line>> |
```

---

## Writing Instructions

**Step 1**: Read existing file

- Read `{reports_dir}/functional-spec-legacy.md`
- Confirm Sections 1-8 exist

**Step 2**: Append to file using Edit tool

- Append Sections 9-17 to the existing file

**Step 3**: Display progress

```text
[ok] Part 2/3 complete: Sections 9-17 appended
  - Functional requirements: [COUNT]
  - Non-negotiables: [COUNT]
  - Data entities: [COUNT]
  - API endpoints: [COUNT]
  - Integration points: [COUNT]
  - Lines generated: [COUNT]

```

---

## Verification Gate

Before proceeding, verify:

- [ ] Sections 9-17 all appended to file
- [ ] Functional requirements have evidence
- [ ] Data models have field definitions
- [ ] API contracts have request/response
- [ ] Integration points have auth methods
- [ ] No placeholders (TODO, TBD, etc.)

**IF verification fails**: Fix missing content before proceeding.

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits Part 3 (Sections 18-24). **Do NOT generate artifacts until you run this command.**
