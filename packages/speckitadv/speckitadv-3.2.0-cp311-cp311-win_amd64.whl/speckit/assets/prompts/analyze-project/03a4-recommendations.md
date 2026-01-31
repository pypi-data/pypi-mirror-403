---
stage: full_app_recommendations
requires: 03a3-validation-scoring
condition: scope == "A"
outputs: full_app_complete
version: 3.4.0
---

{{include:strict-execution-mode.md}}

**Note:** Recommendations-only substage - no files created. Final data saved via CLI.

---

# Stage 3A-4: Recommendations & State Completion

## Purpose

Generate prioritized modernization recommendations and compile the complete Stage 3A state for report generation.

---

## How Context Is Provided

The CLI manages state and provides all context. **Do not read state.json directly.**

Values available (already substituted by CLI):

- Project path, analysis directory, scope, context
- All previous stage artifacts available in analysis directory

---

## AI Context Cache: Recall Analysis Context

Before generating recommendations, recall cached understanding from analysis phases:

```text
# Recall project-level and component understanding
recall_understanding(target="project")
get_understanding_stats(limit=50)

# Use cached understanding to:
# - Inform recommendation priorities based on analyzed complexity
# - Reference gotchas discovered during analysis
# - Ensure recommendations align with actual code patterns
```

---

## Step 1: Generate Prioritized Recommendations

Based on feasibility scores and complexity analysis, generate recommendations.

### Recommendation Logic

**Primary Recommendation Selection:**

```text
IF hybrid_feasibility > 70% AND complexity >= MEDIUM:
  PRIMARY = "Hybrid/Strangler Fig Pattern"
  REASON = "Allows incremental migration with lower risk"

ELSE IF inline_feasibility > 75% AND complexity <= MEDIUM:
  PRIMARY = "Inline Upgrade"
  REASON = "Low complexity enables direct modernization"

ELSE IF greenfield_feasibility > 80% AND complexity >= HIGH:
  PRIMARY = "Greenfield Rewrite"
  REASON = "High complexity makes incremental approach costly"

ELSE:
  PRIMARY = "Phased Hybrid Approach"
  REASON = "Balanced approach for moderate complexity"

```

### Generate Recommendations

```json
{
  "recommendations": {
    "primary": {
      "approach": "{selected approach}",
      "confidence": "{percentage}%",
      "rationale": "{reason}",
      "estimated_duration": "{months} months",
      "estimated_effort": "{person-weeks} person-weeks"
    },
    "alternative": {
      "approach": "{second best approach}",
      "confidence": "{percentage}%",
      "trade_offs": "{why not primary}"
    },
    "quick_wins": [
      {
        "action": "Upgrade runtime to LTS",
        "effort": "LOW",
        "impact": "HIGH",
        "components": ["{list}"]
      },
      {
        "action": "Add observability",
        "effort": "MEDIUM",
        "impact": "HIGH",
        "components": ["{list}"]
      },
      {
        "action": "Fix critical security issues",
        "effort": "MEDIUM",
        "impact": "CRITICAL",
        "components": ["{list}"]
      }
    ],
    "phased_plan": {
      "phase_1": {
        "name": "Foundation (50% value)",
        "duration": "{weeks} weeks",
        "focus": ["{components}"],
        "deliverables": ["{list}"],
        "risk": "LOW"
      },
      "phase_2": {
        "name": "Core Migration (30% value)",
        "duration": "{weeks} weeks",
        "focus": ["{components}"],
        "deliverables": ["{list}"],
        "risk": "MEDIUM"
      },
      "phase_3": {
        "name": "Complete Migration (15% value)",
        "duration": "{weeks} weeks",
        "focus": ["{components}"],
        "deliverables": ["{list}"],
        "risk": "MEDIUM"
      },
      "phase_4": {
        "name": "Optimization (5% value)",
        "duration": "{weeks} weeks",
        "focus": ["{components}"],
        "deliverables": ["{list}"],
        "risk": "LOW"
      }
    },
    "risks": [
      {
        "risk": "{description}",
        "probability": "HIGH|MEDIUM|LOW",
        "impact": "HIGH|MEDIUM|LOW",
        "mitigation": "{strategy}"
      }
    ],
    "success_criteria": [
      "All {count} features migrated and functional",
      "Test coverage >= {target}%",
      "Performance meets or exceeds current",
      "Security vulnerabilities addressed",
      "Zero data loss during migration"
    ]
  }
}
```

---

## Step 2: Display Recommendations to User

