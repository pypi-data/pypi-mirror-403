---
stage: functional_spec_legacy_part1
requires: analyze-project-05-artifacts.json
condition: state.analysis_scope == "A"
outputs: functional_spec_legacy_part1_complete
version: 3.5.0
---

# Stage 6A-1: Functional Specification - Legacy System (Part 1)

## Purpose

Generate **Sections 1-8** of the functional specification documenting WHAT the LEGACY/EXISTING system CURRENTLY does.

**This is Part 1 of 3** for the legacy functional specification.

| Part | Sections | Focus |
|------|----------|-------|
| **Part 1 (this)** | 1-8 | Foundation + Use Cases + Business Logic |
| Part 2 | 9-17 | Requirements + Data + Integration |
| Part 3 | 18-24 | Quirks + Risks + Checklists |

---

{{include:strict-execution-mode.md}}

{{include:analyze-state-management.md}}

{{include:analyze-file-write-policy.md}}

---

## AI Context Cache: Recall Stored Understanding

**[!] CRITICAL: Before generating functional spec, recall ALL cached understanding from analysis phases.**

```text
# FIRST: Discover ALL cached entries (project, modules, files)
get_understanding_stats(limit=50)
# Review output to identify ALL cached targets and their scopes

# Recall project-level understanding
recall_understanding(target="project")

# Recall from ACTUAL cached paths shown in stats output
# Common examples - use paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/auth")      # if exists in stats
recall_understanding(target="{project_path}/api")       # if exists in stats
recall_understanding(target="{project_path}/data")      # if exists in stats
recall_understanding(target="{project_path}/services")  # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check

1. Verify `{reports_dir}/EXECUTIVE-SUMMARY.md` exists
2. Verify `{scope}` = "A" (Full Application analysis)

**IF not Scope A:** This prompt is for Full Application analysis only

---

## Source of Truth

**Extract ALL content from these sources:**

- `{reports_dir}/analysis-report.md` Phase 2 (Feature Catalog)
- `{reports_dir}/analysis-report.md` Phase 3 (Positive Findings)
- `{data_dir}/category-patterns.json` (code patterns)
- `{data_dir}/deep-dive-patterns.json` (detailed analysis)

**Output File:** `{reports_dir}/functional-spec-legacy.md`

---

## Content Rules

**EXTRACTION FOCUS** (Legacy = document what EXISTS):

- Extract from **actual code**, not imagination
- Every finding must include **Evidence** (file:line references)
- Focus on WHAT (business functionality), not HOW (implementation)
- Document existing behaviors exactly as implemented
- NO forward-looking statements or recommendations

**MANDATORY Evidence Requirements:**

- Each use case: minimum 2 file:line references
- Each user story: minimum 1 file:line reference
- Each business rule: exact file:line where implemented
- Each state machine: file:line for state definitions

---

## Sections to Generate (Part 1)

Generate these sections in `{reports_dir}/functional-spec-legacy.md`:

### Section 1: Executive Summary

```markdown
# Functional Specification - Legacy System

**Project**: {project_name}
**Analysis Date**: {date}
**Status**: Legacy System Documentation

---

## 1. Executive Summary

**WHAT**: <<1-2 sentences describing what the legacy system does>>

**WHO**: <<Primary user types/personas extracted from code>>

**WHY**: <<Business purpose derived from functionality analysis>>

**TOP 3 CAPABILITIES**:

1. <<Most important feature from code analysis>>
2. <<Second most important feature>>
3. <<Third most important feature>>

**Evidence**: Analysis of <<N>> files across <<M>> directories
```

---

### Section 2: Current State - Problem & Goals

```markdown
## 2. Current State - Problem & Goals

### Current Business Objectives

Based on analysis of the legacy codebase, the system serves these objectives:

- <<Objective 1>> (Evidence: <<file:line>>)
- <<Objective 2>> (Evidence: <<file:line>>)
- <<Objective 3>> (Evidence: <<file:line>>)

### KPIs/Metrics (Extracted from Code)

