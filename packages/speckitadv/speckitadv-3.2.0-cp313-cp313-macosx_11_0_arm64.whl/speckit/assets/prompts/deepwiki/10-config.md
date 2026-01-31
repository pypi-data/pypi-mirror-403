---
stage: config
requires: models
outputs: "{wiki_dir}/configuration/"
version: 2.1.0
---

# Stage 10: Configuration Guide

Generate configuration documentation covering config files, environment variables, and setup options.

## Prerequisites

- Stage 09 completed (or skipped if no models)
- Mode: `{REPOIX_MODE}` (if "cli", convert MCP calls per AGENTS.md)
- Discovery cache loaded: LIMITS

## Critical Rules

| Rule | Action |
|------|--------|
| Models required | **MUST** verify {wiki_dir}/models.md exists (or stage skipped) |
| Search before skip | **MUST** search for config files before deciding to skip |
| No secrets | **NEVER** document actual secret values |
| Multi-file output | **MUST** create configuration/ directory with separate files |
| Skip if none | **MAY** skip if no configuration found |

---

{{include:ai-cache-enforcement.md}}

## AI Context Cache: Check Cached Understanding

**[!] MANDATORY: Check cache status FIRST.**

```text
# [!] MANDATORY: Check cache status at stage start
get_understanding_stats(limit=50)

# Recall understanding for paths from stats output
recall_understanding(target="project")

# Use ACTUAL paths from YOUR get_understanding_stats output:
# recall_understanding(target="{path_from_stats}")  # if exists in stats

# IF found AND fresh: Use cached analysis to guide config documentation
# IF not found: Proceed with discovery, then MUST store findings
```

---

## Step 1: Verify Previous Stage

```bash
speckitadv deepwiki-update-state verify-stage --stage=10-config --wiki-dir={wiki_dir}
```

---

## Step 2: Load Discovery Cache

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir}
# Extract: LIMITS = discovery_cache.project_size.limits
# Extract: PRIMARY_LANGUAGE = discovery_cache.file_patterns.languages.primary
```

**MCP/CLI conversion (if REPOIX_MODE == "cli"):**

| MCP Call | CLI Equivalent |
|----------|----------------|
| `list_files(pattern="**/*.config.*", limit=100)` | `civyk-repoix query list-files --pattern "**/*.config.*" --limit 100` |
| `search_code(query="process.env", limit=100)` | `civyk-repoix query search-code --query "process.env" --limit 100` |
| `search_symbols(query="%Config", kind="class")` | `civyk-repoix query search-symbols --query "%Config" --kind class` |

---

## Step 3: Find Configuration Files

```text
# Generic config patterns
list_files(pattern="**/*.config.*", limit=100)
list_files(pattern="**/config/**", limit=100)
list_files(pattern="**/settings.*", limit=50)
list_files(pattern="**/.env*", limit=50)

# Language-specific configs
list_files(pattern="**/appsettings*.json", limit=20)
list_files(pattern="**/application*.yml", limit=20)
list_files(pattern="**/pyproject.toml", limit=10)
list_files(pattern="**/tsconfig*.json", limit=20)

# Docker/Infrastructure
list_files(pattern="**/docker-compose*.yml", limit=20)
list_files(pattern="**/Dockerfile*", limit=20)
list_files(pattern="**/terraform/**", limit=50)
list_files(pattern="**/k8s/**", limit=50)
```

---

## Step 4: Find Config Usage

```text
# Environment variable access
search_code(query="process.env", limit=100)
search_code(query="os.environ|os.getenv", is_regex=true, limit=100)
search_code(query="Environment.GetEnvironmentVariable", limit=50)

# Config schemas
search_symbols(query="%Config", kind="class", limit=50)
search_symbols(query="%Settings", kind="class", limit=50)
search_code(query="Pydantic|BaseSettings|Zod|z.object", is_regex=true, limit=50)

# Read config files (check cache first)
recall_understanding(target="<config_file>")
# IF not cached: Read file: <config_file>
# [!] NOW CALL store_understanding for the file above
# -> Extract all config keys
# -> Note default values
# -> Identify required vs optional

# Find validation
get_related_files(path="<config_file>", relationship_types=["test"])

# [!] MANDATORY: Store understanding for EACH config file read
store_understanding(
  scope="file",
  target="<config_file>",
  purpose="Configuration for <area>",
  importance="high",
  key_points=["<config_keys>", "<default_values>", "<required_vs_optional>"],
  gotchas=["<env_specific_overrides>", "<sensitive_values>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Step 5: Write Output

**Required files:**

| File | Content |
|------|---------|
| `{wiki_dir}/configuration/README.md` | Index with quick reference for critical vars |
| `{wiki_dir}/configuration/{area}.md` | Individual config area (environment, database, security) |

**Each config file uses this template:**

{{include:wiki/config-template.md}}

**Fill placeholders with:** Area title, purpose, config keys/variables table, default values, required vs optional indicators, environment-specific variations, examples.

---

## Step 6: Verification Gate (MANDATORY)

**[STOP: VERIFY_MULTI_FILE_OUTPUT]**

Before completing this stage, you MUST verify:

1. [ ] `{wiki_dir}/configuration/README.md` exists (index file)
2. [ ] At least 1 individual config area file exists: `{wiki_dir}/configuration/{area}.md`
3. [ ] Each config file contains: purpose, config keys table, examples

**FAILURE CONDITIONS:**

- If only README.md exists: FAIL - You MUST create individual area files (e.g., `environment.md`, `database.md`)
- If config files have no config key table: FAIL - Each file must list actual config variables

**Count files in directory:**

```bash
ls {wiki_dir}/configuration/
```

Expected: README.md + at least 1 area file (e.g., `environment.md`, `database.md`, `security.md`)

**IF verification fails:** Go back to Step 5 and create the missing individual files.

---

## Step 7: Complete Stage

```bash
speckitadv deepwiki-update-state stage --stage=10-config --status=completed --artifacts="{wiki_dir}/configuration/README.md,{wiki_dir}/configuration/{area-1}.md,..." --wiki-dir={wiki_dir}
```

---

## Output Format

```text
===========================================================
  STAGE COMPLETE: 10-config

  Generated: {wiki_dir}/configuration/
  Config files: {count}
  Environment variables: {count}

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
| No config files | Document CLI arguments instead |
| Secret management detected | Document retrieval patterns, not values |
| Environment-only config | Focus on .env.example documentation |
| Config schema available | Extract field definitions from schema |

---

## Next Stage

Run `{next_command}` - CLI auto-detects current stage and emits next prompt.
