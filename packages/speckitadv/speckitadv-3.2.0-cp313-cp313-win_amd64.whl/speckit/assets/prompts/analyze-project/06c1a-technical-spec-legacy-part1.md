---
stage: technical_spec_legacy_part1
requires: functional_spec_target_complete
condition: state.analysis_scope == "A"
outputs: technical_spec_legacy_part1_complete
version: 3.5.0
---

# Stage 6C1-1: Technical Specification - Legacy System (Part 1)

## Purpose

Generate **Sections 1-8** of the technical specification documenting HOW the LEGACY/EXISTING system is BUILT.

**This is Part 1 of 3** for the legacy technical specification.

| Part | Sections | Focus |
|------|----------|-------|
| **Part 1 (this)** | 1-8 | Architecture + Diagrams |
| Part 2 | 9-16 | Components + Data + Tech Stack |
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

1. Verify both functional specs complete:
   - `{reports_dir}/functional-spec-legacy.md`
   - `{reports_dir}/functional-spec-target.md`

**IF not complete:** STOP - Complete functional specs first.

---

## Source of Truth

**Extract from these sources:**

- `{reports_dir}/analysis-report.md` (all phases)
- `{data_dir}/category-patterns.json` (code patterns)
- `{data_dir}/deep-dive-patterns.json` (detailed analysis)
- `{data_dir}/config-analysis.json` (configuration)
- Both functional specs for context

**Output File:** `{reports_dir}/technical-spec-legacy.md`

---

## Content Rules

**EXTRACTION FOCUS** (Legacy = document HOW it's BUILT):

- Extract from **actual code**, architecture patterns
- Every diagram must reflect actual code structure
- Include file:line references for key patterns
- Focus on HOW (implementation), not WHAT (business logic)

---

## Sections to Generate (Part 1)

### Section 1: Architectural Principles

```markdown
# Technical Specification - Legacy System

**Project**: {project_name}
**Analysis Date**: {date}
**Status**: Legacy Architecture Documentation

---

## 1. Architectural Principles

### Current Architecture Style

**Pattern**: <<Monolith / Microservices / Modular Monolith / Layered>>
**Evidence**: <<file structure analysis>>

### Observed Principles

| Principle | Implementation | Evidence |
|-----------|----------------|----------|
| Separation of Concerns | <<how layers are separated>> | <<folder structure>> |
| Dependency Direction | <<inward/outward>> | <<import analysis>> |
| Error Handling | <<centralized/distributed>> | <<file:line>> |
```

---

### Section 2: C4 Architecture Views

```markdown
## 2. C4 Architecture Views

### 2.1 System Context (C4 Level 1)

{Mermaid C4Context diagram showing system and external actors}

### 2.2 Container View (C4 Level 2)

{Mermaid C4Container diagram showing containers/services}

### 2.3 Component View (C4 Level 3)

{Mermaid C4Component diagram for key containers}

**Evidence**: Extracted from folder structure and dependencies
```

---

### Section 3: Component Dependency Diagram

```markdown
## 3. Component Dependency Diagram

{Mermaid graph showing component dependencies}

### Dependency Analysis

| Component | Depends On | Depended By | Coupling |
|-----------|------------|-------------|----------|
| <<component>> | <<list>> | <<list>> | High/Medium/Low |

**Evidence**: Import analysis across codebase
```

---

### Section 4: Sequence Diagrams

```markdown
## 4. Sequence Diagrams

### 4.1 <<Key Flow 1>>

{Mermaid sequence diagram for critical flow}

**Evidence**: <<file:line>> for each interaction

### 4.2 <<Key Flow 2>>

{Mermaid sequence diagram}

**Evidence**: <<file:line>>
```

---

### Section 5: Deployment Architecture

```markdown
## 5. Deployment Architecture

### Current Deployment Model

**Platform**: <<On-prem / Cloud / Hybrid>>
**Evidence**: <<deployment configs, Dockerfiles>>

{Mermaid deployment diagram}

### Infrastructure Components

| Component | Technology | Purpose | Evidence |
|-----------|------------|---------|----------|
| <<Web Server>> | <<Nginx/Apache>> | <<purpose>> | <<config file>> |
| <<App Server>> | <<Node/Java/etc>> | <<purpose>> | <<config file>> |
| <<Database>> | <<PostgreSQL/MySQL>> | <<purpose>> | <<config file>> |
```

---

### Section 6: Data Flow Diagrams

```markdown
## 6. Data Flow Diagrams

### 6.1 Request/Response Flow

{Mermaid flowchart showing data flow through system}

### 6.2 Data Transformation Points

| Source | Transform | Destination | Evidence |
|--------|-----------|-------------|----------|
| <<source>> | <<transformation>> | <<dest>> | <<file:line>> |

**Evidence**: Traced from controllers through services to data layer
```

---

### Section 7: Resilience Patterns

```markdown
## 7. Resilience Patterns

### Current Patterns

| Pattern | Implementation | Evidence |
|---------|----------------|----------|
| Retry | <<implementation>> | <<file:line>> |
| Circuit Breaker | <<if any>> | <<file:line>> |
| Timeout | <<values>> | <<config file>> |
| Fallback | <<if any>> | <<file:line>> |

### Error Handling Architecture

{Mermaid diagram showing error flow}
```

---

### Section 8: Why This Pattern

```markdown
## 8. Why This Pattern (Legacy Analysis)

### Current Architecture Rationale

Based on code analysis, the legacy architecture choices:

| Choice | Likely Reason | Evidence | Impact |
|--------|---------------|----------|--------|
| <<Monolith>> | <<reason>> | <<evidence>> | <<maintainability>> |
| <<Framework X>> | <<reason>> | <<evidence>> | <<limitations>> |
| <<Database Y>> | <<reason>> | <<evidence>> | <<scalability>> |

### Technical Debt Identified

| Area | Issue | Evidence | Severity |
|------|-------|----------|----------|
| <<area>> | <<issue>> | <<file:line>> | High/Medium/Low |
```

---

## Writing Instructions

**Step 1**: Create the file with Write tool

- File path: `{reports_dir}/technical-spec-legacy.md`
- Content: Complete Sections 1-8

**Step 2**: Display progress

```text
[ok] Part 1/3 complete: Sections 1-8 written
  - C4 diagrams generated: [COUNT]
  - Sequence diagrams: [COUNT]
  - Components documented: [COUNT]
  - Lines generated: [COUNT]

```

---

## Verification Gate

- [ ] Sections 1-8 present
- [ ] C4 diagrams at all 3 levels
- [ ] Deployment diagram included
- [ ] Data flow diagrams included
- [ ] No placeholders

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits Part 2 (Sections 9-16). **Do NOT generate artifacts until you run this command.**
