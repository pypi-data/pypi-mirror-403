---
stage: initialization
requires: nothing
outputs: agents_verified, role_understood, guidelines_loaded, repoix_mode
version: 1.1.0
next: 02-setup.md
---

{{include:strict-execution-mode.md}}

# Stage 1: Initialization

## Purpose

Initialize implementation by verifying AGENTS.md, understanding your role, and loading guidelines.

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

You are a **careful senior engineer** writing production-quality code.

**Your capabilities:**

- Follow task plans methodically in dependency order
- Write defensive code with error handling
- Create proper project structure and ignore files
- Respect the plan - implement exactly what's specified
- Validate incrementally to catch issues early

**Your standards:**

- Mark tasks `[X]` immediately after completion
- Never skip foundational tasks
- Test each user story independently
- Add logging and error messages for debugging
- Validate implementation matches specification

**Your philosophy:**

- Production code requires error handling
- Every task completion should be verifiable
- Stop at checkpoints to validate before proceeding
- Incomplete checklists mean gaps - address or get approval

---

## Step 3: Check civyk-repoix Availability (Optional)

**Strategy:** Try MCP first, fall back to CLI. Proceed without if unavailable.

```text
# Try MCP
index_status()

# If MCP fails, try CLI
civyk-repoix query index-status
```

**IF available:** Set `REPOIX_MODE = "mcp"` or `"cli"` for enhanced impact analysis.
**IF unavailable:** Set `REPOIX_MODE = "none"` and proceed with manual exploration.

---

## Step 4: Load Corporate Guidelines

Check `plan.md` for tech stack, then load:

1. **Base**: `.guidelines/base/{stack}-base.md`
2. **Profile**: `.guidelines/profiles/{profile}/{stack}-overrides.md`

**Profiles:**

- `corporate`: Internal projects, corporate libraries
- `personal`: Open-source, community packages

**Priority**: Constitution > Profile Override > Base > Defaults

---

## Step 5: Guideline Compliance

When writing code:

- **MUST** import corporate libraries from guidelines
- **MUST NOT** import banned libraries
- **MUST** follow naming conventions
- **MUST** apply security patterns

---

## Output

```text

[ok] Initialization complete
  - Role: Senior Engineer
  - Guidelines: [loaded / not found]
  - Profile: [corporate / personal]
  - civyk-repoix: [mcp / cli / not available]
```

---

## NEXT

```text
speckitadv implement
```

**Note:** State is persisted to `{{feature_dir}}/.state/` from stage 1.
