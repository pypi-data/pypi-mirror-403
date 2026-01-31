---
stage: setup
requires: initialization
outputs: feature_dir, design_docs
version: 1.0.0
next: 03-generate.md
---

# Stage 2: Setup

## Purpose

Run setup scripts and load design documents.

---

## Step 1: Collect Preferences

**Arguments provided:**

```text
PREFERENCES: {preferences:$NONE}
```

**IF preferences show "$SKIP"**: User explicitly chose no preferences. Use standard task breakdown by user story with default sizing.

**IF preferences show "$NONE"**: Prompt user:

**[STOP: USER_INPUT_REQUIRED]**

```text
Task preferences? (size, grouping, priority)
Examples: "< 2 hours", "by user story", "backend first"
Type "none" for standard breakdown.
```

Wait for response before proceeding.

**IF preferences have actual value** (not "$NONE" or "$SKIP"): Use them directly and skip prompting.

---

## Step 2: Run Setup Script

Execute from repo root (cross-platform):

```bash
speckitadv check --json
```

Parse: `FEATURE_DIR`, `AVAILABLE_DOCS`

---

## Step 3: Load Design Documents

From FEATURE_DIR:

- **Required**: `plan.md` (tech stack, libraries), `spec.md` (user stories)
- **Optional**: `data-model.md`, `contracts/`, `research.md`, `quickstart.md`

Note: Not all projects have all documents. Generate tasks from available docs.

---

## Output

```text

[ok] Setup complete
  - Feature dir: {{feature_dir}}
  - Docs available: [list]
  - Preferences: [N] loaded
```

---

## NEXT

```text
speckitadv tasks
```

**Note:** State is persisted to `{{feature_dir}}/.state/` throughout the workflow.
