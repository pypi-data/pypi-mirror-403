---
stage: validate-spec
requires: generate-spec
outputs: checklist_file, validation_passed
version: 1.2.0
next: 06-complete.md
---

{{include:verification-rules.md}}

# Stage 5: Validate Specification

## Purpose

Validate the specification against quality criteria.

---

## Step 1: Create Quality Checklist

Use the **Write tool** to create `{{feature_dir}}/checklists/requirements.md` with the following structure:

```markdown
# Specification Quality Checklist: <feature name from spec.md>

**Created**: <today's date>
**Feature**: [Link to spec.md]

## Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

## Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Success criteria are technology-agnostic
- [ ] All acceptance scenarios defined
- [ ] Edge cases identified
- [ ] Scope clearly bounded

## Feature Readiness
- [ ] Functional requirements have acceptance criteria
- [ ] User scenarios cover primary flows
- [ ] No implementation details leaked
```

---

## Step 2: Run Validation

Review spec against each checklist item:

- Mark each item pass/fail
- Document specific issues found

---

## Step 3: Handle Results

**If all items pass:**

- Mark checklist complete
- Continue to completion stage

**If items fail (not clarification markers):**

1. List failing items and issues
2. Update spec to fix issues
3. Re-validate (max 3 iterations)
4. If still failing, document in checklist notes

**If [NEEDS CLARIFICATION] markers remain:**

- Keep only 3 most critical (by scope/security/UX impact)
- Make informed guesses for the rest
- Present clarification questions to user
- Wait for responses, then update spec

---

## Output

```text
[ok] Validation complete
  - Passed: [N]/[Total] items
  - Clarifications: [0-3] pending
```

Then run the next command shown below.
