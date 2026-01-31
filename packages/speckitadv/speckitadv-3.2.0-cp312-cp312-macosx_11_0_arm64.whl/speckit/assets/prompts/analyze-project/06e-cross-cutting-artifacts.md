---
stage: 06e-cross-cutting-artifacts
requires: analyze-project-05-artifacts.json
condition: state.analysis_scope == "B"
outputs: cross_cutting_complete
version: 3.4.0
---

# Stage 6E: Cross-Cutting Concern Artifacts

## Purpose

Generate artifacts specific to Cross-Cutting Concern Migration (Scope B). This includes abstraction assessment, migration plan, and rollback procedures.

---

{{include:strict-execution-mode.md}}

## Writing Approach

The template has been copied to disk. You will:

1. Read the template file
2. Edit sections to replace `<<placeholders>>` with actual content
3. Work through sections in 3 parts (multi-part to avoid token limits)

---

## Pre-Check

1. Verify `{reports_dir}/EXECUTIVE-SUMMARY.md` exists
2. Verify `{scope}` = "B" (Cross-Cutting Concern analysis)
3. Load concern details from `{data_dir}/`

**IF not Scope B:** This prompt is for Cross-Cutting Concern analysis only

---

{{include:analyze-state-management.md}}

{{include:analyze-file-write-policy.md}}

---

## AI Context Cache: Recall Stored Understanding

```text
# FIRST: Discover ALL cached entries (project, modules, files)
get_understanding_stats(limit=50)
# Review output to identify ALL cached targets and their scopes

recall_understanding(target="project")

# Recall from ACTUAL cached paths shown in stats output
# Common examples - use paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/services")  # if exists in stats
recall_understanding(target="{project_path}/config")    # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

**[AUTO-CONTINUE]** Generate all 3 artifacts sequentially without waiting for user input between artifacts.

## Load Concern Context

From Stage 3B state, extract:

- `concern_type`: {type}
- `current_implementation`: {current}
- `target_implementation`: {target}
- `abstraction.score`: {score}
- `abstraction.level`: {HIGH | MEDIUM | LOW}
- `blast_radius`: {classification}
- `migration_strategy.selected`: {strategy}

---

## Artifact 1: Abstraction Assessment

---
**[STOP: GENERATE_ABSTRACTION_ASSESSMENT]**

**Purpose:** Detailed abstraction analysis for the concern

**Template:** Written to `{reports_dir}/abstraction-assessment.md`

{{copy-template:concern-analysis-template.md:abstraction-assessment.md}}

Read the template file and fill in each section. Generate:

```markdown
# Abstraction Assessment: {Concern Type}

## Overview

- **Concern:** {concern_type}
- **Current Implementation:** {current_implementation}
- **Target Implementation:** {target_implementation}
- **Analysis Date:** {date}
- **Chain ID:** {chain_id}

## Abstraction Analysis

### Current Abstraction Level

- **Score:** {score}/10
- **Level:** {HIGH | MEDIUM | LOW}

### Patterns Found

| Pattern | Location | Quality |
|---------|----------|---------|
| {pattern} | {file}:{line} | {good/poor} |

### Issues Found

| Issue | Impact | Location |
|-------|--------|----------|
| {issue} | {impact} | {file}:{line} |

## Touch Points Analysis

### Direct Usage ({count} files)

| File | Usage Type | Lines |
|------|------------|-------|
| {file} | {import/call/config} | {lines} |

### Indirect Dependencies ({count} files)

| File | Dependency Path | Impact |
|------|-----------------|--------|
| {file} | {path} | {impact} |

## Coupling Analysis

### Coupling Type

- **Classification:** {TIGHT | MODERATE | LOOSE}
- **Evidence:** {description}

### Dependency Graph

{Mermaid diagram showing dependencies}

## Refactoring Recommendations

### Before Migration (if abstraction < 7)

