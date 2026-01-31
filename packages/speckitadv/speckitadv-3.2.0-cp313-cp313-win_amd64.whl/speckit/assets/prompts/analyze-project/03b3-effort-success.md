---
stage: cross_cutting_effort
requires: 03b2-migration-strategy
condition: scope == "B"
outputs: cross_cutting_complete
version: 3.4.0
---

{{include:strict-execution-mode.md}}

**Note:** Analysis-only substage - no files created. Final data saved via CLI (see Step 3).

---

# Stage 3B-3: Effort Estimation & Success Criteria

## Purpose

Estimate development effort for the migration and define measurable success criteria.

---

## AI Context Cache: Recall Earlier Analysis

Before estimating effort, recall cached understanding from previous stages:

```text
# Recall all previous stage analyses
recall_understanding(target="{concern_type}")
recall_understanding(target="{concern_type}/migration-strategy")

# IF found AND fresh: Use cached abstraction and strategy analysis
# IF not found: Review previous stage JSON files manually

# AFTER effort estimation completes, store final understanding:
store_understanding(
  scope="module",
  target="{concern_type}/cross-cutting-complete",
  purpose="Complete cross-cutting analysis for {concern_type}",
  importance="critical",
  key_points=["<total effort weeks>", "<team size>", "<key success criteria>"],
  gotchas=["<high risks>", "<critical dependencies>"],
  analysis="<comprehensive migration plan summary>"
)
```

---

## Discovery Tools

{{include:analyze-civyk-repoix-discovery.md}}

**Estimation-specific tools:**

- `get_tests_for(path)` - identify test effort
- `get_hotspots()` - complexity indicators

---

## How Context Is Provided

The CLI manages state and provides all context. **Do not read state.json directly.**

Values available (already substituted by CLI):

- Project path, analysis directory, scope (must be "B"), context
- Concern type, current implementation, target implementation
- Strategy and risk analysis from previous stages are in artifacts

---

## Step 1: Effort Estimation

Calculate effort based on abstraction level, blast radius, and strategy.

---
**[STOP: ESTIMATE_EFFORT]**

**Effort Components:**

### 1. Abstraction Refactoring (if needed)

```text
Based on abstraction level:
  LOW (1-3):   2-4 weeks (create interfaces, DI, isolate)
  MEDIUM (4-6): 1-2 weeks (enhance existing, fix coupling)
  HIGH (7-10):  0 weeks (already abstracted)

```

### 2. New Implementation Setup

```text
Infrastructure setup: 1-2 weeks
  - Environment configuration
  - Dependency installation
  - CI/CD pipeline updates

Integration development: 2-4 weeks
  - Implement adapter/wrapper
  - Connect to target system
  - Handle error cases

Testing setup: 1-2 weeks
  - Unit test stubs
  - Integration test framework
  - Mock/stub configuration

```

### 3. Migration Execution

```text
Per component migration:
  Simple component: 0.5-1 day
  Medium component: 1-2 days
  Complex component: 3-5 days

Total: {component_count} components x average_days

```

### 4. Testing & Validation

```text
Unit testing:       1-2 weeks
Integration testing: 1-2 weeks
E2E testing:        0.5-1 week
Performance testing: 0.5-1 week

```

### 5. Documentation & Training

```text
Technical docs:  3-5 days
Runbooks:        2-3 days
Team training:   1-2 days

```

**Calculate Totals:**

```text
base_effort = refactoring + setup + migration + testing + docs
buffer = base_effort x 0.20 (20% buffer for unknowns)
total_effort = base_effort + buffer

```

**Output:**

```text
Effort Estimation:

Component Breakdown:
  Abstraction Refactoring: {weeks} weeks
  Implementation Setup:    {weeks} weeks
  Migration Execution:     {weeks} weeks
  Testing & Validation:    {weeks} weeks
  Documentation:           {weeks} weeks

  ---------------------------------
  Base Effort:             {weeks} weeks
  Buffer (20%):            {weeks} weeks
  TOTAL EFFORT:            {weeks} weeks
  ---------------------------------

Person-Days: {total_days} days
Recommended Team Size: {n} developers
Calendar Duration: {months} months

```

---

## Step 2: Success Criteria Definition

Define measurable criteria for migration success.

---
**[STOP: DEFINE_SUCCESS_CRITERIA]**

**Functional Criteria:**

```text
[ ] All {count} components migrated to new implementation
[ ] 100% feature parity with legacy implementation
[ ] Zero data loss during migration
[ ] All API contracts maintained (no breaking changes)
[ ] All existing tests passing
[ ] New implementation-specific tests added

```

**Performance Criteria:**

```text
[ ] Response time: <= {current_p95}ms (same or better)
[ ] Throughput: >= {current_rps} requests/sec
[ ] Resource usage: <= {current_usage} (CPU/memory)
[ ] Error rate: < 0.1%

```

