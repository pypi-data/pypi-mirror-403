# civyk-repoix Tools for Review

## MCP/CLI Mode Detection

**MANDATORY FIRST STEP: You MUST detect available mode before any review work.**

### Step 1: Try MCP Tool Call

```text
index_status()
```

### Step 2: Evaluate Result and Set Mode

**If MCP call succeeds** (returns JSON with `status` field):

```text
DISCOVERY_MODE=mcp
```

Use MCP tool calls for all subsequent operations.

**If MCP call fails** (tool not found, connection error, timeout):

[!] **DO NOT set DISCOVERY_MODE=none yet!** You MUST try CLI first.

### Step 3: CLI Fallback (REQUIRED if MCP Failed)

```bash
civyk-repoix query index-status
```

**If CLI succeeds** (returns JSON):

```text
DISCOVERY_MODE=cli
```

Use `civyk-repoix query <command>` via Bash for all subsequent operations.

**If CLI also fails**:

```text
DISCOVERY_MODE=none
```

Proceed with manual file reads only (no index-based tools available).

### Mode Summary

| Mode | When | How to Use Tools |
|------|------|------------------|
| `mcp` | MCP tool call works | `index_status()`, `get_callers(...)`, etc. |
| `cli` | MCP fails, CLI works | `civyk-repoix query index-status`, etc. |
| `none` | Both fail | Manual file reads only |

**CRITICAL**: You MUST attempt both MCP and CLI before falling back to `none`.

---

## Quick Reference by Mode

| Task | MCP (DISCOVERY_MODE=mcp) | CLI (DISCOVERY_MODE=cli) |
|------|--------------------------|--------------------------|
| Branch changes | `build_delta_context_pack(include_symbols=true)` | `civyk-repoix query build-delta-context-pack --include-symbols true` |
| Impact analysis | `analyze_impact(fqn="...", depth=2)` | `civyk-repoix query analyze-impact --fqn "..." --depth 2` |
| Who calls this | `get_callers(fqn="...", depth=2)` | `civyk-repoix query get-callers --fqn "..." --depth 2` |
| Find references | `get_references(fqn="...")` | `civyk-repoix query get-references --fqn "..."` |
| High-risk files | `get_hotspots(since="30d")` | `civyk-repoix query get-hotspots --since 30d` |
| Circular deps | `find_circular_dependencies(level="file")` | `civyk-repoix query find-circular-dependencies --level file` |
| Dead code | `get_dead_code(limit=20)` | `civyk-repoix query get-dead-code --limit 20` |

---

## Primary Review Tools

### 1. Build Delta Context Pack (Branch Review)

**Use for reviewing all changes in current branch:**

```text
# MCP
build_delta_context_pack(include_symbols=true, token_budget=3000)

# CLI
civyk-repoix query build-delta-context-pack --include-symbols true --token-budget 3000
```

Returns: changed files, symbols modified, affected callers, recommended tests.

### 2. Analyze Impact

**Understand ripple effects of a change:**

```text
# MCP
analyze_impact(fqn="src.auth.login.validate_token", depth=3)

# CLI
civyk-repoix query analyze-impact --fqn "src.auth.login.validate_token" --depth 3
```

Returns: direct callers, indirect callers, breaking change risk.

### 3. Get Callers

**Find all code paths calling a function:**

```text
# MCP
get_callers(fqn="src.services.payment.process", depth=2)

# CLI
civyk-repoix query get-callers --fqn "src.services.payment.process" --depth 2
```

### 4. Get References

**Find all usages of a symbol:**

```text
# MCP
get_references(fqn="src.models.User")

# CLI
civyk-repoix query get-references --fqn "src.models.User"
```

### 5. Get Hotspots (High-Risk Areas)

**Files frequently changed = higher review scrutiny:**

```text
# MCP
get_hotspots(since="30d", limit=20)

# CLI
civyk-repoix query get-hotspots --since 30d --limit 20
```

---

## Architecture Quality Tools

### Find Circular Dependencies

```text
# MCP
find_circular_dependencies(level="file")

# CLI
civyk-repoix query find-circular-dependencies --level file
```

### Get Dead Code

```text
# MCP
get_dead_code(limit=30)

# CLI
civyk-repoix query get-dead-code --limit 30
```

### Get Duplicate Code

```text
# MCP
get_duplicate_code(source_only=true, min_similarity=0.8)

# CLI
civyk-repoix query get-duplicate-code --source-only true --min-similarity 0.8
```

---

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
  analysis="<change_summary>: <what_changed>. <impact>: <affected_areas>. <risks>: <potential_issues>."
)
```

---

## First-Time Orientation

```text
# 1. Quick architecture overview (use mode-appropriate call)
get_components()
get_api_endpoints(kind="class", limit=20)

# 2. Targeted context for review area
build_context_pack(task="understand <area> for code review", token_budget=1500, prefer_kinds=["class", "function"])
```

---

## Full CLI Conversion Reference

| MCP | CLI |
|-----|-----|
| `index_status()` | `civyk-repoix query index-status` |
| `build_delta_context_pack(include_symbols=true)` | `civyk-repoix query build-delta-context-pack --include-symbols true` |
| `get_branch_diff(include_symbols=true)` | `civyk-repoix query get-branch-diff --include-symbols true` |
| `analyze_impact(fqn="...", depth=N)` | `civyk-repoix query analyze-impact --fqn "..." --depth N` |
| `get_callers(fqn="...", depth=N)` | `civyk-repoix query get-callers --fqn "..." --depth N` |
| `get_references(fqn="...")` | `civyk-repoix query get-references --fqn "..."` |
| `get_components()` | `civyk-repoix query get-components` |
| `get_api_endpoints(limit=N)` | `civyk-repoix query get-api-endpoints --limit N` |
| `build_context_pack(task="...", token_budget=N)` | `civyk-repoix query build-context-pack --task "..." --token-budget N` |
| `get_hotspots(since="30d")` | `civyk-repoix query get-hotspots --since 30d` |
| `get_recent_changes(since="7d", include_symbols=true)` | `civyk-repoix query get-recent-changes --since 7d --include-symbols true` |
| `get_file_symbols(path="...")` | `civyk-repoix query get-file-symbols --path "..."` |
| `get_file_imports(path="...")` | `civyk-repoix query get-file-imports --path "..."` |
| `get_related_files(path="...")` | `civyk-repoix query get-related-files --path "..."` |
| `get_tests_for(path="...")` | `civyk-repoix query get-tests-for --path "..."` |
| `find_circular_dependencies(level="...")` | `civyk-repoix query find-circular-dependencies --level "..."` |
| `get_dead_code(limit=N)` | `civyk-repoix query get-dead-code --limit N` |
| `get_duplicate_code(source_only=true)` | `civyk-repoix query get-duplicate-code --source-only true` |
| `find_similar(fqn="...", similarity_threshold=N)` | `civyk-repoix query find-similar --fqn "..." --similarity-threshold N` |
| `search_code(query="...", source_only=true)` | `civyk-repoix query search-code --query "..." --source-only true` |
| `search_symbols(query="...", kind="...")` | `civyk-repoix query search-symbols --query "..." --kind "..."` |
| `get_symbol(fqn="...")` | `civyk-repoix query get-symbol --fqn "..."` |
