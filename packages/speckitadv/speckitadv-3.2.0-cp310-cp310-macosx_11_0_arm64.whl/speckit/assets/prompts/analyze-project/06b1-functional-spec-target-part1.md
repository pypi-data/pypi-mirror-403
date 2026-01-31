---
stage: functional_spec_target_part1
requires: functional_spec_legacy_complete
condition: state.analysis_scope == "A"
outputs: functional_spec_target_part1_complete
version: 3.5.0
---

# Stage 6B-1: Functional Specification - Target System (Part 1)

## Purpose

Generate **Sections 1-8** of the functional specification documenting WHAT the MODERNIZED system WILL do.

**This is Part 1 of 3** for the target functional specification.

| Part | Sections | Focus |
|------|----------|-------|
| **Part 1 (this)** | 1-8 | Foundation + Use Cases + Business Logic |
| Part 2 | 9-17 | Requirements + Data + Integration |
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

# Recall all modules for comprehensive target spec
# Use ACTUAL paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/auth")      # if exists in stats
recall_understanding(target="{project_path}/api")       # if exists in stats
recall_understanding(target="{project_path}/data")      # if exists in stats
recall_understanding(target="{project_path}/services")  # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check

1. Verify `{reports_dir}/functional-spec-legacy.md` exists (all 24 sections)

**IF legacy spec not complete:** STOP - Complete functional-spec-legacy first.

---

## Source of Truth

**Primary Sources:**

- `{reports_dir}/functional-spec-legacy.md` (base for all content)
- `{reports_dir}/analysis-report.md` Phase 5-6 (modernization targets)
- `{data_dir}/validation-scoring.json` (user preferences Q1-Q10)

**Output File:** `{reports_dir}/functional-spec-target.md`

---

## Content Rules

**DESIGN FOCUS** (Target = document what WILL BE BUILT):

- Base ALL content on the legacy spec
- Apply user preferences (Q1-Q10) for modernization decisions
- Show Legacy -> Target mapping for each item
- Mark each user story: EXACT | ENHANCED | REPLACED
- Focus on WHAT (business functionality), not HOW (implementation)

**MANDATORY Mapping:**

- Every legacy use case must map to a target use case
- Every legacy business rule must have preservation status
- Every legacy quirk must be categorized: PRESERVE | FIX | REMOVE

---

## User Preferences Reference

Apply these preferences from `{data_dir}/validation-scoring.json`:

| Q# | Topic | User's Choice | Impact |
|----|-------|---------------|--------|
| Q1 | Target Language | {answer} | All code references |
| Q2 | Target Database | {answer} | Data models, migrations |
| Q3 | Message Bus | {answer} | Async patterns |
| Q4 | Package Manager | {answer} | Dependencies |
| Q5 | Deployment | {answer} | Infrastructure |
| Q6 | IaC Tool | {answer} | DevOps |
| Q7 | Container | {answer} | Runtime |
| Q8 | Observability | {answer} | Monitoring |
| Q9 | Security | {answer} | Auth/authz |
| Q10 | Testing | {answer} | Test strategy |

---

## Sections to Generate (Part 1)

Generate these sections in `{reports_dir}/functional-spec-target.md`:

### Section 1: Executive Summary

```markdown
# Functional Specification - Target System

**Project**: {project_name}
**Analysis Date**: {date}
**Status**: Target System Design
**Based On**: functional-spec-legacy.md

---

## 1. Executive Summary

**WHAT**: <<1-2 sentences describing what the TARGET system will do>>

**WHO**: <<Primary user types (same as legacy unless expanding)>>

**WHY**: <<Business purpose + modernization goals>>

**MODERNIZATION GOALS**:

1. <<Goal 1 from user preferences>>
2. <<Goal 2>>
3. <<Goal 3>>

**KEY CHANGES FROM LEGACY**:

| Aspect | Legacy | Target | Rationale |
|--------|--------|--------|-----------|
| Language | <<legacy>> | Q1: <<target>> | <<why>> |
| Database | <<legacy>> | Q2: <<target>> | <<why>> |
| Deployment | <<legacy>> | Q5: <<target>> | <<why>> |
```

---

