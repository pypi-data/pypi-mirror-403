---
stage: remediation
requires: review
outputs: fixes_applied, quality_gates_passed
version: 6.0.0
---

{{include:strict-execution-mode-lite.md}}

# Remediation

Fix all issues from review, run gates, then return to Stage 1 for re-review.

---

## Rules

- Fix all issues before running gates
- Read file before modifying (no blind edits)
- Always return to Stage 1 after fixes (loop ends when review passes)
- Stay within scope (only fix files in `SCOPE_FILES`)

---

## Step 1: Load Scope and Findings

Load from CLI args:

- `REVIEW_SCOPE`: branch | staged | commits | files | uncommitted
- `REVIEW_FOCUS`: full | security | correctness | integration
- `SCOPE_FILES`: list of files in scope

---

## Step 2: Create TODO from Findings

```text
TODO (Iteration {iterations})
=============================
Focus: {REVIEW_FOCUS}
Scope: {REVIEW_SCOPE} ({file_count} files)

CRITICAL: [ ] Issue - file:line
HIGH:     [ ] Issue - file:line
MEDIUM:   [ ] Issue - file:line
LOW:      [ ] Issue - file:line
```

If findings were truncated: re-run Stage 1 first.

---

## Step 3: Recall Cache

```text
recall_understanding(target="<file_path>")
# Use cached understanding to inform fixes
```

---

## Step 4: Fix Each Issue

For each TODO item:

1. Read the code (understand context)
2. Implement minimal fix (smallest change needed)
3. Verify fix (single test or linter check)
4. Mark complete: `[X] Fixed: {description}`

Skip with evidence: `[SKIP] Not an issue - {proof/reason}`

**Fix quality:**

- No features beyond what's needed
- No refactoring surrounding code
- Delete unused code completely

**Scope boundary:**

- Only fix files in `SCOPE_FILES`
- If fix requires changes outside scope, note as: `[DEFER] Requires changes to {file} (out of scope)`

---

## Step 5: Quality Gates

Run once after all fixes (use project's configured commands):

| Gate | Check |
|------|-------|
| Lint | Run linter with auto-fix if available |
| Types | Run type checker (if applicable) |
| Build | Run build command |
| Tests | Run test suite |

Fix any failures before proceeding.

---

## Step 6: Commit

```bash
git status --porcelain | grep '^ M\|^M ' | cut -c4- | xargs git add

git commit -m "$(cat <<'EOF'
fix({focus}): review findings (iteration {iterations})

Scope: {REVIEW_SCOPE}
Focus: {REVIEW_FOCUS}
Fixed:
- [CRITICAL] description
- [HIGH] description
EOF
)"
```

Commit message prefix by focus:

- Security: `fix(security):`
- Correctness: `fix:`
- Integration: `fix(api):` or `fix(integration):`
- Full: `fix:`

Avoid `git add -A` (may include .env, credentials).

---

## Step 7: Summary

```text
Remediation Complete (Iteration {iterations})
Scope: {REVIEW_SCOPE} | Focus: {REVIEW_FOCUS}
Critical: [N] | High: [N] | Medium: [N] | Low: [N]
Fixed: [N] | Skipped: [N] | Deferred: [N]
```

---

## NEXT

```bash
speckitadv review --stage=1 --iterations={next_iteration} \
  --review-scope={REVIEW_SCOPE} \
  --review-focus={REVIEW_FOCUS} \
  --scope-files="{SCOPE_FILES}"
```
