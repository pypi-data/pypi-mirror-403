---
stage: cross_cutting_strategy
requires: 03b1-abstraction-assessment
condition: scope == "B"
outputs: migration_strategy
version: 3.4.0
---

{{include:strict-execution-mode.md}}

**Note:** Analysis-only substage - no files created. Final data saved via CLI (see Step 5).

---

# Stage 3B-2: Migration Strategy & Risk Assessment

## Purpose

Based on abstraction level and blast radius, recommend the optimal migration strategy and assess associated risks.

---

## AI Context Cache: Recall Earlier Analysis

Before defining migration strategy, recall cached understanding from previous stages:

```text
# Recall abstraction assessment from 03b1
recall_understanding(target="{concern_type}")

# IF found AND fresh: Use cached abstraction/blast radius analysis
# IF not found: Review abstraction-assessment.json manually

# AFTER strategy defined, store understanding:
store_understanding(
  scope="module",
  target="{concern_type}/migration-strategy",
  purpose="Migration strategy for {concern_type}: {current} -> {target}",
  importance="critical",
  key_points=["<selected strategy>", "<phase breakdown>", "<duration estimate>"],
  gotchas=["<high risks identified>", "<migration blockers>"],
  analysis="<rationale for strategy selection and phase details>"
)
```

---

## Discovery Tools

{{include:analyze-civyk-repoix-discovery.md}}

**Strategy-specific tools:**

- `get_dependencies()` - component coupling
- `find_circular_dependencies()` - migration blockers

---

## How Context Is Provided

The CLI manages state and provides all context. **Do not read state.json directly.**

Values available (already substituted by CLI):

- Project path, analysis directory, scope (must be "B"), context
- Concern type, current implementation, target implementation
- Abstraction analysis from previous stage is in artifacts

---

## Step 1: Strategy Selection

Select migration strategy based on abstraction level and blast radius.

---
**[STOP: SELECT_STRATEGY]**

**Decision Matrix:**

| Abstraction | Blast Radius | Recommended Strategy |
|-------------|--------------|----------------------|
| HIGH (7-10) | SMALL (<10%) | **Direct Replacement** |
| HIGH (7-10) | MEDIUM/LARGE (10-50%) | **Phased Migration** |
| HIGH (7-10) | CRITICAL (>50%) | **Phased Migration with Feature Flags** |
| MEDIUM (4-6) | SMALL (<10%) | **Refactor Then Replace** |
| MEDIUM (4-6) | MEDIUM (10-30%) | **Strangler Fig Pattern** |
| MEDIUM (4-6) | LARGE/CRITICAL (>30%) | **Strangler Fig with Dual-Write** |
| LOW (1-3) | SMALL (<10%) | **Refactor First (Extract Interface)** |
| LOW (1-3) | MEDIUM/LARGE (10-50%) | **Long-Term Strangler Fig** |
| LOW (1-3) | CRITICAL (>50%) | **Incremental Refactor + Strangler** |

**Strategy Descriptions:**

### Direct Replacement

- **When:** HIGH abstraction + SMALL blast radius
- **Approach:** Swap implementation directly behind existing interface
- **Duration:** Days to 1-2 weeks
- **Risk:** LOW

### Phased Migration

- **When:** HIGH abstraction + larger blast radius
- **Approach:** Migrate module by module, using existing interfaces
- **Duration:** 2-6 weeks
- **Risk:** LOW to MEDIUM

### Refactor Then Replace

- **When:** MEDIUM abstraction + SMALL blast radius
- **Approach:** First create proper abstractions, then swap
- **Duration:** 2-4 weeks
- **Risk:** MEDIUM

### Strangler Fig Pattern

- **When:** MEDIUM/LOW abstraction + MEDIUM+ blast radius
- **Approach:** New implementation alongside old, gradual cutover
- **Duration:** 4-12 weeks
- **Risk:** MEDIUM to HIGH

**Output Selected Strategy:**

```text
Migration Strategy Selection:

Inputs:
  Abstraction Level: {level} ({score}/10)
  Blast Radius: {classification} ({percentage}%)

Selected Strategy: {STRATEGY_NAME}

Rationale:
  {explanation based on decision matrix}

Alternative Considered: {alternative}
  Why Not: {reason}
```

---

## Step 2: Define Migration Phases

Create detailed phase plan using 50/30/15/5 value distribution.

---
**[STOP: DEFINE_PHASES]**

**Phase Template:**

### Phase 1: Foundation & Pilot (50% Value)

**Duration:** 30-40% of timeline
**Focus:**

- Set up target implementation infrastructure
- Create/enhance abstraction layer (if needed)
- Migrate ONE pilot component (lowest risk)
- Validate in staging/production (canary)

**Deliverables:**

- Target implementation running
- Pilot component migrated
- Monitoring in place
- Rollback tested

**Success Criteria:**

- Pilot working for 1+ week
- No performance regression
- Rollback successful when tested

### Phase 2: Expansion (30% Value)

**Duration:** 25-30% of timeline
**Focus:**

- Migrate 3-5 additional components
- Run parallel (old + new) if needed
- Monitor performance and errors
- Document learnings

**Deliverables:**

- Multiple components migrated
- Dual-write/read working (if applicable)
- Error handling validated

**Success Criteria:**

- 50% of components migrated
- Error rate < 0.1%
- Performance within 10% of baseline

### Phase 3: Completion (15% Value)

**Duration:** 15-20% of timeline
**Focus:**

