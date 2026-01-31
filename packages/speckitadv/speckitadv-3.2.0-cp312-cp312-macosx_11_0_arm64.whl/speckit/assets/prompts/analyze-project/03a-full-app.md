---
stage: full_application_analysis
requires: 02e-quality-gates
condition: scope == "A"
outputs: full_app_state
version: 3.4.0
---

<!-- markdownlint-disable MD046 -->

# Stage 3A: Full Application Modernization Analysis

## Purpose

For Full Application Modernization (scope = A), ask 10 progressive questions about target stack and perform comprehensive modernization assessment with scoring matrices.

---

## How Context Is Provided

The CLI manages state and provides all context. **Do not read state.json directly.**

**Available template variables:**

- `{project_path}`, `{analysis_dir}`, `{scope}`, `{context}`
- `{data_dir}` - Data folder for JSON files (`{analysis_dir}/data/`)
- `{reports_dir}` - Reports folder for MD files (`{analysis_dir}/reports/`)

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

## AI Context Cache: Check Cached Understanding

{{include:ai-cache-enforcement.md}}

Before reading source files for analysis, check what's already cached:

```text
# Check cache statistics to see what's available
get_understanding_stats(limit=50)

# Recall project-level and module-level understanding from earlier stages
recall_understanding(target="project")
recall_understanding(target="{project_path}/auth")      # if exists in stats
recall_understanding(target="{project_path}/api")       # if exists in stats

# Use cached understanding to:
# - Skip redundant file reads (saves 70-85% tokens)
# - Leverage patterns and gotchas discovered in deep-dive phase
# - Inform modernization recommendations based on existing analysis
```

**[!] CRITICAL: If you read additional source files during this stage, you MUST follow the 1:1 read:store enforcement from the include above.**

---

## [TARGET] CONSISTENCY CHECKPOINT

**Expected Behavior (MUST be identical across all runs):**

1. Present all 10 modernization questions to user in order
2. Wait for user response for each question
3. Record each answer in state field: `modernization_preferences`
4. Validate each answer matches question's expected options
5. If invalid, re-prompt with error message for that question
6. If valid, proceed to next question
7. After all 10 questions, perform scope validation
8. Calculate complexity and feasibility scores
9. Generate recommendations

**This behavior MUST be consistent regardless of:**

- AI model being used (GPT-4, Claude Sonnet 4, Gemini, etc.)
- Time of day
- Previous conversation context
- Inferred user preferences
- Industry best practices
- Obvious answers from code analysis

**Deviation from this behavior is a CRITICAL ERROR.**

---

## [!] CRITICAL: Questionnaire Execution Rules

**YOU MUST FOLLOW ALL RULES BELOW WHEN ASKING THE 10 MODERNIZATION QUESTIONS:**

### Presentation Rules

1. **Ask questions EXACTLY as written** - Do NOT rephrase, simplify, or modify wording
2. **Present ALL options** - Do NOT remove or combine choices
3. **One question at a time** - Complete each question before moving to next
4. **Ask ALL 10 questions** - Do NOT skip any questions regardless of previous answers

### No Assumptions Policy

- **Wait for user response** - Do NOT assume or guess answers
- **No shortcuts** - Do NOT skip questions even if answer seems obvious from code or industry practice
- **Validate input** - If user provides invalid choice, re-prompt with error message

**Even if the answer seems obvious, you think you know what the user wants, or industry best practices suggest a choice - YOU MUST STILL ASK THE QUESTION EXPLICITLY.**

### Clarification Protocol

**IF in doubt about ANY aspect of the user's answer:**

1. **STOP** immediately
2. **ASK** for clarification using this format:
3. **WAIT** for user response
4. **DO NOT** proceed with assumptions

**Clarification template:**

```text
[!] CLARIFICATION NEEDED

Question [N]: [question topic]

You said: "[user's answer]"
I'm unsure about: "[specific ambiguity]"

Options:
- [A] [Interpretation 1]
- [B] [Interpretation 2]
- [C] Other (please specify)

Your choice: ___

```

