# AI Context Cache Enforcement

**[!] MANDATORY: Follow these rules for ALL source file operations.**

## Pre-Read Protocol

**BEFORE reading ANY source file:**

1. Call `recall_understanding(target="<file_path>")`
2. Check response:
   - `found=true` AND `fresh=true` -> **USE cached understanding, SKIP file read**
   - `found=true` AND `fresh=false` -> File changed, proceed to read and UPDATE cache
   - `found=false` -> Proceed to read, then MUST store understanding

```text
# Example: Before reading auth.py
recall_understanding(target="src/auth/oauth.py")
# IF found=true AND fresh=true: Use cached, no read needed
# IF found=false: Read file, then store_understanding
```

## Post-Read Protocol

**AFTER reading ANY source file thoroughly:**

1. **MUST call `store_understanding`** immediately after the read - do not batch or defer
2. Required parameters:
   - `scope`: file, class, module, or project
   - `target`: exact path read
   - `purpose`: 1-2 sentence summary
   - `importance`: critical/high/medium/low
   - `key_points`: 2-5 main functionality highlights
   - `gotchas`: non-obvious behaviors (IMPORTANT for future sessions)
   - `analysis`: detailed free-form analysis (for complex logic, state machines, workflows)

3. **Track files read vs cached** - maintain running count

```text
# Example: After reading auth.py
# [!] NOW CALL store_understanding for the file above
store_understanding(
  scope="file",
  target="src/auth/oauth.py",
  purpose="OAuth2 authentication with Google/GitHub SSO",
  importance="critical",
  key_points=["OAuth2 code flow", "Token refresh async", "Sessions in Redis"],
  gotchas=["Token refresh race condition", "GitHub scope format differs"],
  analysis="AUTH FLOW: 1) Client redirects to provider 2) Provider callback with code 3) Exchange code for tokens 4) Store refresh token in Redis. TOKEN REFRESH: Async job checks expiry, race condition possible if multiple requests trigger refresh simultaneously."
)
```

## 1:1 Read:Store Enforcement

| Action | Requirement |
|--------|-------------|
| Read 1 file | Store 1 understanding |
| Read 5 files | Store 5 understandings |
| Batch read | Batch store (all files) |

**Exception:** Config files read for quick value lookup (not analysis) may skip store.

## Stage Completion Checklist

### Cache Efficiency Verification

**Before completing any stage that reads source files, verify (non-blocking):**

- [ ] All source files read have corresponding `store_understanding` calls
- [ ] `key_points` captured for each file
- [ ] `gotchas` captured (non-obvious behaviors, edge cases)
- [ ] Cache metrics calculated and reported (see below)

**FAILURE CONDITIONS:**

- If `count_stored < count_read`: FAIL - You missed `store_understanding` calls
- If `count_stored = 0` but `count_read > 0`: FAIL - You never called `store_understanding`
- If cache efficiency < 90%: WARNING - Review which files were not cached

## Cache Metrics Reporting

**[!] MANDATORY: At stage completion, you MUST report actual numbers:**

```text
AI Cache Efficiency:
- Files read: <count_read>
- Files cached (store_understanding): <count_stored>
- Cache hits (found=true, fresh=true): <count_hits>
- Efficiency: <count_stored>/<count_read> = <percentage>%
```

**Target: 90%+ efficiency** (count_stored should equal count_read for thorough analysis stages)

**Note:** Replace `<count_*>` and `<percentage>` with actual numeric values when reporting. Do NOT use placeholder text in your output.

## Common Violations

| Violation | Impact | Fix |
|-----------|--------|-----|
| Read without recall first | Missed cache hit | Always recall before read |
| Read without store after | Lost analysis for future | Always store after thorough read |
| Batch read, partial store | Some files not cached | Store ALL files in batch |
| Missing gotchas | Future sessions miss warnings | Always include gotchas |

## Cache Priming (Empty Cache)

**[!] MANDATORY: When `get_understanding_stats` returns total=0 (empty cache), prime the cache with key files.**

```text
# [!] MANDATORY: Check cache status FIRST
get_understanding_stats(limit=50)

# IF total=0 (empty cache): Prime cache with key files identified by MCP discovery
build_context_pack(task="understand codebase architecture", token_budget=2000)
get_components()
get_api_endpoints(limit=50)

# From discovery results, identify and cache top priority files:
# - Main entry points (from build_context_pack relevance ranking)
# - Key config files (package.json, pyproject.toml, settings.py, etc.)
# - Core classes (from get_components paths)
# - README.md and key documentation

# [!] MANDATORY: Read and store understanding for EACH key file
Read file: <key_file_from_discovery>
# [!] NOW CALL store_understanding for the file above
store_understanding(
  scope="file",
  target="<key_file_from_discovery>",
  purpose="<file purpose from discovery context>",
  importance="critical",
  key_points=["<main exports>", "<patterns>", "<key classes>"],
  gotchas=["<edge cases>", "<non-obvious behaviors>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
# Repeat for top 5-10 key files from discovery results
```

### Cache Priming Verification

**After cache priming, verify (non-blocking):**

```text
get_understanding_stats(limit=10)
# CHECK: total > 0 (cache has entries)
# CHECK: by_scope.file.count >= 5 (key files cached)
```

**If checks fail, note in output but continue** - cache priming is best-effort, not blocking.

---

## Stage-Specific Cache Targets

Different stages have different cache usage patterns:

| Stage Type | Examples | Expected Behavior | Target Metrics |
|------------|----------|-------------------|----------------|
| **Priming** | 02-04 (deepwiki), 02a-02d (analyze) | Many stores, few recalls | stores >= 5, hits low |
| **Analysis** | 05-14 (deepwiki), 03a-03b (analyze) | Many recalls, few stores | hit rate >= 80% |
| **Generation** | 15-16 (deepwiki), 04a-06 (analyze) | All recalls, no stores | hit rate >= 90% |

**Priming Stages (02-04):**
- Focus on `store_understanding` for key files
- Low cache hit rate is expected (cache is being built)
- Target: Cache 10-20 key files for later stages

**Analysis Stages (05-14):**
- Check cache before every file read
- Most files should already be cached from priming
- Target: 80%+ cache hit rate
- Only store understanding for NEW files discovered during analysis

**Generation Stages (15-16):**
- Pure consumers of cached understanding
- Should rarely need to read source files
- Target: 90%+ cache hit rate
- If cache miss on critical file, something went wrong in earlier stages

## Quick Reference

```text
# [!] MANDATORY: Session/stage start - check cache first
get_understanding_stats(limit=50)
# IF total=0: Run cache priming (see above)
# IF total>0: Proceed with recall/read workflow

# Before each file read
recall_understanding(target="<path>")

# After thorough file analysis
store_understanding(
  scope="file",
  target="<path>",
  purpose="...",
  importance="...",
  key_points=[...],
  gotchas=[...],
  analysis="<detailed_flow_or_logic_explanation>"
)

# Stage end
Report: "AI Cache: <count_read> files read, <count_stored> cached, <count_hits> cache hits"
```
