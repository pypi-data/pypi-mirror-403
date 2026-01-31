---
stage: full_app_questions_2
requires: 03a1-questions-part1
condition: scope == "A"
outputs: modernization_prefs_6_10
version: 3.4.0
---

{{include:strict-execution-mode.md}}

**Note:** This substage collects questions only - no files created. Responses stored via CLI at end.

---

# Stage 3A-2: Modernization Questions (Part 2)

## Purpose

Ask questions 6-10 to complete the modernization preferences. These cover infrastructure as code, containerization, observability, security, and testing.

---

## CRITICAL: Question Topics Are FIXED

**[MANDATORY - DO NOT MODIFY]**

You MUST ask these EXACT questions in this EXACT order:

| Q# | Topic | Preference Key |
|----|-------|----------------|
| Q6 | Infrastructure as Code | `q6_iac` |
| Q7 | Containerization Strategy | `q7_containerization` |
| Q8 | Observability Stack | `q8_observability` |
| Q9 | Security & Authentication | `q9_security` |
| Q10 | Testing Strategy | `q10_testing` |

**FORBIDDEN TOPICS (DO NOT ASK ABOUT):**

- [X] Caching strategy (NOT part of this questionnaire)
- [X] Logging framework alone (covered under Q8 observability)
- [X] Frontend approach (NOT part of this questionnaire)
- [X] Search solution (NOT part of this questionnaire)
- [X] Any topics not listed in the table above

**WHY:** The CLI validates preference keys. Using wrong keys (q6_caching, q7_auth, etc.) will cause validation warnings and incomplete state.

---

## How Context Is Provided

The CLI manages state and provides all context. **Do not read state.json directly.**

Values available (already substituted by CLI):

- Project path, analysis directory, scope, context
- Q1-Q5 responses are in artifacts from previous stage

---

## Storing Preferences

After collecting responses for Q6-Q10, store ALL preferences using ONE CLI command:

```bash
speckitadv update-preferences '{"q6_iac": {"value": "..."}, "q7_containerization": {"value": "..."}, ...}'
```

DO NOT store preferences after each question. Collect all 5, then store once at the end.

---

## Question 6: Infrastructure as Code

---
**[STOP: USER_INPUT_REQUIRED - Q6]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 6 of 10: Infrastructure as Code (IaC)

What infrastructure as code tool do you want to use?

Current detected: {detected_iac from Stage 2, or "None detected"}

Options (based on deployment: {q5_deployment.value}):

For Kubernetes:
  [A] Helm charts
  [B] Kustomize
  [C] Kubernetes YAML only

For AWS:
  [A] Terraform
  [B] AWS CDK
  [C] CloudFormation
  [D] Pulumi

For Azure:
  [A] Terraform
  [B] Bicep
  [C] ARM Templates
  [D] Pulumi

For GCP:
  [A] Terraform
  [B] Deployment Manager
  [C] Pulumi

General:
  [X] None (manual deployment)
  [Y] Ansible
  [Z] Other (please specify)

Your choice: ___

TIP: Type "skip" to proceed without IaC.
============================================================

