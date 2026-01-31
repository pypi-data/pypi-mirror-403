---
stage: business-context
requires: check-repoix
outputs: "{wiki_dir}/business-context.json, {wiki_dir}/state.json"
version: 2.1.0
---

# Stage 2: Business Context Discovery

Discover and document what the project does (business purpose) before diving into how it's built (technical architecture).

## Prerequisites

- Stage 01 completed with civyk-repoix verified
- Mode: `{REPOIX_MODE}` (if "cli", convert MCP calls per AGENTS.md)
- State managed via CLI only - never read/write `{wiki_dir}/state.json` directly

## Critical Rules

| Rule | Action |
|------|--------|
| Save business context | **MUST** save via CLI before stage completion |
| Verify before proceeding | **MUST** confirm non-empty `project_name` saved |
| Pagination | **MUST** fetch all pages when `has_more=true` |
| Symbol filtering | Omit `kind` param to include docs; add `kind` for source-only |

---

{{include:ai-cache-enforcement.md}}

## AI Context Cache: Stage Start

```text
# Check cache status - if total=0, follow cache priming protocol in template above
get_understanding_stats(limit=50)

# IF total>0: Recall relevant paths from stats output
recall_understanding(target="{path_from_stats}")
# IF found AND fresh: Use cached analysis to accelerate discovery
# IF not found: Proceed with discovery, then MUST store findings
```

---

## Step 0: Detect Project Size

```text
# Get index metrics
index_status()
# Extract: files_indexed, symbols_indexed
```

**Determine size category and set LIMITS:**

| Files Indexed | Category | LIMITS |
|---------------|----------|--------|
| < 50 | small | `{symbols: 20, code: 20, files: 10}` |
| < 200 | medium | `{symbols: 50, code: 50, files: 30}` |
| < 1000 | large | `{symbols: 75, code: 75, files: 50}` |
| >= 1000 | very_large | `{symbols: 100, code: 100, files: 75}` |

**Save project size to state:**

```bash
speckitadv deepwiki-update-state project-size --category={SIZE_CATEGORY} --files={files_indexed} --symbols={symbols_indexed} --wiki-dir={wiki_dir}
```

**MCP/CLI conversion (if REPOIX_MODE == "cli"):**

| MCP Call | CLI Equivalent |
|----------|----------------|
| `index_status()` | `civyk-repoix query index-status` |
| `search_symbols(query="%User", kind="class")` | `civyk-repoix query search-symbols --query "%User" --kind class` |
| `list_files(pattern="**/*.md", limit=20)` | `civyk-repoix query list-files --pattern "**/*.md" --limit 20` |

**Symbol filtering (IMPORTANT for business context):**

| Tool Call | Searches | Use Case |
|-----------|----------|----------|
| `search_symbols(query="%API")` | ALL files (README.md, docs, source) | Business context discovery |
| `search_symbols(query="%API", kind="class")` | Source code ONLY | Technical discovery |

For business context extraction, **omit `kind` parameter** to capture context from documentation files.

---

## Step 1: Verify Previous Stage

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir} --key=stages
```

Confirm `01-check-repoix` has `status: completed`. **Stop if not complete.**

---

## Step 2: Run File Pattern Discovery

```bash
speckitadv deepwiki-update-state enumerate-index --wiki-dir={wiki_dir}
```

Verify output includes extensions, languages, and component patterns. Re-run if empty.

---

## Step 3: Discover Key Documentation

Use MCP tools to find business context sources:

```text
list_files(pattern="**/README.md", limit=10)
list_files(pattern="**/docs/**/*.md", limit=20)
search_code(query="## Features", file_pattern="*.md", limit=10)
```

**Read key files (with AI cache):**

```text
# FIRST: Check cached understanding for key files
recall_understanding(target="README.md")
recall_understanding(target="<package_file>")

# IF found AND fresh: Use cached analysis
# IF not found: Read files, then MUST store understanding

# Read file: README.md
# [!] NOW CALL store_understanding for the file above
store_understanding(
  scope="file",
  target="README.md",
  purpose="Project documentation and business description",
  importance="critical",
  key_points=["<project_name>", "<features>", "<target_users>"],
  gotchas=["<domain_specific_terms>", "<key_assumptions>"],
  analysis="<detailed_logic_and_flow_explanation>"
)

