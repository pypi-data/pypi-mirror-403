---
stage: review
requires: nothing
outputs: findings_report
version: 8.0.0
---

{{include:strict-execution-mode-lite.md}}

# Deep Code Review

Find **potential issues** and **potential enhancements**. Think like a senior engineer doing thorough PR review - cross-reference related files, check consistency, find what could go wrong.

---

## Direct Mode (Args Provided)

If `{user_args}` contains scope info (e.g., "last 5 commits", "staged changes", file paths):

1. Parse scope from args - NO user prompts needed
2. Jump directly to **Step 1: Analyze Changes**

Examples that trigger direct mode:
- `last 3 commits` -> `git diff HEAD~3..HEAD`
- `staged` -> `git diff --cached`
- `src/auth/` -> files in that path
- `feature branch` -> `git diff main...HEAD`

---

## Interactive Mode (No Args)

Only if `{user_args}` is empty or "$SKIP":

**[STOP: USER_INPUT_REQUIRED]**

What to review? (A) Feature branch, (B) Staged, (C) Last N commits, (D) Files, (E) Uncommitted

---

## Tools: civyk-repoix

{{include:review-civyk-repoix-discovery.md}}

**USE THESE TOOLS** (after mode detection):

| Task | Tool |
|------|------|
| Branch changes | `build_delta_context_pack(include_symbols=true)` |
| Impact of change | `analyze_impact(fqn="...", depth=2)` |
| Who calls this | `get_callers(fqn="...", depth=2)` |
| Find references | `get_references(fqn="...")` |
| Similar code | `find_similar(fqn="...")` or `get_duplicate_code(source_only=true)` |
| File structure | `get_file_symbols(path="...")` |
| Hotspots | `get_hotspots(since="30d")` |

---

## Step 1: Get Changed Files with civyk-repoix

**FIRST: Detect mode** (run `index_status()` or `civyk-repoix query index-status`)

**THEN: Get changes with context:**

```text
# MCP mode:
build_delta_context_pack(include_symbols=true, token_budget=3000)

# CLI mode:
civyk-repoix query build-delta-context-pack --include-symbols true --token-budget 3000
```

This returns: changed files, modified symbols, affected callers - everything needed to understand the change scope.

**Also get git diff for line-level details:**

```bash
git diff {scope} --stat
git log {scope} --oneline  # Commit messages explain intent
```

---

## Step 2: Analyze Impact with civyk-repoix

For each significant changed function/class:

```text
# MCP mode:
analyze_impact(fqn="path.to.function", depth=2, include_tests=true)
get_callers(fqn="path.to.function", depth=2)

# CLI mode:
civyk-repoix query analyze-impact --fqn "path.to.function" --depth 2 --include-tests true
civyk-repoix query get-callers --fqn "path.to.function" --depth 2
```

**Questions to answer:**
- Who calls the changed code? Are callers affected?
- What tests cover this code? Do tests need updating?
- What's the blast radius of this change?

---

## Step 3: Cross-Reference for Consistency

**CRITICAL: If a pattern was changed, check ALL similar files.**

```text
# Find similar code patterns:
# MCP mode:
get_duplicate_code(source_only=true, similarity_threshold=0.7)
find_similar(fqn="path.to.changed.function", similarity_threshold=0.6)

# CLI mode:
civyk-repoix query get-duplicate-code --source-only true --similarity-threshold 0.7
civyk-repoix query find-similar --fqn "path.to.changed.function" --similarity-threshold 0.6
```

**Also use grep for pattern consistency:**

```bash
# Example: if --source-only was fixed in one template
grep -rn "source-only" templates/  # Check ALL templates have same fix
```

**This step often finds MORE issues than the original scope.**

---

## Step 3: Deep Analysis

For each file (changed + related):

### Potential Issues

| Category | Questions |
|----------|-----------|
| **Logic** | Off-by-one? Null handling? Edge cases? |
| **Security** | Injection? Auth bypass? Secrets exposed? |
| **Consistency** | Same pattern everywhere? Naming consistent? |
| **Integration** | Callers updated? Contracts honored? |
| **Error handling** | All errors caught? Meaningful messages? |

### Potential Enhancements

| Category | Questions |
|----------|-----------|
| **Simplification** | Can code be simpler? Dead code? |
| **Robustness** | Missing validation? Better defaults? |
| **Performance** | N+1 queries? Unnecessary loops? |
| **Maintainability** | Magic numbers? Missing types? |

---

## Step 4: Report Findings

### Issues Found

```text
### [CRITICAL/HIGH/MEDIUM/LOW] Brief title

**File:** path/to/file.ext:LINE
**Issue:** What's wrong
**Impact:** What could happen
**Fix:** How to fix it
```

### Enhancements Found

```text
### [ENHANCEMENT] Brief title

**File:** path/to/file.ext:LINE
**Current:** What exists now
**Suggestion:** What would be better
**Rationale:** Why it's better
```

### Cross-Reference Findings

```text
### [CONSISTENCY] Brief title

**Pattern:** What should be consistent
**Files checked:** N files
**Issues:** Which files have inconsistency
**Fix:** Apply same fix to all
```

---

## Step 5: Summary

```text
=== REVIEW COMPLETE ===

Scope: {description}
Files reviewed: {N} (direct) + {M} (cross-referenced)

ISSUES:
- Critical: {N}
- High: {N}
- Medium: {N}
- Low: {N}

ENHANCEMENTS: {N}
CONSISTENCY ISSUES: {N}

{If issues found: List top 3 most important to fix}
```

---

## Gate

**PASS** if: Critical=0 AND High=0
**NEEDS_ATTENTION** if: Critical=0 AND High>0
**FAIL** if: Critical>0

If FAIL or NEEDS_ATTENTION -> Stage 2 (remediation)

---

## NEXT

```bash
speckitadv review --stage=2 --iterations={iterations} \
  --review-scope={REVIEW_SCOPE} \
  --review-focus={REVIEW_FOCUS} \
  --scope-files="{SCOPE_FILES}"
```
