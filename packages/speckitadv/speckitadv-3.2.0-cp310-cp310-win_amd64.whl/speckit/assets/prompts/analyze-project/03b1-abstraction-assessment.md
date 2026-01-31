---
stage: cross_cutting_assessment
requires: 02e-quality-gates
condition: scope == "B"
outputs: abstraction_blast_radius
version: 3.4.0
---

{{include:strict-execution-mode.md}}

**Note:** Analysis-only substage - no files created. Final data saved via CLI (see Step 5).

---

# Stage 3B-1: Abstraction Assessment & Blast Radius

## Purpose

For Cross-Cutting Concern Migration, assess the abstraction level of the current implementation and calculate the blast radius of migration.

---

## AI Context Cache: Check Cached Understanding

Before analyzing the concern, check for cached understanding:

```text
# Check if this concern was already analyzed in a previous session
recall_understanding(target="{concern_type}")
recall_understanding(target="project")

# IF found AND fresh: Use cached abstraction analysis
# IF not found: Proceed with full assessment, then store findings

# AFTER abstraction assessment completes, store understanding:
store_understanding(
  scope="module",
  target="{concern_type}",
  purpose="Abstraction assessment for {concern_type} migration",
  importance="critical",
  key_points=["<abstraction score>", "<interface patterns>", "<coupling level>"],
  gotchas=["<abstraction issues found>", "<high-impact files>"],
  analysis="<detailed blast radius and consumer analysis>"
)
```

---

## Discovery Tools

{{include:analyze-civyk-repoix-discovery.md}}

**Assessment-specific tools:**

- `analyze_impact(fqn, depth=3)` - calculate blast radius
- `get_callers(fqn, depth=2)` - find all consumers
- `get_references(fqn)` - usage patterns

---

## How Context Is Provided

The CLI manages state and provides all context. **Do not read state.json directly.**

Values available (already substituted by CLI):

- Project path, analysis directory, scope (must be "B"), context
- Concern type, current implementation, target implementation

---

## Step 1: Identify Concern Files

Locate all files related to the specified concern.

---
**[STOP: IDENTIFY_CONCERN_FILES]**

Search for files matching the concern type: **{concern_type}**

**Search Patterns by Concern Type:**

| Concern | Search Patterns |
|---------|-----------------|
| Authentication | `*Auth*`, `*Login*`, `*Token*`, `*Session*`, `*Security*`, `*JWT*`, `*OAuth*` |
| Database | `*Repository*`, `*DAO*`, `*Entity*`, `*Model*`, `*Migration*`, `*Schema*` |
| Caching | `*Cache*`, `*Redis*`, `*Memcached*`, `@Cacheable`, `@Cached` |
| Logging | `*Logger*`, `*Log*`, `*Audit*`, `logging.*`, `log4j*`, `winston*` |
| Message Queue | `*Queue*`, `*Message*`, `*Event*`, `*Kafka*`, `*RabbitMQ*`, `*SQS*` |
| API Gateway | `*Gateway*`, `*Proxy*`, `*Route*`, `*Middleware*` |

**Output:**

```text
Concern File Identification: {concern_type}

Files Found: {count}
  Core Implementation:
    - {file1} ({lines} lines)
    - {file2} ({lines} lines)

  Configuration:
    - {config1}
    - {config2}

  Consumers/Callers:
    - {caller1} ({usage_count} usages)
    - {caller2} ({usage_count} usages)

```

Store in: `$CONCERN_FILES`

---

## Step 2: Abstraction Level Assessment

Evaluate how well the concern is abstracted from business logic.

---
**[STOP: ASSESS_ABSTRACTION]**

For each concern file, analyze:

1. **Interface Presence:**
   - Does an interface/abstract class exist?
   - Is dependency injection used?

2. **Implementation Isolation:**
   - Is implementation in a dedicated module/package?
   - Are there clear boundaries?

3. **Consumer Coupling:**
   - Do consumers reference interfaces or concrete classes?
   - Are there direct library calls in business code?

4. **Configuration Externalization:**
   - Are settings externalized?
   - Is the concern configurable without code changes?

**Scoring Matrix:**