### Section 2: Current State - Problem & Goals

```markdown
## 2. Current State - Problem & Goals

### Modernization Objectives

Based on user preferences and legacy analysis:

- <<Objective 1>> (Addresses legacy issue: <<reference>>)
- <<Objective 2>> (User preference: Q<<N>>)
- <<Objective 3>> (Technical improvement: <<reason>>)

### Target KPIs/Metrics

| Metric | Legacy Value | Target Value | Improvement |
|--------|--------------|--------------|-------------|
| Response time | <<legacy>> | <<target>> | <<% better>> |
| Throughput | <<legacy>> | <<target>> | <<% better>> |
| Availability | <<legacy>> | <<target>> | <<improvement>> |
```

---

### Section 3: Personas & User Journeys

```markdown
## 3. Personas & User Journeys

### Personas (Target System)

| Persona | Legacy Capabilities | Target Capabilities | Changes |
|---------|---------------------|---------------------|---------|
| <<Admin>> | <<from legacy spec>> | <<target>> | <<new/enhanced>> |
| <<User>> | <<from legacy spec>> | <<target>> | <<new/enhanced>> |

### Target User Journeys

{Mermaid journey diagram showing TARGET user workflows}

**Changes from Legacy**:
- Journey 1: <<what's different>>
- Journey 2: <<what's different>>
```

---

### Section 4: Use Cases

```markdown
## 4. Use Cases (Target System)

### UC-001: <<Use Case Name>>

| Attribute | Legacy | Target | Status |
|-----------|--------|--------|--------|
| **ID** | UC-001 | UC-001 | EXACT / ENHANCED |
| **Name** | <<legacy name>> | <<target name>> | |
| **Actor(s)** | <<legacy>> | <<target>> | |
| **Priority** | <<legacy>> | <<target>> | |

**Modernization Status**: EXACT | ENHANCED | NEW

**Changes from Legacy**:
- <<Change 1>>
- <<Change 2>>

**Main Flow (Target)**:
1. Actor <<action 1>>
2. System <<response 1>> (using Q<<N>> technology)
3. Actor <<action 2>>
4. System <<response 2>>

**Alternative Flows**: <<same as legacy unless changed>>

**Exception Flows**: <<same as legacy unless changed>>

---

<<Repeat for each use case, mapping from legacy>>
```

---

### Section 5: User Stories

```markdown
## 5. User Stories (Target System)

### CRITICAL Stories

#### US-CRIT-001: <<Story Title>>

**Legacy Reference**: US-CRIT-001 (functional-spec-legacy.md)
**Status**: EXACT | ENHANCED | REPLACED
**Priority**: CRITICAL
**Actor**: <<Persona>>

**Story**:
> As a **<<persona>>**,
> I want to **<<action/capability>>**,
> So that **<<business value>>**.

**Changes from Legacy**:
- <<What's different in target system>>
- <<Technology changes based on Q1-Q10>>

**Acceptance Criteria (Target)**:

Scenario: <<Scenario Name>>
  Given <<initial context/state>>
    And <<additional context>>
  When <<action performed>>
  Then <<expected outcome>>
    And <<additional verification>>

---

### STANDARD Stories

#### US-STD-001: <<Story Title>>

**Legacy Reference**: US-STD-001
**Status**: EXACT | ENHANCED | REPLACED

<<Same format as CRITICAL>>

---

### NEW Stories (Target Only)

#### US-NEW-001: <<New Story Title>>

**Status**: NEW (no legacy equivalent)
**Rationale**: <<Why this is needed in target system>>

<<Full story format>>
```

---

### Section 6: Business Logic

