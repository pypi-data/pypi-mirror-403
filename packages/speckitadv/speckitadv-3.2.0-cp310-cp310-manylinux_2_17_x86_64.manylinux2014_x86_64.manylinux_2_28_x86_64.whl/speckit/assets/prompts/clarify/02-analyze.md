---
stage: analyze
requires: initialization
outputs: questions_list
version: 1.0.0
next: 03-complete.md
---

# Stage 2: Analyze & Question

## Purpose

Scan for ambiguities and ask clarifying questions.

---

## Step 1: Ambiguity Scan

Check each category - mark: Clear / Partial / Missing

**Functional Scope:**

- Core user goals & success criteria
- Explicit out-of-scope declarations
- User roles differentiation

**Domain & Data:**

- Entities, attributes, relationships
- Identity & uniqueness rules
- Lifecycle/state transitions

**Interaction & UX:**

- Critical user journeys
- Error/empty/loading states
- Accessibility notes

**Non-Functional:**

- Performance targets
- Security & privacy
- Scalability limits

**Edge Cases:**

- Negative scenarios
- Conflict resolution
- Rate limiting

---

## Step 2: Generate Questions (Max 5)

For Partial/Missing categories, create questions that:

- Are answerable with short answer (<=5 words) OR multiple-choice
- Materially impact architecture, data, or testing
- Reduce downstream rework risk

**Question Format:**

For multiple-choice:

```text

**Recommended:** Option [X] - [reasoning]

| Option | Description |
|--------|-------------|
| A | [option description] |
| B | [option description] |

Reply with letter, "yes" for recommended, or short answer.
```

---

## Step 3: Ask Questions (Sequential)

- Present ONE question at a time
- Wait for user response
- Validate answer fits constraints
- Record answer in memory
- Move to next question

**Stop when:**

- All critical ambiguities resolved
- User signals done ("no more", "proceed")
- 5 questions asked

---

## Step 4: Update Spec

After each answer:

1. Add to `## Clarifications` section
2. Update relevant spec section
3. Save spec immediately

---

## Output

```text

[ok] Analysis complete
  - Questions asked: [N]/5
  - Categories resolved: [list]
```

---

## NEXT

```text

speckitadv clarify
```