| Criterion | HIGH (7-10) | MEDIUM (4-6) | LOW (1-3) |
|-----------|-------------|--------------|-----------|
| Interface | Interface exists, all consumers use it | Interface exists, partial use | No interface |
| Isolation | Dedicated package/module | Partial separation | Mixed with business |
| Coupling | Loose (DI) | Mixed | Tight coupling |
| Config | Fully externalized | Partial | Hardcoded |

**Calculate Score:**

```text
abstraction_score = AVG(interface, isolation, coupling, config)

```

**Output Format:**

```text
Abstraction Assessment: {concern_type}

Current Implementation: {current_implementation}

Scores:
  Interface Usage:     {score}/10
  Implementation Isolation: {score}/10
  Consumer Coupling:   {score}/10
  Configuration:       {score}/10

  ---------------------------------
  OVERALL SCORE: {average}/10
  LEVEL: {HIGH | MEDIUM | LOW}
  ---------------------------------

Abstraction Patterns Found:
  [ok] {positive patterns}

Abstraction Issues:
  [x] {negative patterns with file:line}
```

---

## Step 3: Blast Radius Calculation

Calculate how many files would be affected by the migration.

---
**[STOP: CALCULATE_BLAST_RADIUS]**

**Count affected files:**

1. **Direct Impact** - Files that directly use the concern:

   ```text
   Count files with imports/references to:
   - Concern implementation classes
   - Concern-specific annotations
   - Concern configuration

   ```

2. **Indirect Impact** - Files that depend on directly impacted files:

   ```text
   For each directly impacted file:
     Count files that import/call it

   ```

3. **Configuration Impact**:

   ```text
   Count config files referencing the concern:
   - Application configs
   - Build files (dependencies)
   - Infrastructure (env vars, secrets)

   ```

4. **Test Impact**:

   ```text
   Count test files for:
   - Concern unit tests
   - Integration tests using concern
   - E2E tests affected

   ```

**Calculate:**

```text
total_affected = direct + indirect + config + tests
blast_radius_percentage = (total_affected / total_project_files) x 100

```

**Classification:**

```text
< 10%:  SMALL (Low risk, localized change)
10-30%: MEDIUM (Moderate risk, significant change)
30-50%: LARGE (High risk, major change)
> 50%:  CRITICAL (Very high risk, affects majority)

```

**Output Format:**

```text
Blast Radius Analysis: {concern_type}

Impact Breakdown:
  Direct Impact:      {count} files
  Indirect Impact:    {count} files
  Configuration:      {count} files
  Test Impact:        {count} test files

  ---------------------------------
  TOTAL AFFECTED: {total} / {project_total} files
  BLAST RADIUS: {percentage}%
  CLASSIFICATION: {SMALL|MEDIUM|LARGE|CRITICAL}
  ---------------------------------

High-Impact Files (top 10):
  1. {file}: {impact_count} dependents
  2. {file}: {impact_count} dependents
  ...

```

---

## Step 4: Compile Assessment Data

```json
{
  "abstraction_assessment": {
    "concern_type": "{type}",
    "current_implementation": "{current}",
    "target_implementation": "{target}",
    "files": {
      "core": ["{list}"],
      "config": ["{list}"],
      "consumers": ["{list}"],
      "total": {count}
    },
    "abstraction": {
      "interface_score": {score},
      "isolation_score": {score},
      "coupling_score": {score},
      "config_score": {score},
      "overall_score": {score},
      "level": "{HIGH|MEDIUM|LOW}",
      "patterns_found": ["{positive}"],
      "issues_found": [
        {"issue": "{description}", "location": "{file:line}"}
      ]
    },
    "blast_radius": {
      "direct": {count},
      "indirect": {count},
      "config": {count},
      "tests": {count},
      "total": {count},
      "percentage": {value},
      "classification": "{SMALL|MEDIUM|LARGE|CRITICAL}",
      "high_impact_files": ["{list}"]
    }
  }
}
```

---

## Step 5: Save Assessment Data

Save the assessment data to the data folder using stdin mode:

```powershell
@"
{
  "abstraction_assessment": { ... full JSON from Step 4 ... }
}
"@ | speckitadv write-data abstraction-assessment.json --stage=03b1-abstraction-assessment --stdin
```

---

## Output Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 03b1-abstraction-assessment

  Concern: {concern_type}
  Current: {current_implementation}
  Target: {target_implementation}

  Abstraction: {score}/10 ({level})
  Blast Radius: {percentage}% ({classification})

  Proceeding to Migration Strategy...
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
