---
stage: overview
requires: quickstart
outputs: "{wiki_dir}/overview.md"
version: 2.1.0
---

# Stage 4: Codebase Overview

Generate a comprehensive overview combining business context with architecture summary and component listing.

## Prerequisites

- Stage 03 completed with quickstart.md generated
- Mode: `{REPOIX_MODE}` (if "cli", convert MCP calls per AGENTS.md)
- Business context populated from Stage 02

## Critical Rules

| Rule | Action |
|------|--------|
| Business context required | **MUST** verify populated before proceeding |
| Component discovery | **MUST** discover at least 1 component or language |
| Mermaid diagrams only | **MUST** use Mermaid syntax for ALL diagrams (no ASCII art) |
| Checkpoint commit | **MUST** commit wiki files at end of this stage |

---

{{include:ai-cache-enforcement.md}}

## AI Context Cache: Check Cached Understanding

**[!] MANDATORY: Check cache status FIRST.**

```text
# [!] MANDATORY: Check cache status at stage start
get_understanding_stats(limit=50)

# Recall understanding for paths from stats output
recall_understanding(target="project")

# IF found AND fresh: Use cached analysis to guide discovery
# IF not found: Proceed with discovery, then MUST store findings
```

---

## Step 1: Verify Previous Stage

```bash
speckitadv deepwiki-update-state verify-stage --stage=04-overview --wiki-dir={wiki_dir}
```

**Stop if CLI returns error.**

---

## Step 2: Load Business Context

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir}
```

Or read full context: `{wiki_dir}/business-context.json`

**Stop if business_context is empty.**

```text
# [!] MANDATORY: Store business context understanding after reading
store_understanding(
  scope="file",
  target="{wiki_dir}/business-context.json",
  purpose="Business context and domain knowledge from stakeholder input",
  importance="critical",
  key_points=["<project_name>", "<key_features>", "<main_entities>", "<business_rules>"],
  gotchas=["<constraints>", "<dependencies>", "<glossary_terms>"],
  analysis="<business_domain>: <what_it_does>. <key_workflows>: <workflow1>, <workflow2>. <data_entities>: <entity1>, <entity2>."
)
```

---

## Step 3: Get Architecture Context

**Load discovered patterns from discovery_cache:**

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir}
# Extract: COMPONENT_SUFFIXES = discovery_cache.file_patterns.component_patterns.suffixes
# Extract: COMPONENT_PREFIXES = discovery_cache.file_patterns.component_patterns.prefixes
# Extract: LIMITS = discovery_cache.project_size.limits
```

```text
# Components and dependencies
get_components()
get_dependencies()
find_circular_dependencies(level="component")
get_hotspots(since="90d", group_by="component", limit=30)

# Code quality indicators
get_dead_code(limit=50)
get_duplicate_code(source_only=true, similarity_threshold=0.7, limit=30)

# Architecture overview
build_context_pack(task="understand codebase architecture", token_budget=3000, prefer_kinds=["class", "function"])

# API entry points
get_api_endpoints(limit=200)
```

**MUST search using ALL YOUR discovered patterns:**

```text
# MANDATORY: For EACH suffix in your COMPONENT_SUFFIXES, search with %<SUFFIX>:
# Example if COMPONENT_SUFFIXES = ["Dto", "Service", "Controller", "Validator"]:
search_symbols(query="%Dto", kind="class", limit=LIMITS.symbols)
search_symbols(query="%Service", kind="class", limit=LIMITS.symbols)
search_symbols(query="%Controller", kind="class", limit=LIMITS.symbols)
search_symbols(query="%Validator", kind="class", limit=LIMITS.symbols)
# ... continue for ALL suffixes in YOUR discovered COMPONENT_SUFFIXES

# MANDATORY: For EACH prefix in your COMPONENT_PREFIXES, search with <PREFIX>%:
# Example if COMPONENT_PREFIXES = ["Base", "I", "Abstract"]:
search_symbols(query="Base%", kind="class", limit=LIMITS.symbols)
search_symbols(query="I%", kind="interface", limit=LIMITS.symbols)
search_symbols(query="Abstract%", kind="class", limit=LIMITS.symbols)
# ... continue for ALL prefixes in YOUR discovered COMPONENT_PREFIXES
```

