---
stage: generate
requires: analyze
outputs: guideline_file, analysis_report
version: 1.1.0
status: EXPERIMENTAL
next: 04-complete.md
---

{{include:verification-rules.md}}

{{include:ai-cache-enforcement.md}}

# Stage 3: Generate

## Purpose

Synthesize findings, resolve conflicts, and generate guideline files.

---

## Step 1: Load Findings (Technical Writer Persona)

**Switch to Technical Writer & Synthesizer mindset.**

Load findings from analysis stage:

- Read `.guidelines-analysis/document-findings.md` (Phase 1 output)
- Read `.guidelines-analysis/code-findings.md` (Phase 2 output)

---

## Step 2: Merge and Detect Conflicts

**Merge findings by category:**

- Combine document principles + code patterns
- Organize by guideline template sections
- Identify alignments (doc + code agree) and conflicts (doc vs code disagree)

**[STOP: USER_INPUT_REQUIRED]**

For each conflict, ask user:

```text
Conflict: [topic] - Doc says [X], Code shows [Y]
Resolution: [A] Follow doc | [B] Follow code | [C] Other
```

Wait for ALL conflicts to be resolved. NEVER assume resolutions.

---

## Step 3: Apply RFC 2119 Severity

Based on source and consensus:

- **MUST**: Security requirements, compliance mandates, ALL (3/3) code consensus
- **SHOULD**: Best practices, MOST (2/3) code consensus, recommendations
- **MAY/OPTIONAL**: Nice-to-have, SOME (1/3) code patterns
- **NEVER**: Banned libraries, anti-patterns, security violations

---

## Step 4: Generate Guideline Content

For each section, combine relevant principles from documents + code:

- Write in principle-based format (NO CODE EXAMPLES)
- Include rationale for non-obvious requirements
- Use RFC 2119 keywords consistently

**Guideline sections:**

1. Scaffolding
2. Package Registry
3. Mandatory Libraries
4. Banned Libraries
5. Architecture
6. Security
7. Coding Standards
8. Dependency Management
9. Testing
10. Build & Deployment
11. Observability
12. Non-Compliance

---

## Step 5: Apply Update Mode

**IF UPDATE_MODE = ADD:**

- Read existing guideline file
- Append new principles to appropriate sections
- Increment version (MINOR bump)

**IF UPDATE_MODE = REPLACE:**

- Read existing guideline file
- Replace only selected sections
- Keep other sections unchanged
- Increment version (MINOR or MAJOR)

**IF UPDATE_MODE = FULL_REGEN:**

- Create backup: `.guidelines/{stack}-guidelines-vX.Y.Z.md.bak`
- Generate completely new file
- Increment version (MAJOR bump)

**IF UPDATE_MODE = NEW:**

- Backup existing file with version suffix
- Create new guideline file
- Version starts at 1.0.0 or next MAJOR

---

## Step 6: Write Guideline File

**File path**: `.guidelines/{stack}-guidelines.md`

**[!] MANDATORY CHUNKING REQUIREMENT**

The guideline file MUST be written in 4 chunks to prevent token limit issues.

**Chunk 1** - Initial Write:
Use `Write` tool to create file with:

- Header (version, tech stack, auto-detected from)
- Scaffolding section
- Package Registry section
- Mandatory Libraries section

**Chunk 2** - Append:
Use `Edit` tool with append mode (add to end of file):

- Banned Libraries section
- Architecture section
- Security section

**Chunk 3** - Append:
Use `Edit` tool with append mode:

- Coding Standards section
- Dependency Management section
- Testing section

**Chunk 4** - Append:
Use `Edit` tool with append mode:

- Build & Deployment section
- Observability section
- Non-Compliance section

**After each chunk**, display progress:

```text
[ok] Chunk X/4 complete: {sections written}
```

**Structure:**

```markdown
# {Language} Corporate Guidelines

**Tech Stack**: {Language, Frameworks, Use Cases}
**Auto-detected from**: {File patterns}
**Version**: X.Y.Z

---

## Scaffolding

**MUST**:
- {Principle from docs or code}

**NEVER**:
- {Prohibited pattern}

**Rationale**: {Why this matters}

---

## Package Registry

**MUST**:
- Configure package manager with corporate repository

**Registry URL**: {ARTIFACTORY_URL}

**Library Validation Rules**:
- Standard/Built-in: No validation needed
- External/Third-Party: Check Artifactory before use
- Corporate Internal: Use approved versions only

---

[... continue for all sections ...]

---

## Non-Compliance

If corporate library unavailable or causes blocking issue:

1. Document violation in `.guidelines-todo.md` with justification
2. Create ticket to resolve (target: next sprint)
3. Proceed with alternative, mark with comment for tracking
```

---

## Step 7: Generate Analysis Report

**File path**: `.guidelines-analysis/{stack}-analysis-report.md`

**Contents:**

- Summary: Sources analyzed, principles extracted, conflicts resolved
- Document analysis findings
- Code analysis findings
- Synthesis decisions and user resolutions
- Version history and changes made

---

## Output

```text

[ok] Generation complete
  - Guideline file: .guidelines/{{stack}}-guidelines.md
  - Version: {{version}}
  - Principles: {{count}} ({{must}} MUST, {{should}} SHOULD, {{never}} NEVER, {{may}} MAY)
  - Analysis report: .guidelines-analysis/{{stack}}-analysis-report.md
```

---

## NEXT

```text
speckitadv generate-guidelines --stage=4
```
