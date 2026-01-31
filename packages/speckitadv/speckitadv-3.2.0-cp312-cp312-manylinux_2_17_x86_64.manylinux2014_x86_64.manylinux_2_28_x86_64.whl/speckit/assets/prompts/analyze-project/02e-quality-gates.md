---
stage: file_analysis_verification
requires: 02d-test-audit complete
outputs: file_analysis_complete
version: 3.6.0
---

# Stage 2E: Quality Gates & Completion

## Purpose

Verify file analysis meets quality standards using CLI-based quality analysis. This is a mandatory verification stage - the workflow cannot continue until all quality gates pass.

---

{{include:strict-execution-mode.md}}

{{include:analyze-state-management.md}}

{{include:verification-rules.md}}

{{include:security-findings-format.md}}

**Branching:** After this stage, CLI auto-routes based on scope:

- Scope A -> Stage 3A (Full App Analysis)
- Scope B -> Stage 3B (Cross-Cutting Analysis)

---

## Pre-Check: Verify Previous Substage

1. Verify `{data_dir}/test-audit.json` exists
2. Load all Phase 1-4 results

**IF not complete:** STOP - Return to 02d-test-audit

---

## Step 1: Run Quality Scan

Execute the deterministic quality-scan CLI command:

```bash
speckitadv quality-scan "{project_path}" --analysis-dir "{analysis_dir}"
```

This single command:

1. Detects circular dependencies
2. Identifies high-churn hotspots
3. Finds dead code
4. Aggregates quality metrics

**Output:** `{data_dir}/quality-gates.json`

---

**[STOP: QUALITY_SCAN]**

Execute the command and verify output.

**IF successful:** quality-gates.json will be created
**IF fails:** Check civyk-repoix daemon status and retry

---

## Step 2: Load All Phase Results

Read the quality scan results and all previous phase data:

```bash
Read file: {data_dir}/quality-gates.json
Read file: {data_dir}/category-patterns.json
Read file: {data_dir}/deep-dive-patterns.json
Read file: {data_dir}/config-analysis.json
Read file: {data_dir}/test-audit.json
```

Review the quality scan results:

- `circular_dependencies` - Detected circular dependency cycles (count and details)
- `dead_code` - Unreferenced symbols (count and symbol list)
- `hotspots` - High-churn files and components
- `quality_score` - Aggregated score, grade (A-F), and issue counts

**Note:** State is managed by CLI. Use data files for analysis results.

---

## Step 3: Quality Gate Verification

---
**[STOP: QUALITY_GATE_CHECK]**

Verify each quality gate. All gates MUST pass before proceeding.

| Gate | Requirement | Recovery Phase |
|------|-------------|----------------|
| File Coverage | >= 70% of important files analyzed | 02b-deep-dive |
| Config Complete | 100% config files analyzed | 02c-config-analysis |
| Features | >= 50 with file:line references | 02b-deep-dive |
| Tech Debt | >= 20 items categorized by severity | 02b-deep-dive |
| Security | >= 10 findings (vulnerabilities or good practices) | 02b-deep-dive |
| Dependencies | Audit complete with vulnerability check | 02d-test-audit |

**Check each gate:**

```text
[ ] File Coverage: {percentage}% >= 70%
[ ] Config Complete: {percentage}% = 100%
[ ] Features: {count} >= 50
[ ] Tech Debt: {count} >= 20
[ ] Security: {count} >= 10
[ ] Dependencies: audit complete
```

**IF ANY GATE FAILS:**

```text
[x] Quality Gate Failed: {gate_name}
Current: {value} (required: {threshold})
Action: Return to {recovery_phase} and complete missing analysis
```

STOP - Do not proceed until all gates pass.

---

## Step 4: Compile Final Stage 2 State

Merge all phase results into comprehensive state:

```json
{
  "schema_version": "3.1.0",
  "chain_id": "{chain_id}",
  "stage": "file_analysis",
  "timestamp": "{ISO-8601}",
  "stages_complete": ["setup_and_scope", "file_analysis"],
  "analysis_scope": "{A or B}",

  "patterns_found": {
    "auth": {
      "type": "{mechanism}",
      "storage": "{user storage}",
      "password_hashing": "{algorithm}",
      "token": "{type with config}",
      "authorization": "{model}"
    },
    "database": {
      "engine": "{database}",
      "orm": "{framework}",
      "entities": {count},
      "relationships": {count},
      "native_queries": {count}
    },
    "api": {
      "style": "{REST/GraphQL}",
      "endpoints": {count},
      "versioning": "{strategy}",
      "documentation": "{type}"
    },
    "caching": {
      "present": true,
      "type": "{Redis/Memcached/etc}",
      "strategy": "{pattern}"
    },
    "observability": {
      "logging": "{framework}",
      "metrics": "{present/absent}",
      "tracing": "{present/absent}"
    }
  },

  "files_analyzed": {
    "total_scanned": {count},
    "total_project": {count},
    "coverage_percentage": "{percentage}%",
    "by_category": {
      "controllers": {count},
      "services": {count},
      "models": {count},
      "repositories": {count},
      "configs": {count},
      "security": {count},
      "tests": {count}
    }
  },

  "features_extracted": {
    "total": {count},
    "with_references": {count},
    "by_type": {
      "endpoints": {count},
      "workflows": {count},
      "business_rules": {count},
      "integrations": {count}
    }
  },

  "technical_debt": {
    "total": {count},
    "by_severity": {
      "high": {count},
      "medium": {count},
      "low": {count}
    },
    "items": [
      {
        "id": "TD-001",
        "severity": "HIGH",
        "category": "{category}",
        "description": "{description}",
        "location": "{file:line}",
        "impact": "{impact}",
        "recommendation": "{fix}"
      }
    ]
  },

  "security_findings": {
    "total": {count},
    "vulnerabilities": {count},
    "good_practices": {count},
    "items": [
      {
        "id": "SEC-001",
        "severity": "HIGH",
        "type": "vulnerability",
        "description": "{description}",
        "location": "{file:line}",
        "recommendation": "{fix}"
      }
    ]
  },

  "dependencies": {
    "total": {count},
    "direct": {count},
    "transitive": {count},
    "vulnerabilities": {
      "critical": {count},
      "high": {count},
      "medium": {count},
      "low": {count}
    },
    "outdated": {
      "major": {count},
      "minor": {count},
      "patch": {count}
    }
  },

  "test_coverage": {
    "framework": "{framework}",
    "test_files": {count},
    "estimated_coverage": "{percentage}%",
    "gaps": ["{critical untested areas}"]
  },

  "quality_gates": {
    "file_coverage": "PASS",
    "config_complete": "PASS",
    "feature_count": "PASS",
    "tech_debt_count": "PASS",
    "security_findings": "PASS",
    "dependency_audit": "PASS",
    "all_passed": true
  }
}

```

---

## Step 5: Save Enhanced Quality Gates

Save the quality gates with verification results to `{data_dir}/quality-gates.json`:

```powershell
@"
{
  "quality_gates": {
    "timestamp": "{ISO-8601}",
    "analysis_scope": "{A or B}",
    "circular_dependencies": {<from CLI output>},
    "dead_code": {<from CLI output>},
    "hotspots": {<from CLI output>},
    "quality_score": {<from CLI output>},
    "verification_results": {
      "file_coverage": {"status": "PASS", "value": "{percentage}%", "threshold": "70%"},
      "config_complete": {"status": "PASS", "value": "100%", "threshold": "100%"},
      "feature_count": {"status": "PASS", "value": {count}, "threshold": 50},
      "tech_debt_count": {"status": "PASS", "value": {count}, "threshold": 20},
      "security_findings": {"status": "PASS", "value": {count}, "threshold": 10},
      "dependency_audit": {"status": "PASS", "value": "complete", "threshold": "complete"}
    },
    "all_gates_passed": true,
    "patterns_found": {<merged from all phase data>},
    "files_analyzed": {<summary from all phases>},
    "features_extracted": {<from phases>},
    "technical_debt": {<from phases>},
    "security_findings": {<from phases>},
    "dependencies": {<from phases>},
    "test_coverage": {<from phases>}
  }
}
"@ | speckitadv write-data quality-gates.json --stage=02e-quality-gates --stdin
```

### Save State

The CLI automatically updates `{analysis_dir}/state.json` when stages complete.

---

## Step 6: Verify Data Files Saved

---
**[STOP: VERIFY_DATA_SAVED]**

Verify all data files from previous phases exist in `{data_dir}/`:

1. `category-patterns.json`
2. `deep-dive-patterns.json`
3. `config-analysis.json`
4. `test-audit.json`

**IF any file missing:** Re-run the corresponding phase to generate it.

---

## Completion Summary

```text
===========================================================
  STAGE COMPLETE: FILE_ANALYSIS

  Chain ID: {chain_id}
  Analysis Scope: {A - Full Application | B - Cross-Cutting}

  ---------------------------------------------------------
  ANALYSIS SUMMARY
  ---------------------------------------------------------

  Files Analyzed: {count}/{total} ({percentage}%)
  Features Extracted: {count}
  Technical Debt Items: {count} ({high} HIGH)
  Security Findings: {count} ({vulns} vulnerabilities)
  Dependency Vulnerabilities: {count} ({critical} critical)
  Test Coverage: ~{percentage}%

  ---------------------------------------------------------
  QUALITY GATES
  ---------------------------------------------------------

  [ok] File Coverage: PASS ({percentage}% >= 70%)
  [ok] Config Complete: PASS (100%)
  [ok] Features: PASS ({count} >= 50)
  [ok] Tech Debt: PASS ({count} >= 20)
  [ok] Security: PASS ({count} >= 10)
  [ok] Dependencies: PASS (audit complete)

  State: {analysis_dir}/state.json

===========================================================

STAGE_COMPLETE:FILE_ANALYSIS

```

---

**[GATE-CHECK]** If ALL quality gates PASS: run the CLI command below.
If ANY gate FAILS: present recovery options and WAIT for user decision.

---

## Next Stage

Run the CLI command below NOW when all gates pass:

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and scope, then emits the correct next prompt. **Do NOT generate artifacts until you run this command.**
