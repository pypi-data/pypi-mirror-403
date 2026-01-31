# civyk-repoix for Project Analysis

**MANDATORY MODE DETECTION**:
1. Try MCP: `index_status()` -> If works: `DISCOVERY_MODE=mcp`
2. If MCP fails -> [!] **MUST try CLI**: `civyk-repoix query index-status` -> If works: `DISCOVERY_MODE=cli`
3. Only if BOTH fail -> `DISCOVERY_MODE=none`

| Task | Tools |
|------|-------|
| Quick orientation | `get_components`, `get_api_endpoints`, `build_context_pack` |
| Architecture | `get_dependencies`, `find_circular_dependencies` |
| Find code | `search_symbols`, `list_files`, `search_code` |
| Understand | `get_file_symbols`, `get_file_imports`, `get_symbol` |
| Trace flow | `get_callers`, `get_references`, `analyze_impact` |
| API surface | `get_type_hierarchy` |
| Quality | `get_dead_code`, `get_hotspots`, `find_similar`, `get_duplicate_code` |
| Tests | `get_tests_for`, `get_code_for_test` |
| Changes | `get_recent_changes`, `get_branch_diff` |

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
  analysis="<architecture>: <layers>, <patterns>. <dependencies>: <key_imports>. <quality_issues>: <dead_code>, <hotspots>."
)
```

## First-Time Orientation

```text
# 1. Quick architecture overview
get_components()
get_api_endpoints(kind="class", limit=20)

# 2. Targeted context for analysis area
build_context_pack(task="understand <area> architecture and patterns", token_budget=2000, prefer_kinds=["class", "function"])
```

## CLI Conversion

| MCP | CLI |
|-----|-----|
| `get_components()` | `civyk-repoix query get-components` |
| `get_api_endpoints(limit=N)` | `civyk-repoix query get-api-endpoints --limit N` |
| `build_context_pack(task="...", token_budget=N)` | `civyk-repoix query build-context-pack --task "..." --token-budget N` |
| `get_dependencies()` | `civyk-repoix query get-dependencies` |
| `find_circular_dependencies(level="...")` | `civyk-repoix query find-circular-dependencies --level "..."` |
| `search_symbols(query="...", kind="...")` | `civyk-repoix query search-symbols --query "..." --kind "..."` |
| `list_files(pattern="...", include_stats=true)` | `civyk-repoix query list-files --pattern "..." --include-stats true` |
| `search_code(query="...", source_only=true)` | `civyk-repoix query search-code --query "..." --source-only true` |
| `get_file_symbols(path="...")` | `civyk-repoix query get-file-symbols --path "..."` |
| `get_file_imports(path="...")` | `civyk-repoix query get-file-imports --path "..."` |
| `get_symbol(fqn="...")` | `civyk-repoix query get-symbol --fqn "..."` |
| `get_callers(fqn="...", depth=N)` | `civyk-repoix query get-callers --fqn "..." --depth N` |
| `get_references(fqn="...")` | `civyk-repoix query get-references --fqn "..."` |
| `analyze_impact(fqn="...", depth=N, include_tests=true)` | `civyk-repoix query analyze-impact --fqn "..." --depth N --include-tests true` |
| `get_type_hierarchy(fqn="...", direction="...")` | `civyk-repoix query get-type-hierarchy --fqn "..." --direction "..."` |
| `get_dead_code(limit=N)` | `civyk-repoix query get-dead-code --limit N` |
| `get_hotspots(since="30d", group_by="...")` | `civyk-repoix query get-hotspots --since 30d --group-by "..."` |
| `find_similar(fqn="...", similarity_threshold=N)` | `civyk-repoix query find-similar --fqn "..." --similarity-threshold N` |
| `get_duplicate_code(source_only=true)` | `civyk-repoix query get-duplicate-code --source-only true` |
| `get_tests_for(path="...", include_indirect=true)` | `civyk-repoix query get-tests-for --path "..." --include-indirect true` |
| `get_code_for_test(path="...")` | `civyk-repoix query get-code-for-test --path "..."` |
| `get_recent_changes(since="7d", include_symbols=true)` | `civyk-repoix query get-recent-changes --since 7d --include-symbols true` |
| `get_branch_diff(include_symbols=true)` | `civyk-repoix query get-branch-diff --include-symbols true` |