**Operational Criteria:**

```text
[ ] Monitoring dashboards operational for new implementation
[ ] Alerting rules configured and tested
[ ] Rollback procedure documented and tested
[ ] Runbooks created for common issues
[ ] On-call documentation updated

```

**Business Criteria:**

```text
[ ] Zero customer-reported issues related to migration
[ ] No service interruptions during migration
[ ] Team trained on new implementation
[ ] Documentation complete and reviewed

```

**Output:**

```text
Success Criteria:

FUNCTIONAL (Must Pass):
  [ok] All components migrated: {count}
  [ok] Feature parity: 100%
  [ok] Data integrity: Zero loss
  [ok] API compatibility: Maintained
  [ok] Tests: All passing

PERFORMANCE (Thresholds):
  [ok] Response Time: <= {n}ms (p95)
  [ok] Throughput: >= {n} req/sec
  [ok] Error Rate: < 0.1%

OPERATIONAL (Checklist):
  [ok] Monitoring: Configured
  [ok] Alerting: Active
  [ok] Rollback: Tested
  [ok] Runbooks: Complete

BUSINESS (Validation):
  [ok] Zero customer issues
  [ok] No interruptions
  [ok] Team trained

```

---

## Step 3: Save Complete Stage 3B Data

Save the complete cross-cutting analysis to the data folder using stdin mode:

```powershell
@"
{
  "schema_version": "3.1.0",
  "chain_id": "{chain_id}",
  "stage": "cross_cutting_analysis",
  "timestamp": "{ISO-8601}",
  "concern_analysis": { ... complete JSON below ... }
}
"@ | speckitadv write-data effort-success.json --stage=03b3-effort-success --stdin
```

**Full JSON structure:**

```json
{
  "schema_version": "3.1.0",
  "chain_id": "{chain_id}",
  "stage": "cross_cutting_analysis",
  "timestamp": "{ISO-8601}",
  "stages_complete": ["setup_and_scope", "file_analysis", "cross_cutting_analysis"],

  "concern_analysis": {
    "concern_type": "{type}",
    "current_implementation": "{current}",
    "target_implementation": "{target}",

    "abstraction": {
      "score": {score},
      "level": "{HIGH|MEDIUM|LOW}",
      "patterns_found": ["{list}"],
      "issues_found": ["{list}"]
    },

    "blast_radius": {
      "direct_impact": {count},
      "indirect_impact": {count},
      "config_impact": {count},
      "test_impact": {count},
      "total_affected": {count},
      "percentage": {value},
      "classification": "{SMALL|MEDIUM|LARGE|CRITICAL}"
    },

    "migration_strategy": {
      "selected": "{strategy}",
      "rationale": "{explanation}",
      "phases": {
        "phase_1": {"name": "Foundation", "duration": "{weeks}w", "value": "50%"},
        "phase_2": {"name": "Expansion", "duration": "{weeks}w", "value": "30%"},
        "phase_3": {"name": "Completion", "duration": "{weeks}w", "value": "15%"},
        "phase_4": {"name": "Optimization", "duration": "{weeks}w", "value": "5%"}
      },
      "total_duration": "{weeks} weeks"
    },

    "risks": {
      "high": ["{list}"],
      "medium": ["{list}"],
      "low": ["{list}"]
    },

    "effort": {
      "abstraction_refactoring": "{weeks}w",
      "implementation_setup": "{weeks}w",
      "migration_execution": "{weeks}w",
      "testing_validation": "{weeks}w",
      "documentation": "{weeks}w",
      "total_weeks": {n},
      "total_person_days": {n},
      "team_size": {n},
      "calendar_months": {n}
    },

    "success_criteria": {
      "functional": ["{list}"],
      "performance": {
        "response_time_ms": {n},
        "throughput_rps": {n},
        "error_rate_max": 0.001
      },
      "operational": ["{list}"],
      "business": ["{list}"]
    }
  }
}
```

### Save State

The CLI automatically updates `{analysis_dir}/state.json` when stages complete.

---

## Step 4: Verify Data Saved

---
**[STOP: VERIFY_DATA_SAVED]**

Verify `{data_dir}/effort-success.json` was written successfully.

**IF missing:** Re-run the CLI command from Step 3.

---

## Completion Marker

```text
===========================================================
  STAGE COMPLETE: CROSS_CUTTING_ANALYSIS

  Chain ID: {chain_id}

  Summary:
    Concern: {concern_type}
    Migration: {current} -> {target}

    Abstraction: {level} ({score}/10)
    Blast Radius: {classification} ({percentage}%)
    Strategy: {strategy}
    Duration: {weeks} weeks
    Effort: {person_days} person-days

  Proceeding to Stage 4: Report Generation
===========================================================

STAGE_COMPLETE:CROSS_CUTTING_ANALYSIS

```

---

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits the next prompt. **Do NOT analyze or generate artifacts until you run this command.**
