---
stage: technical_spec_target_part1
requires: technical_spec_legacy_complete
condition: state.analysis_scope == "A"
outputs: technical_spec_target_part1_complete
version: 3.5.0
---

# Stage 6C2-1: Technical Specification - Target System (Part 1)

## Purpose

Generate **Sections 1-8** of the technical specification documenting HOW the MODERNIZED system will be BUILT.

**This is Part 1 of 3** for the target technical specification.

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

# Recall from ACTUAL cached paths shown in stats output (Architecture, Diagrams)
# Common examples - use paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/src")  # if exists in stats
recall_understanding(target="{project_path}/api")  # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check

1. Verify legacy technical spec complete:
   - `{reports_dir}/technical-spec-legacy.md` (all 23 sections)

**IF not complete:** STOP - Complete technical-spec-legacy first.

---

## Source of Truth

**Primary Sources:**

- `{reports_dir}/technical-spec-legacy.md` (base for all content)
- `{reports_dir}/analysis-report.md` (Phase 5-6 modernization targets)
- `{data_dir}/validation-scoring.json` (user preferences Q1-Q10)
- Both functional specs for feature reference

**Output File:** `{reports_dir}/technical-spec-target.md`

---

## Content Rules

**DESIGN FOCUS** (Target = document HOW it will be BUILT):

- Base ALL content on the legacy technical spec
- Apply user preferences (Q1-Q10) for modernization decisions
- Show Legacy -> Target mapping for architectural decisions
- Focus on HOW (implementation), reference WHAT from functional specs

**User Preferences Reference:**

| Q# | Topic | User's Choice | Impact |
|----|-------|---------------|--------|
| Q1 | Target Language | {answer} | All code/architecture |
| Q2 | Target Database | {answer} | Data layer |
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

### Section 1: Architectural Principles

```markdown
# Technical Specification - Target System

**Project**: {project_name}
**Analysis Date**: {date}
**Status**: Target Architecture Design
**Based On**: technical-spec-legacy.md

---

## 1. Architectural Principles

### Target Architecture Style

**Pattern**: <<Monolith / Microservices / Modular Monolith / Layered>>
**Rationale**: Based on Q1 ({answer}), Q5 ({answer}), Q7 ({answer})

### Legacy vs Target Principles

| Principle | Legacy | Target | Rationale |
|-----------|--------|--------|-----------|
| Separation of Concerns | <<legacy>> | <<target>> | <<why change>> |
| Dependency Direction | <<legacy>> | <<target>> | <<why change>> |
| Error Handling | <<legacy>> | <<target>> | <<why change>> |

### Modernization Goals

Based on user preferences and analysis:

1. **Performance**: <<improvement from Q1, Q2 choices>>
2. **Scalability**: <<improvement from Q5, Q7 choices>>
3. **Maintainability**: <<improvement from Q1, Q4 choices>>
```

---

### Section 2: C4 Architecture Views

```markdown
## 2. C4 Architecture Views

### 2.1 System Context (C4 Level 1) - Target

{Mermaid C4Context diagram showing TARGET system and external actors}

**Changes from Legacy**:
- <<Actor changes>>
- <<System boundary changes>>

### 2.2 Container View (C4 Level 2) - Target

{Mermaid C4Container diagram showing TARGET containers/services}

**Technology Mapping**:
| Container | Legacy Tech | Target Tech | Q# Applied |
|-----------|-------------|-------------|------------|
| <<container>> | <<legacy>> | <<target>> | Q1, Q7 |

### 2.3 Component View (C4 Level 3) - Target

{Mermaid C4Component diagram for key containers}

**Evidence**: Designed based on legacy analysis and user preferences
```

---

### Section 3: Component Dependency Diagram

```markdown
## 3. Component Dependency Diagram (Target)

{Mermaid graph showing TARGET component dependencies}

### Dependency Comparison

| Component | Legacy Deps | Target Deps | Change Reason |
|-----------|-------------|-------------|---------------|
| <<component>> | <<legacy list>> | <<target list>> | <<rationale>> |

### Coupling Analysis (Target)

| Component | Depends On | Depended By | Coupling | Legacy Coupling |
|-----------|------------|-------------|----------|-----------------|
| <<component>> | <<list>> | <<list>> | Low/Medium | <<was>> |

**Evidence**: Designed to reduce coupling identified in legacy analysis
```

---

### Section 4: Sequence Diagrams

```markdown
## 4. Sequence Diagrams (Target)

### 4.1 <<Key Flow 1>> (Target)

{Mermaid sequence diagram showing TARGET flow}

**Changes from Legacy**:
- <<Technology changes based on Q1-Q10>>
- <<Performance improvements>>

**Legacy Reference**: Section 4.1 in technical-spec-legacy.md

### 4.2 <<Key Flow 2>> (Target)

{Mermaid sequence diagram}

**Changes from Legacy**:
- <<What's different>>
```

---

### Section 5: Deployment Architecture

