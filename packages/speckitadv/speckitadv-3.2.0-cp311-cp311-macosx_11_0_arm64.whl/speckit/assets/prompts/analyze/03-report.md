---
description: Cross-artifact consistency analysis - Stage 3: Report generation
stage: 3
total_stages: 3
---

## Produce Compact Analysis Report

Output a Markdown report with the following structure:

### Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| ---- | ---------- | ---------- | ------------- | --------- | ---------------- |
| A1 | Duplication | HIGH | spec.md:L120-134 | Two similar requirements ... | Merge phrasing; keep clearer version |

(One row per finding; generate stable IDs prefixed by category initial.)

### Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
| ----------------- | ----------- | ---------- | ------- |

### Constitution Alignment Issues

(List any violations)

### Unmapped Tasks

(List tasks with no mapped requirement/story)

### Metrics

- Total Requirements
- Total Tasks
- Coverage % (requirements with >=1 task)
- Ambiguity Count
- Duplication Count
- Critical Issues Count

## Provide Next Actions

- If CRITICAL issues exist: Recommend resolving before `speckitadv implement`
- If only LOW/MEDIUM: User may proceed, provide improvement suggestions
- Suggest commands: `speckitadv specify --feature "refined"`, `speckitadv plan --constraints "new"`

## Offer Remediation

Ask: "Would you like me to suggest concrete remediation edits for the top N issues?"

(Do NOT apply edits automatically - this is read-only analysis)

---

## Operating Constraints

**STRICTLY READ-ONLY**: Do not modify any files. Output structured analysis report only.

**Constitution Authority**: The project constitution is **non-negotiable**. Constitution conflicts are automatically CRITICAL and require adjustment of the spec, plan, or tasks-not dilution of the principle.

## Operating Principles

- **Minimal high-signal tokens**: Focus on actionable findings
- **Progressive disclosure**: Load artifacts incrementally
- **Token-efficient output**: Limit to 50 rows; summarize overflow
- **Deterministic results**: Rerunning should produce consistent IDs and counts
- **NEVER modify files**
- **NEVER hallucinate missing sections**
- **Prioritize constitution violations**
- **Report zero issues gracefully** with success report and statistics
