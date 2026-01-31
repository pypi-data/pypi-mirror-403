# civyk-repoix Tools for Tests

## MCP/CLI Mode Detection

**MANDATORY FIRST STEP: You MUST detect available mode before any test work.**

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
| `mcp` | MCP tool call works | `index_status()`, `get_tests_for(...)`, etc. |
| `cli` | MCP fails, CLI works | `civyk-repoix query index-status`, etc. |
| `none` | Both fail | Manual file reads only |

**CRITICAL**: You MUST attempt both MCP and CLI before falling back to `none`.

---

## Quick Reference by Mode

| Task | MCP (DISCOVERY_MODE=mcp) | CLI (DISCOVERY_MODE=cli) |
|------|--------------------------|--------------------------|
| Test recommendations | `get_recommended_tests(changed_files=[...])` | `civyk-repoix query get-recommended-tests --changed-files "f1,f2"` |
| Find existing tests | `get_tests_for(path="src/auth.py")` | `civyk-repoix query get-tests-for --path "src/auth.py"` |
| Find untested code | `get_dead_code(limit=20)` | `civyk-repoix query get-dead-code --limit 20` |
| High-risk files | `get_hotspots(since="30d")` | `civyk-repoix query get-hotspots --since 30d` |
| File structure | `get_file_symbols(path="...")` | `civyk-repoix query get-file-symbols --path "..."` |
| Dependencies | `get_callers(fqn="...", depth=2)` | `civyk-repoix query get-callers --fqn "..." --depth 2` |
| Similar code | `get_duplicate_code(source_only=true)` | `civyk-repoix query get-duplicate-code --source-only true` |

---

## Primary Test Discovery Tools

### 1. Get Recommended Tests (Priority Tool)

**Use for changed files to identify which tests to run/create:**

```text
# MCP
get_recommended_tests(changed_files=["src/auth/login.py", "src/auth/session.py"])

# CLI
civyk-repoix query get-recommended-tests --changed-files "src/auth/login.py,src/auth/session.py"
```

Returns: existing tests covering the changes, gaps needing new tests, priority ranking.

### 2. Get Tests For File

**Find existing tests for a specific file:**

```text
# MCP
get_tests_for(path="src/services/payment.py")

# CLI
civyk-repoix query get-tests-for --path "src/services/payment.py"
```

### 3. Get Dead Code (Untested/Unreachable)

**Identify code that may need tests:**

```text
# MCP
get_dead_code(limit=30)

# CLI
civyk-repoix query get-dead-code --limit 30
```

### 4. Get Hotspots (High-Risk Areas)

**Files frequently changed = higher test priority:**

```text
# MCP
get_hotspots(since="30d", limit=20)

# CLI
civyk-repoix query get-hotspots --since 30d --limit 20
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
  analysis="<test_coverage>: <what_is_tested>. <gaps>: <untested_paths>. <patterns>: <test_conventions>."
)
```

---

## First-Time Orientation

```text
# 1. Quick architecture overview (use mode-appropriate call)
get_components()
get_api_endpoints(kind="class", limit=20)

# 2. Understand test patterns and coverage
build_context_pack(task="understand test structure and patterns", token_budget=1500, prefer_kinds=["class", "function"])
```

---

## Full CLI Conversion Reference

| MCP | CLI |
|-----|-----|
| `index_status()` | `civyk-repoix query index-status` |
| `get_recommended_tests(changed_files=[...])` | `civyk-repoix query get-recommended-tests --changed-files "f1,f2"` |
| `get_tests_for(path="...")` | `civyk-repoix query get-tests-for --path "..."` |
| `get_code_for_test(test_path="...")` | `civyk-repoix query get-code-for-test --test-path "..."` |
| `get_components()` | `civyk-repoix query get-components` |
| `get_api_endpoints(limit=N)` | `civyk-repoix query get-api-endpoints --limit N` |
| `build_context_pack(task="...", token_budget=N)` | `civyk-repoix query build-context-pack --task "..." --token-budget N` |
| `list_files(pattern="...")` | `civyk-repoix query list-files --pattern "..."` |
| `get_dead_code(limit=N)` | `civyk-repoix query get-dead-code --limit N` |
| `get_hotspots(since="30d")` | `civyk-repoix query get-hotspots --since 30d` |
| `get_recent_changes(since="7d", include_symbols=true)` | `civyk-repoix query get-recent-changes --since 7d --include-symbols true` |
| `get_file_symbols(path="...")` | `civyk-repoix query get-file-symbols --path "..."` |
| `get_file_imports(path="...")` | `civyk-repoix query get-file-imports --path "..."` |
| `get_callers(fqn="...", depth=N)` | `civyk-repoix query get-callers --fqn "..." --depth N` |
| `get_symbol(fqn="...")` | `civyk-repoix query get-symbol --fqn "..."` |
| `get_duplicate_code(source_only=true)` | `civyk-repoix query get-duplicate-code --source-only true` |
| `analyze_impact(fqn="...", depth=N)` | `civyk-repoix query analyze-impact --fqn "..." --depth N` |
| `search_symbols(query="...", kind="...")` | `civyk-repoix query search-symbols --query "..." --kind "..."` |