**REMEMBER**: Ask 5 clarification questions rather than make 1 wrong assumption.

**IF you modify questions, skip questions, or assume answers - this is a CRITICAL ERROR and workflow must restart.**

---

## Step 1: 10 Progressive Modernization Questions

**[!] CRITICAL - READ BEFORE PROCEEDING:**

You MUST ask ALL 10 questions below EXACTLY as written. Do NOT:

- Modify, rephrase, or simplify any question text
- Skip any questions (even if answer seems obvious)
- Combine or remove any options
- Assume answers from code analysis or context
- Change the order of questions

**IF YOU MODIFY QUESTIONS OR SKIP QUESTIONS, THIS IS A CRITICAL ERROR.**

Ask user about target modernization stack based on detected legacy stack.

### Detection Flags (for conditional logic)

Based on file analysis, set these flags:

- `HAS_MESSAGE_BUS` - true if Kafka, RabbitMQ, Azure SB, AWS SQS, Redis Pub/Sub detected
- `HAS_OBSERVABILITY` - true if logging frameworks, monitoring configs, APM tools detected
- `IS_TRADITIONAL_DEPLOYMENT` - derived from Q5 answer

---

### Questions

**IMPORTANT**: Present each question EXACTLY as written below. Copy the text verbatim - do not paraphrase or modify.

```text
MODERNIZATION PREFERENCES:

Based on detected legacy stack, please answer the following:

1. Target Language/Framework:
   Current: [detected language/framework]
   Options:
   - [A] [Same language, latest LTS version]
   - [B] [Alternative popular option]
   - [C] Other (please specify)
   Your choice: ___

2. Target Database:
   Current: [detected or "Unknown - please specify"]
   Options:
   - [A] [Same database vendor, latest version]
   - [B] PostgreSQL [latest LTS]
   - [C] MongoDB [latest stable]
   - [D] Other (please specify)
   Your choice: ___

```

3\. Message Bus/Queue [CONDITIONAL]:
   Current: [detected or "None detected"]

   **[!] CRITICAL**: Present this question WITH ALL OPTIONS as written. Do NOT skip, modify, or simplify.

   **IF** `!HAS_MESSAGE_BUS` (no message queue detected):
      Mark as **[OPTIONAL - Not detected in legacy code]**
      Add educational note (present EXACTLY as written):

      ```text
      Since your legacy app doesn't use message queues, you can skip this.
      However, modernization could benefit from async messaging for:
      - Background job processing
      - Event-driven architecture
      - Decoupling services

      Options:
      - [A] None / Not needed - Keep simple
      - [B] Apache Kafka - Industry standard, high throughput
      - [C] RabbitMQ - Feature-rich, easier learning curve
      - [D] Redis Pub/Sub - Lightweight, good if already using Redis
      - [E] Cloud-native (Azure Service Bus / AWS SQS / Google Pub/Sub)
      - [F] Other (please specify)
      Your choice (or press Enter to skip): ___

      ```

   **ELSE** (message queue detected):

      ```text
      Options:
      - [A] Keep current ([detected message bus])
      - [B] Apache Kafka
      - [C] RabbitMQ
      - [D] Redis Pub/Sub
      - [E] Cloud-native (Azure Service Bus / AWS SQS / Google Pub/Sub)
      - [F] Other (please specify)
      Your choice: ___

      ```

4\. Package Manager:
   Current: [detected]
   Options:

- [A] Keep current ([detected])
- [B] [Alternative for stack]
- [C] Other (please specify)
   Your choice: ___

5\. Deployment Target:
   Current: [detected or "Unknown"]
   Options:

- [A] Dedicated server (traditional VM/bare metal)
- [B] Kubernetes (cloud-agnostic container orchestration)
- [C] Azure (App Service, AKS, Container Apps, Container Instances)
- [D] AWS (ECS, EKS, Elastic Beanstalk, Lambda)
- [E] Google Cloud Platform (GKE, Cloud Run, App Engine)
- [F] OpenShift (enterprise Kubernetes distribution)
- [G] Other (please specify)
   Your choice: ___

   **Store choice**:
