# civyk-repoix Tools for Planning

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
  analysis="<architecture>: <layers>, <patterns>. <dependencies>: <key_imports>. <extension_points>: <where_to_add>."
)
```

| Task | Tools |
|------|-------|
| Quick orientation | `get_components`, `get_api_endpoints`, `build_context_pack` |
| Understand architecture | `get_dependencies`, `get_type_hierarchy` |
| Find patterns | `search_symbols`, `get_file_symbols` |
| Identify risks | `get_hotspots`, `find_circular_dependencies`, `get_dead_code` |
| Find duplicates | `get_duplicate_code(source_only=true)`, `find_similar` |
| Understand API surface | `get_references` |

## First-Time Orientation

```text
# 1. Quick architecture overview
get_components()
get_api_endpoints(kind="class", limit=20)

# 2. Targeted context for planning
build_context_pack(task="understand project architecture for planning", token_budget=2000, prefer_kinds=["class", "function"])
```

## Discovery Workflow

```text
# 1. Get architecture overview
get_components()
get_dependencies()
build_context_pack(task="understand project architecture", token_budget=2000)

# 2. Check code quality indicators
find_circular_dependencies(level="component")
get_hotspots(since="90d", group_by="component", limit=30)
get_dead_code(limit=50)
get_duplicate_code(source_only=true, similarity_threshold=0.7, limit=30)

# 3. Find existing patterns to extend
search_symbols(query="%Service", kind="class", limit=50)
search_symbols(query="%Repository", kind="class", limit=50)
search_symbols(query="%Controller", kind="class", limit=50)
```

## CLI Conversion

| MCP | CLI |
|-----|-----|
| `get_components()` | `civyk-repoix query get-components` |
| `get_dependencies()` | `civyk-repoix query get-dependencies` |
| `build_context_pack(task="...", token_budget=N)` | `civyk-repoix query build-context-pack --task "..." --token-budget N` |
| `find_circular_dependencies(level="component")` | `civyk-repoix query find-circular-dependencies --level component` |
| `get_hotspots(since="90d", group_by="...")` | `civyk-repoix query get-hotspots --since 90d --group-by "..."` |
| `get_dead_code(limit=N)` | `civyk-repoix query get-dead-code --limit N` |
| `get_duplicate_code(source_only=true)` | `civyk-repoix query get-duplicate-code --source-only true` |
| `search_symbols(query="...", kind="...")` | `civyk-repoix query search-symbols --query "..." --kind "..."` |