```markdown
## 5. Deployment Architecture (Target)

### Target Deployment Model

Based on Q5 ({answer}), Q6 ({answer}), Q7 ({answer}):

**Platform**: <<Q5 answer>>
**Container**: <<Q7 answer>>
**IaC**: <<Q6 answer>>

{Mermaid deployment diagram for TARGET}

### Infrastructure Comparison

| Component | Legacy | Target | Q# Applied |
|-----------|--------|--------|------------|
| Web Server | <<legacy>> | <<target>> | Q5 |
| App Server | <<legacy>> | <<Q1 runtime>> | Q1 |
| Database | <<legacy>> | <<Q2 answer>> | Q2 |
| Container | <<legacy/none>> | <<Q7 answer>> | Q7 |
| Orchestration | <<legacy/none>> | <<based on Q5>> | Q5 |

### Environment Strategy

| Environment | Purpose | Infrastructure | Config Source |
|-------------|---------|----------------|---------------|
| dev | Development | <<local/cloud>> | .env.development |
| staging | Pre-prod testing | <<Q5 answer>> | .env.staging |
| prod | Production | <<Q5 answer>> | .env.production |
```

---

### Section 6: Data Flow Diagrams

```markdown
## 6. Data Flow Diagrams (Target)

### 6.1 Request/Response Flow (Target)

{Mermaid flowchart showing TARGET data flow}

**Changes from Legacy**:
- Database: <<legacy>> -> <<Q2 answer>>
- Message Bus: <<legacy/none>> -> <<Q3 answer>>

### 6.2 Data Transformation Points (Target)

| Source | Transform | Destination | Legacy | Target | Change |
|--------|-----------|-------------|--------|--------|--------|
| <<source>> | <<transform>> | <<dest>> | <<legacy>> | <<target>> | <<reason>> |

### 6.3 Async Data Flow (NEW)

Based on Q3 ({answer}):

{Mermaid diagram showing async message flow}

| Pattern | Message Bus | Use Case |
|---------|-------------|----------|
| Pub/Sub | <<Q3 answer>> | <<use case>> |
| Event Sourcing | <<Q3 answer>> | <<use case>> |
```

---

### Section 7: Resilience Patterns

```markdown
## 7. Resilience Patterns (Target)

### Target Patterns

| Pattern | Legacy | Target | Implementation |
|---------|--------|--------|----------------|
| Retry | <<legacy impl>> | <<target impl>> | <<Q1 library>> |
| Circuit Breaker | <<legacy impl>> | <<target impl>> | <<Q1 library>> |
| Timeout | <<legacy values>> | <<target values>> | <<config>> |
| Fallback | <<legacy impl>> | <<target impl>> | <<strategy>> |
| Bulkhead | <<legacy/none>> | <<target impl>> | <<Q7 based>> |

### Error Handling Architecture (Target)

{Mermaid diagram showing TARGET error flow}

**Improvements from Legacy**:
- <<Improvement 1>>
- <<Improvement 2>>
```

---

### Section 8: Why This Pattern (Target Rationale)

```markdown
## 8. Why This Pattern (Target Rationale)

### Target Architecture Decisions

Based on user preferences and legacy analysis:

| Decision | Legacy | Target | Rationale | Q# |
|----------|--------|--------|-----------|-----|
| Architecture Style | <<legacy>> | <<target>> | <<why>> | Q5, Q7 |
| Primary Language | <<legacy>> | <<Q1 answer>> | <<why>> | Q1 |
| Database | <<legacy>> | <<Q2 answer>> | <<why>> | Q2 |
| Async Patterns | <<legacy>> | <<Q3 answer>> | <<why>> | Q3 |
| Container Strategy | <<legacy>> | <<Q7 answer>> | <<why>> | Q7 |

### Legacy Technical Debt Addressed

| Legacy Issue | Target Solution | Evidence |
|--------------|-----------------|----------|
| <<issue from legacy spec>> | <<target approach>> | <<how resolved>> |

### Trade-offs Accepted

| Trade-off | Benefit | Cost | Rationale |
|-----------|---------|------|-----------|
| <<trade-off>> | <<benefit>> | <<cost>> | <<why acceptable>> |
```

---

## Writing Instructions

**Step 1**: Read legacy technical spec first

- Read `{reports_dir}/technical-spec-legacy.md` Sections 1-8
- Extract architecture patterns to transform

**Step 2**: Create the file with Write tool

- File path: `{reports_dir}/technical-spec-target.md`
- Content: Complete Sections 1-8 with Legacy -> Target mappings

**Step 3**: Display progress

```text
[ok] Part 1/3 complete: Sections 1-8 written
  - C4 diagrams generated: [COUNT] (target architecture)
  - Sequence diagrams: [COUNT]
  - Components mapped: [COUNT]
  - User preferences applied: Q1, Q2, Q3, Q5, Q6, Q7
  - Lines generated: [COUNT]

```

---

## Verification Gate

- [ ] Sections 1-8 present
- [ ] C4 diagrams at all 3 levels (TARGET architecture)
- [ ] Deployment diagram with Q5, Q6, Q7 applied
- [ ] Data flow diagrams with Q2, Q3 applied
- [ ] Legacy -> Target mapping in each section
- [ ] No placeholders

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits Part 2 (Sections 9-16). **Do NOT generate artifacts until you run this command.**
