---
stage: input-collection
requires: initialization
outputs: jira_number, feature_description
version: 1.1.0
next: 03-branch-setup.md
---

# Stage 2: Input Collection

## Purpose

Collect the JIRA number and feature description from user.

**Note**: This stage runs when starting a NEW specification workflow (from default branch).
The feature description collected here will be used to create the feature branch in Stage 3.

---

## Check for Arguments

**Arguments provided:**

```text
JIRA: {jira:$NONE}
FEATURE: {feature:$NONE}
```

**IF FEATURE is NOT "$NONE":**

- Use provided FEATURE value
- Use JIRA if provided (empty string means no JIRA)
- Skip to "Validate Input" section below

**IF FEATURE shows "$NONE"** (interactive mode):

**[STOP: USER_INPUT_REQUIRED]**

```text
JIRA: C12345-7890 (optional)
FEATURE: <specific, actionable description> (required)

Good: "Add user auth with OAuth2", "Create analytics dashboard"
Bad: "Make it better", "Add security" (too vague)
```

Wait for response before proceeding.

---

## Validate Input

Check the provided input:

1. **JIRA format** (optional): If provided, must match `C[0-9]{5}-[0-9]{4}` pattern
   - Valid: C12345-7890, or empty/blank (no JIRA)
   - Invalid: JIRA-123, 12345 (wrong format)

2. **Feature description** (required): Must be specific and actionable
   - Contains action verb (add, create, implement, build, fix)
   - Describes a concrete outcome
   - Not vague or abstract

**IF invalid**: Show error and re-prompt.

---

## Output

Confirm input collected:

```text
[ok] Input collected
  - JIRA: [number or "none"]
  - Feature: [short summary]
```

Then run the next command shown below.

**IMPORTANT**: Pass `--feature` (required) and `--jira` (optional) to stage 3. State persistence begins at stage 3.
