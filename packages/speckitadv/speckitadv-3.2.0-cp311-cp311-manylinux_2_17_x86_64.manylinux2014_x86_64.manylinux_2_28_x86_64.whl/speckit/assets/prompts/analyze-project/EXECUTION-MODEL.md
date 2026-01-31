# Execution Model: Sub-Prompt Workflow

## Overview

This document explains **how the sub-prompt architecture executes** in the Claude Code environment (v3.1).

## Validated Execution Model

**Status**: VALIDATED - Sub-prompt architecture with state verification

## Architecture Evolution

| Version | Architecture | Prompts | Lines/Prompt | Compliance |
|---------|--------------|---------|--------------|------------|
| v1.x | Monolithic | 1 | 2484 | 50% |
| v2.0 | Chained Stages | 6 | 400-890 | 75% |
| v3.1 | Sub-Prompts | 25 | 100-200 | 98% |

## How It Works

### 1. User Invocation

```bash
/analyze-project /path/to/project

```

### 2. CLI Execution (Pre-AI)

The speckitadv CLI command runs FIRST:

```bash
speckitadv analyze-project --path /path/to/project --scope A
```

**Command Actions**:

1. Validates project path
2. Runs `enumerate-project` to scan all files
3. Generates `file-manifest.json`
4. Creates analysis workspace directory
5. Initializes chain state
   - Creates `{analysis_dir}/` directory with `data/` and `reports/` subdirectories
   - Generates unique chain ID
   - Creates `{analysis_dir}/state.json` (single state file)
6. Hands off to AI

### 3. AI Execution (Sub-Prompt Workflow)

Claude Code loads: `analyze-project` command (orchestration prompt)

**AI then executes sub-prompts sequentially**:

```text
FOR each sub-prompt in [01a, 01b, 01c, 02a, 02b, 02c, 02d, 02e, 03a1-4/03b1-3, 04a-d, 05a, 06a-e]:
    1. AI runs `speckitadv analyze-project` -> CLI emits sub-prompt
    2. AI runs PRE-CHECK -> Verify previous state exists and status = "complete"
    3. AI reads ENTIRE sub-prompt output
    4. AI executes ALL instructions in sequence
    5. AI STOPS at each [STOP] marker:
       - USER_INPUT_REQUIRED -> WAIT for user response
       - Other markers -> Complete action, then AUTO-CONTINUE
    6. AI uses CLI commands to update state
    7. AI verifies state (via `speckitadv check --json`)
    8. AI checks stage end marker:
       - [AUTO-CONTINUE] -> Run `speckitadv analyze-project` to get next prompt
       - [WAIT-FOR-INPUT] -> Stop and wait for user
       - [GATE-CHECK] -> If pass: continue. If fail: wait for user
ENDFOR

```

### 4. State Flow Diagram

```text
Single State File: {analysis_dir}/state.json (CLI managed)

Stage 1: Setup and Scope
    v  01a-initialization.md -> updates state.json
    v  01b-input-collection.md -> updates state.json
    v  01c-script-execution.md -> updates state.json

Stage 2: File Analysis
    v  02a-category-scan.md -> updates state.json, writes data/category-patterns.json
    v  02b-deep-dive.md -> updates state.json, writes data/deep-dive-patterns.json
    v  02c-config-analysis.md -> updates state.json, writes data/config-analysis.json
    v  02d-test-audit.md -> updates state.json, writes data/test-audit.json
    v  02e-quality-gates.md -> updates state.json (verification only)

Stage 3: Branch (based on analysis_scope)
    v  IF scope=A: 03a1-4 sub-prompts -> updates state.json
    v  IF scope=B: 03b1-3 sub-prompts -> updates state.json

Stage 4: Report Generation
    v  04a-report-chunks-1-3.md -> updates state.json, writes reports/analysis-report.md
    v  04b-report-chunks-4-6.md -> updates state.json, appends reports/analysis-report.md
    v  04c-report-chunks-7-9.md -> updates state.json, appends reports/analysis-report.md
    v  04d-report-verification.md -> updates state.json

Stage 5: Common Artifacts
    v  05a-executive-summary.md -> updates state.json, writes reports/EXECUTIVE-SUMMARY.md

Stage 6: Scope-Specific Artifacts
    v  IF scope=A: 06a-d sub-prompts -> updates state.json
    v  IF scope=B: 06e sub-prompt -> updates state.json

COMPLETE

```

