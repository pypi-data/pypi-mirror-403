---
stage: cross_cutting_analysis
requires: 02e-quality-gates
condition: scope == "B"
outputs: concern_state
version: 3.4.0
---

# Stage 3B: Cross-Cutting Concern Migration Analysis

## Purpose

For Cross-Cutting Concern Migration (scope = B), perform deep-dive analysis of the specific concern, assess abstraction quality, calculate blast radius, and recommend migration strategy.

---

## How Context Is Provided

The CLI manages state and provides all context. **Do not read state.json directly.**

**Available template variables:**

- `{project_path}`, `{analysis_dir}`, `{scope}`, `{context}`
- `{data_dir}` - Data folder for JSON files (`{analysis_dir}/data/`)
- `{reports_dir}` - Reports folder for MD files (`{analysis_dir}/reports/`)
- Concern type, current implementation, target implementation

**Previous artifacts required (in data/ folder):**

- `{data_dir}/tech-stack.json` - Detected technologies
- `{data_dir}/category-patterns.json` - Category patterns
- `{data_dir}/deep-dive-patterns.json` - Deep analysis results

---

## [!] MANDATORY: Read Agent Instructions First

**BEFORE PROCEEDING:**

1. Check if `AGENTS.md` exists in repository root
2. **IF EXISTS:** Read it in FULL - instructions are NON-NEGOTIABLE
3. Follow all AGENTS.md guidelines for the duration of this command execution

**Verification:** After reading AGENTS.md (if it exists), acknowledge with:
   "[ok] Read AGENTS.md v[X.X] - Following all guidelines"

**If AGENTS.md does not exist:** Proceed with default behavior.

---

{{include:ai-cache-enforcement.md}}

---

## AI Context Cache: Recall Earlier Analysis

Before analyzing cross-cutting concerns, recall cached understanding from earlier stages:

```text
# FIRST: Discover ALL cached entries (project, modules, files)
get_understanding_stats(limit=50)
# Review output to identify ALL cached targets and their scopes

# Recall project-level understanding
recall_understanding(target="project")

# Recall from ACTUAL cached paths shown in stats output
# Common examples - use paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/services")  # if exists in stats
recall_understanding(target="{project_path}/auth")      # if exists in stats

# Use cached understanding to:
# - Identify concern touch points without re-reading files
# - Understand existing patterns and abstractions
# - Identify dependencies and coupling

# AFTER cross-cutting analysis, store understanding:
store_understanding(
  scope="module",
  target="{concern_type}",
  purpose="Cross-cutting concern analysis for {concern_type}",
  importance="critical",
  key_points=["<abstraction level>", "<touch points>", "<migration complexity>"],
  gotchas=["<coupling issues>", "<breaking change risks>"],
  analysis="<detailed concern analysis and blast radius>"
)
```

---

## Step 1: Abstraction Level Assessment

Evaluate how well the current implementation is abstracted from business logic.

### Scoring Criteria

**HIGH Abstraction (Score: 7-10)**:

- Concern isolated in dedicated module/package
- Clear interfaces/abstractions between concern and business logic
- Minimal direct dependencies
- Easy to swap implementations
- **Examples**:
  - Auth via `@PreAuthorize` annotations (declarative)
  - Database via repository pattern with interfaces
  - Caching via `@Cacheable` annotations

**MEDIUM Abstraction (Score: 4-6)**:

- Concern somewhat separated but with coupling
- Some direct usage in business code
- Interfaces exist but not consistently used
- Would require refactoring to swap
- **Examples**:
  - Auth checks mixed in controllers
  - Some raw SQL queries alongside ORM
  - Cache calls sprinkled in services

**LOW Abstraction (Score: 1-3)**:

- Concern tightly coupled to business logic
- No clear separation
- Direct implementation details throughout code
- Major refactoring needed to swap
- **Examples**:
  - Auth logic embedded in every method
  - Raw SQL queries everywhere
  - Direct cache library calls in business logic

### Assessment Process

1. **Identify all touch points** where concern is used
2. **Analyze coupling** - How tightly integrated is it?
3. **Check for interfaces/abstractions** - Are there clear boundaries?
4. **Find duplicate patterns** - Use `get_duplicate_code(source_only=true)` to find similar implementations
5. **Evaluate swap difficulty** - How hard would migration be?

### Output