- Migrate remaining components
- Deprecate old implementation
- Remove dual-write/feature flags
- Clean up legacy code

**Deliverables:**

- All components on new implementation
- Old implementation decommissioned
- Code cleanup complete

**Success Criteria:**

- 100% migrated
- Old code removed
- Tests passing

### Phase 4: Optimization (5% Value)

**Duration:** 10-15% of timeline
**Focus:**

- Performance tuning
- Documentation updates
- Remove migration scaffolding
- Knowledge transfer

**Deliverables:**

- Optimized implementation
- Complete documentation
- Team trained

**Output:**

```text
Migration Phases ({strategy}):

Phase 1 - Foundation & Pilot (50%)
  Duration: {weeks} weeks
  Components: {list pilot components}
  Exit Criteria: Pilot stable for 1 week

Phase 2 - Expansion (30%)
  Duration: {weeks} weeks
  Components: {list next components}
  Exit Criteria: 50% migrated, < 0.1% errors

Phase 3 - Completion (15%)
  Duration: {weeks} weeks
  Components: {list remaining}
  Exit Criteria: 100% migrated

Phase 4 - Optimization (5%)
  Duration: {weeks} weeks
  Focus: Performance, docs, cleanup
  Exit Criteria: Production stable 30 days

```

---

## Step 3: Risk Assessment

Identify and categorize migration risks.

---
**[STOP: ASSESS_RISKS]**

**Risk Categories:**

### Technical Risks

```text
For each, rate: Probability (H/M/L) x Impact (H/M/L)

1. Breaking Changes
   - New implementation has different behavior
   - Missing features in target
   - API incompatibility

2. Performance Regression
   - Target slower than current
   - Resource usage increase
   - Latency spikes

3. Data Integrity
   - Data format differences
   - Migration data loss
   - Inconsistent state during dual-write

4. Integration Failures
   - Downstream systems impacted
   - External API changes needed
   - Protocol mismatches

```

### Business Risks

```text
1. User Experience Disruption
   - Downtime during migration
   - Feature degradation
   - Error rate increase

2. Timeline Overrun
   - Underestimated complexity
   - Dependency delays
   - Team availability

3. Training Gap
   - Team unfamiliar with target
   - Documentation lag
   - Support burden

```

### Operational Risks

```text
1. Rollback Complexity
   - Can't rollback cleanly
   - Data divergence
   - Cascading failures

2. Monitoring Gaps
   - Blind spots during transition
   - Alert fatigue
   - Debugging difficulty

3. Cost Overrun
   - Running dual systems
   - Extended timeline
   - Additional resources

```

**Output Format:**

```text
Risk Assessment:

[!] HIGH RISKS (Probability x Impact = HIGH)
-------------------------------------------------------------
  1. {risk_name}
     Probability: HIGH, Impact: HIGH
     Description: {description}
     Mitigation: {strategy}
     Owner: {role}

  2. {risk_name}
     ...

[!] MEDIUM RISKS
-------------------------------------------------------------
  1. {risk_name}
     Probability: {P}, Impact: {I}
     Description: {description}
     Mitigation: {strategy}

[ok] LOW RISKS
-------------------------------------------------------------
  1. {risk_name}
     ...

```

---

## Step 4: Compile Strategy Data

```json
{
  "migration_strategy": {
    "selected": "{strategy name}",
    "rationale": "{explanation}",
    "alternative": "{alternative strategy}",
    "phases": {
      "phase_1": {
        "name": "Foundation & Pilot",
        "value_percentage": 50,
        "duration_weeks": {n},
        "components": ["{list}"],
        "exit_criteria": ["{list}"]
      },
      "phase_2": {
        "name": "Expansion",
        "value_percentage": 30,
        "duration_weeks": {n},
        "components": ["{list}"],
        "exit_criteria": ["{list}"]
      },
      "phase_3": {
        "name": "Completion",
        "value_percentage": 15,
        "duration_weeks": {n},
        "components": ["{list}"],
        "exit_criteria": ["{list}"]
      },
      "phase_4": {
        "name": "Optimization",
        "value_percentage": 5,
        "duration_weeks": {n},
        "focus": ["{list}"],
        "exit_criteria": ["{list}"]
      }
    },
    "total_duration_weeks": {n},
    "risks": {
      "high": [
        {"name": "{name}", "probability": "HIGH", "impact": "HIGH", "mitigation": "{strategy}"}
      ],
      "medium": [
        {"name": "{name}", "probability": "{P}", "impact": "{I}", "mitigation": "{strategy}"}
      ],
      "low": [
        {"name": "{name}", "probability": "{P}", "impact": "{I}", "mitigation": "{strategy}"}
      ]
    }
  }
}
```

---

## Step 5: Save Strategy Data

Save the strategy data to the data folder using stdin mode:

```powershell
@"
{
  "migration_strategy": { ... full JSON from Step 4 ... }
}
"@ | speckitadv write-data migration-strategy.json --stage=03b2-migration-strategy --stdin
```

---

## Output Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 03b2-migration-strategy

  Strategy: {strategy name}
  Duration: {total_weeks} weeks

  Phases:
    P1: Foundation ({weeks}w) - {components}
    P2: Expansion ({weeks}w) - {components}
    P3: Completion ({weeks}w) - {components}
    P4: Optimization ({weeks}w)

  Risks: {high} HIGH, {medium} MEDIUM, {low} LOW

  Proceeding to Effort & Success Criteria...
===========================================================

```

---

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits the next prompt. **Do NOT analyze or generate artifacts until you run this command.**
