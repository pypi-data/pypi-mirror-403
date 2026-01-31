---
stage: setup
requires: initialization
outputs: feature_spec, impl_plan, specs_dir
version: 1.1.0
next: 03-research.md
---

# Stage 2: Setup

## Purpose

Run setup scripts, collect constraints, and create plan.md template.

---

## Step 1: Collect Constraints

**Arguments provided:**

```text
CONSTRAINTS: {constraints:$NONE}
```

**IF constraints show "$SKIP" or "none"**: User chose no constraints. Proceed with standard best practices from the specification.

**IF constraints have actual value** (not "$NONE" or "$SKIP"): Use them directly.

**IF constraints show "$NONE"**: Ask user for constraints:

**[STOP: USER_INPUT_REQUIRED]**

```text
Planning constraints? (tech, architecture, performance, compliance)
Examples: "PostgreSQL required", "< 200ms response", "GDPR compliant"
Reply with constraints or "none" to skip.
```

Wait for response before proceeding.

---

## Step 2: Run Setup Script

Execute from repo root:

```bash
speckitadv setup-plan --json
```

Parse JSON output for:

- `FEATURE_SPEC` - path to spec.md
- `SPECS_DIR` - feature specs directory
- `BRANCH` - current feature branch

---

## Step 3: Load Context

1. Read `FEATURE_SPEC` (the specification)
2. Read `memory/constitution.md` (principles)

---

## Step 4: Edit Plan Template

The `setup-plan` command above copied the plan template to `{{feature_dir}}/plan.md`.

Now edit `{{feature_dir}}/plan.md` with these initial replacements:

- Replace `[FEATURE]` with the feature name from spec.md
- Replace `[DATE]` with today's date
- Replace `[###-feature-name]` with the actual feature directory name
- Keep all other `[...]` placeholders - they will be filled in subsequent stages

**IMPORTANT**: Subsequent stages will fill in remaining sections.

---

## Output

```text
[ok] Setup complete
  - Spec: <path to spec.md>
  - Plan: {{feature_dir}}/plan.md (template created)
  - Constraints: [N] loaded
```

Then run the next command shown below.
