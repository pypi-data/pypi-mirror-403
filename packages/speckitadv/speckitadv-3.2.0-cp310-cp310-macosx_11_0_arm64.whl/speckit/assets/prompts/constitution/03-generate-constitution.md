---
stage: generate-constitution
requires: collect-principles
outputs: constitution_file
version: 1.1.0
next: null
---

{{include:ai-cache-enforcement.md}}

# Stage 3: Generate Constitution

## Purpose

Create the formal constitution document from collected principles.

---

## Step 1: Load Template

Load the constitution template from `memory/constitution.md`.

If template doesn't exist, use this structure:

```markdown
# Project Constitution

## Preamble
[PROJECT_MISSION]

## Article I: Engineering Principles
[PRINCIPLES]

## Article II: Quality Standards
[QUALITY_STANDARDS]

## Article III: Governance
[GOVERNANCE]

## Metadata
- Version: [VERSION]
- Ratified: [DATE]
- Last Amended: [DATE]
```

---

## Step 2: Fill Template

Replace all placeholders with concrete values:

- `[PROJECT_NAME]` -> Actual project name
- `[PRINCIPLES]` -> Formatted list of collected principles
- `[VERSION]` -> Semantic version (start at 1.0.0 for new)
- `[DATE]` -> ISO format YYYY-MM-DD

**Formatting rules:**

- Each principle: "**Name**: MUST/SHOULD/MAY description"
- Group related principles under appropriate articles
- Use normative language consistently

---

## Step 3: Validate

Before saving, verify:

- [ ] No unexplained placeholder tokens remain
- [ ] Version follows semantic versioning
- [ ] Dates in ISO format (YYYY-MM-DD)
- [ ] All principles are declarative and testable
- [ ] No vague language - each rule is enforceable

---

## Step 4: Save and Report

Write constitution to `memory/constitution.md`.

Output completion summary:

```text

[ok] Constitution created successfully

Version: 1.0.0
Location: memory/constitution.md
Principles: [N] total

Suggested commit message:
  docs: create project constitution v1.0.0

Next steps:
  - Review memory/constitution.md
```

---

## WORKFLOW COMPLETE

The constitution has been created. No further stages.
