# Verification Rules

**MUST execute verification steps EXACTLY as written.**

## Core Rules

| Rule | Description |
|------|-------------|
| Report PASS or FAIL | Each step gets explicit status |
| Stop on first FAIL | Do not continue past failures |
| Read plan in full | Understand all steps before starting |

## MUST NOT

- Skip, modify, or add steps not in the plan
- Interpret ambiguous instructions (mark as FAIL instead)
- Assume success without verification

## Gate Status Format

```text
[ ] Gate pending
[ok] Gate PASS
[x] Gate FAIL - {reason}
```

## Failure Recovery

When a gate fails:

1. Report which gate failed and why
2. Identify the recovery phase (where to return)
3. Do NOT continue past the failure
4. Wait for user decision if unclear