| Metric | Current Implementation | Evidence |
|--------|------------------------|----------|
| <<Metric name>> | <<How it's tracked>> | <<file:line>> |
| <<Response time>> | <<Hardcoded timeout/config>> | <<file:line>> |
| <<Throughput>> | <<Rate limit/throttle config>> | <<file:line>> |
```

---

### Section 3: Personas & User Journeys

```markdown
## 3. Personas & User Journeys

### Personas (Extracted from Code)

<<Extract from authentication, authorization, RBAC, user roles>>

| Persona | Evidence | Permissions/Capabilities |
|---------|----------|--------------------------|
| <<Admin>> | <<auth.js:45-67>> | <<Full access, user management>> |
| <<User>> | <<auth.js:89-102>> | <<Read/write own data>> |
| <<Guest>> | <<auth.js:115-120>> | <<Read-only public data>> |

### Top User Journeys (From Code Paths)

{Mermaid journey diagram showing extracted user workflows}

**Evidence**:
- Journey 1: <<controller paths, workflow files>>
- Journey 2: <<service methods, state machines>>
```

---

### Section 4: Use Cases

```markdown
## 4. Use Cases (Extracted from Code)

### UC-001: <<Use Case Name>>

| Attribute | Value |
|-----------|-------|
| **ID** | UC-001 |
| **Name** | <<Use Case Name>> |
| **Actor(s)** | <<Primary Actor>>, <<Secondary Actor>> |
| **Priority** | CRITICAL / STANDARD |
| **Evidence** | <<file:line>> |

**Preconditions**:
1. <<Precondition 1>>
2. <<Precondition 2>>

**Main Flow (Happy Path)**:
1. Actor <<action 1>>
2. System <<response 1>>
3. Actor <<action 2>>
4. System <<response 2>>
5. System <<final outcome>>

**Alternative Flows**:

| ID | Trigger | Steps | Outcome |
|----|---------|-------|---------|
| AF-1 | <<condition>> | <<steps>> | <<outcome>> |

**Exception Flows**:

| ID | Trigger | Steps | Outcome |
|----|---------|-------|---------|
| EF-1 | <<error condition>> | <<error handling>> | <<recovery>> |

**Postconditions**:
1. <<State after successful completion>>
2. <<Data changes made>>

---

<<Repeat for each use case discovered in code>>
```

**Minimum Use Cases by Project Size:**

- Small (< 5,000 LOC): 5-15 use cases
- Medium (5,000-50,000 LOC): 15-50 use cases
- Large (> 50,000 LOC): 50-150 use cases

---

### Section 5: User Stories

```markdown
## 5. User Stories (Given-When-Then Format)

### CRITICAL Stories

#### US-CRIT-001: <<Story Title>>

**Evidence**: <<file:line>>
**Priority**: CRITICAL
**Actor**: <<Persona>>

**Story**:
> As a **<<persona>>**,
> I want to **<<action/capability>>**,
> So that **<<business value>>**.

**Acceptance Criteria (Given-When-Then)**:

Scenario: <<Scenario Name>>
  Given <<initial context/state>>
    And <<additional context>>
  When <<action performed>>
  Then <<expected outcome>>
    And <<additional verification>>

---

### STANDARD Stories

#### US-STD-001: <<Story Title>>

<<Same format as CRITICAL>>

---

<<Repeat for all user stories extracted from code>>
```

**Minimum User Stories by Project Size:**

- Small: 10-30 stories
- Medium: 30-100 stories
- Large: 100-300 stories

---

### Section 6: Business Logic

```markdown
## 6. Business Logic (Algorithms, Rules & Calculations)

### 6.1 Validation Rules

#### VAL-001: <<Validation Name>>

**Evidence**: <<file:line>>
**Category**: Input / Business / Data Integrity

| Field | Rule | Error Message | Evidence |
|-------|------|---------------|----------|
| <<field>> | <<validation logic>> | <<error text>> | <<file:line>> |

---

### 6.2 Decision Trees

#### DT-001: <<Decision Name>>

**Evidence**: <<file:line>>

{Mermaid flowchart showing decision logic}

**Decision Table**:

| Condition 1 | Condition 2 | Action |
|-------------|-------------|--------|
| TRUE | TRUE | <<action>> |
| TRUE | FALSE | <<action>> |
| FALSE | * | <<action>> |

---

