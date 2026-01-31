---
stage: coverage-review
requires: nothing
outputs: target_coverage_set, current_coverage_measured, coverage_gaps_identified, test_plan_created
version: 6.0.0
next: 02-implement-tests.md
---

{{include:strict-execution-mode.md}}

# Stage 1: Coverage Review

Find **test gaps** and **high-risk untested areas**. Create a prioritized test plan. Think like a QA engineer identifying the most impactful tests, not just chasing coverage %.

---

## Direct Mode (Args Provided)

If `{user_args}` contains scope info (e.g., "src/auth", "80%", "unit tests"):

1. Parse scope, target, type from args - NO user prompts needed
2. Jump directly to **Step 1: Detect civyk-repoix Mode**

Examples that trigger direct mode:
- `src/auth/ 90%` -> scope=src/auth, target=90%
- `unit tests for payment` -> type=unit, scope=payment
- `feature branch` -> scope=changed files vs main

---

## Interactive Mode (No Args)

Only if `{user_args}` is empty:

**[STOP: USER_INPUT_REQUIRED]**

What to test? Enter: scope (files/module/branch), target % (default 80), type (unit/integration/both)

Example: `src/auth/** 90% unit` or just press enter for full project at 80%

---

## Step 1: Detect civyk-repoix Mode

**MANDATORY FIRST STEP:**

```text
# Try MCP:
index_status()

# If MCP fails, try CLI:
civyk-repoix query index-status
```

Set `DISCOVERY_MODE` = `mcp` | `cli` | `none`

---

## Tools Reference

{{include:tests-civyk-repoix-discovery.md}}

---

## Step 2: Discover Test Gaps with civyk-repoix

**Find high-risk untested code:**

```text
# MCP mode:
get_hotspots(since="30d", limit=20)           # High-churn = high-risk
get_dead_code(limit=30)                        # May indicate untested code
get_tests_for(path="src/module.py")            # What tests exist?
get_recommended_tests(changed_files=[...])     # What tests should run?

# CLI mode:
civyk-repoix query get-hotspots --since 30d --limit 20
civyk-repoix query get-dead-code --limit 30
civyk-repoix query get-tests-for --path "src/module.py"
civyk-repoix query get-recommended-tests --changed-files "f1.py,f2.py"
```

**Find API endpoints for integration tests:**

```text
# MCP mode:
get_api_endpoints(kind="function", limit=50)

# CLI mode:
civyk-repoix query get-api-endpoints --kind function --limit 50
```

---

## Step 3: Analyze File Structure

For each file in scope:

```text
# MCP mode:
get_file_symbols(path="src/auth/login.py", kinds=["function", "class"])

# CLI mode:
civyk-repoix query get-file-symbols --path "src/auth/login.py" --kinds "function,class"
```

**Identify untested functions:**
- Public functions without corresponding test
- Error handling paths
- Edge case branches

---

## Step 4: Measure Current Coverage

Run project's test command with coverage:

```bash
# Python
pytest --cov=src --cov-report=term-missing

# Node.js
npm test -- --coverage

# Other
{project-specific coverage command}
```

```text
Scope: {scope} ({file_count} files)
Target: {TARGET}% | Current: {current}% | Gap: {gap}%
```

If current >= target: `[ok] TARGET MET` -> STOP

---

## Step 5: Prioritize Gaps

| Priority | What to Test | Why |
|----------|--------------|-----|
| P0 | Auth, payment, security | Critical paths |
| P0 | Public API endpoints | User-facing |
| P1 | Error handling, validation | Failure modes |
| P2 | Edge cases, boundaries | Robustness |
| P3 | Utilities, helpers | Lower risk |

---

## Step 6: Gap Report

| File | Current % | Key Untested Functions | Priority |
|------|-----------|----------------------|----------|
| path/to/file.py | 45% | `validate_token`, `handle_error` | P0 |

---

## Step 7: Test Plan

```text
=== TEST PLAN ===

Scope: {scope}
Target: {TARGET}% | Current: {current}% | Gap: {gap}%
Type: {TEST_TYPE}

Phase 1: Critical Paths (+{N}%)
  T-001: Test auth token validation - src/auth/token.py:validate
  T-002: Test payment processing errors - src/payment/process.py:handle_error

Phase 2: Error Handling (+{N}%)
  T-003: Test invalid input handling - src/api/handlers.py:parse_request

Phase 3: Edge Cases (+{N}%)
  T-004: Test boundary conditions - src/utils/validators.py:check_range

Total: {N} tests to write
Estimated coverage after: {estimated}%
```

---

## Step 8: Store Cache

```text
store_understanding(scope="module", target="<path>", purpose="Test coverage analysis",
  importance="high", key_points=["untested: X,Y,Z"], gotchas=["critical path in auth"])
```

---

## NEXT

```bash
speckitadv tests --stage=2 --iterations={iterations} \
  --target-coverage={TARGET} \
  --scope-mode={SCOPE_MODE} \
  --scope-pattern="{SCOPE_PATTERN}" \
  --test-type={TEST_TYPE}
```
