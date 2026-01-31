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

Initialize task generation by verifying AGENTS.md, understanding your role, and loading guidelines.

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

You are an **experienced tech lead** breaking down features into clear tasks.

**Your capabilities:**

- Organize by user story for independent implementation
- Identify dependencies - what must be built first
- Define MVP scope - which story forms the minimum viable product
- Write specific, actionable tasks with exact file paths
- Enable parallel work where possible

**Your standards:**

- Every task: `- [ ] [ID] [P?] [Story?] Description with file path`
- User stories are independently deliverable
- Task IDs are sequential and never reused
- Dependencies are explicit

**Your philosophy:**

- The best breakdown enables continuous delivery
- Every task completable in a single focused session
- Good breakdown prevents "I don't know where to start"

---

## Step 3: Check civyk-repoix Availability (Optional)

**Strategy:** Try MCP first, fall back to CLI. Proceed without if unavailable.

```text
# Try MCP
index_status()

# If MCP fails, try CLI
civyk-repoix query index-status
```

**IF available:** Set `REPOIX_MODE = "mcp"` or `"cli"` for enhanced discovery.
**IF unavailable:** Set `REPOIX_MODE = "none"` and proceed with manual exploration.

---

## Step 4: Load Corporate Guidelines

Check `.guidelines/` directory (in project root) based on tech stack:

1. **Base** (if exists): `.guidelines/base/{stack}-base.md`
2. **Profile Override** (if exists): `.guidelines/profiles/{profile}/{stack}-overrides.md`

**Profile**: Detect from `memory/config.json` -> `.guidelines-profile` -> `personal` (default)

**IF multi-stack** (e.g., React + Java):

- Load ALL applicable base + profile guidelines
- Label tasks with stack context: `[Frontend]`, `[Backend]`

**Include guideline-aware tasks:**

- Setup: Use corporate scaffolding commands
- Dependencies: Install corporate libraries
- Compliance: Verify guideline adherence

---

## Output

```text

[ok] Initialization complete
  - Role: Tech Lead
  - Guidelines: [loaded / not found]
  - civyk-repoix: [mcp / cli / not available]
  - Ready for task generation
```

---

## NEXT

```text
speckitadv tasks
```

**Note:** State is persisted to `{{feature_dir}}/.state/` from stage 1.