### 6.3 Calculation Formulas

#### CALC-001: <<Calculation Name>>

**Evidence**: <<file:line>>
**Precision**: <<decimal places, rounding rules>>

**Formula**:
```text
result = (base_amount * rate) + fixed_fee
```

**Variables**:

| Variable | Source | Type | Range |
|----------|--------|------|-------|
| base_amount | <<source>> | Decimal | 0.01 - 999999.99 |
| rate | <<config>> | Decimal | 0.00 - 1.00 |

---

### 6.4 Business Constants

| Constant | Value | Purpose | Evidence |
|----------|-------|---------|----------|
| <<MAX_RETRY>> | 3 | <<purpose>> | <<file:line>> |
| <<TIMEOUT_MS>> | 30000 | <<purpose>> | <<file:line>> |

---

### 6.5 Data Transformations

#### TRANSFORM-001: <<Transformation Name>>

**Evidence**: <<file:line>>

| Source Field | Target Field | Transformation | Null Handling |
|--------------|--------------|----------------|---------------|
| <<input>> | <<output>> | <<logic>> | <<default/error>> |

---

### Section 7: State Machines

```markdown
## 7. State Machines

### SM-001: <<Entity>> State Machine

**Evidence**: <<file:line>>

{Mermaid stateDiagram showing all states and transitions}

**States**:

| State | Description | Entry Actions | Exit Actions |
|-------|-------------|---------------|--------------|
| <<DRAFT>> | <<description>> | <<actions>> | <<actions>> |
| <<PENDING>> | <<description>> | <<actions>> | <<actions>> |
| <<APPROVED>> | <<description>> | <<actions>> | <<actions>> |

**Transitions**:

| From | To | Trigger | Guard Condition | Actions |
|------|----|---------| ----------------|---------|
| DRAFT | PENDING | submit() | isValid() | notify() |
| PENDING | APPROVED | approve() | hasPermission() | updateStatus() |

**Invalid Transitions** (explicitly blocked):

| From | To | Reason |
|------|----|--------|
| APPROVED | DRAFT | Cannot revert approved items |
```

---

### Section 8: Configuration-Driven Behaviors

```markdown
## 8. Configuration-Driven Behaviors

### Config-Driven Feature Flags

| Flag | Default | Purpose | Evidence |
|------|---------|---------|----------|
| <<FEATURE_X_ENABLED>> | false | <<purpose>> | <<file:line>> |

### Config-Driven Business Rules

| Config Key | Type | Default | Business Impact | Evidence |
|------------|------|---------|-----------------|----------|
| <<max.items.per.order>> | Integer | 100 | Limits cart size | <<file:line>> |
| <<payment.timeout.ms>> | Integer | 30000 | Payment processing timeout | <<file:line>> |

### Environment-Specific Behaviors

| Behavior | Dev | Staging | Prod | Evidence |
|----------|-----|---------|------|----------|
| <<Email sending>> | Mock | Mock | Real | <<file:line>> |
| <<Rate limiting>> | Disabled | Enabled | Enabled | <<file:line>> |
```

---

## Writing Instructions

**Step 1**: Create the file with Write tool

- File path: `{reports_dir}/functional-spec-legacy.md`
- Content: Complete Sections 1-8 as specified above

**Step 2**: Verify content

- Read the file back
- Confirm all sections present
- Confirm file:line references included

**Step 3**: Display progress

```text
[ok] Part 1/3 complete: Sections 1-8 written
  - Use cases documented: [COUNT]
  - User stories documented: [COUNT]
  - Business rules documented: [COUNT]
  - State machines documented: [COUNT]
  - Lines generated: [COUNT]

```

---

## Verification Gate

Before proceeding, verify:

- [ ] File exists at `{reports_dir}/functional-spec-legacy.md`
- [ ] Sections 1-8 all present with headers
- [ ] Use cases have file:line evidence
- [ ] User stories have Given-When-Then format
- [ ] Business logic has formulas and evidence
- [ ] State machines have transition tables
- [ ] No placeholders (TODO, TBD, etc.)

**IF verification fails**: Fix missing content before proceeding.

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits Part 2 (Sections 9-17). **Do NOT generate artifacts until you run this command.**
