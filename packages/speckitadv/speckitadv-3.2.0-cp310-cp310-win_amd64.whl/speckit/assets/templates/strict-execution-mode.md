# STRICT MODE

Follow instructions EXACTLY. No deviations.

## Mandatory Execution Rules

**CRITICAL: You MUST follow these rules without exception:**

1. **Execute ALL prompt instructions** - Do NOT summarize this prompt or skip steps
2. **Run CLI for EACH stage** - Always run `speckitadv analyze-project` to get the next stage
3. **Never bypass prompts** - Do NOT generate content without loading the stage prompt first
4. **Read full output files** - If CLI output is truncated, READ the full saved file
5. **Never ask to continue** - When told "agentic", proceed through ALL stages without pausing

## Core Rules

| Rule | Description |
|------|-------------|
| No Skipping | Execute every step in order |
| No Combining | Do not merge steps |
| No Improvising | Follow documented approach only |
| No Inventing | Do not create stages/files/parameters not specified |
| Checkpoint First | Complete each checkpoint before proceeding |
| Exact Formats | Match specified formats exactly |
| No Summarizing | Execute prompt steps, do not summarize them |
| No Permission Asking | Do not ask "should I continue?" - just continue |

## Stage IDs

- Use ONLY stage IDs from prompt frontmatter (`stage:` line)
- CLI validates stage IDs - invented IDs cause errors
- Valid: `--stage=02a-category-scan`, `--stage=06-flows`
- INVALID: `--stage=06a4-technical-spec` (doesn't exist)

## Multi-Part Sequences

When prompt says "Part X of Y":

1. Complete ALL parts (Part 1 -> Part 2 -> ... -> Part Y)
2. Run `speckitadv analyze-project` between each part
3. Never skip to completion after Part 1

## Output Files

- Create ONLY files specified in prompt
- No extra "helper" or "summary" files
- Use exact filenames (e.g., `FUNCTIONAL-SPEC-LEGACY.md` not `functional-spec.md`)

## Common Violations

| Violation | Wrong | Correct |
|-----------|-------|---------|
| Inventing stages | `--stage=06a4-technical-spec` | Use stage from frontmatter |
| Combining outputs | `TECHNICAL-SPEC.md` | `TECHNICAL-SPEC-LEGACY.md` AND `TECHNICAL-SPEC-TARGET.md` |
| Skipping parts | Part 1 -> Complete | Part 1 -> Part 2 -> Part 3 -> Complete |
| Wrong keys | `q6_caching` | `q6_iac` (from prompt table) |
| Ad-hoc files | `testing/README.md` | Only files specified in prompt |

## CLI Commands

Copy command EXACTLY from prompt:

```text
DO:   speckitadv write-report FUNCTIONAL-SPEC-LEGACY.md --stage=06a1-functional-spec-legacy-part1 --stdin
DON'T: speckitadv write-report FUNCTIONAL-SPEC.md --stage=06a-functional-spec --stdin
```

## Question Rules

- Ask EXACTLY the questions listed
- Use EXACT preference keys (e.g., `q6_iac`, not `q6_caching`)
- Do NOT substitute your own questions

## JSON Escaping

Escape backslashes in Windows paths: `\\` not `\`

| Path | In JSON | In bash argument |
|------|---------|------------------|
| `VEERU-PC\SQL` | `"VEERU-PC\\SQL"` | `'{"s":"VEERU-PC\\\\SQL"}'` |

Use heredoc to avoid double escaping:

```bash
speckitadv write-data file.json --stdin <<'EOF'
{"server": "VEERU-PC\\SQLEXPRESS"}
EOF
```

## Handling Truncated Output

When CLI output shows "Output too large... Full output saved to: [path]":

1. **READ the full file** using the Read tool
2. **Follow ALL instructions** in the full file
3. **Do NOT skip** based on the preview alone

## [AUTO-CONTINUE] Rule

**CRITICAL: When you see `[AUTO-CONTINUE]` in a prompt, it means:**

1. **RUN THE CLI COMMAND** shown in the `## Next Stage` section below it
2. **DO NOT** continue analyzing or generating artifacts on your own
3. **DO NOT** call MCP tools or read files without the next stage prompt
4. **WAIT** for the CLI to emit the next stage prompt before doing anything else

**Why this matters:** Each stage has specific templates and instructions. If you skip the CLI call, you will:
- Generate wrong artifacts (missing templates)
- Use wrong formats (missing stage-specific formatting)
- Miss required steps (each stage has unique requirements)

## Agentic Mode

When user says "continue with all stages" or "agentic way":

1. **Run `speckitadv analyze-project`** after EACH stage completes
2. **Load and follow** each stage prompt completely
3. **Do NOT invent** your own stage sequence
4. **Do NOT generate content** without the stage prompt

## Recovery

If violation occurred:

1. STOP immediately
2. Identify broken rule
3. Run correct command
4. Do NOT continue with wrong approach

## Behavioral Guidelines

From prompt-base.md:

| Rule | Requirement |
|------|-------------|
| Read before modify | Read files before suggesting changes |
| No time estimates | Never predict how long tasks will take |
| Use indexed tools | Prefer civyk-repoix over grep/find |
| PASS/FAIL explicit | Report verification results explicitly |
| No rounding up | "Almost working" is not "working" |

## Stage Completion Checklist

Before proceeding to next stage, verify:

- [ ] Ran CLI command exactly as shown in NEXT: line
- [ ] Read full prompt output (not just preview)
- [ ] Followed ALL steps in prompt
- [ ] Used correct stage IDs (not invented)
- [ ] Created only specified output files