```markdown
## 6. Business Logic (Target System)

### 6.1 Validation Rules

#### VAL-001: <<Validation Name>>

**Legacy Reference**: VAL-001 (functional-spec-legacy.md)
**Preservation Status**: EXACT | MODERNIZED

| Field | Legacy Rule | Target Rule | Change Reason |
|-------|-------------|-------------|---------------|
| <<field>> | <<legacy>> | <<target>> | <<why changed>> |

---

### 6.2 Decision Trees

#### DT-001: <<Decision Name>>

**Legacy Reference**: DT-001
**Preservation Status**: EXACT | MODERNIZED

{Mermaid flowchart showing TARGET decision logic}

**Changes from Legacy**:
- <<What's different>>

---

### 6.3 Calculation Formulas

#### CALC-001: <<Calculation Name>>

**Legacy Reference**: CALC-001
**Preservation Status**: EXACT | MODERNIZED
**Precision**: <<decimal places, rounding rules>>

**Formula (Target)**:
```text
result = (base_amount * rate) + fixed_fee
```

**Changes from Legacy**:

- <<What's different, if any>>

---

### 6.4 Business Constants

| Constant | Legacy Value | Target Value | Change Reason |
|----------|--------------|--------------|---------------|
| <<MAX_RETRY>> | <<legacy>> | <<target>> | <<reason>> |
| <<TIMEOUT_MS>> | <<legacy>> | <<target>> | <<reason>> |

---

### 6.5 Data Transformations

#### TRANSFORM-001: <<Transformation Name>>

**Legacy Reference**: TRANSFORM-001
**Preservation Status**: EXACT | MODERNIZED

| Source Field | Target Field | Legacy Transform | Target Transform |
|--------------|--------------|------------------|------------------|
| <<input>> | <<output>> | <<legacy>> | <<target>> |

---

### Section 7: State Machines

```markdown
## 7. State Machines (Target System)

### SM-001: <<Entity>> State Machine

**Legacy Reference**: SM-001 (functional-spec-legacy.md)
**Preservation Status**: EXACT | MODERNIZED

{Mermaid stateDiagram showing TARGET states and transitions}

**Changes from Legacy**:

| Aspect | Legacy | Target | Reason |
|--------|--------|--------|--------|
| States | <<legacy states>> | <<target states>> | <<reason>> |
| Transitions | <<legacy>> | <<target>> | <<reason>> |
```

---

### Section 8: Configuration-Driven Behaviors

```markdown
## 8. Configuration-Driven Behaviors (Target System)

### Config-Driven Feature Flags

| Flag | Legacy Default | Target Default | Change Reason |
|------|----------------|----------------|---------------|
| <<FEATURE_X_ENABLED>> | <<legacy>> | <<target>> | <<reason>> |

### Config-Driven Business Rules (Target)

| Config Key | Type | Legacy | Target | Impact |
|------------|------|--------|--------|--------|
| <<key>> | <<type>> | <<legacy>> | <<target>> | <<change impact>> |

### Environment-Specific Behaviors (Target)

Based on Q5 (Deployment: {answer}) and Q7 (Container: {answer}):

| Behavior | Dev | Staging | Prod | Target Change |
|----------|-----|---------|------|---------------|
| <<behavior>> | <<target>> | <<target>> | <<target>> | <<what's new>> |
```

---

## Writing Instructions

**Step 1**: Read legacy spec first

- Read `{reports_dir}/functional-spec-legacy.md` Sections 1-8
- Extract content to transform for target

**Step 2**: Create the file with Write tool

- File path: `{reports_dir}/functional-spec-target.md`
- Content: Complete Sections 1-8 with Legacy -> Target mappings

**Step 3**: Display progress

```text
[ok] Part 1/3 complete: Sections 1-8 written
  - Use cases mapped: [COUNT] (EXACT: N, ENHANCED: N, NEW: N)
  - User stories mapped: [COUNT] (EXACT: N, ENHANCED: N, REPLACED: N)
  - Business rules preserved: [COUNT]
  - State machines mapped: [COUNT]
  - Lines generated: [COUNT]

```

---

## Verification Gate

Before proceeding, verify:

- [ ] File exists at `{reports_dir}/functional-spec-target.md`
- [ ] Sections 1-8 all present with headers
- [ ] Use cases show Legacy -> Target mapping
- [ ] User stories have EXACT/ENHANCED/REPLACED status
- [ ] Business logic shows preservation status
- [ ] User preferences (Q1-Q10) applied
- [ ] No placeholders (TODO, TBD, etc.)

**IF verification fails**: Fix missing content before proceeding.

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits Part 2 (Sections 9-17). **Do NOT generate artifacts until you run this command.**
