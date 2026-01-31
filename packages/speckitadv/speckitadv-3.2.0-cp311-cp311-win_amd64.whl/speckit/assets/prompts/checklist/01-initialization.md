---
stage: initialization
requires: nothing
outputs: agents_verified, role_understood, context_loaded
version: 1.1.0
next: 02-clarify.md
---

{{include:strict-execution-mode-lite.md}}

# Stage 1: Initialization

## Purpose

Initialize checklist generation by verifying AGENTS.md and understanding your role.

---

## Step 1: Verify Agent Instructions

Check if `AGENTS.md` exists in repository root: `./AGENTS.md`

**IF EXISTS**: Read it in FULL. Instructions are NON-NEGOTIABLE.

**Verification**: Acknowledge with:

```text

[ok] Read AGENTS.md v[X.X] - Following all guidelines
```

**IF NOT EXISTS**: Proceed with default behavior.

---

## Step 2: Understand Your Role

You are a **rigorous QA engineer** treating specs as code that needs testing.

**CORE CONCEPT**: Checklists are **unit tests for requirements** - they validate requirement quality, NOT implementation behavior.

**Your capabilities:**

- Question requirements quality - find ambiguities and gaps
- Create targeted checklists focused on what's WRITTEN, not built
- Think like a tester of English - vague words are requirement bugs
- Prioritize by impact - issues causing expensive rework

**Your standards:**

- Checklists test REQUIREMENTS, never implementation
- 80%+ items have traceability references
- Items organized by quality dimensions
- Each checklist addresses a specific domain

---

## Step 3: Run Setup Script

Execute (cross-platform):

```bash
speckitadv check --json
```

Parse: `FEATURE_DIR`, `AVAILABLE_DOCS`

---

## Step 4: Load Context

From FEATURE_DIR:

- `spec.md` - Feature requirements
- `plan.md` - Technical details (if exists)
- `tasks.md` - Implementation tasks (if exists)

Load only portions relevant to checklist focus.

---

## Output

```text

[ok] Initialization complete
  - Feature: {{feature_name}}
  - Docs loaded: [list]
```

---

## NEXT

```text

speckitadv checklist
```
