---
stage: full_app_questions_1
requires: 02e-quality-gates
condition: scope == "A"
outputs: modernization_prefs_1_5
version: 3.4.0
---

{{include:strict-execution-mode.md}}

**Note:** This substage collects questions only - no files created. Responses stored via CLI at end.

---

# Stage 3A-1: Modernization Questions (Part 1)

## Purpose

Ask the first 5 modernization questions to understand the user's target technology preferences. Each question MUST be asked exactly as written and MUST wait for user response.

---

## How Context Is Provided

The CLI manages state and provides all context. **Do not read state.json directly.**

Values available in this prompt (already substituted by CLI):

- Project path, analysis directory, scope (must be "A"), context

---

## Question Protocol

**Rules for asking questions:**

1. Present EACH question EXACTLY as written below
2. Show ALL options - do not remove or combine choices
3. Wait for user response before proceeding to next question
4. Validate response matches expected format
5. Record exact user response

**Response Handling:**

- If user provides valid option -> Record and proceed
- If user provides invalid response -> Re-prompt with clarification
- If user requests clarification -> Provide context, then re-ask
- If user types "skip" -> Record as "skip" (use existing/default)

---

## Storing Preferences

After collecting responses for Q1-Q5, store ALL preferences using ONE CLI command:

```bash
speckitadv update-preferences '{"q1_language": {"value": "..."}, "q2_database": {"value": "..."}, ...}'
```

DO NOT store preferences after each question. Collect all 5, then store once at the end.

---

## Question 1: Target Language/Runtime

---
**[STOP: USER_INPUT_REQUIRED - Q1]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 1 of 10: Target Language/Runtime

What language or runtime do you want to use for the
modernized application?

Current detected: {detected_languages from Stage 2}

Options:
  [A] Keep current language (upgrade version if needed)
  [B] Java (LTS: 17, 21)
  [C] Python (3.11, 3.12)
  [D] Node.js/TypeScript (LTS: 20, 22)
  [E] Go (1.21+)
  [F] Rust (latest stable)
  [G] C# / .NET (LTS: 6, 8)
  [H] Other (please specify)

Your choice: ___

TIP: Type the letter (A-H) or specify your preference.
     Type "skip" to use current language.
============================================================
```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q1 Response

Store user's choice in:

```json
{
  "q1_language": {
    "choice": "{letter or custom}",
    "value": "{resolved language/version}",
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Question 2: Target Database

---
**[STOP: USER_INPUT_REQUIRED - Q2]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 2 of 10: Target Database

What database do you want to use?

Current detected: {detected_database from Stage 2}

Options:
  [A] Keep current database (upgrade version if needed)
  [B] PostgreSQL (16+)
  [C] MySQL / MariaDB (8.0+)
  [D] MongoDB (7.0+)
  [E] SQL Server (2022)
  [F] Oracle (19c+)
  [G] Cloud-native (Aurora, Cloud SQL, Cosmos DB)
  [H] Other (please specify)

Your choice: ___

TIP: Type the letter (A-H) or specify your preference.
     Type "skip" to use current database.
============================================================
```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q2 Response

Store user's choice in:

```json
{
  "q2_database": {
    "choice": "{letter or custom}",
    "value": "{resolved database/version}",
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Question 3: Message Bus / Async Communication

---
**[STOP: USER_INPUT_REQUIRED - Q3]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 3 of 10: Message Bus / Async Communication

What message bus or async communication do you need?

Current detected: {detected_message_queue from Stage 2, or "None detected"}

Options:
  [A] None needed (synchronous only)
  [B] Keep current ({current if detected})
  [C] Apache Kafka
  [D] RabbitMQ
  [E] AWS SQS/SNS
  [F] Azure Service Bus
  [G] Google Cloud Pub/Sub
  [H] Redis Pub/Sub
  [I] Other (please specify)

Your choice: ___

TIP: Type "skip" if async is not needed.
============================================================
```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q3 Response

Store user's choice in:

```json
{
  "q3_message_bus": {
    "choice": "{letter or custom}",
    "value": "{resolved message bus or 'none'}",
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Question 4: Package Manager / Build Tool

---
**[STOP: USER_INPUT_REQUIRED - Q4]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 4 of 10: Package Manager / Build Tool

What package manager or build tool do you want to use?

Current detected: {detected_build_tool from Stage 2}

Options based on language choice ({q1_language.value}):

For Java:
  [A] Maven
  [B] Gradle (Groovy DSL)
  [C] Gradle (Kotlin DSL)

For Node.js/TypeScript:
  [A] npm
  [B] yarn
  [C] pnpm
  [D] bun

For Python:
  [A] pip + requirements.txt
  [B] Poetry
  [C] pipenv
  [D] uv

For other languages:
  [X] Default for {language} (specify if custom)

Your choice: ___

TIP: Type "skip" to use current build tool.
============================================================
```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q4 Response

Store user's choice in:

```json
{
  "q4_package_manager": {
    "choice": "{letter or custom}",
    "value": "{resolved package manager}",
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Question 5: Deployment Target

---
**[STOP: USER_INPUT_REQUIRED - Q5]**

Present this question EXACTLY as written:

```text
============================================================
QUESTION 5 of 10: Deployment Target

Where will the modernized application be deployed?

Current detected: {detected_deployment from Stage 2, or "Not detected"}

Options:
  [A] Same as current
  [B] Kubernetes cluster (self-managed)
  [C] AWS (EKS, ECS, Lambda)
  [D] Azure (AKS, Container Apps, Functions)
  [E] Google Cloud (GKE, Cloud Run)
  [F] Docker Compose (simple deployment)
  [G] Traditional VMs / Bare metal
  [H] Serverless-first (FaaS)
  [I] Other (please specify)

Your choice: ___

TIP: Type "skip" to use current deployment method.
============================================================
```

**WAIT for user response. DO NOT proceed until answered.**

---

### Record Q5 Response

Store user's choice in:

```json
{
  "q5_deployment": {
    "choice": "{letter or custom}",
    "value": "{resolved deployment target}",
    "rationale": "{user's reason if provided}"
  }
}
```

---

## Progress Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 03a1-questions-part1

  Questions Completed: 5/10

  Responses Collected:
    Q1 Language: {value}
    Q2 Database: {value}
    Q3 Message Bus: {value}
    Q4 Build Tool: {value}
    Q5 Deployment: {value}

  Proceeding to Questions 6-10...
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
