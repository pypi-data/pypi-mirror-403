---
stage: generate-spec
requires: branch-setup
outputs: spec_file
version: 1.3.0
next: 05-validate-spec.md
---

{{include:ai-cache-enforcement.md}}

# Stage 4: Generate Specification

## Purpose

Create spec.md using a chunked approach to handle large specifications.

---

## File Write Best Practices

**For large specifications:**

- Use chunked writing (Steps 3-6 below are already chunked)
- Keep each edit operation under 2000 characters
- If using shell commands with content, be aware of OS limits (~8000 chars on Windows)

---

## Step 1: Create Spec Template

The CLI automatically copies the spec template to the feature directory:

{{copy-template:spec-template.md:spec.md}}

Now edit `{{feature_dir}}/spec.md` with these initial replacements:

- Replace `[Feature Name]` with feature name
- Replace `[DATE]` with today's date
- Keep all other `[...]` placeholders for now

---

## Tools (if REPOIX_MODE != "none")

{{include:spec-civyk-repoix-discovery.md}}

---

## Step 2: Parse Feature Description

Extract from the feature description:

- **Actors**: Who uses this feature?
- **Actions**: What can they do?
- **Data**: What information is involved?
- **Constraints**: What limitations exist?

---

## Step 3: Fill Sections (Chunk 1 - Header & Overview)

Edit `{{feature_dir}}/spec.md` to fill:

- **Title and metadata** section
- **Overview** section (brief description)
- **Scope** section (In Scope / Out of Scope)

---

## Step 4: Fill Sections (Chunk 2 - User Stories)

Edit `{{feature_dir}}/spec.md` to fill:

- **User Stories** section with format:
  - Priority (P1/P2/P3)
  - "As a [user], I want [goal] so that [benefit]"
  - Acceptance scenarios in Given/When/Then format

**Guidelines:**

- P1 = Must have (MVP)
- P2 = Should have
- P3 = Nice to have
- Each scenario must be testable

---

## Step 5: Fill Sections (Chunk 3 - Requirements)

Edit `{{feature_dir}}/spec.md` to fill:

- **Functional Requirements** (FR-001, FR-002, etc.)
- **Non-Functional Requirements** (if applicable)
- **Assumptions** section

**Guidelines:**

- Each requirement independently testable
- Use reasonable defaults for unspecified details
- Document assumptions

---

## Step 6: Fill Sections (Chunk 4 - Technical Context)

Edit `{{feature_dir}}/spec.md` to fill:

- **Technical Context** section
- **Success Criteria** section

**Success Criteria Guidelines:**

- Measurable outcomes (time, percentage, count)
- Technology-agnostic (no frameworks, APIs)
- User-focused (business perspective)

**Good examples:**

- "Users can complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"

**Bad examples (too technical):**

- "API response time is under 200ms"
- "Redis cache hit rate above 80%"

---

## Step 7: Handle Ambiguities

Review the spec for unclear items:

**Only mark with [NEEDS CLARIFICATION] if:**

- Choice significantly impacts scope or UX
- Multiple reasonable interpretations exist
- No reasonable default applies

**LIMIT: Maximum 3 clarification markers.**

Prioritize: scope > security > user experience > technical

**Make informed guesses for:**

- Data retention (industry standard)
- Performance (standard web expectations)
- Error handling (user-friendly messages)
- Authentication (standard OAuth2/sessions)

---

## Step 8: Final Validation

Verify spec.md is complete:

```bash
# Check for remaining placeholders
grep -E '\[.*\]' {{feature_dir}}/spec.md | grep -v 'NEEDS CLARIFICATION'
```

**All placeholders must be replaced** (except [NEEDS CLARIFICATION] markers).

---

## Output

After completing all chunks:

```text
[ok] Specification generated
  - File: {{feature_dir}}/spec.md
  - User stories: [N]
  - Requirements: [N]
  - Clarifications needed: [0-3]
```

Then run the next command shown below.
