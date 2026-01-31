---
stage: check-repoix
requires: nothing
outputs: mcp_verified, index_ready, repoix_mode
version: 2.1.0
---

# Stage 1: Check civyk-repoix

## CRITICAL: Read AGENTS.md First

**Before doing anything else:** If `./AGENTS.md` exists in the repository root, read and honor all instructions in that file. AGENTS.md contains project-specific guidelines that take precedence over default behavior.

---

Verify civyk-repoix is available (via MCP or CLI) and codebase index is ready before generating documentation.

**This is the first stage** - all subsequent stages depend on successful civyk-repoix connection and ready index.

## Critical Rules

| Rule | Action |
|------|--------|
| Connection required | **NEVER** proceed without verified civyk-repoix (MCP or CLI) |
| Index ready | **NEVER** proceed with index status != "ready" |
| Files indexed | **NEVER** proceed with zero files indexed |
| Protect custom | **NEVER** modify {wiki_dir}/custom/ directory |

---

## Step 1: Check civyk-repoix Availability

**Strategy:** Try MCP first, fall back to CLI if MCP fails.

### Step 1a: Try MCP First

```text
mcp__civyk-repoix__index_status()
```

**IF MCP succeeds:** Set `REPOIX_MODE = "mcp"` and proceed to Step 2.

### Step 1b: CLI Fallback (if MCP fails)

```bash
civyk-repoix query index-status
```

**IF CLI succeeds:** Set `REPOIX_MODE = "cli"` and proceed to Step 2.

### Step 1c: Both Failed

```text
[x] Cannot connect to civyk-repoix
    - MCP: not available
    - CLI: not available

    To fix:
    1. Install: pip install civyk-repoix
    2. Start daemon: civyk-repoix daemon start
    3. Verify: civyk-repoix query index-status
```

**STOP** - Cannot proceed without civyk-repoix.

---

## Step 2: Validate Index Ready

| Check | Condition | Required |
|-------|-----------|----------|
| Connection | Response received | Yes |
| Status | `status == "ready"` | Yes |
| Files | `file_count > 0` | Yes |
| Symbols | `symbol_count > 0` | Yes |

**IF ALL pass:** Proceed to Step 3.
**IF status == "indexing":** Wait for completion.
**IF file_count == 0:** Cannot generate wiki for empty repository.

---

## Step 3: Verify Component Detection

```text
# MCP mode:
mcp__civyk-repoix__get_components()

# CLI mode:
civyk-repoix query get-components
```

---

## Step 4: Initialize Wiki State

```bash
speckitadv deepwiki-update-state init --files=<file_count> --symbols=<symbol_count> --components="<component_list>" --repoix-mode=<REPOIX_MODE> --wiki-dir={wiki_dir}
```

**Example:**

```bash
speckitadv deepwiki-update-state init --files=702 --symbols=2968 --components="core,api,ui" --repoix-mode=mcp --wiki-dir={wiki_dir}
```

---

## Step 5: File Preservation Rules

| Type | Path | Action |
|------|------|--------|
| Generated | `{wiki_dir}/*.md` | MAY overwrite |
| Protected | `{wiki_dir}/custom/**` | NEVER modify |

---

## Step 6: Large Codebase Strategy

| Content Type | Chunk Size | Strategy |
|--------------|------------|----------|
| Component docs | 500-800 lines | One component per chunk |
| API docs | 300-500 lines | Endpoints in groups |
| Flow diagrams | 300-500 lines | One flow per chunk |

**IF components > 50:** Use chunked generation strategy.

---

## Step 7: Mark Stage Complete

```bash
speckitadv deepwiki-update-state stage --stage=01-check-repoix --status=completed --wiki-dir={wiki_dir}
```

---

## Output Format

```text
===========================================================
  STAGE COMPLETE: 01-check-repoix

  Summary:
    - civyk-repoix: connected ({REPOIX_MODE} mode)
    - Index: ready ({file_count} files, {symbol_count} symbols)
    - Components: {count} detected
    - Protected: {wiki_dir}/custom/ (preserved)

  Next: Run {next_command}
===========================================================
```

---

## Edge Cases

| Scenario | Action |
|----------|--------|
| MCP unavailable, CLI works | Use CLI mode for all stages |
| Neither MCP nor CLI | Stop - install civyk-repoix first |
| Index not ready | Wait for indexing to complete |
| Empty repository | Cannot generate wiki |
| Very large repo (>10k files) | Use --component flag for incremental generation |

---

## Next Stage

Run `{next_command}` - CLI auto-detects current stage and emits next prompt.