```text
Abstraction Assessment for {concern_type}:

Current Implementation: {current_implementation}
Abstraction Score: {score}/10
Abstraction Level: {LOW | MEDIUM | HIGH}

Touch Points Identified:
- {package/file}: {count} usages ({type of usage})
- {package/file}: {count} usages ({type of usage})
...

Abstraction Patterns Found:
- [ok] {positive pattern}
- [x] {negative pattern}
...

Migration Complexity: {LOW | MEDIUM | HIGH}

```

---

## Step 2: Blast Radius Calculation

Determine how many files would be affected by migration.

### Calculation

1. **Direct Impact** - Files that directly use the concern
   - Count files with imports/references to concern
   - Example: Files importing `JwtTokenProvider`, `SecurityConfig`

2. **Indirect Impact** - Files that depend on directly impacted files
   - Files that call methods in directly impacted files
   - Depth 1 dependencies

3. **Configuration Impact** - Config files that need updates
   - Application configs
   - Build configs (dependencies)
   - Infrastructure configs (env vars, secrets)

4. **Test Impact** - Tests that need updates
   - Unit tests for affected files
   - Integration tests
   - E2E tests

### Formula

```text
Total Affected Files = Direct + Indirect + Config + Tests

Blast Radius % = (Total Affected / Total Project Files) * 100

```

### Classification

- **Small** (< 10%): Localized change, low risk
- **Medium** (10-30%): Significant change, moderate risk
- **Large** (30-50%): Major change, high risk
- **Critical** (> 50%): Affects majority of codebase, very high risk

### Output

```text
Blast Radius Analysis:

Direct Impact: {count} files ({list key files})
Indirect Impact: {count} files
Configuration Impact: {count} files
Test Impact: {count} tests

Total Affected Files: {total} out of {project_total}
Blast Radius: {percentage}% ({SMALL | MEDIUM | LARGE | CRITICAL})

Risk Level: {LOW | MEDIUM | HIGH | VERY HIGH}

```

---

## Step 3: Migration Strategy Recommendation

Based on abstraction level and blast radius, recommend migration approach.

### Decision Matrix

| Abstraction | Blast Radius | Recommended Strategy |
| ------------- | -------------- | ---------------------- |
| HIGH | SMALL | **Direct Replacement** - Swap implementation directly |
| HIGH | MEDIUM/LARGE | **Phased Migration** - Gradual rollout with feature flags |
| MEDIUM | SMALL | **Refactor Then Replace** - Improve abstractions first |
| MEDIUM | MEDIUM/LARGE | **Strangler Pattern** - New implementation alongside old |
| LOW | SMALL | **Refactor Then Replace** - Extract to module first |
| LOW | MEDIUM/LARGE | **Strangler Pattern** - Long-term gradual migration |

### Migration Phases (50/30/15/5 Pattern)

**Phase 1 (50%)**: Foundation & Pilot

- Refactor abstractions if needed
- Set up new implementation infrastructure
- Migrate one pilot module/service
- Verify functionality in production
- Duration: 30-40% of total timeline

**Phase 2 (30%)**: Expansion

- Migrate 3-5 additional modules
- Parallel running (old + new)
- Monitor performance and issues
- Duration: 25-30% of total timeline

**Phase 3 (15%)**: Completion

- Migrate remaining modules
- Remove old implementation
- Clean up code
- Duration: 15-20% of total timeline

**Phase 4 (5%)**: Optimization & Cleanup

- Performance tuning
- Documentation
- Remove feature flags/toggle code
- Duration: 10-15% of total timeline

### Output

```text
Migration Strategy: {RECOMMENDED_STRATEGY}

Justification:
- Abstraction Level: {level}
- Blast Radius: {radius}
- Risk: {risk_level}

Migration Plan (4-Phase Approach):

Phase 1 - Foundation & Pilot (50%):
- Refactor {specific areas} to use interface
- Set up {target_implementation}
- Migrate {pilot module} (lowest risk)
- Deploy to staging, then 10% production
- Duration: {weeks/months}

Phase 2 - Expansion (30%):
- Migrate {module list}
- Feature flag: Enable new implementation for 50% traffic
- Monitor: Error rates, performance, user experience
- Duration: {weeks/months}

Phase 3 - Completion (15%):
- Migrate remaining {count} modules
- Ramp to 100% new implementation
- Deprecate old implementation
- Duration: {weeks/months}

Phase 4 - Cleanup (5%):
- Remove old {current_implementation} code
- Remove feature flags
- Optimize performance
- Update documentation
- Duration: {weeks/months}

Total Estimated Timeline: {total_timeline}

```

