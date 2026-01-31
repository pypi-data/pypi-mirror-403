---
stage: complete
requires: generate
outputs: tasks_file
version: 1.1.0
next: null
---

{{include:verification-rules.md}}

# Stage 4: Complete

## Purpose

Validate and report task generation results.

---

## Step 1: Validate Format

Verify all tasks follow the required format:

- [ ] Every task has checkbox `- [ ]`
- [ ] Every task has ID (T001, T002...)
- [ ] User story tasks have `[USn]` label
- [ ] Tasks have file paths
- [ ] Parallel tasks correctly marked `[P]`

**Common issues:**

- Missing Task ID
- Missing file paths
- Incorrect [P] or [Story] markers

---

## Step 2: Validate Organization

- [ ] User stories map to spec.md priorities
- [ ] Foundational phase contains blocking tasks
- [ ] Parallel tasks are truly independent
- [ ] Dependencies are explicit

---

## Step 3: Generate Summary

```markdown
# Task Summary

**Total Tasks**: [N]
**Phases**: [N]

| Phase | Tasks | Parallel |
|-------|-------|----------|
| Setup | [N] | [N] |
| Foundational | [N] | [N] |
| US1: [name] | [N] | [N] |
| US2: [name] | [N] | [N] |
| Polish | [N] | [N] |

**MVP Scope**: User Story 1 (P1)
**Parallel Opportunities**: [N] tasks
```

---

## Output

```text

[ok] Task generation complete

File: {{feature_dir}}/tasks.md
Tasks: [N] total across [N] phases

Format validation: PASSED
Organization: PASSED
```

---

## WORKFLOW COMPLETE

Tasks are ready. Proceed to implementation.

**Recovery note**: Task generation is repeatable. Delete tasks.md and re-run if needed.
