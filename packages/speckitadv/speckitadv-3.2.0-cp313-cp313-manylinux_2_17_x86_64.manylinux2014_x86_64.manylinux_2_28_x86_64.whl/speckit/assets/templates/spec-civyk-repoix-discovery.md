# civyk-repoix Tools for Specification

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
  analysis="<domain_model>: <entities>, <relationships>. <patterns>: <existing_conventions>. <scope>: <boundaries>."
)
```

| Task | Tools |
|------|-------|
| Quick orientation | `get_components`, `get_api_endpoints`, `build_context_pack` |
| Understand architecture | `get_type_hierarchy`, `get_dependencies` |
| Find related patterns | `search_symbols`, `get_file_symbols` |
| Identify dependencies | `get_file_imports` |
| Assess existing coverage | `get_tests_for`, `get_related_files` |

## First-Time Orientation

```text
# 1. Quick architecture overview
get_components()
get_api_endpoints(kind="class", limit=20)

# 2. Targeted context for specification
build_context_pack(task="understand codebase for <feature> specification", token_budget=1500, prefer_kinds=["class", "function"])
```

## Discovery Workflow for Specification

```text
# 1. Understand existing architecture
get_components()
get_api_endpoints(limit=50)
build_context_pack(task="understand codebase for <feature> specification", token_budget=1500)

# 2. Find related existing patterns
search_symbols(query="%<RelatedTerm>%", kind="class", limit=30)
search_symbols(query="%<RelatedTerm>%", kind="function", limit=30)

# 3. Understand data models in scope
get_type_hierarchy(fqn="<BaseModel>", direction="descendants")
get_file_symbols(path="<models_dir>", kinds=["class"])
```

## CLI Conversion

| MCP | CLI |
|-----|-----|
| `get_components()` | `civyk-repoix query get-components` |
| `get_api_endpoints(limit=N)` | `civyk-repoix query get-api-endpoints --limit N` |
| `build_context_pack(task="...", token_budget=N)` | `civyk-repoix query build-context-pack --task "..." --token-budget N` |
| `search_symbols(query="...", kind="...")` | `civyk-repoix query search-symbols --query "..." --kind "..."` |
| `get_file_symbols(path="...", kinds=["..."])` | `civyk-repoix query get-file-symbols --path "..." --kinds "..."` |
| `get_type_hierarchy(fqn="...")` | `civyk-repoix query get-type-hierarchy --fqn "..."` |