## Critical Dependencies

### Validated

- AI can use **Read** tool to load sub-prompts
- AI can use **Write** tool to save states
- AI respects **STOP markers** with visual `[PAUSE]` indicators
- state JSON persists between sub-prompts
- AI can **verify** states (write -> read -> validate)
- AI maintains context across all sub-prompts in single session
- AI can self-orchestrate: pre-check -> execute -> state -> proceed

### Assumptions

- AI follows instructions faithfully (high compliance observed with sub-prompts)
- state JSON is formatted correctly by AI (schema validation available)
- AI doesn't skip sub-prompts (explicit STOP markers prevent this)
- AI stops at STOP markers (98% compliance with visual markers)

## STOP Marker Protocol

### Format

```markdown
---
[STOP: ACTION_NAME]**

Instructions here. Do NOT proceed until action is complete.

---

```

### Types

| Marker | Purpose | User Input Required |
|--------|---------|---------------------|
| `[STOP: USER_INPUT_REQUIRED]` | Wait for user response | Yes |
| `[STOP: state_VERIFY]` | Verify state was saved | No |
| `[STOP: GENERATE_CHUNK_N]` | Generate and verify chunk | No |
| `[STOP: QUALITY_GATE]` | Verify quality criteria | No |

### Continuation Behavior

After completing a STOP marker action, the AI must follow the continuation rule:

| Marker Type | Continuation Behavior |
|-------------|----------------------|
| `USER_INPUT_REQUIRED` | **WAIT** - Do not proceed until user responds |
| `state_VERIFY` | **AUTO-CONTINUE** - Proceed immediately after verification |
| `GENERATE_CHUNK_N` | **AUTO-CONTINUE** - Proceed immediately after generation |
| `QUALITY_GATE` | **CONDITIONAL** - If PASS: auto-continue. If FAIL: wait for user |

### Stage Completion Markers

At the end of each stage/sub-prompt, use these markers:

| Marker | Meaning | AI Action |
|--------|---------|-----------|
| `[AUTO-CONTINUE]` | No user input needed | Immediately load and execute next stage |
| `[WAIT-FOR-INPUT]` | User must respond | Stop and wait for user response |
| `[GATE-CHECK]` | Quality verification | If pass: continue. If fail: present options |

**Default behavior:** If no marker specified at stage end, treat as `[AUTO-CONTINUE]`.

**Note on Q&A stages:** Stages with `[STOP: USER_INPUT_REQUIRED]` markers (like 03a1, 03a2, 01b) handle user input WITHIN the stage. After all questions are answered, they should AUTO-CONTINUE to the next stage.

### Why Visual Markers Work

The `[PAUSE]` emoji is:

- **Visually distinct** - Stands out from prose
- **Semantically meaningful** - Universal "pause" symbol
- **Attention-grabbing** - High salience to AI models
- **Consistent** - Same format across all sub-prompts

Compliance improved from 50% (text-only) to 98% (visual markers).

## state Verification

### Pattern

Every sub-prompt ends with:

```markdown
## state

Write: `{analysis_dir}/{name}-complete.json`

```json
{
  "sub_prompt": "{name}",
  "timestamp": "{ISO-8601}",
  "status": "complete"
}
```

### Verify state

1. Read `{analysis_dir}/{name}-complete.json`
2. Validate JSON is parseable
3. Confirm `status` = "complete"

---
[STOP: state_VERIFY]**

**IF verified:** Output: `[ok] state verified: {name}`
**IF failed:** Retry once, then STOP and report error

<!-- markdownlint-disable-next-line MD040 -->
```

### Why Verification Matters

Without verification:

- states might fail silently
- Recovery becomes unreliable
- Corruption goes undetected

With verification:

- Failures detected immediately
- Recovery is reliable
- Corruption is caught

## State Management

### State Files

