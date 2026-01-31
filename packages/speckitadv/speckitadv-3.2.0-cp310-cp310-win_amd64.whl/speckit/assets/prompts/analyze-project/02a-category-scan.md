---
stage: file_analysis_phase1
requires: 01c-script-execution
outputs: category_patterns
version: 3.6.0
time_allocation: 25%
---

# Stage 2A: Category Scan (Phase 1)

## Purpose

Scan codebase for architectural patterns using deterministic CLI discovery, then read key files for deeper understanding. This phase provides a broad architectural overview before deep-diving into priority areas.

**Time Allocation:** 25% of file analysis effort

---

{{include:strict-execution-mode.md}}

{{include:analyze-state-management.md}}

{{include:analyze-file-write-policy.md}}

---

## AI Context Cache

{{include:ai-cache-enforcement.md}}

```text
# Check cache status - if total=0, follow cache priming protocol in template above
get_understanding_stats(limit=50)

# IF total>0: Recall cached understanding
recall_understanding(target="project")
# If found AND fresh: Use cached patterns to guide analysis
# If not found: Proceed with discovery, then store findings
```

---

## Pre-Check: Verify Previous Stage

Required files from Stage 1C:

- `{data_dir}/file-manifest.json` - File listing
- `{data_dir}/tech-stack.json` - Detected technologies
- `{data_dir}/repoix-status.json` - civyk-repoix status

**IF files missing:** STOP - Return to Stage 1C

---

## Step 1: Run Category Patterns Discovery

Execute the enhanced category-patterns CLI command:

```bash
speckitadv category-patterns "{project_path}" --analysis-dir "{analysis_dir}"
```

This command provides comprehensive pattern discovery:

1. Analyzes all class/interface symbols to discover prefix/suffix patterns
2. Detects file extension patterns grouped by language
3. Searches for common patterns (Controller, Service, Repository, Model, etc.)
4. Searches for discovered patterns (like deepwiki does)
5. Gets architectural components and cross-component dependencies

**Output:** `{data_dir}/category-patterns.json`

---

**[STOP: CATEGORY_PATTERNS]**

Execute the command and verify output.

**IF successful:** category-patterns.json will be created
**IF fails:** Check civyk-repoix daemon status and retry

---

## Step 2: Read Discovery Results

Read the generated category patterns:

```bash
Read file: {data_dir}/category-patterns.json
```

Review the discovered patterns:

- `pattern_discovery` - Discovered prefix/suffix patterns from analyzing symbol names
  - `suffixes` - Common suffixes found (e.g., Service, Controller, Handler, Repository)
  - `prefixes` - Common prefixes found (e.g., User, Admin, Base, I)
  - `suffix_counts` - Count per suffix (top 30)
  - `prefix_counts` - Count per prefix (top 20)
- `file_patterns` - File extension and language patterns
  - `extensions` - Count per file extension
  - `languages` - Count per language
- `categories` - Categorized symbols by type (controllers, services, repositories, models, etc.)
- `total_category_symbols` - Total symbols found across all categories
- `components` - Architectural components from civyk-repoix
- `dependencies` - Cross-component dependencies
- `default_patterns_searched` - Hardcoded patterns that were searched
- `discovered_patterns_searched` - Dynamically discovered patterns that were searched

---

## Step 3: Deep Read Key Files (AI Understanding)

Based on discovery results, read key source files for deeper understanding:

### 3.1 Read Key Files by Category

For each category (controllers, services, models, repositories), select 2-3 representative files:

```text
# For each file:
recall_understanding(target="<file_path>")
# IF not cached: Read file, then store_understanding
```

**Extract per category:**

| Category | Focus Areas |
|----------|-------------|
| Controllers | Endpoints, auth decorators, error handling |
| Services | DI patterns, transactions, integrations |
| Models | ORM mappings, relationships, validation |
| Repositories | Query patterns, caching strategies |

---

## Step 3.5: Store Understanding

For each file read, call `store_understanding` with:

- `scope="file"`, `target="<path>"`, `purpose`, `importance`, `key_points`, `gotchas`, `analysis`

Also store project-level understanding:

```text
store_understanding(scope="project", target="project", purpose="...", importance="critical", key_points=["..."], analysis="...")
```

---

## Step 4: Compile Enhanced Category Analysis

Combine CLI discovery with file reading insights:

```json
{
  "category_scan": {
    "discovery_mode": "cli",
    "components_discovered": ["<from category-patterns.json>"],
    "controllers": {
      "count": "<from category-patterns.json>",
      "api_endpoints": "<count from reading files>",
      "patterns": {
        "api_style": "<REST/GraphQL/RPC - from reading files>",
        "auth_types": ["<extracted from file reading>"],
        "validation": "<pattern from file reading>"
      }
    },
    "services": {
      "count": "<from category-patterns.json>",
      "patterns": {
        "di_style": "<constructor/property/method - from files>",
        "transaction_style": "<pattern from files>",
        "integrations": ["<list from files>"]
      }
    },
    "models": {
      "entities_count": "<count>",
      "dtos_count": "<count>",
      "patterns": {
        "orm_type": "<EF Core/JPA/Sequelize/etc - from files>",
        "relationship_styles": ["<from files>"],
        "inheritance_depth": "<from files>"
      }
    },
    "repositories": {
      "count": "<from category-patterns.json>",
      "patterns": {
        "query_style": "<ORM/native SQL/mixed - from files>",
        "custom_queries": "<count from files>",
        "caching": "<strategy from files>"
      }
    },
    "security": {
      "auth_mechanism": "<JWT/OAuth/Session - from reading files>",
      "authorization": "<RBAC/ABAC/ACL>",
      "middleware_count": "<count>"
    },
    "key_files_analyzed": [
      "<list of files read for deep understanding>"
    ]
  }
}
```

---

## Step 5: Save Enhanced Analysis

Write to ONE file only (see analyze-file-write-policy).

Update category patterns with enhanced analysis:

**Use stdin for the full JSON (RECOMMENDED):**

```powershell
@"
{
  "category_scan": {
    "discovery_mode": "cli",
    ...
  }
}
"@ | speckitadv write-data category-patterns.json --stage=02a-category-scan --stdin
```

**Or use --content for smaller JSON:**

```bash
speckitadv write-data category-patterns.json --stage=02a-category-scan --content '<full-json>'
```

---

## Output Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 02a-category-scan (Phase 1)

  Discovery Mode: cli (deterministic)
  Components Found: {count}
  Files Analyzed: {count key files read}
  Time Used: 25% allocation

  Pattern Summary:
    Controllers: {count} ({api_style})
    Services: {count}
    Models: {entities + dtos}
    Repositories: {count}
    Auth: {mechanism}

  AI Cache Efficiency:
    Files read: <count_read>
    Files cached (store_understanding): <count_stored>
    Cache hits (found=true): <count_hits>
    Efficiency: <efficiency>% (target: 90%+)

  Proceeding to Phase 2: Deep Dive
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
