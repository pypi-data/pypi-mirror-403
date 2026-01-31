---
stage: implement-tests
requires: coverage-review
outputs: tests_implemented, coverage_improved, changes_committed
version: 5.0.0
next: 01-coverage-review.md
---

{{include:strict-execution-mode.md}}

# Stage 2: Implement Tests

Implement all tests from Stage 1 plan, then return to Stage 1 for re-measurement.

---

## Rules

- Read code before writing tests (no guessing signatures)
- Implement all tests before running suite
- Return to Stage 1 after implementation (loop ends when target met)
- Respect test type from scope configuration

---

## Reference

{{include:tests-industry-standards-brief.md}}

---

## Step 1: Load Plan and Scope

`speckitadv check --json` -> `target`, `current`, `gap`

Load from CLI args:

- `SCOPE_MODE`: branch | module | files | full
- `SCOPE_PATTERN`: glob or class pattern (if applicable)
- `TEST_TYPE`: unit | integration | both
- `TARGET`: coverage percentage

---

## Step 2: Recall Cache

```text
recall_understanding(target="<module_path>")
# Use cached understanding for edge cases and gotchas
```

---

## Step 3: Implement Tests

Complete every test (T-001 to T-NNN) before Step 4.

For each test:

1. Read target code
2. Write test following type conventions (see below)
3. Verify single test passes
4. Mark: `[X] T-001: Done`

**Test quality:**

- One behavior per test
- No unnecessary setup/teardown
- Read before write (no guessing)

```text
Planned: [N] | Done: [N] | Remaining: [0]
```

---

## Test Type Conventions

### Unit Tests (`TEST_TYPE=unit`)

**File naming:**

- JavaScript/TypeScript: `*.test.ts`, `*.test.js`, `*.spec.ts`
- Python: `test_*.py`, `*_test.py`
- Java: `*Test.java`
- Go: `*_test.go`

**Characteristics:**

- Mock all external dependencies
- No database, network, or file system calls
- Fast execution (< 100ms per test)
- Isolated - no shared state between tests

**Example structure:**

```text
describe('UserValidator', () => {
  it('should reject empty email', () => {
    // Arrange - setup with mocks
    // Act - call the function
    // Assert - verify behavior
  });
});
```

### Integration Tests (`TEST_TYPE=integration`)

**File naming:**

- JavaScript/TypeScript: `*.integration.ts`, `*.e2e.ts`, `*.integration.test.ts`
- Python: `test_*_integration.py`, `*_integration_test.py`
- Java: `*IntegrationTest.java`, `*IT.java`
- Go: `*_integration_test.go`

**Characteristics:**

- Use real dependencies (database, services)
- Test module boundaries and contracts
- May require setup/teardown for resources
- Slower execution (acceptable)

**Example structure:**

```text
describe('UserAPI Integration', () => {
  beforeAll(() => {
    // Setup test database, seed data
  });

  afterAll(() => {
    // Cleanup resources
  });

  it('should create user and return 201', () => {
    // Test real API endpoint
  });
});
```

### Both (`TEST_TYPE=both`)

Assign test type based on what's being tested:

| Testing | Type | Rationale |
|---------|------|-----------|
| Pure functions | unit | No dependencies |
| Validators | unit | Logic only |
| API endpoints | integration | Full request/response cycle |
| Database operations | integration | Real data layer |
| Service orchestration | integration | Multiple components |
| Error handling (internal) | unit | Logic flow |
| Error handling (external) | integration | Real error responses |

---

## Step 4: Run Suite

Run project's test command with coverage enabled.

**Filter by test type if needed:**

- Unit only: run fast test suite (exclude integration tags/folders)
- Integration only: run integration suite (specific tags/folders)
- Both: run full suite

---

## Step 5: Commit

```bash
# Add test files by pattern (match test type naming)
git add <test-files>

git commit -m "$(cat <<'EOF'
test({type}): add {test_type} tests for coverage improvement

Scope: {SCOPE_MODE}
Coverage: {old}% -> {new}%
Tests added: [list test files]
EOF
)"
```

Commit message prefix by type:

- Unit: `test(unit):`
- Integration: `test(integration):`
- Both: `test:`

Avoid `git add -A` (may include secrets, binaries).

---

## Step 6: Gate

If new >= target: `[ok] TARGET ACHIEVED` -> STOP

---

## NEXT

```bash
speckitadv tests --stage=1 --iterations={next_iteration} \
  --target-coverage={TARGET} \
  --scope-mode={SCOPE_MODE} \
  --scope-pattern="{SCOPE_PATTERN}" \
  --test-type={TEST_TYPE}
```
