---
stage: file_analysis_phase2
requires: 02a-category-scan complete
outputs: deep_patterns
version: 3.6.0
time_allocation: 40%
---

# Stage 2B: Deep Dive (Phase 2)

## Purpose

Focus on HIGH-PRIORITY areas with 60-80% file coverage using CLI-based discovery followed by deep file reading. This is where detailed pattern extraction happens for authentication, database, and API layers.

**Time Allocation:** 40% of file analysis effort (largest phase)

---

{{include:strict-execution-mode.md}}

{{include:analyze-state-management.md}}

{{include:analyze-file-write-policy.md}}

{{include:ai-cache-enforcement.md}}

{{include:security-findings-format.md}}

---

## Pre-Check: Verify Previous Substage

1. Verify `{data_dir}/category-patterns.json` exists (from Phase 1)
2. Load category patterns to identify key files for deep dive

**IF not complete:** STOP - Return to 02a-category-scan

---

## Priority Areas

| Priority | Area | Target Coverage | Rationale |
|----------|------|-----------------|-----------|
| **P1** | Authentication/Security | 80% | Critical for security assessment |
| **P2** | Database Access | 80% | Understand data layer completely |
| **P3** | API Endpoints | 70% | Map complete API surface |
| **P4** | Core Business Logic | 60% | Understand key workflows |

---

## Step 1: Identify Key Files for Deep Dive

Read category patterns to identify files:

```bash
Read file: {data_dir}/category-patterns.json
```

**Extract key files for each priority area:**

P1 (Auth/Security):

- Files from `categories.middleware.files`
- Files matching "*Auth*", "*Security*", "*Token*"

P2 (Database):

- Files from `categories.repositories.files`
- Files from `categories.models.files`

P3 (API):

- Files from `categories.controllers.files`

P4 (Business Logic):

- Files from `categories.services.files`

---

## Step 2: Run Deep Dive Scan

For each priority area, run the deep-dive-scan CLI with key files.

### 2.1 Authentication Deep Dive

```bash
speckitadv deep-dive-scan "{project_path}" --analysis-dir "{analysis_dir}" --files="{auth_file_1},{auth_file_2},{auth_file_3}"
```

This analyzes:

- Callers and references for each file's symbols
- Impact analysis
- Type hierarchy for auth classes

---

**[STOP: DEEP_DIVE_AUTH]**

Execute the command, then read the results:

```bash
Read file: {data_dir}/deep-dive-patterns.json
```

**AI Context Cache: Check cached understanding before reading source files:**

```text
# Check for cached understanding (saves 70-85% tokens if available)
recall_understanding(target="{project_path}/{auth_file_1}")
recall_understanding(target="{project_path}/{auth_file_2}")

# IF found AND fresh: Use cached analysis
# IF not found OR stale: Read files below, then store understanding
```

Now read the actual source files for detailed understanding (only if not cached):

```text
# IF recall above returned not found OR stale:
# Read file: {project_path}/{auth_file_1}
# [!] NOW CALL store_understanding for the file above

# IF recall above returned not found OR stale:
# Read file: {project_path}/{auth_file_2}
# [!] NOW CALL store_understanding for the file above
```

**After analyzing auth files, store understanding for future sessions:**

```text
store_understanding(
  scope="module",
  target="{project_path}/auth",
  purpose="Authentication module handling user login, tokens, and security",
  importance="critical",
  key_points=["<auth mechanism>", "<token type>", "<password hashing>"],
  gotchas=["<security issues found>"],
  related_to=["<related_modules>"]
)
```

**Extract:**

1. **Authentication Flow:** Registration, Login, Token generation, Logout
2. **User Storage:** Database table, External provider (LDAP, OAuth)
3. **Password Handling:** Hashing algorithm, Salt strategy
4. **Token Configuration:** Type, Algorithm, Expiration
5. **Authorization:** Permission model (RBAC/ABAC), Role definitions
6. **Security Issues:** Missing validations, Hardcoded secrets

---

### 2.2 Database Deep Dive

Run deep dive scan for repository and model files:

```bash
speckitadv deep-dive-scan "{project_path}" --analysis-dir "{analysis_dir}" --files="{repo_file_1},{repo_file_2},{model_file_1}"
```

---

**[STOP: DEEP_DIVE_DATABASE]**

Read results and source files:

```text
Read file: {data_dir}/deep-dive-patterns.json

# Check cache first
recall_understanding(target="{project_path}/{entity_file_1}")
# IF not cached: Read file: {project_path}/{entity_file_1}
# [!] NOW CALL store_understanding for the file above

recall_understanding(target="{project_path}/{repository_file_1}")
# IF not cached: Read file: {project_path}/{repository_file_1}
# [!] NOW CALL store_understanding for the file above
```

**Extract:**

1. **Entity Definition:** Table/collection name, Primary key, Fields
2. **Relationships:** OneToOne, OneToMany, ManyToMany, Cascade
3. **Constraints:** NOT NULL, UNIQUE, Foreign keys
4. **Queries:** Native SQL count, Complex queries
5. **Performance Issues:** N+1 patterns, Missing indexes

