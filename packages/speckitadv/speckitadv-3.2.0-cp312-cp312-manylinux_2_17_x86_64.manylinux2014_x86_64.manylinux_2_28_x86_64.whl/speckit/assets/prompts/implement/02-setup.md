---
stage: setup
requires: initialization
outputs: feature_dir, checklist_status
version: 1.0.0
next: 03-load-context.md
---

# Stage 2: Setup

## Purpose

Run setup scripts and check checklist status.

---

## Step 1: Collect Notes

**Arguments provided:**

```text
NOTES: {notes:$NONE}
```

**IF notes show "$SKIP"**: User explicitly chose no notes. Execute the task plan using standard best practices.

**IF notes show "$NONE"**: Prompt user:

**[STOP: USER_INPUT_REQUIRED]**

```text
Implementation notes? (execution order, scope, testing)
Examples: "database first", "P1 only", "write tests first"
Type "none" for standard implementation.
```

Wait for response before proceeding.

**IF notes have actual value** (not "$NONE" or "$SKIP"): Use them directly and skip prompting.

---

## Step 2: Run Setup Script

Execute (cross-platform):

```bash
speckitadv check --json --require-tasks --include-tasks
```

Parse: `FEATURE_DIR`, `AVAILABLE_DOCS`

---

## Step 3: Check Checklists

Scan `{{feature_dir}}/checklists/`:

```text

| Checklist | Total | Complete | Incomplete | Status |
|-----------|-------|----------|------------|--------|
| ux.md     | 12    | 12       | 0          | [ok] PASS |
| test.md   | 8     | 5        | 3          | [x] FAIL |
```

**If any incomplete:**

- Display table
- **[STOP: USER_CONFIRMATION_REQUIRED]** Ask: "Some checklists incomplete. Proceed anyway? (yes/no)"
- MUST wait for user response before proceeding

**If all complete:**

- Display table
- Proceed automatically

---

## Output

```text

[ok] Setup complete
  - Feature: {{feature_dir}}
  - Checklists: [PASS / user approved]
```

---

## NEXT

```text
speckitadv implement
```

**Note:** State is persisted to `{{feature_dir}}/.state/` throughout the workflow.
