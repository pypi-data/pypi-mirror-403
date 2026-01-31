---
stage: quickstart
requires: business-context
outputs: "{wiki_dir}/quickstart.md"
version: 2.1.0
---

# Stage 3: Quick Start Guide

Generate a Quick Start guide enabling new developers to run the project in under 30 minutes.

## Prerequisites

- Stage 02 completed with business context saved
- Mode: `{REPOIX_MODE}` (if "cli", convert MCP calls per AGENTS.md)
- Business context must be populated (non-empty `project_name`)

## Critical Rules

| Rule | Action |
|------|--------|
| Business context required | **MUST** verify business_context populated before proceeding |
| Entry point required | **MUST** identify at least 1 package file OR entry point |
| Prerequisites section | **MUST** include in generated quickstart.md |

---

## AI Context Cache: Check Cached Understanding

**[!] MANDATORY: Check cache status FIRST.**

```text
# [!] MANDATORY: Check cache status at stage start
get_understanding_stats(limit=50)

# Recall understanding for paths from stats output
recall_understanding(target="project")

# Use ACTUAL paths from YOUR get_understanding_stats output:
# recall_understanding(target="{path_from_stats}")  # if exists in stats

# IF found AND fresh: Use cached tech stack and setup info
# IF not found: Proceed with discovery, then MUST store findings
```

---

## Step 1: Verify Previous Stage

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir}
```

Confirm:

- `02-business-context` in `stages_complete`
- `business_context_file` is set
- `business_context.project_name` exists

**Stop if business context is empty.**

---

## Step 2: Detect Git Remote

```bash
git remote -v 2>/dev/null || echo "No remotes configured"
```

Extract URL for clone instructions. Use placeholder if no remote found.

---

## Step 3: Gather Project Information

Find package/dependency files:

```text
list_files(pattern="**/package.json", limit=20)
list_files(pattern="**/pyproject.toml", limit=10)
list_files(pattern="**/requirements*.txt", limit=20)
list_files(pattern="**/Cargo.toml", limit=10)
list_files(pattern="**/go.mod", limit=10)
```

Find config files:

```text
list_files(pattern="**/.env*", limit=20)
list_files(pattern="**/docker-compose*.yml", limit=10)
list_files(pattern="**/Makefile", limit=10)
```

**Read key files (with AI cache):**

```text
# FIRST: Check cached understanding for key files
recall_understanding(target="README.md")
recall_understanding(target="<package_file>")  # e.g., package.json, pyproject.toml

# IF found AND fresh: Use cached analysis
# IF not found: Read files, then MUST store understanding

# [!] MANDATORY: Store understanding for EACH file read
store_understanding(
  scope="file",
  target="README.md",
  purpose="Project documentation and setup instructions",
  importance="high",
  key_points=["<project_description>", "<prerequisites>", "<setup_steps>"],
  gotchas=["<common_issues>", "<special_requirements>"],
  analysis="<detailed_logic_and_flow_explanation>"
)

# [!] NOW CALL store_understanding for the file above
store_understanding(
  scope="file",
  target="<package_file>",
  purpose="Package configuration and dependencies",
  importance="high",
  key_points=["<main_entry>", "<scripts>", "<key_dependencies>"],
  gotchas=["<version_constraints>", "<peer_dependencies>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Step 4: Identify Entry Points

```text
# Python
search_code(query="if __name__", file_pattern="*.py", limit=50)
search_code(query="@click.command", limit=30)

# Node.js
search_code(query="\"scripts\":", file_pattern="package.json", limit=20)

# Go/Rust/Java
search_code(query="func main", file_pattern="*.go", limit=20)
search_code(query="fn main", file_pattern="*.rs", limit=20)
search_code(query="public static void main", limit=20)

# API endpoints
get_api_endpoints(limit=100)
```

**Target:** At least 1 entry point (package script, main function, CLI command, OR API endpoint).

---

## Step 5: Generate Quick Start

Write to `{wiki_dir}/quickstart.md` using this template:

{{include:wiki/quickstart-template.md}}

**Fill placeholders with discovered information from Steps 2-4.**

---

## Step 6: Complete Stage

```bash
speckitadv deepwiki-update-state stage --stage=03-quickstart --status=completed --artifacts="{wiki_dir}/quickstart.md" --wiki-dir={wiki_dir}
```

---

## Output Format

```text
===========================================================
  STAGE COMPLETE: 03-quickstart

  Summary:
    - Generated: {wiki_dir}/quickstart.md
    - Git remote: {URL or "placeholder"}
    - Prerequisites: {count} identified
    - Entry points: {count} found

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
| No package files | Look for Makefile, Dockerfile, shell scripts |
| No entry points | Check bin/, scripts/ folders; document as library if applicable |
| Mixed languages | Document prerequisites for each language |

---

## Next Stage

Run `{next_command}` - CLI auto-detects current stage and emits next prompt.