- Set `IS_TRADITIONAL_DEPLOYMENT = true` if user selects **[A]** (Dedicated server)
- Set `IS_TRADITIONAL_DEPLOYMENT = false` if user selects **[B], [C], [D], [E], [F]** (any cloud/container platform)
- If user selects **[G] Other**, ask clarifying question: "Is this a cloud/container platform (Kubernetes, Docker, etc.)?"
  - If yes -> Set `IS_TRADITIONAL_DEPLOYMENT = false`
  - If no -> Set `IS_TRADITIONAL_DEPLOYMENT = true`

6\. Infrastructure as Code (IaC) [CONDITIONAL - Based on Q5 Answer]:

   **[!] CRITICAL**: Present this question WITH ALL OPTIONS as written (when applicable). Do NOT skip, modify, or simplify.

   **CRITICAL LOGIC: Check the user's answer to Question 5 above.**

   **IF user selected [A] "Dedicated server" in Question 5**:
      Display this message and SKIP to Question 8:

      ```text
      [SKIPPED - Not applicable for traditional deployment]

      Note: Infrastructure as Code is typically used with cloud deployments.
      For traditional deployments, consider:
      - Deployment scripts (bash/PowerShell)
      - Configuration management (Ansible, Puppet, Chef)
      - Windows DSC (for Windows Server)

      If you migrate to cloud in the future, IaC becomes relevant.

      ```

   **ELSE IF user selected [B], [C], [D], [E], or [F] in Question 5** (Kubernetes, Azure, AWS, GCP, OpenShift):
      **ASK this question**:

      ```text
      Infrastructure as Code (IaC):
      Options:
      - [A] Terraform (cloud-agnostic)
      - [B] Helm charts (for Kubernetes)
      - [C] Azure ARM templates / Bicep (if chose Azure)
      - [D] AWS CloudFormation (if chose AWS)
      - [E] Google Cloud Deployment Manager (if chose GCP)
      - [F] Ansible / Puppet / Chef
      - [G] None / Manual deployment
      - [H] Other (please specify)
      Your choice: ___

      ```

   **ELSE IF user selected [G] "Other" in Question 5**:
      - If they answered "yes" to the clarifying question (is cloud/container platform) -> **ASK this question** (same as above)
      - If they answered "no" -> **SKIP to Question 8** (same skip message as [A])

7\. Containerization Strategy [CONDITIONAL - Based on Q5 Answer]:

   **[!] CRITICAL**: Present this question WITH ALL OPTIONS as written (when applicable). Do NOT skip, modify, or simplify.

   **CRITICAL LOGIC: Check the user's answer to Question 5 above.**

   **IF user selected [A] "Dedicated server" in Question 5**:
      Display this message and SKIP to Question 8:

      ```text
      [SKIPPED - Not applicable for traditional deployment]

      Note: Containerization requires migrating away from traditional servers.
      Benefits of containerization:
      - Consistent environments (dev/test/prod)
      - Easier scaling and orchestration
      - Cloud portability

      This becomes relevant if you choose cloud deployment in the future.

      ```

   **ELSE IF user selected [B], [C], [D], [E], or [F] in Question 5** (Kubernetes, Azure, AWS, GCP, OpenShift):
      **ASK this question**:

      ```text
      Containerization Strategy:
      Options:
      - [A] Docker containers only
      - [B] Docker + Kubernetes orchestration
      - [C] Docker + Docker Compose (development)
      - [D] No containerization
      - [E] Other (please specify)
      Your choice: ___

      ```

   **ELSE IF user selected [G] "Other" in Question 5**:
      - If they answered "yes" to the clarifying question (is cloud/container platform) -> **ASK this question** (same as above)
      - If they answered "no" -> **SKIP to Question 8** (same skip message as [A])

