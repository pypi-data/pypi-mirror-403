# civyk-repoix Tools for Task Generation

**MANDATORY MODE DETECTION**:
1. Try MCP: `index_status()` -> If works: `DISCOVERY_MODE=mcp`
2. If MCP fails -> [!] **MUST try CLI**: `civyk-repoix query index-status` -> If works: `DISCOVERY_MODE=cli`
3. Only if BOTH fail -> `DISCOVERY_MODE=none`

| Task | Tools |
|------|-------|
| Quick orientation | `get_components`, `get_api_endpoints`, `build_context_pack` |
| Understand structure | `get_file_symbols`, `list_files` |
| Find dependencies | `get_file_imports`, `get_callers`, `get_references` |
| Identify risky areas | `get_hotspots`, `get_recent_changes` |
| Find similar patterns | `get_duplicate_code(source_only=true)`, `find_similar` |
| Understand API | `get_type_hierarchy` |

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
  analysis="<module_purpose>: <what_it_does>. <dependencies>: <key_imports>. <complexity>: <task_breakdown_hints>."
)
```

## First-Time Orientation

```text
# 1. Quick architecture overview
get_components()
get_api_endpoints(kind="class", limit=20)

# 2. Targeted context for task breakdown
build_context_pack(task="understand project for task breakdown", token_budget=1500, prefer_kinds=["class", "function"])
```

## Discovery Workflow

```text
# 1. Understand project structure
get_components()
list_files(include_stats=true, limit=100)
build_context_pack(task="understand project for task breakdown", token_budget=1500)

# 2. Identify risky/complex areas (may need more tasks)
get_hotspots(since="90d", group_by="file", limit=30)
get_dead_code(limit=30)

# 3. Find existing patterns (determine file locations)
search_symbols(query="%Service", kind="class", limit=30)
search_symbols(query="%Model", kind="class", limit=30)
get_api_endpoints(limit=50)
```

## CLI Conversion

| MCP | CLI |
|-----|-----|
| `get_components()` | `civyk-repoix query get-components` |
| `list_files(include_stats=true)` | `civyk-repoix query list-files --include-stats true` |
| `build_context_pack(task="...", token_budget=N)` | `civyk-repoix query build-context-pack --task "..." --token-budget N` |
| `get_hotspots(since="90d")` | `civyk-repoix query get-hotspots --since 90d` |
| `get_dead_code(limit=N)` | `civyk-repoix query get-dead-code --limit N` |
| `search_symbols(query="...", kind="...")` | `civyk-repoix query search-symbols --query "..." --kind "..."` |
| `get_api_endpoints(limit=N)` | `civyk-repoix query get-api-endpoints --limit N` |
