---
stage: complete
requires: generate
outputs: summary_displayed
version: 1.1.0
status: EXPERIMENTAL
---

{{include:verification-rules.md}}

# Stage 4: Complete

## Purpose

Display summary, handle errors, and provide next steps.

---

## Step 1: Display Summary

```text
[ok] GUIDELINE GENERATION COMPLETE

Generated: .guidelines/{{stack}}-guidelines.md
Version: {{version}} (updated from {{previous_version}})
Update Mode: {{update_mode}}
Backup: {{backup_file}}

Sources Analyzed:
- Documents: {{doc_count}} files
- Reference Projects: {{project_count}} projects
- Total Files Scanned: {{file_count}} files

Principles Extracted:
- From Documents: {{doc_principles}} explicit principles
- From Code: {{code_high}} HIGH confidence, {{code_medium}} MEDIUM confidence
- Total Synthesized: {{total}} principles ({{must}} MUST, {{should}} SHOULD, {{never}} NEVER, {{may}} MAY)

Conflicts Resolved: {{conflict_count}}

Sections Updated:
1. Scaffolding [ok]
2. Package Registry [ok]
3. Mandatory Libraries [ok]
4. Banned Libraries [ok]
5. Architecture [ok]
6. Security [ok]
7. Coding Standards [ok]
8. Dependency Management [ok]
9. Testing [ok]
10. Build & Deployment [ok]
11. Observability [ok]

Analysis Report: .guidelines-analysis/{{stack}}-analysis-report.md
```

---

## Step 2: Provide Next Steps

```text
Next Steps:
1. Review generated guideline: .guidelines/{{stack}}-guidelines.md
2. Review detailed analysis: .guidelines-analysis/{{stack}}-analysis-report.md
3. Commit updated guidelines to version control
4. Share with development teams
5. Update any project-specific constitution if needed
```

---

## Error Recovery

**If SOURCES_PATH doesn't exist:**

- ERROR: "Sources path not found: [PATH]. Please verify the path and try again."

**If SOURCES_PATH has no docs/ or reference-projects/ subdirectories:**

- WARN: "Expected subdirectories not found. Looking for files in root..."
- Attempt to categorize files by extension

**If no documents found:**

- ERROR: "No corporate documents found. At least one document is required."
- Suggest: "Place standards documents (PDF, Markdown) in docs/ subdirectory"

**If no reference projects found:**

- ERROR: "No reference projects found. At least one reference project is required."
- Suggest: "Place reference codebases in reference-projects/ subdirectory"

**If tech stack cannot be detected:**

- WARN: "Could not auto-detect tech stack."
- ASK: "Please specify tech stack manually (java, python, reactjs, dotnet, nodejs): ___"

**If document parsing fails:**

- WARN: "Could not read [document-name]. Skipping this document."
- CONTINUE: Proceed with other documents

**If UPDATE_MODE = REPLACE but sections not found:**

- ERROR: "Selected sections not found in existing guideline file."
- SUGGEST: "Use FULL_REGEN mode or select valid section numbers"

**If consensus is too low (all patterns are 1/3):**

- WARN: "Reference projects show no consensus patterns."
- ASK: "Do you want to continue anyway? [Y/N]"

---

## Notes

- RFC 2119 keywords: MUST, SHOULD, MAY, MUST NOT, SHOULD NOT, NEVER
- Version management follows semantic versioning (MAJOR.MINOR.PATCH)
- Multi-stack support: Generate separate guideline files for each detected stack

---

## Workflow Complete

Guideline generation workflow is complete. No further stages.
