---
stage: stage_prompts
requires: technical_spec_target_complete
condition: state.analysis_scope == "A"
outputs: stage_prompts_complete
version: 3.4.0
---

# Stage 6D: Stage Prompts Generation

## Purpose

Generate staged implementation prompts for Spec Kit workflow integration. These prompts enable the user to use the analysis results with Spec Kit's constitution, clarify, tasks, and implement commands.

---

{{include:strict-execution-mode.md}}

## Pre-Check

1. Verify `{reports_dir}/technical-spec-target.md` exists
2. Load analysis data from `{data_dir}/`

**IF not complete:** STOP - Return to 06c2c-technical-spec-target-part3.md

---

{{include:analyze-state-management.md}}

---

## AI Context Cache: Recall Stored Understanding

```text
# FIRST: Discover ALL cached entries (project, modules, files)
get_understanding_stats(limit=50)
# Review output to identify ALL cached targets and their scopes

recall_understanding(target="project")

# Recall from ACTUAL cached paths shown in stats output
# Common examples - use paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/auth")  # if exists in stats
recall_understanding(target="{project_path}/api")   # if exists in stats
recall_understanding(target="{project_path}/data")  # if exists in stats
```

**Track cache usage:** Note which recalls return `found=true` for efficiency metrics.

---

## [!] File Write Exception: Stage Prompts

**EXCEPTION:** Stage prompts are written using the AI Write tool directly to `{analysis_dir}/stage-prompts/`.

This is the ONLY exception to the CLI file write policy because:

1. Stage prompts are auxiliary files for Spec Kit workflow integration
2. They are not tracked as individual artifacts in state.json
3. The CLI tracks completion via the stage completion marker

**For ALL other artifacts (reports, specs, data files), use CLI commands only.**

---

## Templates

{{include:stage-prompt-templates/constitution-prompt-template.md}}

{{include:stage-prompt-templates/clarify-prompt-template.md}}

{{include:stage-prompt-templates/tasks-prompt-template.md}}

{{include:stage-prompt-templates/implement-prompt-template.md}}

---

## Create Output Directory

Create: `{analysis_dir}/stage-prompts/`

**[AUTO-CONTINUE]** Generate all 4 prompts sequentially without waiting for user input between prompts.

---

## Prompt 1: Constitution Prompt

---
**[STOP: GENERATE_CONSTITUTION_PROMPT]**

**Purpose:** Extract project principles from legacy code for `/speckitadv.constitution` command

**Template:** Use constitution-prompt template above

**Content to extract:**

```markdown
# Project Constitution: {Project Name}

## Core Values

{Extract from legacy code patterns and documentation}

## Coding Standards

- Naming conventions observed in legacy
- Code organization patterns
- Documentation style

## Architecture Decisions

| Decision | Context | Rationale |
|----------|---------|-----------|
| {ADR from legacy} | {why} | {justification} |

## Quality Standards

- Test coverage expectations
- Performance benchmarks
- Security requirements

## Legacy Preservation

{Critical behaviors that MUST be preserved exactly}
- {behavior 1} (Source: {file}:{line})
- {behavior 2} (Source: {file}:{line})

```

Write to: `{analysis_dir}/stage-prompts/constitution-prompt.md`

**Output:** `[ok] Generated: constitution-prompt.md`

---

## Prompt 2: Clarify Prompt

---
**[STOP: GENERATE_CLARIFY_PROMPT]**

**Purpose:** Use legacy code as source of truth for clarifications with `/speckitadv.clarify` command

**Template:** Use clarify-prompt template above

**Content to extract:**

```markdown
# Clarification Guide: {Project Name}

## Legacy Code References

When clarifying ambiguous requirements, reference these legacy implementations:

### Authentication & Authorization

- Source: {auth files with line numbers}
- Key behaviors: {list}

### Business Logic

- Source: {business logic files with line numbers}
- Critical rules: {list}

### Data Validation

- Source: {validation files with line numbers}
- Validation patterns: {list}

## Ambiguity Resolution Patterns

| Ambiguous Spec | Legacy Behavior | Resolution |
|----------------|-----------------|------------|
| "{ambiguous text}" | {what legacy does} | {clarification} |

## Edge Cases Discovered

- {edge case 1}: Handled by {file}:{line}
- {edge case 2}: Handled by {file}:{line}

## Questions for Stakeholders

{List of unresolved ambiguities requiring business decision}

```

Write to: `{analysis_dir}/stage-prompts/clarify-prompt.md`

**Output:** `[ok] Generated: clarify-prompt.md`

---

## Prompt 3: Tasks Prompt

---
**[STOP: GENERATE_TASKS_PROMPT]**

**Purpose:** Break down implementation with legacy complexity awareness for `/speckitadv.tasks` command

**Template:** Use tasks-prompt template above

**Content to extract:**

