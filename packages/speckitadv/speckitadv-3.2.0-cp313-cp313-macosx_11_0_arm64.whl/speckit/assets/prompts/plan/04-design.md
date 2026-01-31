---
stage: design
requires: research
outputs: data_model, contracts, quickstart
version: 1.1.0
next: null
---

# Stage 4: Design & Complete Plan

## Purpose

1. Fill remaining plan.md sections (Chunks 2 and 3)
2. Generate supporting artifacts (data-model.md, contracts/, quickstart.md)

---

## [!] File Write Best Practices

**For large artifacts:**

- Use chunked writing when content exceeds 2000 characters
- Steps 1-2 are already chunked for plan.md
- For supporting artifacts (Step 3), write each section separately if large
- If using shell commands with content, be aware of OS limits (~8000 chars on Windows)

---

## Discovery-First (with AI Context Cache)

Before designing new components, discover existing codebase patterns:

```text
# FIRST: Check what's cached from earlier stages
get_understanding_stats(limit=50)

# Recall cached understanding of relevant modules
recall_understanding(target="<relevant_module_path>")
# IF found AND fresh: Use cached patterns/conventions
# IF not found OR stale: Proceed with discovery below
```

- Use civyk-repoix MCP/CLI to discover existing infrastructure, frameworks, patterns
- Use `get_duplicate_code(source_only=true)` to find similar implementations to consolidate or extend
- Design on top of existing architecture rather than introducing parallel approaches
- Consider edge cases in architectural decisions

```text
# [!] MANDATORY: Store understanding for key patterns discovered
store_understanding(
  scope="module",
  target="<module_path>",
  purpose="<module purpose>",
  importance="medium",
  key_points=["<patterns_found>", "<conventions>"],
  gotchas=["<edge_cases>", "<constraints>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Prerequisites

Verify before proceeding:

- [ ] `{{feature_dir}}/plan.md` exists with template
- [ ] `{{feature_dir}}/research.md` is complete
- [ ] Summary, Technical Context, Constitution Check are filled

---

## Step 1: Fill Plan Sections (Chunk 2 of 3)

Edit `{{feature_dir}}/plan.md` to fill these sections:

### 1.1 Project Structure

- Choose appropriate structure (single/web/mobile)
- Remove unused options
- Fill actual directory paths

### 1.2 High-Level Architecture

- Create component interaction diagram (Mermaid)
- Define architecture pattern and justification
- Fill component responsibilities table

### 1.3 Cross-Cutting Concerns

Fill applicable subsections (delete if not needed):

- Error Handling
- Security
- Observability
- Caching Strategy
- Resilience Patterns
- API Design
- Configuration

**IMPORTANT**: Replace ALL `[...]` placeholders with actual content.

---

## Step 2: Fill Plan Sections (Chunk 3 of 3)

Continue editing `{{feature_dir}}/plan.md`:

### 2.1 Data Architecture

- Data Model (entities, relationships)
- Database Schema (with DDL)
- Data Flow Diagram
- Data Validation rules

### 2.2 Integration Architecture

- External Dependencies table (with Artifactory validation - see below)
- Integration Patterns
- Failure Handling table
- API Contracts

**Validate External Dependencies:**

{{include:artifactory-validation.md}}

Ensure External Dependencies table includes Artifactory status:

```markdown
| Dependency | Version | Purpose | Artifactory Status |
|------------|---------|---------|-------------------|
| package-a  | ^1.2.0  | Auth    | [VERIFIED]        |
| package-b  | ^3.0.0  | ORM     | [NOT FOUND - blocked] |
```

**For blocked dependencies:** Add to Risk Assessment (2.4) as blockers.

### 2.3 Migration/Rollout Plan (if applicable)

- Backward Compatibility
- User Communication

### 2.4 Risk Assessment (if applicable)

- Risks table
- Assumptions table
- Dependencies & Blockers
- Open Questions

**IMPORTANT**: Replace ALL remaining `[...]` placeholders. Delete sections marked "CONDITIONAL" if not applicable.

---

## Step 3: Generate Supporting Artifacts

### 3.1 Create data-model.md

Use the **Write tool** to create `{{feature_dir}}/data-model.md`:

```markdown
# Data Model: <feature name>

## Entity: [Name]

**Fields:**

- field1: type (constraints)
- field2: type (constraints)

**Relationships:**

- has_many: [Entity]
- belongs_to: [Entity]

**Validation:**

- [rule from requirements]
```

### 3.2 Create contracts/ Directory

Create API contract files in `{{feature_dir}}/contracts/`:

- OpenAPI spec (for REST)
- GraphQL schema (if applicable)

### 3.3 Create quickstart.md

Use the **Write tool** to create `{{feature_dir}}/quickstart.md`:

- Local development setup
- Environment variables
- Database setup
- Running tests
- API examples

---

## Step 4: Final Validation

Verify plan.md is complete:

```bash
# Check for remaining placeholders
grep -E '\[.*\]|NEEDS CLARIFICATION|ACTION REQUIRED' {{feature_dir}}/plan.md
```

**All placeholders must be replaced or sections deleted.**

---

## Output

```text
[ok] Planning complete

Artifacts generated:
  - {{feature_dir}}/plan.md (all sections filled)
  - {{feature_dir}}/research.md
  - {{feature_dir}}/data-model.md
  - {{feature_dir}}/contracts/
  - {{feature_dir}}/quickstart.md
```

**Note:** Next steps are generated by CLI (`emit_complete`) - do not duplicate here.

---

## WORKFLOW COMPLETE

Planning is done. Proceed to task generation.
