---
stage: load-context
requires: setup
outputs: tasks_loaded, structure_verified
version: 1.0.0
next: 04-execute.md
---

# Stage 3: Load Context

## Purpose

Load design documents and verify project structure.

---

## Step 1: Load Design Documents (with AI Context Cache)

**FIRST:** Check cached understanding from prior sessions:

```text
# Check what's cached from earlier stages
get_understanding_stats(limit=50)

# Recall cached feature understanding
recall_understanding(target="{{feature_dir}}")
# IF error (MCP connection failed): Load documents manually
# IF found AND fresh: Use cached context, verify key points still apply
# IF not found OR stale: Load documents below and store understanding
```

From FEATURE_DIR:

- **REQUIRED**: `tasks.md` - Complete task list
- **REQUIRED**: `plan.md` - Tech stack, architecture
- **IF EXISTS**: `data-model.md` - Entities
- **IF EXISTS**: `contracts/` - API specs
- **IF EXISTS**: `research.md` - Decisions
- **IF EXISTS**: `quickstart.md` - Integration scenarios

**AFTER loading:** Store feature understanding for cross-session recall:

```text
# [!] MANDATORY: Store understanding after loading feature context
store_understanding(
  scope="module",
  target="{{feature_dir}}",
  purpose="Feature implementation context for <feature_name>",
  importance="high",
  key_points=["<tech_stack>", "<key_entities>", "<main_tasks>"],
  gotchas=["<constraints>", "<dependencies>"],
  analysis="<detailed_logic_and_flow_explanation>",
  related_to=["<spec.md>", "<plan.md>", "<tasks.md>"]
)
```

---

## Step 2: Verify Project Setup

Create/verify ignore files based on tech stack:

**Detection:**

- `git rev-parse --git-dir` -> create .gitignore
- `Dockerfile*` exists -> create .dockerignore
- `.eslintrc*` exists -> create .eslintignore

**Common Patterns by Stack:**

- **Node.js**: `node_modules/`, `dist/`, `*.log`, `.env*`
- **Python**: `__pycache__/`, `.venv/`, `*.pyc`
- **Java**: `target/`, `*.class`, `build/`
- **.NET**: `bin/`, `obj/`, `*.user`
- **Universal**: `.DS_Store`, `.idea/`, `.vscode/`

**If file exists**: Append missing critical patterns only
**If missing**: Create with full pattern set

**Error handling**: If file write fails (permission denied, read-only), log warning and continue. Ignore file failures are non-blocking.

---

## Step 3: Parse Task Structure

From tasks.md extract:

- **Phases**: Setup, Tests, Core, Integration, Polish
- **Dependencies**: Sequential vs parallel rules
- **Details**: ID, description, file paths, `[P]` markers
- **Execution flow**: Order and dependency requirements

---

## Output

```text

[ok] Context loaded
  - Tasks: [N] across [N] phases
  - Tech stack: [detected]
  - Ignore files: [verified / created]

  AI Cache Status:
    - Feature context cached: [yes/no]
    - Design docs read: <count_read>
    - Understanding stored: <count_stored>
    - Compliance: <count_stored>/<count_read> = <percentage>%
```

**AI Cache Compliance Check:**

Before proceeding to execute, verify:

1. Feature context stored via `store_understanding(scope="module", target="{{feature_dir}}")`
2. Each design doc read has corresponding understanding stored
3. If compliance < 100%, go back and store missing understandings

---

## NEXT

```text

speckitadv implement
```
