---
stage: execute
requires: load-context
outputs: tasks_completed
version: 1.0.0
next: 05-complete.md
---

# Stage 4: Execute Tasks

## Purpose

Execute implementation following the task plan.

---

## [!] File Write Best Practices

**For large file generation:**

- Create files in chunks if content exceeds 2000 characters
- Write skeleton first, then fill sections incrementally
- If using shell commands with content, be aware of OS limits (~8000 chars on Windows)

---

## Tools (if REPOIX_MODE != "none")

{{include:implement-civyk-repoix-discovery.md}}

---

## Code Generation Guidelines

**Discovery-First (with AI Context Cache):**

```text
# FIRST: Check what's cached from earlier stages
get_understanding_stats(limit=50)

# Check cached understanding before reading files
recall_understanding(target="<module_or_file_path>")
# IF found AND fresh: Use cached patterns/conventions
# IF not found: Discover via tools below and store understanding after
```

- Use civyk-repoix MCP/CLI to discover existing utils, base classes, methods, patterns before creating new
- Use `get_duplicate_code(source_only=true)` to find similar implementations to extend
- Use `analyze_impact(fqn, depth=3)` BEFORE modifying any existing code
- Use `get_tests_for(path)` to identify tests that need updating
- Prefer extending existing patterns over introducing new ones

```text
# [!] MANDATORY: Store understanding for discovered patterns
store_understanding(
  scope="module",
  target="<module_path>",
  purpose="<module purpose>",
  importance="medium",
  key_points=["<patterns>", "<conventions>", "<key_classes>"],
  gotchas=["<edge_cases>", "<constraints>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Per-Task AI Cache Protocol

**For EACH task in tasks.md, apply 1:1 Read:Store rule:**

Note: `get_understanding_stats(limit=50)` was called at stage start - use its output to identify cached files.

```text
# BEFORE starting task: Check cache for files you'll need to read
# (Reference get_understanding_stats output from stage start)
recall_understanding(target="<file_you_need_to_read>")
# IF found AND fresh: Use cached analysis, skip file read
# IF not found OR stale: Read file, then MUST store understanding

# [!] MANDATORY: Store understanding for EACH file read
store_understanding(
  scope="file",
  target="<file_path>",
  purpose="<what this file does>",
  importance="<critical|high|medium|low>",
  key_points=["<main classes/functions>", "<patterns used>"],
  gotchas=["<edge_cases>", "<non-obvious_behaviors>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

**Per-Task Workflow:**

1. **Parse task** - identify files to read/modify
2. **For each file:** `recall_understanding()` - if not cached, read & `store_understanding()`
3. **Execute task** - create/modify code
4. **Mark [X]** in tasks.md
5. **Repeat** for next task

**Quality Standards:**

- Production-ready, functionally deterministic and idempotent
- Consider all edge cases in design, implementation, and test coverage
- Small commits (1 scenario, <300 lines)

**Quality Gates (Pre-Commit):**

- Zero compile errors
- Zero warnings (treat warnings as errors)
- Run: Formatters -> Linters -> Type checkers -> Build
- All new implementations covered by tests
- All new tests must pass

---

## Execution Rules

1. **Phase-by-phase**: Complete each phase before next
2. **Respect dependencies**: Sequential tasks in order
3. **Parallel tasks [P]**: Can run together
4. **File coordination**: Same-file tasks run sequentially
5. **Validation checkpoints**: Verify each phase

---

## Phase Order

### Phase 1: Setup

- Initialize project structure
- Install dependencies (validate against Artifactory first - see below)
- Create configuration

**Before installing dependencies:**

{{include:artifactory-validation.md}}

**Validation workflow:**

1. Extract dependencies from `package.json`, `requirements.txt`, `*.csproj`, etc.
2. Run `speckitadv search-lib <package>` for each
3. If `NOT FOUND`: STOP and report to user before installing
4. If `VERIFIED` or `SKIPPED`: Proceed with installation

**Phase 2: Foundational** (BLOCKING)

- Core infrastructure
- Shared utilities
- Must complete before user stories

### Phase 3+: User Stories

- One phase per story (P1, P2, P3...)
- Within each: Tests -> Models -> Services -> Endpoints
- Test each story independently

### Final: Polish

- Cross-cutting concerns
- Documentation
- Compliance verification

---

## Task Completion Tracking

**CRITICAL: EDIT tasks.md to mark [X] immediately after EACH task**

**Required action after completing any task:**

1. **STOP** before moving to next task
2. **EDIT** the tasks.md file directly
3. **CHANGE** `- [ ]` to `- [X]` for the completed task
4. **VERIFY** the edit saved successfully
5. **REPORT** progress to user

```markdown
Before: - [ ] T012 [US1] Create User model
After:  - [X] T012 [US1] Create User model
```

**Rules:**

- Do NOT batch completions - mark each task immediately
- Do NOT just report completion - you MUST edit tasks.md
- Verify previous task is marked [X] before starting next task
- If you cannot edit the file, STOP and report the issue

**After each phase completes:**

1. Verify ALL tasks in that phase show `[X]`
2. Count and report: "Phase N: X/Y tasks complete"
3. Run relevant tests to validate phase
4. Commit changes before proceeding to next phase

---

## Error Handling

- **Sequential task fails**: Halt execution
- **Parallel task fails**: Continue others, report failed
- Provide clear error messages with context
- If stopping mid-phase, report completed [X] vs remaining [ ]

---

## Output

After each task:

```text

[ok] T012 [US1] Create User model - COMPLETE
  - File: src/models/user.py
```

After each phase:

```text

[ok] Phase 3 (US1) Complete
  - Tasks: 8/8
  - Tests: Passing

  AI Cache Efficiency:
    - Files read this phase: <count_read>
    - Files cached (store_understanding): <count_stored>
    - Cache hits (found=true, fresh=true): <count_hits>
    - Compliance: <count_stored>/<count_read> = <percentage>%
```

**AI Cache Compliance Check:**

Before moving to the next phase, verify:

1. Every file read has a corresponding `store_understanding` call
2. `recall_understanding` was called before each file read
3. If compliance < 100%, go back and store missing understandings

---

## NEXT

```text

speckitadv implement
```
