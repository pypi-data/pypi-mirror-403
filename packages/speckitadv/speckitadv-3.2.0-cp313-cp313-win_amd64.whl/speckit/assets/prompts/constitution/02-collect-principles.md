---
stage: collect-principles
requires: initialization
outputs: principles_collected
version: 1.1.0
next: 03-generate-constitution.md
---

{{include:verification-rules.md}}

# Stage 2: Collect Principles

## Purpose

Structure the collected principles for constitution generation.

---

## Pre-Check: Verify Principles Provided

**IF** `{principles}` is empty or shows only "$NONE":

```text
[!] ERROR: No principles provided

Stage 2 requires either --defaults or --principles flag.
Re-run with:
  speckitadv constitution --defaults
  OR
  speckitadv constitution --principles="Your principles here"
```

**STOP** - Do not proceed until principles are provided via CLI flags.

---

## Collected Principles

The following principles have been collected:

{principles}

Source: {source:User input}

---

## Task

Review and validate the principles above:

1. **Check completeness** - Are all key areas covered?
   - Code quality and standards
   - Testing requirements
   - Documentation standards
   - Security practices
   - Architecture constraints

2. **Check clarity** - Is each principle:
   - Specific and measurable?
   - Using normative language (MUST, SHOULD, MAY)?
   - Actionable in code reviews?

3. **Identify gaps** - Suggest additional principles if critical areas are missing

---

## Output

Confirm principles are ready for constitution generation:

```text
[ok] Principles validated: [N] principles
  - Quality coverage: [Complete/Needs additions]
  - Ready for constitution generation
```

---

## NEXT

Run the next stage to generate the constitution:

```bash
speckitadv constitution
```
