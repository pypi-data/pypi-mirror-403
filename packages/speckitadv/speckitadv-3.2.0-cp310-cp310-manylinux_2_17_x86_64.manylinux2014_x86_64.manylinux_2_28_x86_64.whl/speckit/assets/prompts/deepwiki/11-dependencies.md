---
stage: dependencies
requires: config
outputs: "{wiki_dir}/dependencies.md"
version: 2.1.0
---

# Stage 11: Dependency Documentation

Generate documentation of external dependencies, internal component relationships, and circular dependency analysis.

## Prerequisites

- Stage 10 completed (or skipped if no config)
- Mode: `{REPOIX_MODE}` (if "cli", convert MCP calls per AGENTS.md)
- Discovery cache loaded: LIMITS

## Critical Rules

| Rule | Action |
|------|--------|
| Config required | **MUST** verify {wiki_dir}/configuration/README.md exists (or stage skipped) |
| Analyze manifests | **MUST** analyze package manifests for external deps |
| Version context | **NEVER** document versions without noting pinned vs floating |
| Circular deps | **SHOULD** identify circular dependencies if found |

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

# IF found AND fresh: Use cached analysis to guide dependency documentation
# IF not found: Proceed with discovery, then MUST store findings
```

---

## Step 1: Verify Previous Stage

```bash
speckitadv deepwiki-update-state verify-stage --stage=11-dependencies --wiki-dir={wiki_dir}
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
| `get_dependencies()` | `civyk-repoix query get-dependencies` |
| `find_circular_dependencies(level="component")` | `civyk-repoix query find-circular-dependencies --level component` |
| `get_file_imports(path="...", resolve_internal=true)` | `civyk-repoix query get-file-imports --path "..." --resolve-internal true` |

---

## Step 3: Get Cross-Component Dependencies

```text
# Component-level dependencies
get_dependencies()
get_components()
build_context_pack(task="understand all dependencies", token_budget=2000)

# Find circular dependencies
find_circular_dependencies(level="component")
find_circular_dependencies(level="file")

# Code quality analysis
get_dead_code(limit=100)
get_duplicate_code(source_only=true, similarity_threshold=0.7, limit=50)
```

---

## Step 4: Get File-Level Imports

```text
# For each main file
get_file_imports(path="<main_file>", resolve_internal=true)

# Find entry points
list_files(pattern="**/index.*", include_stats=true, limit=50)
list_files(pattern="**/main.*", include_stats=true, limit=50)
list_files(pattern="**/__init__.py", include_stats=true, limit=50)

# Understand coupling
get_references(fqn="<key_class>")
```

---

## Step 5: Analyze Package Files

```text
# Find all package manifests
list_files(pattern="**/package.json", limit=20)
list_files(pattern="**/requirements*.txt", limit=20)
list_files(pattern="**/pyproject.toml", limit=10)
list_files(pattern="**/Cargo.toml", limit=10)
list_files(pattern="**/go.mod", limit=10)
list_files(pattern="**/pom.xml", limit=10)
list_files(pattern="**/build.gradle*", limit=10)

# Read each manifest (check cache first)
recall_understanding(target="<manifest>")
# IF not cached: Read file: <manifest>
# [!] NOW CALL store_understanding for the file above
# -> Extract production dependencies
# -> Extract dev dependencies
# -> Note version constraints

# [!] MANDATORY: Store understanding for EACH manifest file read
store_understanding(
  scope="file",
  target="<manifest>",
  purpose="Dependency manifest for <package_manager>",
  importance="high",
  key_points=["<production_deps>", "<dev_deps>", "<version_constraints>"],
  gotchas=["<outdated_deps>", "<security_advisories>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Step 6: Generate Documentation

Write `{wiki_dir}/dependencies.md` using this template:

{{include:wiki/dependencies-template.md}}

**Fill placeholders with:** Dependencies summary, package manager, Mermaid dependency graph, internal/production/development dependencies tables, circular dependencies (if found).

---

## Step 7: Complete Stage

```bash
speckitadv deepwiki-update-state stage --stage=11-dependencies --status=completed --artifacts="{wiki_dir}/dependencies.md" --wiki-dir={wiki_dir}
```

---

## Output Format

```text
===========================================================
  STAGE COMPLETE: 11-dependencies

  Generated: {wiki_dir}/dependencies.md
  External dependencies: {count}
  Internal dependencies: {count}

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
| No package manager | Document from import statements |
| Vendored dependencies | Document separately |
| Monorepo internal packages | Distinguish from external |
| Native dependencies | Include system requirements |

---

## Next Stage

Run `{next_command}` - CLI auto-detects current stage and emits next prompt.