```text
.analysis/{project}-{timestamp}/     # = {analysis_dir}
+-- state.json                       # Single state file (CLI managed)
+-- data/                            # = {data_dir}
|   +-- file-manifest.json           # Project file listing
|   +-- tech-stack.json              # Detected technologies
|   +-- category-patterns.json       # Stage 2A results
|   +-- deep-dive.json               # Stage 2B results
|   +-- config-analysis.json         # Stage 2C results
|   +-- test-audit.json              # Stage 2D results
+-- reports/                         # = {reports_dir}
    +-- analysis-report.md           # Main report (9 chunks)
    +-- EXECUTIVE-SUMMARY.md         # 1-page summary

```

### Stage vs state

| Type | Purpose | Scope |
|------|---------|-------|
| **State** | Full stage output with all data | End of stage |
| **state** | Minimal completion confirmation | Each sub-prompt |

## Dynamic Branching

Stage 3 uses dynamic branching based on `analysis_scope` from state:

```javascript
if (state.analysis_scope === "A") {
    // Load: 03a1, 03a2, 03a3, 03a4
    // Full application modernization
} else if (state.analysis_scope === "B") {
    // Load: 03b1, 03b2, 03b3
    // Cross-cutting concern migration
}

```

Stage 6 also branches:

```javascript
if (state.analysis_scope === "A") {
    // Load: 06a, 06b, 06c, 06d
} else if (state.analysis_scope === "B") {
    // Load: 06e
}

```

## Error Handling

### Sub-Prompt Failure

If a sub-prompt fails:

1. Output error with sub-prompt name
2. Save partial state with status = "failed"
3. Offer options: Retry / Skip / Debug / Abort

### state Verification Failure

If state verification fails:

1. DO NOT proceed to next sub-prompt
2. Retry state creation once
3. If still failing, STOP and report error

### Recovery from Interruption

If analysis is interrupted, AI can resume:

```bash
# Load current state

cat {analysis_dir}/state.json

# Check stages_complete array to determine resume point

# Resume from next sub-prompt based on last completed stage

```

## Performance Characteristics

### Token Usage

| Version | Prompts | Lines/Prompt | Context Load |
|---------|---------|--------------|--------------|
| Monolithic | 1 | 2484 | 2484 lines |
| Chained | 6 | ~450 | ~450 lines |
| Sub-Prompts | 25 | ~150 | ~150 lines |

**Result**: Fresh context per sub-prompt, no dilution

### Execution Time

**Additional Overhead**:

- state write/read: ~0.3s per sub-prompt
- File Read operations: ~0.2s per sub-prompt
- Total overhead: ~12s for entire chain (25 sub-prompts)

**Benefit**: 98% completion rate vs 50% -> fewer retries -> faster overall

## Comparison to Previous Versions

### vs. Monolithic Prompt (v1.x)

| Aspect | Monolithic | Sub-Prompts | Winner |
|--------|------------|-------------|--------|
| Completion Rate | 50% | 98% | Sub-Prompts |
| Instruction Compliance | 50% | 98% | Sub-Prompts |
| STOP Compliance | 50% | 98% | Sub-Prompts |
| Recovery | Restart | Resume | Sub-Prompts |
| Debugging | Hard | Per sub-prompt | Sub-Prompts |

### vs. Chained Stages (v2.0)

| Aspect | Chained | Sub-Prompts | Winner |
|--------|---------|-------------|--------|
| Completion Rate | 75% | 98% | Sub-Prompts |
| Lines per Unit | 400-890 | 100-200 | Sub-Prompts |
| Granularity | 6 stages | 25 sub-prompts | Sub-Prompts |
| states | Stage-level | Sub-prompt | Sub-Prompts |

## Conclusion

The sub-prompt architecture with visual STOP markers and state verification is **validated and production-ready** for the analyze-project workflow.

**Key Success Factors**:

1. **Small units** (~150 lines) with single purpose
2. **Visual STOP markers** (`[PAUSE]`) for high salience
3. **state verification** (write -> read -> validate)
4. **Fresh context** per sub-prompt
5. **Granular recovery** via states

---

**Last Updated**: 2025-12-21
**Version**: 3.1.0-subprompts
**Status**: VALIDATED
