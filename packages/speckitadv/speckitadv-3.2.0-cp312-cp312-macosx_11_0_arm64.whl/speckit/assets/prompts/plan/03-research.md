---
stage: research
requires: setup
outputs: research_md
version: 1.1.0
next: 04-design.md
---

# Stage 3: Research & Initial Plan Sections

## Purpose

1. Create research.md with technical decisions
2. Fill initial plan.md sections (Summary, Technical Context, Constitution Check)

---

## Tools (if REPOIX_MODE != "none")

{{include:plan-civyk-repoix-discovery.md}}

---

## Discovery-First (with AI Context Cache)

Before researching external solutions, discover existing codebase patterns:

```text
# FIRST: Check what's cached from earlier stages
get_understanding_stats(limit=50)

# Recall cached understanding of relevant modules
recall_understanding(target="<relevant_module_path>")
# IF error (MCP connection failed): Fallback to manual exploration
# IF found AND fresh: Use cached patterns/conventions
# IF not found OR stale: Proceed with discovery below
```

- Use civyk-repoix MCP/CLI to discover existing utils, base classes, methods, patterns
- Use `get_duplicate_code(source_only=true)` to find similar implementations you can extend
- Use `find_similar(fqn)` to find related code when you identify a relevant symbol
- Prefer extending existing patterns over introducing new ones
- Consider edge cases in design decisions

```text
# [!] MANDATORY: Store understanding for key patterns discovered
store_understanding(
  scope="module",
  target="<module_path>",
  purpose="<module purpose>",
  importance="medium",
  key_points=["<patterns found>", "<conventions>"],
  gotchas=["<anti-patterns to avoid>"],
  analysis="<detailed_logic_and_flow_explanation>",
  related_to=["<related_modules>"]
)
```

**IF REPOIX_MODE == "none":** Manually explore codebase via file reading.

---

## Step 1: Extract Unknowns

Review the specification for:

- Items marked "NEEDS CLARIFICATION"
- Dependencies requiring best practices research
- Integrations requiring pattern research
- Technology choices not specified

---

## Step 2: Execute Research

For each unknown or technology choice:

1. Search for authoritative sources
2. Evaluate options and tradeoffs
3. Document findings

---

## Step 2.5: Validate Dependencies Against Artifactory

{{include:artifactory-validation.md}}

**When to validate:**

- After identifying required dependencies in Step 2
- Before finalizing technology choices in research.md

**Add to research.md:**

```markdown
## Dependency Validation

| Package | Version | Purpose | Artifactory Status |
|---------|---------|---------|-------------------|
| ... | ... | ... | [VERIFIED] / [NOT FOUND] / [SKIPPED] |

**Blocked Dependencies** (if any):
- `<package>`: Not found in Artifactory - alternative: `<alternative>`
```

---

## Step 3: Create research.md

Use the **Write tool** to create `{{feature_dir}}/research.md`:

```markdown
# Research: <feature name>

## Decision: [Topic 1]

**Chosen**: [what was selected]
**Rationale**: [why selected]
**Alternatives considered**: [what else evaluated]
**Sources**: [links/references]

## Decision: [Topic 2]

...
```

---

## Step 4: Fill Plan Sections (Chunk 1 of 3)

Edit `{{feature_dir}}/plan.md` to fill these sections:

### 4.1 Summary Section

Replace the `[Extract from feature spec...]` placeholder with:

- Primary requirement from spec
- Technical approach from research

### 4.2 Technical Context Section

Fill ALL fields, replacing `[...]` and `NEEDS CLARIFICATION`:

- Language/Version
- Primary Dependencies
- Storage
- Testing
- Target Platform
- Project Type
- Performance Goals
- Constraints
- Scale/Scope

### 4.3 Constitution Check Section

Validate spec against constitution principles. Fill the section with:

- Each principle from constitution.md
- Pass/fail status for each
- Notes on any violations

**IMPORTANT**: Do NOT leave any `[...]` placeholders in these sections.

---

## Step 5: Validate Chunk 1

Verify all sections are filled:

- [ ] research.md created with all decisions
- [ ] Summary section filled (no placeholders)
- [ ] Technical Context filled (no placeholders)
- [ ] Constitution Check completed

**IF violations found in Constitution Check**: Document in Complexity Tracking section.

---

## Output

```text
[ok] Research complete
  - Decisions: [N] documented
  - File: {{feature_dir}}/research.md
  - Plan sections filled: Summary, Technical Context, Constitution Check
```

Then run the next command shown below.