---

## Step 4: Risk Assessment

Identify and categorize risks.

### Risk Categories

**Technical Risks**:

- Breaking changes in new implementation
- Performance degradation
- Data migration issues
- Integration incompatibilities

**Business Risks**:

- User experience disruption
- Downtime during migration
- Training requirements
- Vendor lock-in (if switching to SaaS)

**Operational Risks**:

- Monitoring gaps during transition
- Rollback complexity
- Support burden (dual systems)
- Cost overruns

### Output

```text
Risk Assessment:

HIGH Risks:
- {risk}: {description} (Mitigation: {mitigation})
- {risk}: {description} (Mitigation: {mitigation})

MEDIUM Risks:
- {risk}: {description} (Mitigation: {mitigation})
- {risk}: {description} (Mitigation: {mitigation})

LOW Risks:
- {risk}: {description} (Mitigation: {mitigation})

```

---

## Step 5: Effort Estimation

Estimate development effort for migration.

### Factors

1. **Abstraction Refactoring** (if needed)
   - LOW abstraction: 2-4 weeks
   - MEDIUM abstraction: 1-2 weeks
   - HIGH abstraction: 0 weeks

2. **New Implementation Setup**
   - Infrastructure setup: 1-2 weeks
   - Integration development: 2-4 weeks
   - Testing setup: 1-2 weeks

3. **Migration Execution**
   - Per module migration: 1-3 days each
   - Total modules: {count}

4. **Testing & Validation**
   - Unit testing: 1-2 weeks
   - Integration testing: 1-2 weeks
   - E2E testing: 1 week

5. **Documentation & Training**
   - Technical docs: 3-5 days
   - Runbooks: 2-3 days
   - Team training: 1-2 days

### Output

```text
Effort Estimation:

Development Effort:
- Abstraction Refactoring: {weeks} weeks
- New Implementation: {weeks} weeks
- Migration Execution: {weeks} weeks
- Testing: {weeks} weeks
- Documentation: {weeks} weeks

Total: {total_weeks} weeks ({total_days} person-days)

Team Size Recommendation: {developers} developers
Calendar Duration: {months} months (with {team_size} team)

```

---

## Step 6: Success Criteria & Metrics

Define how to measure migration success.

```text
Success Criteria:

Functional:
- [ ] All {endpoints/features} working with new implementation
- [ ] 100% test coverage for migration code
- [ ] Zero data loss
- [ ] Feature parity with old implementation

Performance:
- [ ] Response time: < {threshold}ms (same or better)
- [ ] Throughput: {requests/sec} (same or better)
- [ ] Error rate: < 0.1%

Operational:
- [ ] Monitoring dashboards operational
- [ ] Alerting configured
- [ ] Rollback procedure tested
- [ ] Documentation complete

Business:
- [ ] Zero customer-reported issues
- [ ] No service interruptions
- [ ] Team trained on new system

```

---

## Output State

```json
{
  ...previous_state,
  "stage": "cross_cutting_analysis",
  "timestamp": "2025-11-14T11:00:00Z",
  "stages_complete": [..., "cross_cutting_analysis"],
  "concern_analysis": {
    "concern_type": "Authentication/Authorization",
    "current": "Custom JWT with bcrypt",
    "target": "Okta",
    "abstraction": {
      "score": 6,
      "level": "MEDIUM",
      "touch_points": 45,
      "patterns": [...]
    },
    "blast_radius": {
      "direct_impact": 15,
      "indirect_impact": 30,
      "config_impact": 5,
      "test_impact": 28,
      "total_affected": 78,
      "percentage": 32,
      "classification": "LARGE"
    },
    "migration_strategy": "Strangler Pattern",
    "migration_phases": {
      "phase_1": "Foundation & Pilot (50%): 4 weeks",
      "phase_2": "Expansion (30%): 3 weeks",
      "phase_3": "Completion (15%): 2 weeks",
      "phase_4": "Cleanup (5%): 1 week",
      "total": "10 weeks"
    },
    "risks": [...],
    "effort": {
      "total_weeks": 10,
      "total_person_days": 50,
      "team_size": 2,
      "calendar_months": 3
    }
  }
}

```

---

## Completion Marker

```text
STAGE_COMPLETE:CROSS_CUTTING

```

The CLI automatically updates `{analysis_dir}/state.json` when stages complete.

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits the next prompt. **Do NOT generate artifacts until you run this command.**