8\. Observability Stack [CONDITIONAL]:
   Current: [detected or "None detected"]

   **[!] CRITICAL**: Present this question WITH ALL OPTIONS as written. Do NOT skip, modify, or simplify.

   **IF** `!HAS_OBSERVABILITY` (no structured logging/monitoring detected):
      Mark as **[OPTIONAL - Not detected in legacy code]**
      Add educational note (present EXACTLY as written):

      ```text
      No structured observability stack detected in legacy code.
      Modern observability includes:
      - Structured logging (JSON logs, log aggregation)
      - Metrics collection (application and infrastructure)
      - Distributed tracing (request flow across services)
      - Dashboards and alerting

      Options:
      - [A] ELK Stack (Elasticsearch, Logstash, Kibana) - Self-hosted
      - [B] Prometheus + Grafana - Cloud-native, Kubernetes-friendly
      - [C] Azure Monitor / Application Insights (if chose Azure)
      - [D] AWS CloudWatch + X-Ray (if chose AWS)
      - [E] Google Cloud Operations (if chose GCP)
      - [F] OpenTelemetry (vendor-neutral, future-proof)
      - [G] Datadog / New Relic (commercial SaaS, turnkey)
      - [H] Basic logging only (not recommended for production)
      - [I] Other (please specify)
      Your choice (or press Enter to skip): ___

      ```

   **ELSE** (observability stack detected):

      ```text
      Options:
      - [A] Keep current ([detected stack])
      - [B] ELK Stack (Elasticsearch, Logstash, Kibana)
      - [C] Prometheus + Grafana
      - [D] Azure Monitor / Application Insights
      - [E] AWS CloudWatch + X-Ray
      - [F] Google Cloud Operations
      - [G] OpenTelemetry (vendor-neutral)
      - [H] Datadog / New Relic (commercial SaaS)
      - [I] Other (please specify)
      Your choice: ___

      ```

9\. Security & Authentication:
   Current: [detected from code or "Unknown"]
   Options:

- [A] OAuth 2.0 / OpenID Connect
- [B] JWT tokens
- [C] SAML 2.0
- [D] API Keys
- [E] Mutual TLS (mTLS)
- [F] Keep current auth mechanism
- [G] Other (please specify)
   Your choice: ___

10\. Testing Strategy:
    Current: [detected test coverage or "No tests detected"]
    Target:
    - [A] Unit tests only (minimum viable)
    - [B] Unit + Integration tests
    - [C] Unit + Integration + E2E tests (comprehensive)
    - [D] Unit + Integration + E2E + Contract tests (full suite)
    - [E] Minimal testing (not recommended)
    Your choice: ___

**Store all responses** in state as `modernization_preferences`.

---

## Step 1.1: Modernization Scope Validation

**CRITICAL**: Before proceeding to scoring, validate scope boundaries.

**Purpose**: Ensure we only modernize components the user explicitly wants to change.

### Validation Logic

For each of the 10 modernization questions, apply this logic:

```text
IF user provided EXPLICIT answer (selected option with specific technology):
  -> Component is IN SCOPE for modernization
  -> Store as explicit target in state
  -> Include in complexity scoring
  -> Include in migration planning

IF user pressed Enter / skipped / provided NO answer:
  -> Component is OUT OF SCOPE
  -> Store as "Use existing as-is" in state
  -> EXCLUDE from complexity scoring (no migration cost)
  -> Document as "Out of Scope - Keep existing [component] as-is" in recommendations

IF answer is ambiguous or unclear:
  -> STOP and ask clarifying question
  -> Wait for explicit confirmation
  -> Do NOT assume or guess

```

### Component-by-Component Validation

**Run through each question systematically and record:**

#### Q1: Target Language/Framework

```text
User answer: [record exact answer]
Scope: [IN SCOPE - explicit target: X] OR [OUT OF SCOPE - no target provided]
Action: [Full migration to X] OR [Keep existing language/framework as-is]

```

#### Q2: Target Database

```text
User answer: [record exact answer]
Scope: [IN SCOPE - explicit target: X] OR [OUT OF SCOPE - no target provided]
Action: [Database migration to X] OR [Keep existing database as-is]

```

#### Q3: Message Bus/Queue

