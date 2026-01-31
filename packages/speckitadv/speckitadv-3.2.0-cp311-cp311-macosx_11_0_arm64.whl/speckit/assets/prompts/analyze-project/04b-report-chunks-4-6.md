---
stage: report_generation_2
requires: 04a-report-chunks-1-3 complete
outputs: report_chunks_4_6
version: 3.4.0
---

# Stage 4B: Report Generation (Chunks 4-6)

## Purpose

Generate chunks 4-6: Data Layer, Positive Findings, and Technical Debt & Issues.

---

{{include:strict-execution-mode.md}}

{{include:analyze-state-management.md}}

{{include:analyze-file-write-policy.md}}

---

## AI Context Cache: Recall Stored Understanding

**Before generating report content, recall cached understanding:**

```text
# FIRST: Discover ALL cached entries (project, modules, files)
get_understanding_stats(limit=50)
# Review output to identify ALL cached targets and their scopes

# Recall project-level understanding
recall_understanding(target="project")

# Recall from ACTUAL cached paths shown in stats output
recall_understanding(target="{project_path}/data")  # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## Pre-Check

1. Verify `{reports_dir}/analysis-report.md` exists with Phase 1-2.2 content

---

## Chunk 4: Phase 2.3 - Data Layer

---
**[STOP: GENERATE_CHUNK_4]**

**Append to report:**

```markdown
### 2.3 Data Layer (Models & Repositories)

**Total Entities:** {count}
**Total Repositories:** {count}

#### Entity: {EntityName}

**File:** `{path}:{lines}`
**Table:** `{table_name}`

| Field | Type | Constraints | PII | Evidence |
|-------|------|-------------|-----|----------|
| {field} | {type} | {constraints} | {Y/N} | `{line}` |

**Relationships:**
- {relationship with evidence}

#### Repository: {RepositoryName}

**File:** `{path}:{lines}`

**Query Methods:**

| Method | Type | Complexity | Evidence |
|--------|------|------------|----------|
| {method} | {ORM/Native SQL} | {L/M/H} | `{line}` |

**Data Layer Issues:**
- {N+1 queries, missing indexes, etc. with evidence}

---

```

---
**[STOP: VERIFY_CHUNK_4]**

Output: `[ok] Chunk 4/9: Data Layer ({entities} entities, {lines} lines)`

---

## Chunk 5: Phase 3 - Positive Findings

---
**[STOP: GENERATE_CHUNK_5]**

**Append to report:**

```markdown
## Phase 3: What's Working Well

**Total Positive Findings:** {count}

### 3.1 Architecture & Design

| Finding | Evidence | Impact |
|---------|----------|--------|
| {good practice} | `{file}:{line}` | {positive impact} |

### 3.2 Code Quality

| Finding | Evidence | Impact |
|---------|----------|--------|
| {good practice} | `{file}:{line}` | {positive impact} |

### 3.3 Security Practices

| Finding | Evidence | Impact |
|---------|----------|--------|
| {secure pattern} | `{file}:{line}` | {benefit} |

### 3.4 Testing & Quality Assurance

| Finding | Evidence | Impact |
|---------|----------|--------|
| {good testing} | `{file}:{line}` | {benefit} |

### 3.5 Documentation & Maintainability

| Finding | Evidence | Impact |
|---------|----------|--------|
| {documentation} | `{file}:{line}` | {benefit} |

---

```

---
**[STOP: VERIFY_CHUNK_5]**

Output: `[ok] Chunk 5/9: Positive Findings ({count} findings, {lines} lines)`

---

## Chunk 6: Phase 4 - Technical Debt & Issues

---
**[STOP: GENERATE_CHUNK_6]**

**Append to report:**

```markdown
## Phase 4: Technical Debt & Issues

### 4.1 Technical Debt

**Total Items:** {count}

#### HIGH Severity

| ID | Issue | Location | Impact | Recommendation |
|----|-------|----------|--------|----------------|
| TD-001 | {issue} | `{file}:{line}` | {impact} | {fix} |

#### MEDIUM Severity

| ID | Issue | Location | Impact | Recommendation |
|----|-------|----------|--------|----------------|
| TD-002 | {issue} | `{file}:{line}` | {impact} | {fix} |

#### LOW Severity

| ID | Issue | Location | Impact | Recommendation |
|----|-------|----------|--------|----------------|
| TD-003 | {issue} | `{file}:{line}` | {impact} | {fix} |

### 4.2 Security Vulnerabilities

**Total Vulnerabilities:** {count}

| ID | Severity | Issue | Location | CVE | Remediation |
|----|----------|-------|----------|-----|-------------|
| SEC-001 | {sev} | {issue} | `{file}:{line}` | {CVE if any} | {fix} |

### 4.3 Code Quality Issues

| Category | Count | Examples |
|----------|-------|----------|
| Code Duplication | {n} | `{file}:{line}` |
| Long Methods | {n} | `{file}:{line}` |
| Complex Conditionals | {n} | `{file}:{line}` |
| Missing Error Handling | {n} | `{file}:{line}` |

### 4.4 Architecture Issues

| Issue | Severity | Impact | Location | Recommendation |
|-------|----------|--------|----------|----------------|
| {issue} | {sev} | {impact} | `{files}` | {fix} |

---

```

---
**[STOP: VERIFY_CHUNK_6]**

Output: `[ok] Chunk 6/9: Tech Debt ({debt_count} debt, {sec_count} security, {lines} lines)`

---

## Output Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 04b-report-chunks-4-6

  Chunks Generated: 6/9
  Cumulative Lines: {count}

  Content:
    Phase 2.3: Data Layer ({entities} entities) [ok]
    Phase 3: Positive Findings ({count}) [ok]
    Phase 4: Tech Debt & Issues ({count}) [ok]

  Proceeding to Chunks 7-9...
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