**[!] CRITICAL:** The patterns above are examples. You **MUST** use YOUR actual discovered COMPONENT_SUFFIXES and COMPONENT_PREFIXES from enumerate-index output, not these examples.

**Read key files:** README.md for architecture, main entry point for bootstrap sequence.

```text
# [!] MANDATORY: Store MCP discovery summary after gathering architecture context
store_understanding(
  scope="module",
  target="discovery/architecture",
  purpose="Architecture discovery results from MCP analysis",
  importance="high",
  key_points=["<component_count> components", "<api_endpoint_count> endpoints", "<circular_deps_if_any>"],
  gotchas=["<dead_code_areas>", "<duplicate_code_hotspots>", "<hotspot_files>"],
  analysis="<components>: <component_list>. <dependencies>: <dep_graph_summary>. <patterns>: <suffix_patterns>, <prefix_patterns>. <quality_issues>: <dead_code>, <duplicates>."
)

# ALSO store understanding for any key files read (README.md, main entry point)
# (Apply 1:1 Read:Store rule)
```

---

## Step 4: Analyze Tech Stack

```text
list_files(pattern="**/*", include_stats=true, limit=50)
```

Identify: primary languages, frameworks, database type, key dependencies.

---

## Step 5: Generate Overview

Write to `{wiki_dir}/overview.md` using this template:

{{include:wiki/overview-template.md}}

**Fill placeholders with:**

- Business context (from Stage 02): project_name, features, entities, rules, glossary
- MCP discovery: tech stack, components, architecture
- All diagrams MUST use Mermaid syntax

---

## Step 6: Store Project Understanding (AI Context Cache)

After analyzing the codebase architecture, persist understanding for future stages:

```text
# Store project-level understanding for cross-session recall
store_understanding(
  scope="project",
  target="project",
  purpose="<1-2 sentence summary of what this codebase does>",
  importance="critical",
  key_points=[
    "<Primary language and framework>",
    "<Main architectural pattern>",
    "<Key components discovered>",
    "<Notable patterns or conventions>"
  ],
  gotchas=[
    "<Any architectural concerns found>",
    "<Circular dependencies if any>",
    "<Dead code areas if significant>"
  ],
  analysis="<architecture_summary>: <layers>, <patterns>. <data_flow>. <key_decisions>.",
  related_to=["<main_entry_points>", "<key_config_files>"]
)
```

**Benefits:** Later stages (05-16) can `recall_understanding(target="project")` to quickly access this analysis without re-running discovery.

---

## Step 7: Complete Stage

```bash
speckitadv deepwiki-update-state stage --stage=04-overview --status=completed --artifacts="{wiki_dir}/overview.md" --wiki-dir={wiki_dir}
```

---

## Step 8: Checkpoint Commit

```bash
git add {wiki_dir}/
git commit -m "docs(wiki): add overview and quickstart documentation

Generated via deepwiki stages 01-04:
- {wiki_dir}/quickstart.md
- {wiki_dir}/overview.md
- {wiki_dir}/business-context.json

[*] Generated with SpecKit DeepWiki"
```

Verify with `git status`. **Do not push yet.**

---

## Output Format

```text
===========================================================
  STAGE COMPLETE: 04-overview

  Summary:
    - Generated: {wiki_dir}/overview.md
    - Features: {count} documented
    - Components: {count} documented
    - Tech stack: {languages} / {frameworks}

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
| Missing business context | Re-run stage 02 |
| No components detected | Use directory structure as component boundaries |
| Large codebase (>1000 files) | Focus on top-level components only |
| Monorepo | Document each package as separate component |

---

## Next Stage

Run `{next_command}` - CLI auto-detects current stage and emits next prompt.
