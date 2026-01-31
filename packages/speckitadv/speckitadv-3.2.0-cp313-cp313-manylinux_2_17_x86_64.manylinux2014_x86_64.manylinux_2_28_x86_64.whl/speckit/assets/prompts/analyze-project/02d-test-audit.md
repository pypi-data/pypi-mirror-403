---
stage: file_analysis_phase4
requires: 02c-config-analysis complete
outputs: test_and_dependency_audit
version: 3.6.0
time_allocation: 20%
---

# Stage 2D: Test Coverage & Dependency Audit (Phase 4)

## Purpose

Analyze test coverage and patterns using CLI-based discovery followed by deep file reading. Also perform comprehensive dependency audit for security vulnerabilities and outdated packages.

**Time Allocation:** 20% of file analysis effort

---

{{include:strict-execution-mode.md}}

{{include:analyze-state-management.md}}

{{include:analyze-file-write-policy.md}}

{{include:ai-cache-enforcement.md}}

---

## AI Context Cache: Check Cached Understanding

Before running test discovery, check for cached test-related understanding:

```text
recall_understanding(target="project")
recall_understanding(target="tests")
# IF found AND fresh: Use cached, then store_understanding after audit

store_understanding(
  scope="module",
  target="tests",
  purpose="Test coverage and quality patterns",
  importance="high",
  key_points=["<test framework>", "<coverage estimate>", "<test patterns>"],
  gotchas=["<coverage gaps>", "<untested critical paths>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Pre-Check: Verify Previous Substage

1. Verify `{data_dir}/config-analysis.json` exists
2. Load configuration analysis results

**IF not complete:** STOP - Return to 02c-config-analysis

---

## Step 1: Run Test Scan

Execute the deterministic test-scan CLI command:

```bash
speckitadv test-scan "{project_path}" --analysis-dir "{analysis_dir}"
```

This single command:

1. Finds all test files by pattern
2. Searches for test-related symbols (test classes)
3. Maps tests to source files via `get_code_for_test`

**Output:** `{data_dir}/test-audit.json`

---

**[STOP: TEST_SCAN]**

Execute the command and verify output.

**IF successful:** test-audit.json will be created
**IF fails:** Check civyk-repoix daemon status and retry

---

## Step 2: Read Discovery Results

Read the generated test scan results:

```bash
Read file: {data_dir}/test-audit.json
```

Review the discovered test structure:

- `test_files` - All test files found with path, language, symbol count
- `total_test_files` - Total count of test files
- `test_classes` - Test class symbols found (name, file, FQN)
- `coverage_mapping` - Tests mapped to source files they cover
- `patterns_searched` - Test file patterns that were searched

---

## Step 3: Test Framework Analysis

Read representative test files for deeper understanding:

```text
# Check cache first
recall_understanding(target="{project_path}/{test_file_1}")
# IF not cached: Read file: {project_path}/{test_file_1}
# [!] NOW CALL store_understanding for the file above

recall_understanding(target="{project_path}/{test_file_2}")
# IF not cached: Read file: {project_path}/{test_file_2}
# [!] NOW CALL store_understanding for the file above
```

---
**[STOP: DETECT_TEST_FRAMEWORK]**

Identify the testing frameworks and patterns in use:

**Detection Patterns:**

| Framework | Language | Indicators |
|-----------|----------|------------|
| JUnit 4/5 | Java | `org.junit`, `@Test`, `junit-*.jar` |
| TestNG | Java | `org.testng`, `@Test`, `testng.xml` |
| Jest | JavaScript | `jest.config.js`, `@jest`, `describe/it/test` |
| Mocha | JavaScript | `mocha.opts`, `mocharc.*`, `describe/it` |
| pytest | Python | `pytest.ini`, `conftest.py`, `test_*.py` |
| unittest | Python | `unittest`, `TestCase` |
| RSpec | Ruby | `_spec.rb`, `spec_helper.rb` |
| xUnit | .NET | `xunit`, `[Fact]`, `[Theory]` |
| NUnit | .NET | `nunit`, `[Test]`, `[TestCase]` |
| Go testing | Go | `*_test.go`, `testing.T` |

**Output:**

```text
Test Framework Detection:

Primary Framework: {framework}
Version: {version if detectable}
Configuration File: {path if exists}
Additional Frameworks: {list if multiple}

```

---

## Step 4: Test Coverage Analysis

Based on discovery results, analyze test coverage:

---
**[STOP: ANALYZE_TEST_COVERAGE]**

Using data from test-audit.json and file reading, estimate coverage:

**Metrics to Extract:**

1. **Test File Count:**
   - Unit tests
   - Integration tests
   - E2E tests
   - Performance tests

2. **Test Distribution:**
   - Tests per module/package
   - Coverage by category (controllers, services, models)

3. **Test Patterns:**
   - Naming conventions
   - Setup/teardown patterns
   - Mock usage
   - Data factories/fixtures

4. **Test Quality Indicators:**
   - Assertions per test (average)
   - Test isolation (mocking external deps)
   - Parameterized/data-driven tests
   - Negative tests (error cases)

**Output Format:**

```text
Test Coverage Analysis:

Test Files: {count}
  Unit Tests: {count}
  Integration Tests: {count}
  E2E Tests: {count}

Test Distribution by Module:
  {module1}: {test_count} tests
  {module2}: {test_count} tests
  ...

Coverage Estimate:
  Controllers: {percentage}% covered
  Services: {percentage}% covered
  Models: {percentage}% covered
  Repositories: {percentage}% covered
  Overall: {percentage}% estimated

Test Quality:
  Avg Assertions/Test: {n}
  Mocking Used: {yes/no}
  Parameterized Tests: {count}
  Error Case Tests: {count}