```text
User answer: [record exact answer]
Was marked OPTIONAL: [Yes/No]
Scope: [IN SCOPE - explicit target: X] OR [OUT OF SCOPE - user skipped/no answer]
Action: [Add/migrate messaging to X] OR [No messaging changes, keep existing if any]

```

#### Q4-Q10: [Similar validation for remaining questions]

### Output Scope Summary

After validation, display summary:

```text
=== MODERNIZATION SCOPE VALIDATION ===

Components IN SCOPE (explicit targets provided by user):
  [ok] Language/Framework: [target]
  [ok] Database: [target]
  [ok] Deployment: [target]

Components OUT OF SCOPE (no targets, use existing as-is):
  * Message Bus: Keep existing [current implementation] as-is (user skipped)
  * Observability: Keep existing logging/monitoring as-is (user skipped)
  * IaC: Not applicable (traditional deployment)

Validation Status: [ok] PASSED
Ready to proceed with complexity scoring for IN SCOPE components only.

```

### Store in State

```json
{
  "modernization_scope": {
    "in_scope": [
      {"component": "language", "current": "...", "target": "...", "explicit": true},
      {"component": "database", "current": "...", "target": "...", "explicit": true}
    ],
    "out_of_scope": [
      {"component": "message_bus", "current": "None", "reason": "User skipped question (optional)", "action": "No changes"},
      {"component": "observability", "current": "Basic logging", "reason": "User provided no answer", "action": "Keep as-is"}
    ],
    "validation_passed": true
  }
}

```

---

## Step 2: Modernization Complexity Scoring

Calculate complexity scores using scoring matrices.

### Scoring Matrix

**Factors**:

1. **Code Size** (0-20 points)
   - < 10K LOC: 2 points
   - 10K-50K LOC: 5 points
   - 50K-100K LOC: 10 points
   - 100K-500K LOC: 15 points
   - > 500K LOC: 20 points

2. **Tech Stack Gap** (0-20 points)
   - Same stack, version upgrade: 5 points
   - Same language, framework change: 10 points
   - Language change (compatible paradigm): 15 points
   - Language change (different paradigm): 20 points

3. **Database Migration** (0-15 points)
   - Same DB, version upgrade: 3 points
   - SQL to SQL (different vendor): 8 points
   - SQL to NoSQL or vice versa: 15 points

4. **Architecture Change** (0-15 points)
   - Minimal changes: 3 points
   - Modularization: 8 points
   - Monolith to microservices: 15 points

5. **Integration Complexity** (0-10 points)
   - Few integrations (< 5): 2 points
   - Moderate (5-10): 5 points
   - Many (10-20): 8 points
   - Extensive (> 20): 10 points

6. **Test Coverage Gap** (0-10 points)
   - High coverage (>70%): 2 points
   - Moderate (40-70%): 5 points
   - Low (< 40%): 10 points

7. **Technical Debt** (0-10 points)
   - Low debt: 2 points
   - Moderate debt: 5 points
   - High debt: 10 points

**Total Score**: 0-100 points

**Complexity Rating**:

- 0-30: **LOW** - Straightforward upgrade
- 31-60: **MEDIUM** - Moderate effort required
- 61-80: **HIGH** - Significant transformation
- 81-100: **VERY HIGH** - Consider greenfield rewrite

### Calculate Scores

```text
Complexity Score = {calculated_score}
Complexity Rating = {LOW | MEDIUM | HIGH | VERY HIGH}

```

---

## Step 3: Feasibility Analysis

Calculate three feasibility scores:

### 3.1: Inline Upgrade Feasibility

```text
Formula:
Inline_Score = 100 - (Complexity_Score * 0.7) - (Tech_Debt_Score * 0.3)

Where:
- Complexity_Score = from Step 2 (0-100)
- Tech_Debt_Score = normalized from tech debt items (0-100)

```

**Rating**:

- 70-100%: **HIGHLY FEASIBLE** - Recommended approach
- 50-69%: **FEASIBLE** - Manageable with planning
- 30-49%: **CHALLENGING** - Requires significant effort
- 0-29%: **NOT RECOMMENDED** - Consider alternatives