1. {refactoring step 1}
   - Files: {files}
   - Effort: {estimate}
2. {refactoring step 2}
   - Files: {files}
   - Effort: {estimate}

### Interface Design

```text
// Recommended abstraction interface
{interface code}
```

## Migration Readiness

### Readiness Score: {score}/10

| Criterion | Status | Notes |
|-----------|--------|-------|
| Abstraction level | {[ok]/[x]} | {notes} |
| Test coverage | {[ok]/[x]} | {notes} |
| Documentation | {[ok]/[x]} | {notes} |
| Team familiarity | {[ok]/[x]} | {notes} |

### Blockers

{List any blockers that must be resolved before migration}

### Recommendations

{Prioritized list of pre-migration tasks}

<!-- markdownlint-disable-next-line MD040 -->
```

**Write using CLI:**

```bash
speckitadv write-report abstraction-assessment.md --content '<generated-content>' --stage=06e-cross-cutting-artifacts
```

**Verify:** Read file, confirm no placeholders.

**Output:** `[ok] Generated: abstraction-assessment.md`

---

## Artifact 2: Concern Migration Plan (3 Parts)

### Part 1: Strategy + Phasing

---
**[STOP: GENERATE_MIGRATION_PLAN_PART_1]**

**Template:** Written to `{reports_dir}/concern-migration-plan.md`

{{copy-template:concern-migration-plan-template.md:concern-migration-plan.md}}

Read the template file above and fill in each section.

```markdown
# Migration Plan: {Concern Type}

## 1. Executive Summary

| Aspect | Value |
|--------|-------|
| Migration | {current} -> {target} |
| Strategy | {selected strategy} |
| Duration | {total weeks} weeks |
| Effort | {person-days} person-days |
| Risk Level | {HIGH/MEDIUM/LOW} |

## 2. Migration Strategy

### Selected Approach: {strategy}

**Rationale:**
{explanation from Stage 3B}

**Alternatives Considered:**

| Strategy | Score | Why Not Selected |
|----------|-------|------------------|
| {alt1} | {score} | {reason} |
| {alt2} | {score} | {reason} |

## 3. Phased Plan

### Phase 1: Foundation (50% value)

- **Duration:** {weeks} weeks
- **Focus:** {description}
- **Deliverables:**
  - {deliverable 1}
  - {deliverable 2}
- **Milestone:** {milestone}

### Phase 2: Expansion (30% value)

- **Duration:** {weeks} weeks
- **Focus:** {description}
- **Deliverables:**
  - {deliverable 1}
  - {deliverable 2}
- **Milestone:** {milestone}

### Phase 3: Completion (15% value)

- **Duration:** {weeks} weeks
- **Focus:** {description}
- **Deliverables:**
  - {deliverable 1}
  - {deliverable 2}
- **Milestone:** {milestone}

### Phase 4: Optimization (5% value)

- **Duration:** {weeks} weeks
- **Focus:** {description}
- **Deliverables:**
  - {deliverable 1}
  - {deliverable 2}
- **Milestone:** {milestone}

```

**Write using CLI:**

```bash
speckitadv write-report concern-migration-plan.md --content '<generated-content>' --stage=06e-cross-cutting-artifacts
```

**Output:**

```text
concern-migration-plan.md Part 1/3 complete: Strategy + Phasing
  - Strategy: {strategy}
  - Phases: 4
  - Lines: [COUNT]

```

---

### Part 2: Implementation + Testing

---
**[STOP: GENERATE_MIGRATION_PLAN_PART_2]**

```markdown
## 4. Environment Setup

### Prerequisites

- [ ] {prerequisite 1}
- [ ] {prerequisite 2}

### Setup Steps

1. {step 1}
2. {step 2}
3. {step 3}

### Configuration

```text
{configuration example}
```

## 5. Code Changes

### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| {file} | {add/modify/delete} | {description} |

### Migration Pattern

```text
// Before (Legacy)
{legacy code}

// After (Target)
{target code}
```

