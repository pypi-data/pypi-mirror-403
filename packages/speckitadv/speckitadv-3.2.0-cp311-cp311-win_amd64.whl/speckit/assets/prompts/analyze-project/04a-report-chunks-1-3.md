---
stage: report_generation_1
requires: analyze-project-03a-full-app.json OR analyze-project-03b-cross-cutting.json
outputs: report_chunks_1_3
version: 3.4.0
---

# Stage 4A: Report Generation (Chunks 1-3)

## Purpose

Generate the first three chunks of the analysis report: Project Discovery, Controllers/API, and Services/Business Logic.

---

{{include:strict-execution-mode.md}}

{{include:analyze-state-management.md}}

{{include:analyze-file-write-policy.md}}

---

## AI Context Cache: Recall Stored Understanding

**[!] CRITICAL: Before generating report content, recall cached understanding from analysis phases.**

```text
# FIRST: Discover ALL cached entries (project, modules, files)
get_understanding_stats(limit=50)
# Review output to identify ALL cached targets and their scopes

# Recall project-level understanding
recall_understanding(target="project")

# Recall from ACTUAL cached paths shown in stats output
# Common examples - use paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/auth")      # if exists in stats
recall_understanding(target="{project_path}/api")       # if exists in stats
recall_understanding(target="{project_path}/data")      # if exists in stats
recall_understanding(target="{project_path}/services")  # if exists in stats
```

**Benefits:**

- Saves 70-85% tokens by using cached analysis
- Includes gotchas and edge cases discovered during deep-dive
- Maintains consistency across report sections

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check: Verify Previous Stage

1. Verify Stage 3 data exists in `{data_dir}/` (validation-scoring.json or effort-success.json)
2. Load analysis results and preferences from `{data_dir}/`

**IF data missing:** STOP - Return to Stage 3

---

## Important: Chunking Strategy

**DO NOT generate the entire report in one operation.**

Generate in 3 chunks per substage:

- 04a: Chunks 1-3 (this file)
- 04b: Chunks 4-6
- 04c: Chunks 7-9

Each chunk MUST be written to file before proceeding to next.

---

## Resume Detection

Check for existing partial report:

```bash
if [ -f "{reports_dir}/analysis-report.md" ]; then
  # Check which chunks exist
fi
```

**IF resuming:** Skip completed chunks, continue from first incomplete.

---

## Chunk 1: Phase 1 - Project Discovery

---
**[STOP: GENERATE_CHUNK_1]**

Generate Phase 1 content. This section documents the project's technology stack and architecture.

**Required Sections:**

- 1.1 Technology Stack
- 1.2 System Architecture
- 1.3 Project Statistics
- 1.4 Configuration Analysis
- 1.5 Build & Deployment

**Content Requirements:**

- Use data from `{data_dir}/file-manifest.json` and `{data_dir}/tech-stack.json`
- Include file:line references where applicable
- NO placeholders (TODO, TBD, etc.)

**Generate and Write:**

Use CLI to write: `speckitadv write-report analysis-report.md --stage=04a-report-chunks-1-3 --content '<md>' --analysis-dir "{analysis_dir}"`

This saves to: `{reports_dir}/analysis-report.md`

```markdown
# Analysis Report: {project_name}

**Analysis Date:** {date}
**Chain ID:** {chain_id}
**Analysis Scope:** {Full Application | Cross-Cutting Concern}

---

## Phase 1: Project Discovery

### 1.1 Technology Stack

**Languages:**
{List with versions and file counts}

**Frameworks:**

| Framework | Version | Purpose | Evidence |
|-----------|---------|---------|----------|
| {name} | {version} | {purpose} | {file:line} |

**Build Tools:**
{List with evidence}

### 1.2 System Architecture

**Architecture Pattern:** {pattern}

**Evidence:**
- {evidence 1 with file:line}
- {evidence 2 with file:line}

**Architecture Diagram:**
{Mermaid diagram if determinable}

### 1.3 Project Statistics

| Metric | Value |
|--------|-------|
| Total Files | {count} |
| Lines of Code | {count} |
| Source Files | {count} |
| Test Files | {count} |
| Config Files | {count} |

### 1.4 Configuration Analysis

**Configuration Files Analyzed:** {count}

| File | Purpose | Key Settings |
|------|---------|--------------|
| {file} | {purpose} | {settings} |

### 1.5 Build & Deployment

**Build Tool:** {tool} v{version}
**Build Command:** `{command}`
**Test Command:** `{command}`

**Deployment:**
{Detected deployment method with evidence}

---

```