### 3.2: Greenfield Rewrite Feasibility

```text
Formula:
Rewrite_Score = (Complexity_Score * 0.5) + (Tech_Debt_Score * 0.3) + (Coverage_Gap * 0.2)

Where:
- Complexity_Score = from Step 2 (0-100)
- Tech_Debt_Score = normalized (0-100)
- Coverage_Gap = (100 - test_coverage_percentage)

```

**Rating**:

- 70-100%: **RECOMMENDED** - Rewrite is justified
- 50-69%: **CONSIDER** - Cost-benefit analysis needed
- 30-49%: **QUESTIONABLE** - Likely more expensive
- 0-29%: **NOT JUSTIFIED** - Upgrade instead

### 3.3: Hybrid Approach Feasibility

```text
Formula:
Hybrid_Score = 100 - abs(Inline_Score - Rewrite_Score)

Rationale: Hybrid works best when inline and rewrite are equally viable

```

**Rating**:

- 70-100%: **VIABLE** - Good candidate for phased approach
- 50-69%: **POSSIBLE** - Consider if timeline is flexible
- 0-49%: **NOT OPTIMAL** - Choose inline or rewrite

---

## Step 4: Modernization Recommendations

Based on scores, generate prioritized recommendations:

### Quick Wins (Low Effort, High Value)

- Update dependencies to latest LTS versions
- Add missing indexes to database
- Implement caching for frequently accessed data
- Fix critical security vulnerabilities

### Strategic Improvements (Medium Effort, High Value)

- Migrate to {target framework} {version}
- Implement automated testing to reach {target coverage}%
- Add observability stack (logging, metrics, tracing)
- Refactor high-complexity modules

### Long-term Goals (High Effort, High Value)

- Migrate to {target deployment platform}
- Implement {containerization strategy}
- Migrate to {target database}
- Adopt {IaC tool} for infrastructure

---

## Output State

```json
{
  ...previous_state,
  "stage": "full_application_analysis",
  "timestamp": "2025-11-14T11:00:00Z",
  "stages_complete": [..., "full_application_analysis"],
  "modernization_preferences": {
    "q1_language": "Java 17 LTS",
    "q2_database": "PostgreSQL 15",
    "q3_message_bus": "Apache Kafka",
    "q4_package_manager": "Gradle 8.x",
    "q5_deployment": "Kubernetes",
    "q6_iac": "Terraform",
    "q7_containerization": "Docker with official images",
    "q8_observability": {"metrics": "Prometheus", "logging": "Loki", "tracing": "Jaeger"},
    "q9_security": "OAuth 2.0 / OpenID Connect",
    "q10_testing": {"strategy": "Full pyramid", "coverage_target": "80%"}
  },
  "scoring": {
    "complexity_score": 58,
    "complexity_rating": "MEDIUM",
    "feasibility": {
      "inline_upgrade": 62,
      "greenfield_rewrite": 45,
      "hybrid_approach": 77
    }
  },
  "recommendations": {
    "primary_approach": "hybrid",
    "confidence": 75,
    "quick_wins": [...],
    "strategic_improvements": [...],
    "long_term_goals": [...]
  }
}

```

---

## Stage Completion Validation

**Before proceeding to next stage, verify:**

- [ ] All 10 questions asked exactly as written (no modifications)
- [ ] All user responses recorded in state (modernization_preferences)
- [ ] No assumptions made (all answers from user, not inferred)
- [ ] Scope validation completed (IN SCOPE vs OUT OF SCOPE)
- [ ] Complexity scoring calculated
- [ ] Feasibility scores generated (inline/greenfield/hybrid)
- [ ] Recommendations generated with confidence scores
- [ ] State saved successfully

**IF any checkbox is unchecked, STOP and fix the issue before proceeding.**

---

## Completion Marker

```text
STAGE_COMPLETE:FULL_APP
STATE_PATH: {analysis_dir}/state.json
```

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits the next prompt. **Do NOT generate artifacts until you run this command.**
