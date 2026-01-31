---
stage: full_app_validation
requires: 03a2-questions-part2
condition: scope == "A"
outputs: scoring_complete
version: 3.4.0
---

{{include:strict-execution-mode.md}}

**Note:** Analysis-only substage - no files created. Final data saved via CLI (see Step 5).

---

# Stage 3A-3: Scope Validation & Feasibility Scoring

## Purpose

Validate the modernization scope with the user and calculate complexity/feasibility scores for different modernization approaches.

---

## How Context Is Provided

The CLI manages state and provides all context. **Do not read state.json directly.**

Values available (already substituted by CLI):

- Project path, analysis directory, scope, context
- Q1-Q10 responses from previous stages are in artifacts

---

## Step 1: Scope Validation with User

Display the scope summary and ask user to confirm what's IN and OUT of scope.

---
**[STOP: USER_INPUT_REQUIRED - SCOPE_VALIDATION]**

Present this confirmation EXACTLY as written:

```text
============================================================
SCOPE VALIDATION

Based on your answers, here's what will be modernized.
Please confirm what's IN SCOPE and OUT OF SCOPE.

-------------------------------------------------------------
IN SCOPE (Will be modernized):
-------------------------------------------------------------

  {IF q1 != skip: [ok] Language: {current} -> {target}}
  {IF q2 != skip: [ok] Database: {current} -> {target}}
  {IF q3 != skip && q3 != none: [ok] Message Bus: {current} -> {target}}
  {IF q4 != skip: [ok] Build Tool: {current} -> {target}}
  {IF q5 != skip: [ok] Deployment: {current} -> {target}}
  {IF q6 != skip && q6 != none: [ok] IaC: {current} -> {target}}
  {IF q7 != skip: [ok] Containerization: {current} -> {target}}
  {IF q8 != skip: [ok] Observability: {current} -> {target}}
  {IF q9 != skip: [ok] Security/Auth: {current} -> {target}}
  {IF q10 != skip: [ok] Testing: {current} -> {target}}

-------------------------------------------------------------
OUT OF SCOPE (Will keep as-is):
-------------------------------------------------------------

  {List components where user typed "skip" or kept current}

-------------------------------------------------------------

Is this scope correct?

  [Y] Yes, proceed with this scope
  [N] No, I need to change something

Your choice [Y/N]: ___
============================================================

```

**WAIT for user response. DO NOT proceed until answered.**

---

### Handle Scope Changes

**IF user chooses [N]:**

```text
Which question(s) do you want to change?
Enter question numbers separated by commas (e.g., "1, 5, 9"):
___

```

**For each question to change:**

1. Re-display that question
2. Wait for new response
3. Update the stored value

**Loop until user confirms scope with [Y].**

---

## Step 2: Complexity Scoring

Calculate complexity scores for the modernization based on Stage 2 findings and user preferences.

### Complexity Factors

| Factor | Weight | Score Range | Calculation |
|--------|--------|-------------|-------------|
| Codebase Size | 15% | 1-10 | Based on LOC |
| Tech Stack Change | 25% | 1-10 | Distance from current to target |
| Database Migration | 20% | 1-10 | Schema complexity + data volume |
| Integration Count | 15% | 1-10 | External systems to update |
| Test Coverage Gap | 10% | 1-10 | Based on current coverage |
| Security Changes | 15% | 1-10 | Auth mechanism changes |

### Calculate Each Factor

**Codebase Size Score:**

```text
IF LOC < 10,000: Score = 2
IF LOC 10,000-50,000: Score = 4
IF LOC 50,000-100,000: Score = 6
IF LOC 100,000-500,000: Score = 8
IF LOC > 500,000: Score = 10

```

**Tech Stack Change Score:**

```text
IF keeping same language: Score = 1
IF minor version upgrade: Score = 2
IF major version upgrade: Score = 4
IF same family language: Score = 6
IF different language: Score = 8
IF different paradigm: Score = 10

```

**Database Migration Score:**

```text
IF keeping same DB: Score = 1
IF same DB type upgrade: Score = 3
IF same DB type different vendor: Score = 5
IF different DB type (SQL->SQL): Score = 7
IF different DB paradigm (SQL->NoSQL): Score = 10

```

**Integration Count Score:**

```text
Score = MIN(10, integration_count)

```

**Test Coverage Gap Score:**

```text
Score = 10 - (current_coverage / 10)
Example: 40% coverage -> Score = 6

```

**Security Changes Score:**

```text
IF keeping current auth: Score = 1
IF upgrading same approach: Score = 3
IF switching to standard (OAuth): Score = 5
IF switching to external provider: Score = 7
IF complete auth overhaul: Score = 9

```