# Read file: <package_file>
# [!] NOW CALL store_understanding for the file above
store_understanding(
  scope="file",
  target="<package_file>",
  purpose="Package manifest and dependencies",
  importance="high",
  key_points=["<package_name>", "<dependencies>", "<scripts>"],
  gotchas=["<version_constraints>", "<peer_dependencies>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Step 4: Identify Domain Entities

### 4.0 Load Discovery Cache (MANDATORY)

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir}
# Extract: COMPONENT_SUFFIXES = discovery_cache.file_patterns.component_patterns.suffixes
# Extract: COMPONENT_PREFIXES = discovery_cache.file_patterns.component_patterns.prefixes
# Extract: LIMITS = discovery_cache.project_size.limits
```

### 4.1 Broad Discovery

**MUST** iterate over ALL discovered `COMPONENT_SUFFIXES` and `COMPONENT_PREFIXES` from the discovery cache. Do NOT use only hardcoded patterns.

```text
# MANDATORY: For EACH suffix in YOUR COMPONENT_SUFFIXES, search with %<SUFFIX> pattern:
# Example if COMPONENT_SUFFIXES = ["Dto", "Service", "Controller", "Repository", "Validator"]:
search_symbols(query="%Dto", limit=LIMITS.symbols)
search_symbols(query="%Service", limit=LIMITS.symbols)
search_symbols(query="%Controller", limit=LIMITS.symbols)
search_symbols(query="%Repository", limit=LIMITS.symbols)
search_symbols(query="%Validator", limit=LIMITS.symbols)
# ... continue for ALL suffixes in YOUR discovered COMPONENT_SUFFIXES

# MANDATORY: For EACH prefix in YOUR COMPONENT_PREFIXES, search with <PREFIX>% pattern:
# Example if COMPONENT_PREFIXES = ["Base", "Abstract", "I", "Create", "Update"]:
search_symbols(query="Base%", kind="class", limit=LIMITS.symbols)
search_symbols(query="Abstract%", kind="class", limit=LIMITS.symbols)
search_symbols(query="I%", kind="interface", limit=LIMITS.symbols)
# ... continue for ALL prefixes in YOUR discovered COMPONENT_PREFIXES

# Architecture overview
get_components()
get_dependencies()
```

**[!] CRITICAL:** The patterns above are examples. You **MUST** use YOUR actual discovered COMPONENT_SUFFIXES and COMPONENT_PREFIXES from enumerate-index output, not these examples.

### 4.2 Deep Dive for Key Entities

For each key domain class found:

```text
1. get_symbol(fqn="<found_fqn>")
2. get_references(fqn="<found_fqn>")
3. get_callers(fqn="<found_fqn>", depth=3)
4. get_type_hierarchy(fqn="<found_fqn>", direction="both", depth=5)
5. Read the actual file for business meaning
   # [!] NOW CALL store_understanding for the file above
   store_understanding(
     scope="file",
     target="<entity_file>",
     purpose="Domain entity for <business_concept>",
     importance="high",
     key_points=["<entity_fields>", "<relationships>", "<business_rules>"],
     gotchas=["<validation_rules>", "<edge_cases>"],
     analysis="<detailed_logic_and_flow_explanation>"
   )
6. get_file_imports(path="<entity_file>")
```

**Target coverage:** small=10, medium=20, large=30, very_large=50 entities.

---

## Step 5: Discover User-Facing Features

Find all entry points:

```text
get_api_endpoints(limit=100)
search_code(query="@route|@app.get|@app.post", is_regex=true, limit=50)
search_code(query="@click.command|def main", is_regex=true, limit=30)
```

Group into business features (Authentication, CRUD, Workflows, etc.). Target: 2+ features.

---

## Step 6: Extract Business Rules

```text
search_code(query="validate|Validator", limit=50)
search_symbols(query="%Validator", kind="class", limit=30)
search_code(query="permission|authorize", is_regex=true, limit=30)
search_symbols(query="%Error", kind="class", limit=30)
```

Read source files to understand rule rationale and enforcement locations.

---

## Step 7: Save Business Context

### 7a: Write Context File

Write to `{wiki_dir}/business-context.json`:

```json
{
  "project_name": "<<PROJECT_NAME>>",
  "tagline": "<<ONE_LINE_DESCRIPTION>>",
  "problem_solved": "<<WHAT_PROBLEM_DOES_THIS_SOLVE>>",
  "target_users": ["<<USER_TYPE_1>>", "<<USER_TYPE_2>>"],
  "key_features": [{"name": "...", "description": "...", "business_value": "..."}],
  "domain_entities": [{"name": "...", "description": "...", "location": "..."}],
  "business_rules": [{"rule": "...", "rationale": "...", "enforced_in": "..."}],
  "glossary": {"<<TERM>>": "<<DEFINITION>>"},
  "use_cases": [{"actor": "...", "action": "...", "outcome": "..."}]
}
```

**Required fields:** project_name (non-empty), key_features (2+), domain_entities (3+).

### 7b: Register with CLI

```bash
speckitadv deepwiki-update-state business-context --context-file={wiki_dir}/business-context.json --wiki-dir={wiki_dir}
```

### 7c: Verify Saved

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir}
```

Confirm `business_context_file` is set and `business_context.project_name` exists. **Stop if empty.**

---

## Step 8: Complete Stage

```bash
speckitadv deepwiki-update-state stage --stage=02-business-context --status=completed --artifacts="{wiki_dir}/business-context.json" --wiki-dir={wiki_dir}
```

---

## Output Format

```text
===========================================================
  STAGE COMPLETE: 02-business-context

  Summary:
    - Project: {project_name}
    - Features: {count} identified
    - Entities: {count} found
    - Business rules: {count} extracted

  AI Cache Efficiency:
    - Files read: <count_read>
    - Files cached (store_understanding): <count_stored>
    - Cache hits (found=true, fresh=true): <count_hits>

  Next: Run {next_command}
===========================================================
```

---

## Edge Cases

| Scenario | Action |
|----------|--------|
| No README found | Check docs/index.md, package.json description, specs/*.md |
| Minimal documentation | Infer from code: docstrings, API names, test descriptions |
| Library project | Focus on API purpose and integration use cases |
| Multi-module project | Aggregate context from each module README |

---

## Next Stage

Run `{next_command}` - CLI auto-detects current stage and emits next prompt.