```text
===========================================================
MODERNIZATION RECOMMENDATIONS
===========================================================

PRIMARY RECOMMENDATION
-------------------------------------------------------------

  Approach: {primary.approach}
  Confidence: {primary.confidence}%

  Rationale:
  {primary.rationale}

  Estimated Timeline: {primary.estimated_duration}
  Estimated Effort: {primary.estimated_effort}

ALTERNATIVE APPROACH
-------------------------------------------------------------

  Approach: {alternative.approach}
  Confidence: {alternative.confidence}%
  Trade-offs: {alternative.trade_offs}

QUICK WINS (Do First)
-------------------------------------------------------------

  1. {quick_win_1.action}
     Effort: {effort}, Impact: {impact}

  2. {quick_win_2.action}
     Effort: {effort}, Impact: {impact}

  3. {quick_win_3.action}
     Effort: {effort}, Impact: {impact}

PHASED MIGRATION PLAN
-------------------------------------------------------------

  Phase 1: {phase_1.name} ({phase_1.duration})
    Focus: {phase_1.focus}
    Risk: {phase_1.risk}

  Phase 2: {phase_2.name} ({phase_2.duration})
    Focus: {phase_2.focus}
    Risk: {phase_2.risk}

  Phase 3: {phase_3.name} ({phase_3.duration})
    Focus: {phase_3.focus}
    Risk: {phase_3.risk}

  Phase 4: {phase_4.name} ({phase_4.duration})
    Focus: {phase_4.focus}
    Risk: {phase_4.risk}

TOP RISKS
-------------------------------------------------------------

  [!] {risk_1}: {mitigation_1}
  [!] {risk_2}: {mitigation_2}
  [ok] {risk_3}: {mitigation_3}

===========================================================

```

---

## Step 3: Compile Complete Stage 3A State

Merge all Stage 3A data into comprehensive state:

```json
{
  "schema_version": "3.1.0",
  "chain_id": "{chain_id}",
  "stage": "full_app_analysis",
  "timestamp": "{ISO-8601}",
  "stages_complete": ["setup_and_scope", "file_analysis", "full_app_analysis"],

  "modernization_preferences": {
    "q1_language": "{q1 value}",
    "q2_database": "{q2 value}",
    "q3_message_bus": "{q3 value}",
    "q4_package_manager": "{q4 value}",
    "q5_deployment": "{q5 value}",
    "q6_iac": "{q6 value}",
    "q7_containerization": "{q7 value}",
    "q8_observability": {
      "metrics": "{value}",
      "logging": "{value}",
      "tracing": "{value}"
    },
    "q9_security": "{q9 value}",
    "q10_testing": {
      "strategy": "{q10 value}",
      "coverage_target": "{percentage}"
    }
  },

  "scope": {
    "validated": true,
    "in_scope": ["{list of components to modernize}"],
    "out_of_scope": ["{list of components to keep}"]
  },

  "scoring": {
    "complexity": {
      "codebase_size": {score},
      "tech_stack_change": {score},
      "database_migration": {score},
      "integration_count": {score},
      "test_coverage_gap": {score},
      "security_changes": {score},
      "overall": {score},
      "rating": "{rating}"
    },
    "feasibility": {
      "inline_upgrade": {score},
      "greenfield_rewrite": {score},
      "hybrid_approach": {score}
    }
  },

  "recommendations": {
    "primary": {
      "approach": "{approach}",
      "confidence": {percentage},
      "rationale": "{reason}",
      "estimated_duration": "{duration}",
      "estimated_effort": "{effort}"
    },
    "alternative": {
      "approach": "{approach}",
      "confidence": {percentage}
    },
    "quick_wins": ["{list}"],
    "phased_plan": {
      "phase_1": {"name": "{name}", "duration": "{duration}"},
      "phase_2": {"name": "{name}", "duration": "{duration}"},
      "phase_3": {"name": "{name}", "duration": "{duration}"},
      "phase_4": {"name": "{name}", "duration": "{duration}"}
    },
    "risks": ["{list}"],
    "success_criteria": ["{list}"]
  }
}
```

### Save State

The CLI automatically updates `{analysis_dir}/state.json` when stages complete.

---

## Step 4: Verify Data Saved

---
**[STOP: VERIFY_DATA_SAVED]**

Verify `{data_dir}/validation-scoring.json` exists (from 03a3).

**IF missing:** Re-run 03a3-validation-scoring.

---

## Completion Marker

```text
===========================================================
  STAGE COMPLETE: FULL_APP_ANALYSIS

  Chain ID: {chain_id}

  Summary:
    Questions Answered: 10/10
    Scope Validated: [ok]
    Complexity: {rating}
    Primary Recommendation: {approach} ({confidence}%)

  Proceeding to Stage 4: Report Generation
===========================================================

STAGE_COMPLETE:FULL_APP_ANALYSIS

```

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits the next prompt. **Do NOT analyze or generate artifacts until you run this command.**