### Calculate Overall Complexity

```text
Overall = (Size x 0.15) + (Stack x 0.25) + (DB x 0.20) +
          (Integration x 0.15) + (Testing x 0.10) + (Security x 0.15)

```

**Complexity Rating:**

```text
1.0-3.0: LOW - Straightforward modernization
3.1-5.0: MEDIUM - Moderate effort required
5.1-7.0: HIGH - Significant effort and risk
7.1-10.0: VERY HIGH - Major undertaking, consider phasing

```

---

## Step 3: Feasibility Scoring

Calculate feasibility for different modernization approaches.

### Approach 1: Inline Upgrade

**Factors (% influence on score):**

- Abstraction level from Stage 2 (30%)
- Framework availability for target (20%)
- Team familiarity (assumed moderate - 20%)
- Breaking changes in upgrades (30%)

**Formula:**

```text
inline_feasibility = 100 - (complexity_score x 10) + abstraction_bonus

abstraction_bonus:
  HIGH abstraction: +20
  MEDIUM abstraction: +10
  LOW abstraction: 0

```

### Approach 2: Greenfield Rewrite

**Factors:**

- Complexity of existing system (inverse)
- Feature count from Stage 2
- Data migration complexity
- Timeline pressure (assumed moderate)

**Formula:**

```text
greenfield_feasibility = 50 + (abstraction_penalty) - (feature_count / 10)

abstraction_penalty:
  LOW abstraction: +30 (easier to rewrite than refactor)
  MEDIUM abstraction: +15
  HIGH abstraction: 0 (refactor is easier than rewrite)

```

### Approach 3: Hybrid (Strangler Fig)

**Factors:**

- Module independence
- API surface area
- Deployment flexibility
- Data isolation

**Formula:**

```text
hybrid_feasibility = (inline_feasibility + greenfield_feasibility) / 2 + 10
(Hybrid gets bonus for flexibility)

```

---

## Step 4: Display Scoring Summary

```text
===========================================================
COMPLEXITY & FEASIBILITY ANALYSIS
===========================================================

COMPLEXITY BREAKDOWN
-------------------------------------------------------------
  Codebase Size:      {score}/10 ({LOC} LOC)
  Tech Stack Change:  {score}/10 ({current} -> {target})
  Database Migration: {score}/10 ({current} -> {target})
  Integration Count:  {score}/10 ({count} integrations)
  Test Coverage Gap:  {score}/10 ({coverage}% current)
  Security Changes:   {score}/10 ({current} -> {target})

  -------------------------------------------------
  OVERALL COMPLEXITY: {score}/10 ({rating})
  -------------------------------------------------

FEASIBILITY SCORES
-------------------------------------------------------------
  Inline Upgrade:     {score}% feasible
  Greenfield Rewrite: {score}% feasible
  Hybrid/Strangler:   {score}% feasible * (recommended if > 70%)

RECOMMENDATION PREVIEW
-------------------------------------------------------------
  {Primary approach based on highest feasibility}
  Confidence: {percentage}%

===========================================================

```

---

## Step 5: Save Scoring Data

Save the complexity and feasibility scores to the data folder using stdin mode:

```powershell
@"
{
  "schema_version": "3.1.0",
  "stage": "validation_scoring",
  "timestamp": "{ISO-8601}",
  "scope_validated": true,
  "complexity": {
    "codebase_size": {"score": {n}, "details": "{LOC} LOC"},
    "tech_stack_change": {"score": {n}, "details": "{current} -> {target}"},
    "database_migration": {"score": {n}, "details": "{current} -> {target}"},
    "integration_count": {"score": {n}, "details": "{count} integrations"},
    "test_coverage_gap": {"score": {n}, "details": "{coverage}% current"},
    "security_changes": {"score": {n}, "details": "{current} -> {target}"},
    "overall_score": {n},
    "rating": "{LOW|MEDIUM|HIGH|VERY HIGH}"
  },
  "feasibility": {
    "inline_upgrade": {n},
    "greenfield_rewrite": {n},
    "hybrid_approach": {n},
    "recommended_approach": "{approach}",
    "confidence_percentage": {n}
  }
}
"@ | speckitadv write-data validation-scoring.json --stage=03a3-validation-scoring --stdin
```

---

## Output Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 03a3-validation-scoring

  Scope Validated: [ok]
  Complexity Score: {score}/10 ({rating})
  Top Feasibility: {approach} ({score}%)

  Proceeding to Final Recommendations...
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