### Key Transformations

1. {transformation 1}
2. {transformation 2}

## 6. Testing Strategy

### Test Categories

| Type | Scope | Automation |
|------|-------|------------|
| Unit | {scope} | {yes/no} |
| Integration | {scope} | {yes/no} |
| E2E | {scope} | {yes/no} |

### Parallel Testing

{How to run legacy and target in parallel for comparison}

### Rollback Test

{How to verify rollback works before going live}

<!-- markdownlint-disable-next-line MD040 -->
```

**Append using CLI:**

```bash
speckitadv write-report concern-migration-plan.md --content '<generated-content>' --append --stage=06e-cross-cutting-artifacts
```

**Output:**

```text
concern-migration-plan.md Part 2/3 complete: Implementation + Testing
  - Files to modify: [COUNT]
  - Test types: [COUNT]
  - Lines: [COUNT]

```

---

### Part 3: Deployment + Operations + Success

---
**[STOP: GENERATE_MIGRATION_PLAN_PART_3]**

```markdown
## 7. Deployment Strategy

### Deployment Approach

- **Method:** {Blue-Green | Canary | Rolling | Big Bang}
- **Rationale:** {why this approach}

### Deployment Steps

1. {step 1}
2. {step 2}
3. {step 3}

### Feature Flags

| Flag | Purpose | Default |
|------|---------|---------|
| {flag} | {purpose} | {on/off} |

## 8. Monitoring & Alerting

### Key Metrics

| Metric | Baseline | Target | Alert Threshold |
|--------|----------|--------|-----------------|
| {metric} | {current} | {target} | {threshold} |

### Dashboards

- {dashboard 1}: {purpose}
- {dashboard 2}: {purpose}

### Alerts

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| {alert} | {condition} | {sev} | {action} |

## 9. Success Criteria

### Functional Criteria

- [ ] All {count} components migrated
- [ ] 100% feature parity
- [ ] Zero data loss
- [ ] All tests passing

### Performance Criteria

- [ ] Response time: <= {threshold}ms
- [ ] Throughput: >= {threshold} req/sec
- [ ] Error rate: < 0.1%

### Operational Criteria

- [ ] Monitoring operational
- [ ] Alerting configured
- [ ] Rollback tested
- [ ] Runbooks complete

## 10. Post-Migration

### Cleanup Tasks

1. {cleanup task 1}
2. {cleanup task 2}

### Documentation Updates

- [ ] Architecture docs
- [ ] Runbooks
- [ ] API docs

### Lessons Learned

{Template for post-migration retrospective}

```

**Append using CLI:**

```bash
speckitadv write-report concern-migration-plan.md --content '<generated-content>' --append --stage=06e-cross-cutting-artifacts
```

**Verify:** Read complete file, confirm all 10 sections present.

**Output:**

```text
concern-migration-plan.md Part 3/3 complete: Deployment + Operations + Success
  - Lines: [COUNT]

concern-migration-plan.md COMPLETE (3/3 parts)
   Total lines: [COUNT]

```

---

## Artifact 3: Rollback Procedure

---
**[STOP: GENERATE_ROLLBACK_PROCEDURE]**

Generate detailed rollback procedure:

```markdown
# Rollback Procedure: {Concern Type} Migration

## Overview

- **Migration:** {current} -> {target}
- **Last Updated:** {date}
- **Owner:** {team/person}

## When to Rollback

### Automatic Rollback Triggers

- Error rate > {threshold}%
- Response time > {threshold}ms for > {duration}
- {Critical metric} breach

### Manual Rollback Triggers

- Customer-reported critical issue
- Data integrity concern
- Security vulnerability discovered

## Pre-Rollback Checklist

- [ ] Confirm rollback is necessary (not a transient issue)
- [ ] Notify stakeholders
- [ ] Capture current state for analysis
- [ ] Verify rollback environment ready

