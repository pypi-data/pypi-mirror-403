---
stage: generate
requires: clarify
outputs: checklist_file
version: 1.1.0
next: null
---

{{include:verification-rules.md}}

# Stage 3: Generate Checklist

## Purpose

Generate "unit tests for requirements" checklist.

---

## File Write Best Practices

**For large checklists:**

- Write checklist in sections if total content exceeds 2000 characters
- Group by quality dimension: Completeness, then Clarity, etc.
- If using shell commands with content, be aware of OS limits (~8000 chars on Windows)

---

## Item Format

**[ok] CORRECT (Testing requirements):**

- "Are visual hierarchy requirements defined with measurable criteria? [Clarity]"
- "Are hover state requirements consistent across all elements? [Consistency]"
- "Is fallback behavior defined when images fail to load? [Edge Case, Gap]"

**[x] WRONG (Testing implementation):**

- "Verify button clicks correctly"
- "Test hover states work"
- "Confirm API returns 200"

---

## Quality Dimensions

Organize items by:

- **Completeness**: Are all requirements present?
- **Clarity**: Are requirements unambiguous?
- **Consistency**: Do requirements align?
- **Measurability**: Can requirements be verified?
- **Coverage**: Are all scenarios addressed?
- **Edge Cases**: Are boundaries defined?

---

## Traceability

80%+ items MUST include:

- `[Spec SX.Y]` - Reference to spec section
- `[Gap]` - Missing requirement
- `[Ambiguity]` - Unclear requirement
- `[Conflict]` - Contradicting requirements

---

## File Structure

Create: `{{feature_dir}}/checklists/[domain].md`

```markdown
# [Domain] Requirements Quality Checklist

**Purpose**: Validate [domain] requirement quality
**Created**: {{date}}
**Feature**: {{feature_name}}

## Requirement Completeness
- [ ] CHK001 - Are [X] requirements defined? [Gap]

## Requirement Clarity
- [ ] CHK002 - Is '[term]' quantified? [Ambiguity, Spec SX]

## Scenario Coverage
- [ ] CHK003 - Are [edge cases] addressed? [Coverage]
```

---

## Output

```text

[ok] Checklist generated

File: {{feature_dir}}/checklists/[domain].md
Items: [N] total
Traceability: [N]% with references

Focus: [domain]
Audience: [audience]
```

---

## WORKFLOW COMPLETE

Checklist ready for requirements validation.

**Note**: Each `/speckitadv.checklist` run creates a NEW file. Use descriptive domain names.
