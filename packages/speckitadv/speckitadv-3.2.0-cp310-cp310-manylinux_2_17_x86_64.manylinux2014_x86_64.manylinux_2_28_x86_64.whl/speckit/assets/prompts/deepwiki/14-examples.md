---
stage: examples
requires: errors
outputs: "{wiki_dir}/examples.md"
version: 2.1.0
---

# Stage 14: Usage Examples

Generate usage examples and code snippets for common operations and integrations.

## Prerequisites

- Stage 13 completed with errors.md generated
- Mode: `{REPOIX_MODE}` (if "cli", convert MCP calls per AGENTS.md)
- Discovery cache loaded: LIMITS, TEST_PATTERNS

## Critical Rules

| Rule | Action |
|------|--------|
| Errors required | **MUST** verify {wiki_dir}/errors.md exists |
| Search existing | **MUST** search for existing examples before creating |
| Complete examples | **NEVER** generate broken or incomplete code |
| Include imports | **SHOULD** include import statements in snippets |

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

# IF found AND fresh: Use cached analysis to guide example creation
# IF not found: Proceed with discovery, then MUST store findings
```

---

## Step 1: Verify Previous Stage

```bash
speckitadv deepwiki-update-state verify-stage --stage=14-examples --wiki-dir={wiki_dir}
```

---

## Step 2: Load Discovery Cache

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir}
# Extract: LIMITS = discovery_cache.project_size.limits
# Extract: TEST_PATTERNS = discovery_cache.file_patterns.test_patterns
```

**MCP/CLI conversion (if REPOIX_MODE == "cli"):**

| MCP Call | CLI Equivalent |
|----------|----------------|
| `list_files(pattern="**/examples/**", limit=100)` | `civyk-repoix query list-files --pattern "**/examples/**" --limit 100` |
| `get_tests_for(path="...", include_indirect=true)` | `civyk-repoix query get-tests-for --path "..." --include-indirect true` |
| `get_api_endpoints(limit=200)` | `civyk-repoix query get-api-endpoints --limit 200` |

---

## Step 3: Find Existing Examples

```text
# Example directories and files
list_files(pattern="**/examples/**", include_stats=true, limit=100)
list_files(pattern="**/*example*", include_stats=true, limit=50)
list_files(pattern="**/*demo*", include_stats=true, limit=50)
list_files(pattern="**/*sample*", include_stats=true, limit=50)

# Documentation with examples
list_files(pattern="**/docs/**/*.md", limit=50)
search_code(query="```|example|usage|how to", is_regex=true, file_pattern="*.md", limit=50)

# Notebooks
list_files(pattern="**/*.ipynb", limit=30)
```

---

## Step 4: Find Test Cases as Examples

```text
# Test files
list_files(pattern="**/test*/**", include_stats=true, limit=100)
list_files(pattern="**/*.test.*", include_stats=true, limit=100)
list_files(pattern="**/*.spec.*", include_stats=true, limit=100)
list_files(pattern="**/test_*.py", include_stats=true, limit=100)

# Integration tests (best examples)
list_files(pattern="**/integration/**", limit=50)
list_files(pattern="**/e2e/**", limit=50)

# Test mapping
get_tests_for(path="<source_file>", include_indirect=true)
get_code_for_test(path="<test_file>")

# Related test files
get_related_files(path="<main_component>", relationship_types=["test"])
```

---

## Step 5: Find Entry Points

```text
# API endpoints
get_api_endpoints(limit=200)

# Main functions
search_code(query="if __name__|func main|public static void main", is_regex=true, limit=50)

# CLI commands
search_code(query="@click.command|@click.group|argparse", is_regex=true, limit=50)

# Get file symbols
get_file_symbols(path="<main_file>", kinds=["function", "class", "method"])
get_symbol(fqn="<class_fqn>")
get_callers(fqn="<function_fqn>", depth=2)
```

---

## Step 6: Extract Examples

For each example file:

```text
# Check cache first
recall_understanding(target="<example_file>")
# IF not cached: Read file: <example_file>
# [!] NOW CALL store_understanding for the file above
# -> Extract runnable code snippets
# -> Note input/output patterns
# -> Identify configuration needed

recall_understanding(target="<test_file>")
# IF not cached: Read file: <test_file>
# [!] NOW CALL store_understanding for the file above
# -> Extract setup code
# -> Extract assertions (expected behavior)

get_file_imports(path="<example_file>")
find_similar(fqn="<example_function>", similarity_threshold=0.5, limit=20)

# [!] MANDATORY: Store understanding for EACH file read above
store_understanding(
  scope="file",
  target="<example_file>",
  purpose="Usage example for <feature>",
  importance="medium",
  key_points=["<code_patterns>", "<inputs_outputs>", "<config_needed>"],
  gotchas=["<prerequisites>", "<common_mistakes>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
store_understanding(
  scope="file",
  target="<test_file>",
  purpose="Test examples for <feature>",
  importance="medium",
  key_points=["<setup_code>", "<assertions>", "<edge_cases>"],
  gotchas=["<test_dependencies>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Step 7: Generate Documentation

**[!] CRITICAL OUTPUT FILE: You MUST write to `{wiki_dir}/examples.md`**

- Do NOT create `usage.md`, `samples.md`, `demos.md`, or any other filename
- The output MUST be exactly: `{wiki_dir}/examples.md`

Write `{wiki_dir}/examples.md` using this template:

{{include:wiki/examples-template.md}}

**Fill placeholders with:** Examples summary by category, basic usage example, common operations code snippets, Mermaid workflow diagrams, test examples, SDK usage (if applicable).

---

## Step 8: Complete Stage

```bash
speckitadv deepwiki-update-state stage --stage=14-examples --status=completed --artifacts="{wiki_dir}/examples.md" --wiki-dir={wiki_dir}
```

---

## Step 9: Checkpoint Commit

```bash
git add {wiki_dir}/
git commit -m "docs(wiki): add reference documentation and examples

Generated via deepwiki stages 05-14:
- {wiki_dir}/architecture/
- {wiki_dir}/flows/
- {wiki_dir}/components/
- {wiki_dir}/api.md, models.md, configuration/
- {wiki_dir}/dependencies.md, errors.md, examples.md

[*] Generated with SpecKit DeepWiki"
```

---

## Output Format

```text
===========================================================
  STAGE COMPLETE: 14-examples

  Generated: {wiki_dir}/examples.md
  Examples: {count}
  Code snippets: {count}

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
| No examples directory | Extract from tests |
| Tests as primary examples | Reference test files |
| Interactive examples | Include notebook/REPL |
| No clear entry points | Base on public API |

---

## Next Stage

Run `{next_command}` - CLI auto-detects current stage and emits next prompt.
