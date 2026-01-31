# civyk-repoix Tools for Implementation

**MANDATORY MODE DETECTION**:
1. Try MCP: `index_status()` -> If works: `DISCOVERY_MODE=mcp`
2. If MCP fails -> [!] **MUST try CLI**: `civyk-repoix query index-status` -> If works: `DISCOVERY_MODE=cli`
3. Only if BOTH fail -> `DISCOVERY_MODE=none`

## AI Context Cache Protocol

**BEFORE reading any file:**

```text
# Check what's cached from earlier stages
get_understanding_stats(limit=50)
recall_understanding(target="<file_path>")
# IF found AND fresh: Use cached analysis, skip file read
# IF not found: Read file, then MUST store understanding
```

**AFTER reading any source file:**

```text
store_understanding(
  scope="file",
  target="<file_path>",
  purpose="<what this file does>",
  importance="<critical|high|medium|low>",
  key_points=["<main functionality>", "<key patterns>"],
  gotchas=["<edge cases>", "<non-obvious behaviors>"],
  analysis="<module_structure>: <classes>, <functions>. <patterns>: <existing_conventions>. <integration_points>: <what_to_extend>."
)
```

| Task | Tools |
|------|-------|
| Quick orientation | `get_components`, `get_api_endpoints`, `build_context_pack` |
| Before modifying | `analyze_impact`, `get_callers`, `get_references` |
| Find patterns | `get_file_symbols`, `get_duplicate_code(source_only=true)`, `find_similar` |
| Understand deps | `get_file_imports`, `get_dependencies` |
| Find tests | `get_tests_for`, `get_related_files` |
| Verify integration | `get_dead_code`, `find_circular_dependencies` |

## First-Time Orientation

```text
# 1. Quick architecture overview
get_components()
get_api_endpoints(kind="class", limit=20)

# 2. Targeted context for implementation
build_context_pack(task="understand codebase patterns for <feature>", token_budget=1500, prefer_kinds=["class", "function"])
```

## Before Modifying Any Code

```text
# 1. Understand what you're changing
get_file_symbols(path="<file_to_modify>", include_private=true)
get_file_imports(path="<file_to_modify>")

# 2. Analyze impact BEFORE making changes
analyze_impact(fqn="<symbol_to_modify>", depth=3, include_tests=true)
get_callers(fqn="<function_to_modify>", depth=2)
get_references(fqn="<class_to_modify>")

# 3. Find tests to update
get_tests_for(path="<file_to_modify>", include_indirect=true)
```

## Before Creating New Code

```text
# 1. Check for similar existing code
get_duplicate_code(source_only=true, similarity_threshold=0.7, limit=30)
find_similar(fqn="<similar_class>", similarity_threshold=0.6)

# 2. Understand existing patterns
build_context_pack(task="find existing patterns for <feature>", token_budget=1500)
search_symbols(query="%<PatternName>", kind="class", limit=20)
```

## After Implementation

```text
# Verify no orphaned code
get_dead_code(limit=30)

# Check for new circular dependencies
find_circular_dependencies(level="file")
```

## CLI Conversion

| MCP | CLI |
|-----|-----|
| `get_components()` | `civyk-repoix query get-components` |
| `get_api_endpoints(kind="...", limit=N)` | `civyk-repoix query get-api-endpoints --kind "..." --limit N` |
| `build_context_pack(task="...", token_budget=N)` | `civyk-repoix query build-context-pack --task "..." --token-budget N` |
| `get_file_symbols(path="...", include_private=true)` | `civyk-repoix query get-file-symbols --path "..." --include-private true` |
| `get_file_imports(path="...")` | `civyk-repoix query get-file-imports --path "..."` |
| `analyze_impact(fqn="...", depth=N, include_tests=true)` | `civyk-repoix query analyze-impact --fqn "..." --depth N --include-tests true` |
| `get_callers(fqn="...", depth=N)` | `civyk-repoix query get-callers --fqn "..." --depth N` |
| `get_references(fqn="...")` | `civyk-repoix query get-references --fqn "..."` |
| `get_tests_for(path="...", include_indirect=true)` | `civyk-repoix query get-tests-for --path "..." --include-indirect true` |
| `get_duplicate_code(source_only=true)` | `civyk-repoix query get-duplicate-code --source-only true` |
| `find_similar(fqn="...", similarity_threshold=N)` | `civyk-repoix query find-similar --fqn "..." --similarity-threshold N` |
| `search_symbols(query="...", kind="...")` | `civyk-repoix query search-symbols --query "..." --kind "..."` |
| `get_dead_code(limit=N)` | `civyk-repoix query get-dead-code --limit N` |
| `find_circular_dependencies(level="file")` | `civyk-repoix query find-circular-dependencies --level file` |