**Store understanding for each file read** (use `store_understanding` with purpose, key_points, gotchas, analysis).

---

### 2.3 API Endpoints Deep Dive

Run deep dive scan for controller files:

```bash
speckitadv deep-dive-scan "{project_path}" --analysis-dir "{analysis_dir}" --files="{controller_file_1},{controller_file_2},{controller_file_3}"
```

---

**[STOP: DEEP_DIVE_API]**

Read results and source files:

```text
Read file: {data_dir}/deep-dive-patterns.json

# Check cache first
recall_understanding(target="{project_path}/{controller_file_1}")
# IF not cached: Read file: {project_path}/{controller_file_1}
# [!] NOW CALL store_understanding for the file above

recall_understanding(target="{project_path}/{controller_file_2}")
# IF not cached: Read file: {project_path}/{controller_file_2}
# [!] NOW CALL store_understanding for the file above
```

**Extract:**

1. **Endpoint Definition:** HTTP method, Path pattern, Purpose
2. **Request/Response:** DTOs, Query params, Path params
3. **Authentication:** Required?, Auth type, Roles
4. **Validation:** Input validation, Error responses
5. **API Issues:** Missing auth, Missing validation

**Store understanding for each controller file read.**

---

### 2.4 Business Logic Deep Dive

Run deep dive scan for service files:

```bash
speckitadv deep-dive-scan "{project_path}" --analysis-dir "{analysis_dir}" --files="{service_file_1},{service_file_2}"
```

---

**[STOP: DEEP_DIVE_BUSINESS]**

Read results and source files:

```text
Read file: {data_dir}/deep-dive-patterns.json

# Check cache first
recall_understanding(target="{project_path}/{service_file_1}")
# IF not cached: Read file: {project_path}/{service_file_1}
# [!] NOW CALL store_understanding for the file above
```

**Extract:**

1. **Key Workflows:** Steps, Decision points, Error handling
2. **Business Rules:** Rule descriptions, Implementation locations
3. **Integrations:** External services, Message queues

**Store understanding for each service file read.**

---

## Step 3: Compile Deep Dive Results

Merge all deep dive findings from CLI discovery + file reading:

```json
{
  "deep_dive": {
    "authentication": {
      "type": "{mechanism}",
      "user_storage": "{type}",
      "password_hashing": "{algorithm}",
      "token": {
        "type": "{JWT/session/etc}",
        "algorithm": "{HS256/RS256/etc}",
        "expiration": "{duration}"
      },
      "authorization": "{RBAC/ABAC}",
      "roles": ["{list}"],
      "issues": [
        {"severity": "HIGH", "issue": "{description}", "location": "{file:line}"}
      ],
      "files_analyzed": ["{list}"],
      "coverage": "{percentage}%"
    },
    "database": {
      "orm": "{framework}",
      "engine": "{database}",
      "entities": {count},
      "relationships": {count},
      "native_queries": {count},
      "issues": [
        {"severity": "HIGH", "issue": "{description}", "location": "{file:line}"}
      ],
      "files_analyzed": ["{list}"],
      "coverage": "{percentage}%"
    },
    "api": {
      "style": "{REST/GraphQL}",
      "endpoints": {count},
      "versioning": "{strategy}",
      "auth_required": "{percentage}%",
      "issues": [
        {"severity": "HIGH", "issue": "{description}", "location": "{file:line}"}
      ],
      "files_analyzed": ["{list}"],
      "coverage": "{percentage}%"
    },
    "business_logic": {
      "workflows": {count},
      "rules": {count},
      "integrations": {count},
      "files_analyzed": ["{list}"],
      "coverage": "{percentage}%"
    }
  }
}
```

---

## Step 4: Save Deep Dive Patterns (SINGLE FILE)

Write to ONE file only (see analyze-file-write-policy).

Save all deep-dive findings to `{data_dir}/deep-dive-patterns.json`:

**Use stdin for full JSON (RECOMMENDED):**

```powershell
@"
{
  "deep_dive": {
    "authentication": { ... },
    "database": { ... },
    "api": { ... },
    "business_logic": { ... }
  }
}
"@ | speckitadv write-data deep-dive-patterns.json --stage=02b-deep-dive --stdin
```

**Or use --content for smaller JSON:**

```bash
speckitadv write-data deep-dive-patterns.json --stage=02b-deep-dive --content '{"deep_dive":{...complete object...}}'
```

---

## Output Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 02b-deep-dive (Phase 2)

  Discovery: CLI-based (deep-dive-scan)
  Time Used: 40% allocation

  Coverage Achieved:
    Authentication: {percentage}% (target: 80%)
    Database: {percentage}% (target: 80%)
    API: {percentage}% (target: 70%)
    Business Logic: {percentage}% (target: 60%)

  Issues Found:
    [!] HIGH: {count}
    [!] MEDIUM: {count}
    [ok] LOW: {count}

  AI Cache Efficiency:
    Files read: <count_read>
    Files cached (store_understanding): <count_stored>
    Module-level cached: <count_modules>
    Cache hits (found=true): <count_hits>
    Efficiency: <efficiency>% (target: 90%+)

  Proceeding to Phase 3: Configuration Analysis
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