```markdown
# Task Breakdown: {Project Name}

## Migration Phases

### Phase 1: Foundation (50% value)

| Task | Legacy Source | Complexity | Effort |
|------|--------------|------------|--------|
| {task} | {file}:{line} | {H/M/L} | {days} |

### Phase 2: Core Migration (30% value)

| Task | Legacy Source | Complexity | Effort |
|------|--------------|------------|--------|
| {task} | {file}:{line} | {H/M/L} | {days} |

### Phase 3: Complete Migration (15% value)

| Task | Legacy Source | Complexity | Effort |
|------|--------------|------------|--------|
| {task} | {file}:{line} | {H/M/L} | {days} |

### Phase 4: Optimization (5% value)

| Task | Legacy Source | Complexity | Effort |
|------|--------------|------------|--------|
| {task} | {file}:{line} | {H/M/L} | {days} |

## Complexity Hotspots

{Files/components with highest complexity scores}
- {file}: Complexity {score}, Effort: {estimate}

## Dependencies

{Task dependencies and ordering constraints}

## Risk Mitigation Tasks

{Additional tasks to reduce migration risk}

```

Write to: `{analysis_dir}/stage-prompts/tasks-prompt.md`

**Output:** `[ok] Generated: tasks-prompt.md`

---

## Prompt 4: Implement Prompt

---
**[STOP: GENERATE_IMPLEMENT_PROMPT]**

**Purpose:** Reference legacy code during implementation for `/speckitadv.implement` command

**Template:** Use implement-prompt template above

**Content to extract:**

```markdown
# Implementation Guide: {Project Name}

## Must-Preserve Behaviors

### CRITICAL - Exact Preservation Required

These behaviors must be implemented EXACTLY as in legacy:

| Behavior | Legacy Source | Why Critical |
|----------|--------------|--------------|
| {behavior} | {file}:{line} | {reason} |

### Code Patterns to Follow

{Legacy patterns that should be replicated}

```text
// Legacy Pattern: {name}
// Source: {file}:{line}
{code snippet}
```

## Edge Cases Catalog

| Scenario | Legacy Handling | Test Case |
|----------|-----------------|-----------|
| {edge case} | {behavior} | {test ref} |

## API Contract Preservation

{Endpoints/interfaces that must maintain backwards compatibility}

## Data Migration Notes

{Critical data handling from legacy that affects implementation}

## Testing Checkpoints

| Checkpoint | Validation | Legacy Reference |
|------------|------------|------------------|
| {checkpoint} | {how to verify} | {file}:{line} |

<!-- markdownlint-disable-next-line MD040 -->
```

Write to: `{analysis_dir}/stage-prompts/implement-prompt.md`

**Output:** `[ok] Generated: implement-prompt.md`

---

## Generate Stage 6 State (Scope A)

```json
{
  "schema_version": "3.1.0",
  "chain_id": "{chain_id}",
  "stage": "scope_artifact_generation",
  "timestamp": "{ISO-8601}",
  "stages_complete": [..., "scope_artifact_generation"],
  "scope_artifacts_generated": [
    "functional-spec-legacy.md",
    "functional-spec-target.md",
    "technical-spec-legacy.md",
    "technical-spec-target.md",
    "stage-prompts/constitution-prompt.md",
    "stage-prompts/clarify-prompt.md",
    "stage-prompts/tasks-prompt.md",
    "stage-prompts/implement-prompt.md"
  ],
  "total_scope_artifacts": 8,
  "all_artifacts_complete": true
}

```

The CLI automatically updates `{analysis_dir}/state.json` when stages complete.

---

## Completion Marker

```text
===========================================================
  STAGE COMPLETE: SCOPE_ARTIFACTS (Full Application)

  Chain ID: {chain_id}

  Artifacts Generated (8 total):
    [ok] functional-spec-legacy.md
    [ok] functional-spec-target.md
    [ok] technical-spec-legacy.md
    [ok] technical-spec-target.md
    [ok] stage-prompts/constitution-prompt.md
    [ok] stage-prompts/clarify-prompt.md
    [ok] stage-prompts/tasks-prompt.md
    [ok] stage-prompts/implement-prompt.md
===========================================================

STAGE_COMPLETE:SCOPE_ARTIFACTS

```

---

## Analysis Chain Complete

```text
===========================================================
           ANALYSIS CHAIN COMPLETE
===========================================================

Chain ID: {chain_id}

All Stages Completed:
  [ok] Stage 1: Setup and Scope
  [ok] Stage 2: File Analysis
  [ok] Stage 3A: Full Application Analysis
  [ok] Stage 4: Report Generation
  [ok] Stage 5: Common Artifacts
  [ok] Stage 6: Scope-Specific Artifacts

Analysis Directory: {analysis_dir}

Generated Artifacts:
  Common:
    * EXECUTIVE-SUMMARY.md
    * dependency-audit.json
    * metrics-summary.json
    * analysis-report.md

  Scope-Specific:
    * functional-spec-legacy.md
    * functional-spec-target.md
    * technical-spec-legacy.md
    * technical-spec-target.md
    * stage-prompts/ (4 files)

Next Steps:
  1. Review generated artifacts in {analysis_dir}
  2. Use stage-prompts/ with Spec Kit commands
  3. Begin implementation

===========================================================

```
