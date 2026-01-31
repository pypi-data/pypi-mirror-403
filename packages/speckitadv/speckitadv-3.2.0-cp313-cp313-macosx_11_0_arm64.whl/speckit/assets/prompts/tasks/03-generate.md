---
stage: generate
requires: setup
outputs: task_list
version: 1.2.0
next: 04-complete.md
---

{{include:ai-cache-enforcement.md}}

# Stage 3: Generate Tasks

## Purpose

Generate tasks organized by user story.

---

## File Write Best Practices

**For large task lists:**

- Write tasks.md in chunks if total content exceeds 2000 characters
- Group by phase: write Phase 1, then Phase 2, etc.
- If using shell commands with content, be aware of OS limits (~8000 chars on Windows)

---

## Tools (if REPOIX_MODE != "none")

{{include:task-civyk-repoix-discovery.md}}

### AI Context Cache for Task Generation

Before generating tasks, check cached understanding of codebase structure:

```text
# Recall cached project/module understanding for file path decisions
recall_understanding(target="project")
# IF error (MCP connection failed): Discover via file exploration
# IF found AND fresh: Use cached structure for accurate file paths
# IF not found OR stale: Discover via repoix tools
```

---

## Task Format (REQUIRED)

Every task MUST follow:

```text

- [ ] [TaskID] [P?] [Story?] Description with file path
```

Components:

1. **Checkbox**: Always `- [ ]`
2. **Task ID**: Sequential (T001, T002...)
3. **[P]**: Include ONLY if parallelizable
4. **[Story]**: Required for user story phases: `[US1]`, `[US2]`
5. **Description**: Clear action with exact file path

**Examples:**

- [ok] `- [ ] T001 Create project structure per plan`
- [ok] `- [ ] T005 [P] Implement auth middleware in src/middleware/auth.py`
- [ok] `- [ ] T012 [P] [US1] Create User model in src/models/user.py`
- [x] `- [ ] Create User model` (missing ID, Story)

---

## Phase Structure

**Phase 1: Setup** (no Story label)

- Project initialization
- Dependencies installation
- Configuration files

**Phase 2: Foundational** (no Story label)

- Blocking prerequisites for ALL user stories
- Core infrastructure

**Phase 3+: User Stories** (MUST have Story label)

- One phase per user story (P1, P2, P3...)
- Within each: Models -> Services -> Endpoints

**Final Phase: Polish** (no Story label)

- Cross-cutting concerns
- Documentation
- Guideline compliance verification

---

## Task Sources

1. **From User Stories** (spec.md): Each story gets its own phase
2. **From Contracts**: Map endpoints to stories
3. **From Data Model**: Map entities to stories
4. **From Setup**: Shared infrastructure -> Setup phase

---

## Step: Write Tasks File

Use the **Write tool** to create `{{feature_dir}}/tasks.md` with **complete content**.

**IMPORTANT:** Generate actual tasks from the user stories in spec.md. Do NOT include sample/placeholder tasks.

**Template structure:**

{{include:tasks-template.md}}

**Generation rules:**

- Replace ALL sample tasks with actual feature-specific tasks
- Remove all HTML comments (`<!-- ... -->`) from output
- Generate tasks from the actual user stories in spec.md
- Use sequential task IDs (T001, T002...)
- Mark parallelizable tasks with [P]
- Label user story tasks with [US1], [US2], etc.
- Include exact file paths in descriptions

---

## Output

```text
[ok] Tasks generated
  - Total: [N] tasks
  - Phases: [N] phases
  - Parallel opportunities: [N]
```

**Note:** Next command shown by CLI (`emit_stage`) - do not duplicate here.