```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q6 Response

```json
{
  "q6_iac": {
    "choice": "{letter or custom}",
    "value": "{resolved IaC tool or 'none'}",
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Question 7: Containerization Strategy

---
**[STOP: USER_INPUT_REQUIRED - Q7]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 7 of 10: Containerization Strategy

What containerization approach do you want to use?

Current detected: {detected_containerization from Stage 2}

Options:
  [A] Docker + Kubernetes
  [B] Docker + Docker Compose
  [C] Podman
  [D] Buildpacks (Cloud Native)
  [E] Serverless containers (Fargate, Cloud Run)
  [F] No containers (traditional deployment)

Your choice: ___

TIP: Type "skip" to use current approach.
============================================================

```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q7 Response

```json
{
  "q7_containerization": {
    "choice": "{letter or custom}",
    "value": "{resolved strategy}",
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Question 8: Observability Stack

---
**[STOP: USER_INPUT_REQUIRED - Q8]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 8 of 10: Observability Stack

What observability tools do you want to use?

Current detected: {detected_observability from Stage 2}

Options:

Metrics:
  [A] Prometheus + Grafana
  [B] Datadog
  [C] New Relic
  [D] CloudWatch / Azure Monitor / Cloud Monitoring
  [E] Other (please specify)

Logging:
  [A] ELK Stack (Elasticsearch, Logstash, Kibana)
  [B] Loki + Grafana
  [C] Splunk
  [D] Cloud-native logging
  [E] Other (please specify)

Tracing:
  [A] Jaeger
  [B] Zipkin
  [C] OpenTelemetry
  [D] Commercial APM (Datadog, New Relic)
  [E] Other (please specify)

Your choice (format: metrics/logging/tracing): ___

Example: "A/B/C" for Prometheus, Loki, Jaeger
         Or describe your preferred stack

TIP: Type "skip" to determine based on deployment target.
============================================================

```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q8 Response

```json
{
  "q8_observability": {
    "choice": "{user input}",
    "value": {
      "metrics": "{resolved tool}",
      "logging": "{resolved tool}",
      "tracing": "{resolved tool}"
    },
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Question 9: Security & Authentication

---
**[STOP: USER_INPUT_REQUIRED - Q9]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 9 of 10: Security & Authentication

What authentication/authorization approach do you want?

Current detected: {detected_auth from Stage 2}

Options:
  [A] Keep current approach (upgrade if needed)
  [B] OAuth 2.0 / OpenID Connect (self-hosted)
  [C] Okta
  [D] Auth0
  [E] AWS Cognito
  [F] Azure AD / Entra ID
  [G] Keycloak
  [H] Firebase Auth
  [I] Custom JWT (modernized)
  [J] Other (please specify)

Your choice: ___

TIP: Type "skip" to keep current auth approach.
============================================================

```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q9 Response

```json
{
  "q9_security": {
    "choice": "{letter or custom}",
    "value": "{resolved auth provider}",
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Question 10: Testing Strategy

---
**[STOP: USER_INPUT_REQUIRED - Q10]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 10 of 10: Testing Strategy

What testing approach do you want for the modernized app?

Current detected: {detected_testing from Stage 2}

Options:
  [A] Keep current testing approach
  [B] Unit + Integration tests only
  [C] Unit + Integration + E2E tests
  [D] Full pyramid (Unit > Integration > E2E)
  [E] Contract testing (Pact, etc.)
  [F] BDD with Cucumber/SpecFlow
  [G] Property-based testing
  [H] Custom combination (please specify)

Coverage target: ___% (enter a number, e.g., 80)

Your choice: ___

TIP: Type "skip" to use current approach.
============================================================

```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q10 Response

```json
{
  "q10_testing": {
    "choice": "{letter or custom}",
    "value": "{resolved testing strategy}",
    "coverage_target": "{percentage or default 80}",
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Compile All Preferences

Merge all Q1-Q10 responses into modernization preferences:

```json
{
  "modernization_preferences": {
    "q1_language": "{q1_language.value}",
    "q2_database": "{q2_database.value}",
    "q3_message_bus": "{q3_message_bus.value}",
    "q4_package_manager": "{q4_package_manager.value}",
    "q5_deployment": "{q5_deployment.value}",
    "q6_iac": "{q6_iac.value}",
    "q7_containerization": "{q7_containerization.value}",
    "q8_observability": {
      "metrics": "{q8 metrics}",
      "logging": "{q8 logging}",
      "tracing": "{q8 tracing}"
    },
    "q9_security": "{q9_security.value}",
    "q10_testing": {
      "strategy": "{q10_testing.value}",
      "coverage_target": "{q10_testing.coverage_target}"
    }
  }
}
```

---

## Persist Preferences

After collecting all 10 responses, persist them to state.json using the CLI:

```bash
speckitadv update-preferences '{"q1_language": {"value": "{q1 value}"}, "q2_database": {"value": "{q2 value}"}, "q3_message_bus": {"value": "{q3 value}"}, "q4_package_manager": {"value": "{q4 value}"}, "q5_deployment": {"value": "{q5 value}"}, "q6_iac": {"value": "{q6 value}"}, "q7_containerization": {"value": "{q7 value}"}, "q8_observability": {"value": {"metrics": "{q8 metrics}", "logging": "{q8 logging}", "tracing": "{q8 tracing}"}}, "q9_security": {"value": "{q9 value}"}, "q10_testing": {"value": "{q10 strategy}", "coverage_target": "{q10 coverage}"}}'
```

This stores all preferences in `{analysis_dir}/state.json` under the `modernization_preferences` field.

---

## Progress Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 03a2-questions-part2

  All 10 Questions Completed [ok]

  Modernization Preferences Summary:
  ---------------------------------------------------------
    Language: {q1 value}
    Database: {q2 value}
    Message Bus: {q3 value}
    Build Tool: {q4 value}
    Deployment: {q5 value}
    IaC: {q6 value}
    Containers: {q7 value}
    Observability: {q8 value}
    Security: {q9 value}
    Testing: {q10 value}
  ---------------------------------------------------------

  Proceeding to Scope Validation & Scoring...
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