## Rollback Steps

### Step 1: Initiate Rollback

```bash
{command or action}
```

- **Expected Duration:** {time}
- **Verification:** {how to verify}

### Step 2: Switch Traffic

```bash
{command or action}
```

- **Expected Duration:** {time}
- **Verification:** {how to verify}

### Step 3: Disable New Implementation

```bash
{command or action}
```

- **Expected Duration:** {time}
- **Verification:** {how to verify}

### Step 4: Verify Legacy Active

```bash
{command or action}
```

- **Expected Duration:** {time}
- **Verification:** {how to verify}

## Post-Rollback Verification

### Functional Verification

- [ ] Core functionality working
- [ ] No error spikes
- [ ] Data integrity confirmed

### Performance Verification

- [ ] Response times normal
- [ ] Throughput normal
- [ ] No resource issues

### Monitoring Verification

- [ ] All dashboards green
- [ ] No active alerts

## Post-Rollback Actions

### Immediate (within 1 hour)

1. {action 1}
2. {action 2}

### Short-term (within 24 hours)

1. {action 1}
2. {action 2}

### Analysis Required

1. Root cause analysis
2. Fix identification
3. Re-migration planning

## Escalation Contacts

| Role | Contact | When to Escalate |
|------|---------|------------------|
| {role} | {contact} | {condition} |

## Revision History

| Date | Change | Author |
|------|--------|--------|
| {date} | Initial version | {author} |

<!-- markdownlint-disable-next-line MD040 -->
```

**Write using CLI:**

```bash
speckitadv write-report rollback-procedure.md --content '<generated-content>' --stage=06e-cross-cutting-artifacts
```

**Verify:** Read file, confirm no placeholders.

**Output:** `[ok] Generated: rollback-procedure.md`

---

## Generate Stage 6 State (Scope B)

```json
{
  "schema_version": "3.1.0",
  "chain_id": "{chain_id}",
  "stage": "scope_artifact_generation",
  "timestamp": "{ISO-8601}",
  "stages_complete": [..., "scope_artifact_generation"],
  "scope_artifacts_generated": [
    "abstraction-assessment.md",
    "concern-migration-plan.md",
    "rollback-procedure.md"
  ],
  "total_scope_artifacts": 3,
  "all_artifacts_complete": true
}

```

The CLI automatically updates `{analysis_dir}/state.json` when stages complete.

---

## Completion Marker

```text
===========================================================
  STAGE COMPLETE: SCOPE_ARTIFACTS (Cross-Cutting Concern)

  Chain ID: {chain_id}

  Concern: {concern_type}
  Migration: {current} -> {target}
  Strategy: {strategy}

  Artifacts Generated (3 total):
    [ok] abstraction-assessment.md
    [ok] concern-migration-plan.md
    [ok] rollback-procedure.md
===========================================================

STAGE_COMPLETE:SCOPE_ARTIFACTS

```

---

## Analysis Chain Complete

```text
===========================================================
           ANALYSIS CHAIN COMPLETE
===========================================================

Chain ID: {chain_id}

All Stages Completed:
  [ok] Stage 1: Setup and Scope
  [ok] Stage 2: File Analysis
  [ok] Stage 3B: Cross-Cutting Concern Analysis
  [ok] Stage 4: Report Generation
  [ok] Stage 5: Common Artifacts
  [ok] Stage 6: Scope-Specific Artifacts

Analysis Directory: {analysis_dir}

Generated Artifacts:
  Common:
    * EXECUTIVE-SUMMARY.md
    * dependency-audit.json
    * metrics-summary.json
    * analysis-report.md

  Scope-Specific:
    * abstraction-assessment.md
    * concern-migration-plan.md
    * rollback-procedure.md

Next Steps:
  1. Review abstraction-assessment.md for pre-migration work
  2. Follow concern-migration-plan.md phases
  3. Keep rollback-procedure.md accessible during migration

===========================================================

```