```

---

## Step 5: Coverage Gaps Identification

Using `coverage_mapping` and file reading to identify gaps:

---
**[STOP: IDENTIFY_COVERAGE_GAPS]**

Identify files and modules WITHOUT corresponding tests:

**Gap Analysis:**

1. **Source files without test files:**
   - List files in `src/` without corresponding test
   - Prioritize by criticality

2. **Critical untested code:**
   - Security-related code
   - Payment/financial logic
   - Authentication flows
   - Error handling paths

**Output Format:**

```text
Test Coverage Gaps:

Untested Files: {count}/{total} ({percentage}%)

Critical Gaps (HIGH priority):
  [!] {SecurityConfig.java} - No test file
  [!] {PaymentService.java} - No test file
  [!] {AuthController.java} - Only {n} tests

Moderate Gaps (MEDIUM priority):
  [!] {UserService.java} - Partial coverage
  [!] {OrderRepository.java} - Missing edge cases

Low Priority Gaps:
  [ok] {UtilityHelper.java} - Utility class

```

---

## Step 6: Dependency Audit

Read dependency files from the project:

```text
# Check cache first for each dependency file
recall_understanding(target="{project_path}/package.json")
# IF not cached AND exists: Read file: {project_path}/package.json
# [!] NOW CALL store_understanding for the file above

recall_understanding(target="{project_path}/requirements.txt")
# IF not cached AND exists: Read file: {project_path}/requirements.txt
# [!] NOW CALL store_understanding for the file above

recall_understanding(target="{project_path}/pom.xml")
# IF not cached AND exists: Read file: {project_path}/pom.xml
# [!] NOW CALL store_understanding for the file above

recall_understanding(target="{project_path}/go.mod")
# IF not cached AND exists: Read file: {project_path}/go.mod
# [!] NOW CALL store_understanding for the file above
```

---
**[STOP: AUDIT_DEPENDENCIES]**

Perform comprehensive dependency security and freshness audit:

**For Each Dependency:**

1. **Version Status:**
   - Current version
   - Latest stable version
   - Latest LTS version (if applicable)
   - Version age

2. **Security Check:**
   - Known CVEs
   - Severity (CRITICAL/HIGH/MEDIUM/LOW)
   - Affected versions
   - Fixed version

3. **Maintenance Status:**
   - Last publish date
   - Active maintenance
   - Deprecation status

**Data Sources to Reference:**

- NPM audit / npm outdated
- Maven dependency:check
- pip-audit / safety
- cargo audit
- OWASP Dependency Check patterns
- Snyk database patterns

**Output Format:**

```text
Dependency Audit:

Total Dependencies: {count}
  Direct: {count}
  Transitive: {count}

===========================================================
SECURITY VULNERABILITIES
===========================================================

[!] CRITICAL ({count}):
  {package} v{current}
    CVE: {CVE-YYYY-NNNNN}
    Description: {brief description}
    Fix: Upgrade to v{fixed_version}

[!] HIGH ({count}):
  {package} v{current}
    CVE: {CVE-YYYY-NNNNN}
    Description: {brief description}
    Fix: Upgrade to v{fixed_version}

[!] MEDIUM ({count}):
  {package} v{current} - {issue}

[ok] LOW ({count}):
  {package} v{current} - {issue}

===========================================================
OUTDATED DEPENDENCIES
===========================================================

Major Version Behind ({count}):
  {package}: v{current} -> v{latest} (major update)

Minor Version Behind ({count}):
  {package}: v{current} -> v{latest} (minor update)

Patch Behind ({count}):
  {package}: v{current} -> v{latest} (patch update)

===========================================================
DEPRECATED PACKAGES
===========================================================

{package} - Deprecated, use {replacement}

```

---

## Step 7: Compile Audit Results

Merge CLI discovery with file reading insights into comprehensive audit summary:

```json
{
  "test_audit": {
    "framework": "{framework}",
    "framework_version": "{version}",
    "test_files": {
      "unit": {count},
      "integration": {count},
      "e2e": {count},
      "total": {count}
    },
    "coverage_estimate": {
      "controllers": "{percentage}%",
      "services": "{percentage}%",
      "models": "{percentage}%",
      "overall": "{percentage}%"
    },
    "quality_metrics": {
      "avg_assertions": {n},
      "mocking_used": true,
      "parameterized_tests": {count}
    },
    "gaps": {
      "untested_files": {count},
      "critical_gaps": ["{list}"],
      "moderate_gaps": ["{list}"]
    }
  },
  "dependency_audit": {
    "total": {count},
    "direct": {count},
    "transitive": {count},
    "vulnerabilities": {
      "critical": {count},
      "high": {count},
      "medium": {count},
      "low": {count},
      "total": {count}
    },
    "outdated": {
      "major": {count},
      "minor": {count},
      "patch": {count}
    },
    "deprecated": {count},
    "vulnerable_packages": [
      {
        "name": "{package}",
        "version": "{current}",
        "severity": "CRITICAL",
        "cve": "{CVE}",
        "fixed_in": "{version}"
      }
    ]
  }
}

```

Save test and dependency audit to `{data_dir}/test-audit.json`:

```powershell
@"
<full test_audit and dependency_audit json here>
"@ | speckitadv write-data test-audit.json --stage=02d-test-audit --stdin
```

---

## Output Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 02d-test-audit (Phase 4)

  Time Used: 20% allocation

  Test Analysis:
    Framework: {framework}
    Test Files: {count}
    Coverage Estimate: {percentage}%
    Critical Gaps: {count}

  Dependency Audit:
    Total Dependencies: {count}
    Vulnerabilities: {count} ({critical} critical)
    Outdated: {count}

  Proceeding to Quality Gates
===========================================================

```

---

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits the next prompt. **Do NOT analyze or generate artifacts until you run this command.**
