---
stage: analyze
requires: initialization
outputs: tech_stack, registry_url, update_mode, document_findings, code_findings
version: 1.1.0
status: EXPERIMENTAL
next: 03-generate.md
---

{{include:strict-execution-mode.md}}

{{include:ai-cache-enforcement.md}}

# Stage 2: Analyze

## Purpose

Detect tech stack, configure options, and analyze documents and code.

---

## Step 1: Detect Tech Stack

Scan reference projects for markers:

- **ReactJS**: `package.json` with `"react"` dependency
- **Java**: `pom.xml`, `build.gradle`, or `*.java` files
- **.NET**: `*.csproj`, `*.sln`, or `*.cs` files
- **NodeJS**: `package.json` with backend dependencies (express, fastify, koa)
- **Python**: `requirements.txt`, `pyproject.toml`, `setup.py`, or `*.py` files

Display detected stacks and ask user:

**[STOP: USER_INPUT_REQUIRED]**

```text
Detected: [list stacks found]
Generate guidelines for: [A] Java | [B] ReactJS | [C] Both | [D] Other
```

Wait for response before proceeding.

Store user's choice for use throughout the workflow.

---

## Step 2: Configure Package Registry

**[STOP: USER_INPUT_REQUIRED]**

```text
Corporate package registry (Artifactory/Nexus)?
[A] Yes - provide URL | [B] No - skip
```

**IF [A]**: Ask for URL, store as ARTIFACTORY_URL.
**IF [B]**: Set ARTIFACTORY_URL = "Not configured".

---

## Step 3: Select Update Mode

Check if guideline file already exists in `.guidelines/` directory.

**IF existing file found:**

**[STOP: USER_INPUT_REQUIRED]**

```text
Existing file: .guidelines/{stack}-guidelines.md v[X.Y.Z]
Update mode: [A] ADD | [B] REPLACE | [C] FULL_REGEN | [D] NEW
```

Wait for response.

**IF choice = [B] REPLACE**: Ask which sections to replace.

**IF no existing file found**: Set UPDATE_MODE = FULL_REGEN (new file creation).

---

## Step 4: Document Analysis (Standards Architect Persona)

**Switch to Standards Architect mindset.**

**Objective**: Extract explicit principles from corporate documents with full traceability.

**Process:**

1. **Load document manifest**: Read `.guidelines-analysis/documents-manifest.json`

2. **For each document**:
   - Read full content (use Read tool for Markdown/text)
   - Extract principles, rules, requirements, mandates
   - Identify RFC 2119 keywords: MUST, SHOULD, MAY, NEVER
   - Record source reference: `document-name.ext:section`

3. **Categorize extracted principles** by guideline sections:
   - Scaffolding, Package Registry, Mandatory Libraries, Banned Libraries
   - Architecture, Security, Coding Standards, Dependency Management
   - Testing, Build & Deployment, Observability

4. **Flag conflicts** between documents (do NOT resolve - document for user)

5. **Output findings** to `.guidelines-analysis/document-findings.md`

---

## Step 5: Code Analysis (Code Archeologist Persona)

**Switch to Code Archeologist mindset.**

**Objective**: Reverse-engineer implicit standards from reference project codebases.

**Process:**

1. **Load project manifest**: Read `.guidelines-analysis/projects-manifest.json`

2. **For each reference project**, scan:
   - Project structure: Folder layout, module organization
   - Dependencies: pom.xml, package.json, requirements.txt
   - Architecture: Controllers, services, repositories, layers
   - Naming conventions: Classes, methods, variables, files
   - Security: Auth implementations, input validation
   - Configuration: application.yml, .env patterns
   - Testing: Test structure, frameworks, coverage
   - Observability: Logging, metrics, health checks

3. **Categorize dependencies:**
   - `[STANDARD]`: Language/framework built-ins (no validation needed)
   - `[EXTERNAL - CHECK ARTIFACTORY]`: Third-party libraries
   - `[CORPORATE - CHECK ARTIFACTORY]`: Company packages

4. **Calculate consensus across projects:**
   - ALL projects (3/3): High confidence -> MUST
   - MOST projects (2/3): Medium confidence -> SHOULD
   - SOME projects (1/3): Low confidence -> ask user

5. **Convert patterns to principles** (NO CODE examples)

6. **Output findings** to `.guidelines-analysis/code-findings.md`

---

## Output

```text

[ok] Analysis complete
  - Tech stack: {{tech_stack}}
  - Registry: {{registry_url}}
  - Update mode: {{update_mode}}
  - Document findings: .guidelines-analysis/document-findings.md
  - Code findings: .guidelines-analysis/code-findings.md
  - Conflicts detected: [N]
```

---

## NEXT

```text
speckitadv generate-guidelines --stage=3
```
