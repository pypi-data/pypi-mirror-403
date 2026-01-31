---
stage: initialization
requires: nothing
outputs: agents_verified, role_understood, sources_path
version: 1.1.0
status: EXPERIMENTAL
next: 02-analyze.md
---

{{include:strict-execution-mode.md}}

# Stage 1: Initialization

## Purpose

Initialize guideline generation by verifying AGENTS.md, understanding your role, and collecting user input.

---

## Step 1: Verify Agent Instructions

Check if `AGENTS.md` exists in repository root: `./AGENTS.md`

**IF EXISTS**: Read it in FULL. Instructions are NON-NEGOTIABLE.

**Verification**: Acknowledge with:

```text

[ok] Read AGENTS.md v[X.X] - Following all guidelines
```

**IF NOT EXISTS**: Proceed with default behavior.

---

## Step 2: Understand Your Role

Embody **THREE personas** sequentially for comprehensive analysis:

| Persona | Focus | Key Standards |
|---------|-------|---------------|
| **Standards Architect** | Extract principles from docs | Source refs, RFC 2119 keywords, flag ambiguities |
| **Code Archeologist** | Reverse-engineer patterns | file:line evidence, consensus (3/3=MUST, 2/3=SHOULD) |
| **Technical Writer** | Synthesize into guidelines | Principle-based, version-agnostic, no code examples |

**Core Rules:**

- Reference source (document:page or file:line) for every principle
- Use RFC 2119 keywords: MUST/SHOULD/MAY/NEVER
- Flag conflicts for user resolution - never guess
- Extract principles, NEVER copy code examples

**Guideline Philosophy:**

Guidelines define WHAT/WHY, never HOW with code:

| Benefit | Reason |
|---------|--------|
| Version-agnostic | Works across framework versions without updates |
| AI-adaptable | Agents choose syntax for detected version |
| Maintenance-free | Update only when principles change |

---

## Step 3: Collect User Input

**Arguments provided:**

```text
SOURCES_PATH: {sources_path:$NONE}
```

**IF sources_path shows "$SKIP"**: User explicitly chose no input. Cannot proceed without sources.

**IF sources_path shows "$NONE"**: Prompt user:

**[STOP: USER_INPUT_REQUIRED]**

```text
SOURCES_PATH: /path/to/folder (with docs/ and reference-projects/ subdirs)
```

Wait for response before proceeding.

**IF sources_path has actual value** (not "$NONE" or "$SKIP"): Use it directly and skip prompting.

---

## Step 4: Run Setup Script

Execute from repo root (cross-platform).

Note: Replace `{{SOURCES_PATH}}` with the actual path provided or collected above.

```bash
speckitadv generate-guidelines {{SOURCES_PATH}} --setup-only
```

The command will:

- Enumerate all files in SOURCES_PATH
- Categorize into docs/ and reference-projects/
- Generate manifests (documents-manifest.json, projects-manifest.json)
- Create analysis workspace: `.guidelines-analysis/`

Parse: `SOURCES_PATH`, `DOCUMENTS_MANIFEST`, `PROJECTS_MANIFEST`

---

## Output

```text

[ok] Initialization complete
  - AGENTS.md: [Found/Not found]
  - Role: Guidelines Generator (3 personas)
  - Sources path: {{sources_path}}
  - Analysis workspace: .guidelines-analysis/
```

---

## NEXT

```text
speckitadv generate-guidelines --stage=2
```

**Note:** Standalone commands require --stage flag for progression.