### Verify Chunk 1 Written

1. Read `{reports_dir}/analysis-report.md`
2. Confirm Phase 1 sections present
3. Confirm no placeholders

---
**[STOP: VERIFY_CHUNK_1]**

**IF verified:** Output: `[ok] Chunk 1/9: Project Discovery ({lines} lines)`
**IF failed:** Retry generation

---

## Chunk 2: Phase 2.1 - Controllers & API Endpoints

---
**[STOP: GENERATE_CHUNK_2]**

Generate Phase 2.1 content. Document every controller and API endpoint.

**Content Requirements:**

- List EVERY controller file analyzed
- Document EVERY API endpoint
- Include file:line references
- Document auth requirements per endpoint

**Append to report:**

```markdown
## Phase 2: Codebase Analysis

### 2.1 Controllers & API Endpoints

**Total Controllers:** {count}
**Total Endpoints:** {count}

#### Controller: {ControllerName}

**File:** `{path}` (Lines: {start}-{end})

| Method | Path | Purpose | Auth | Evidence |
|--------|------|---------|------|----------|
| GET | `/api/...` | {purpose} | {required/optional} | `{file}:{line}` |
| POST | `/api/...` | {purpose} | {required/optional} | `{file}:{line}` |

{Repeat for each controller}

**API Summary:**
- Public endpoints: {count}
- Protected endpoints: {count}
- Admin-only endpoints: {count}

---

```

### Verify Chunk 2

1. Append to analysis-report.md
2. Confirm content appended
3. Count endpoints documented

---
**[STOP: VERIFY_CHUNK_2]**

**IF verified:** Output: `[ok] Chunk 2/9: Controllers ({count} endpoints, {lines} lines)`
**IF failed:** Retry generation

---

## Chunk 3: Phase 2.2 - Services & Business Logic

---
**[STOP: GENERATE_CHUNK_3]**

Generate Phase 2.2 content. Document services and business logic.

**Content Requirements:**

- List EVERY service file analyzed
- Document business workflows
- Identify external integrations
- Note transaction patterns

**Append to report:**

```markdown
### 2.2 Services & Business Logic

**Total Services:** {count}
**External Integrations:** {count}

#### Service: {ServiceName}

**File:** `{path}` (Lines: {start}-{end})

**Responsibilities:**
- {responsibility 1}
- {responsibility 2}

**Key Methods:**

| Method | Purpose | Complexity | Evidence |
|--------|---------|------------|----------|
| `{method}` | {purpose} | {LOW/MEDIUM/HIGH} | `{file}:{line}` |

**Integrations:**
- {external service with evidence}

**Transactions:**
- {transaction pattern with evidence}

{Repeat for each service}

**Business Workflows:**

1. **{Workflow Name}**
   - Entry: `{file}:{line}`
   - Steps: {description}
   - Exit: {outcome}

---

```

### Verify Chunk 3

1. Append to analysis-report.md
2. Confirm content appended
3. Count services documented

---
**[STOP: VERIFY_CHUNK_3]**

**IF verified:** Output: `[ok] Chunk 3/9: Services ({count} services, {lines} lines)`
**IF failed:** Retry generation

---

## Output Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 04a-report-chunks-1-3

  Chunks Generated: 3/9
  Total Lines: {count}

  Content:
    Phase 1: Project Discovery [ok]
    Phase 2.1: Controllers ({endpoints} endpoints) [ok]
    Phase 2.2: Services ({services} services) [ok]

  Proceeding to Chunks 4-6...
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
