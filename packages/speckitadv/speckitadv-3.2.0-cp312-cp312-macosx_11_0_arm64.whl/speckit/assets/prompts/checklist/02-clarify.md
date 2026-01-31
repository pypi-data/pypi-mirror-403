---
stage: clarify
requires: initialization
outputs: checklist_focus
version: 1.0.0
next: 03-generate.md
---

# Stage 2: Clarify Intent

## Purpose

Determine checklist focus through clarifying questions.

---

## Step 1: Extract Signals

From user input and spec, identify:

- Domain keywords (auth, UX, API, security)
- Risk indicators ("critical", "must", "compliance")
- Stakeholder hints ("QA", "review", "security team")
- Deliverables ("a11y", "rollback", "contracts")

---

## Step 2: Generate Questions (Max 3)

**[STOP: USER_INPUT_REQUIRED]**

Ask up to THREE contextual questions about:

- **Scope**: Include integration touchpoints or stay local?
- **Risk**: Which areas need mandatory gating checks?
- **Depth**: Lightweight sanity or formal release gate?
- **Audience**: Author only or peer review?
- **Exclusions**: Skip performance tuning this round?

**Question Format:**

| Option | Candidate | Why It Matters |
|--------|-----------|----------------|
| A | [option] | [impact] |
| B | [option] | [impact] |

**[STOP: USER_INPUT_REQUIRED]**

MUST wait for user response before generating checklist.

---

## Step 3: Consolidate Requirements

Combine arguments + answers:

- Derive checklist theme (security, review, deploy, ux)
- Consolidate must-have items
- Map focus to category scaffolding
- Infer missing context from docs

---

## Defaults (if no interaction)

- Depth: Standard
- Audience: Reviewer (PR)
- Focus: Top 2 relevance clusters

---

## Output

```text

[ok] Intent clarified
  - Theme: [domain]
  - Focus areas: [list]
  - Audience: [author/reviewer/QA]
```

---

## NEXT

```text

speckitadv checklist
```
