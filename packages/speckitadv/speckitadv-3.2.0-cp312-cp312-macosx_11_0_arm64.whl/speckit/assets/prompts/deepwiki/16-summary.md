---
stage: summary
requires: enrichment
outputs: "{wiki_dir}/README.md"
version: 2.1.0
---

# Stage 16: Summary & Finalization

Complete wiki generation with main README, navigation index, quality metrics, and workflow completion.

## Prerequisites

- Stage 15 completed with enrichment applied
- Mode: `{REPOIX_MODE}` (if "cli", convert MCP calls per AGENTS.md)
- Discovery cache loaded: PROJECT_SIZE, PRIMARY_LANGUAGE

## Critical Rules

| Rule | Action |
|------|--------|
| Enrichment required | **MUST** verify enrichment stage completed |
| Protect custom | **NEVER** overwrite {wiki_dir}/custom/ directory |
| Quality metrics | **MUST** calculate and report quality metrics |
| Generate README | **MUST** generate {wiki_dir}/README.md with index |
| Final commit | **MUST** commit all wiki files at end |

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

# IF found AND fresh: Use cached analysis for summary generation
# IF not found: Use discovery tools, then MUST store findings
```

---

## Step 1: Verify Previous Stage

```bash
speckitadv deepwiki-update-state verify-stage --stage=16-summary --wiki-dir={wiki_dir}
```

---

## Step 2: List Generated Files

Verify all expected wiki files were generated:

```text
{wiki_dir}/
  README.md           (this stage creates)
  quickstart.md
  overview.md
  architecture/       (diagrams, decisions)
  flows/              (README + flow files)
  components/         (README + component files)
  api.md
  models.md
  configuration/      (README + config files)
  dependencies.md
  errors.md
  examples.md
```

---

## Step 3: Get Final Statistics

```text
index_status()
get_components()
```

---

## Step 4: Calculate Quality Metrics

```text
QUALITY_METRICS = {
  coverage: components_documented / components_total,
  cross_references: internal_links_count,
  completeness: stages_completed / 15,
  business_context: features_documented > 0
}

QUALITY_SCORE = (coverage * 30) + (xref * 25) + (completeness * 25) + (business * 20)
# Score 0-100, Rating: 90+ Excellent, 70-89 Good, 50-69 Fair, <50 Needs Work
```

---

## Step 5: Generate README

Write `{wiki_dir}/README.md` with:

```markdown
# <<PROJECT_NAME>> Documentation

> Auto-generated via [SpecKit DeepWiki](https://github.com/speckit)

## Quick Navigation
- [Quick Start](quickstart.md)
- [Overview](overview.md)
- [Components](components/README.md)

## Documentation Index

### Core Documentation
| Document | Description |
|----------|-------------|
| [Quick Start](quickstart.md) | Installation and first steps |
| [Overview](overview.md) | Codebase architecture |
| [Diagrams](architecture/diagrams.md) | Visual architecture |
| [Flows](flows/README.md) | Request and data flows |

### Reference Documentation
| Document | Description |
|----------|-------------|
| [API Reference](api.md) | Endpoints and usage |
| [Data Models](models.md) | Entity definitions |
| [Configuration](configuration/README.md) | Config options |
| [Dependencies](dependencies.md) | Deps and relationships |

### Advanced Documentation
| Document | Description |
|----------|-------------|
| [Decisions](architecture/decisions.md) | Arch decisions |
| [Errors](errors.md) | Error handling |
| [Examples](examples.md) | Usage examples |

## Statistics
- Files Indexed: <<FILE_COUNT>>
- Components: <<COMPONENT_COUNT>>
- Generated: <<TIMESTAMP>>

## Custom Documentation
Add custom docs in `{wiki_dir}/custom/` - preserved during regeneration.
```

---

## Step 6: Mark Stage Complete

```bash
speckitadv deepwiki-update-state stage --stage=16-summary --status=completed --artifacts="{wiki_dir}/README.md" --wiki-dir={wiki_dir}
```

---

## Step 7: Mark Workflow Complete

```bash
speckitadv deepwiki-update-state complete
```

---

## Step 8: Final Commit

```bash
git add {wiki_dir}/
git commit -m "docs(wiki): complete deepwiki documentation generation

Generated complete wiki documentation:
- {wiki_dir}/README.md (main index)
- {wiki_dir}/quickstart.md, overview.md
- {wiki_dir}/architecture/, flows/, components/
- {wiki_dir}/api.md, models.md, configuration/
- {wiki_dir}/dependencies.md, errors.md, examples.md

Quality Score: {score}/100

[*] Generated with SpecKit DeepWiki"
```

---

## Output Format

```text
+==============================================================+
|                    DeepWiki Generation Complete              |
+==============================================================+
|  Files Generated: {count}                                    |
|  Components documented: {count}                              |
|  Quality Score: {score}/100 ({rating})                       |
|                                                              |
|  AI Cache Efficiency:                                        |
|    - Files read: <count_read>                                |
|    - Files cached (store_understanding): <count_stored>      |
|    - Cache hits (found=true, fresh=true): <count_hits>       |
|                                                              |
|  Next Steps:                                                 |
|    1. Review generated documentation                         |
|    2. Add custom docs to {wiki_dir}/custom/ if needed        |
|    3. Push to repository                                     |
+==============================================================+

WORKFLOW_COMPLETE:DEEPWIKI
```

---

## Edge Cases

| Scenario | Action |
|----------|--------|
| Partial generation | Update README for available sections |
| Previous wiki exists | Preserve {wiki_dir}/custom/ |
| Large wiki (>50 files) | Suggest enabling search |

---

## Workflow Complete

Run `speckitadv deepwiki-update-state show` to view final state with all artifacts tracked.
