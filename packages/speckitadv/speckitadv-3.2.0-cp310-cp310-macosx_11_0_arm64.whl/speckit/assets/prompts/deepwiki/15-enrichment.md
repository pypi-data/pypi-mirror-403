---
stage: enrichment
requires: examples
outputs: "{wiki_dir}/*.md (updated)"
version: 2.3.0
---

# Stage 15: Documentation Enrichment & Verification

Revisit ALL wiki docs with full context. Verify accuracy against source code, eliminate hallucinated content, and enrich with substantive improvements.

## Prerequisites

- Stage 14 completed with examples.md generated
- Mode: `{REPOIX_MODE}` (if "cli", convert MCP calls per AGENTS.md)
- Discovery cache loaded: LIMITS, PRIMARY_LANGUAGE

## Critical Rules

| Rule | Action |
|------|--------|
| Examples required | **MUST** verify {wiki_dir}/examples.md exists |
| Update only | **NEVER** create new wiki files - ONLY update existing |
| No new README | **NEVER** create README.md or any new document |
| No new files | **NEVER** create glossary.md, maintenance.md, or ANY new files |
| Protect custom | **NEVER** modify {wiki_dir}/custom/ directory |
| Preserve content | **NEVER** remove existing content unless incorrect |
| Edit tool only | **MUST** use Edit tool (NOT Write tool) |
| **Verify before keeping** | **MUST** read source code to verify each claim |

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

# IF found AND fresh: Use cached analysis for verification
# IF not found: Proceed with verification, then MUST store findings
```

---

## Why This Stage Matters

**Problem:** Earlier stages may contain hallucinated content because:

1. AI generated docs from limited context (README, package files only)
2. Assumptions made without verifying actual source code
3. Generic patterns described that may not exist in this codebase

**Solution:** With full project context, verify EVERY claim against actual code:

- Class names, method signatures, file paths
- Architectural patterns described
- Error handling behavior
- Integration patterns
- Configuration options

| Stage | Context Available | Potential Issues |
|-------|-------------------|------------------|
| 02-03 | README only | May describe patterns not in code |
| 04-06 | Components | May miss actual implementation details |
| 07-09 | API, models | May have incorrect signatures |
| 10-14 | Full context | Can now verify everything |

---

## Step 1: Verify Previous Stage

```bash
speckitadv deepwiki-update-state verify-stage --stage=15-enrichment --wiki-dir={wiki_dir}
```

---

## Step 2: Initialize Progress Tracking

**Track enrichment, verification, AND See Also for each document:**

```text
ENRICHMENT_TRACKER = {
  "overview.md":           { verified: false, enriched: false, see_also: false, fixes: 0 },
  "diagrams.md":           { verified: false, enriched: false, see_also: false, fixes: 0 },
  "flows/README.md":       { verified: false, enriched: false, see_also: false, fixes: 0 },
  "components/README.md":  { verified: false, enriched: false, see_also: false, fixes: 0 },
  "api.md":                { verified: false, enriched: false, see_also: false, fixes: 0 },
  "models.md":             { verified: false, enriched: false, see_also: false, fixes: 0 },
  "configuration/README.md": { verified: false, enriched: false, see_also: false, fixes: 0 },
  "dependencies.md":       { verified: false, enriched: false, see_also: false, fixes: 0 },
  "decisions.md":          { verified: false, enriched: false, see_also: false, fixes: 0 },
  "errors.md":             { verified: false, enriched: false, see_also: false, fixes: 0 },
  "examples.md":           { verified: false, enriched: false, see_also: false, fixes: 0 }
}

# Update after each document:
[x] overview.md        - VERIFIED, enriched, See Also [OK], 3 fixes   (1/11)
[>] diagrams.md        - verifying against code...                  (2/11)
[ ] flows/README.md    - pending                                    (3/11)
```

---

## Step 3: Load Discovery Cache

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir}
# Extract: LIMITS = discovery_cache.project_size.limits
# Extract: PRIMARY_LANGUAGE = discovery_cache.file_patterns.languages.primary
```

---

## Step 4: Recall Cached Understanding (AI Context Cache)

**CRITICAL:** Before verifying documents against source code, check cached understanding from earlier stages (04-14):

```text
# Recall project-level understanding (from Stage 04)
recall_understanding(target="project")

# Recall component understanding (from Stage 07)
recall_understanding(target="<component_path>")

# For each source file you need to verify against:
recall_understanding(target="<file_path>")

# Decision logic:
# IF error (MCP connection failed):
#   -> Fallback to manual file read
#   -> Log warning, continue with full verification
# IF found=true AND fresh=true (source_hash matches current file):
#   -> Use cached understanding for verification
#   -> Compare wiki claims against cached key_points, gotchas
#   -> Skip source file read (saves 80-90% tokens)
# IF found=false OR fresh=false:
#   -> Read source file
#   -> After verification, store_understanding for future use
```

**Benefits:** Stages 04-14 already analyzed most files. Enrichment can recall instead of re-reading, dramatically reducing token usage.

---

## Step 5: Load Full Context for Verification

```text
# Business context - check cache first
recall_understanding(target="{wiki_dir}/business-context.json")
# IF not cached: Read file: {wiki_dir}/business-context.json
# [!] NOW CALL store_understanding for the file above

# [!] MANDATORY: Store business context if freshly read
store_understanding(
  scope="file",
  target="{wiki_dir}/business-context.json",
  purpose="Business context and domain knowledge for verification",
  importance="critical",
  key_points=["<project_name>", "<key_features>", "<main_entities>"],
  gotchas=["<constraints>", "<glossary_terms>"],
  analysis="<business_domain>: <what_it_does>. <key_workflows>. <verification_focus_areas>."
)

# Project structure - needed to verify claims (check cache first)
recall_understanding(target="project")
# IF not cached: run discovery below
get_components()
get_dependencies()
get_api_endpoints(limit=200)
build_context_pack(task="documentation verification and enrichment", token_budget=3000)

# [!] MANDATORY: Store MCP discovery summary if newly gathered
store_understanding(
  scope="module",
  target="discovery/enrichment",
  purpose="Discovery results for documentation verification",
  importance="high",
  key_points=["<component_count> components", "<endpoint_count> endpoints", "<symbol_patterns>"],
  gotchas=["<verification_targets>", "<potential_hallucinations>"],
  analysis="<components>: <list>. <endpoints>: <count>. <patterns_to_verify>: <suffixes>, <prefixes>."
)

# Get actual symbol names for verification
search_symbols(query="%Service%", kind="class", limit=50)
search_symbols(query="%Controller%", kind="class", limit=50)
search_symbols(query="%Repository%", kind="class", limit=50)
```

---

## Step 6: Verify & Enrich Each Document

**CRITICAL: For EACH wiki document, follow this process:**

### 6.1 Read Document & Extract Claims

```text
Read file: {wiki_dir}/[document].md

# Extract all verifiable claims:
- Class/interface names mentioned
- File paths referenced
- Method signatures described
- Architectural patterns claimed
- Configuration options listed
- Error types mentioned
```

### 6.2 Verify Against Source Code (Use Cached Understanding)

**For EACH claim, check cache FIRST, then verify:**

```text
# Example verification workflow for overview.md:

# Claim: "AuthService handles authentication"
# FIRST: Check cached understanding
recall_understanding(target="src/services/auth.py")
# IF found AND fresh: Verify claim against cached key_points
# IF not found: search and read as below

search_symbols(query="AuthService", kind="class")
# If found: get_symbol(fqn="...AuthService") - verify behavior
# If NOT found: This is hallucinated - MUST correct

# After verification, store understanding if not cached:
store_understanding(
  scope="file",
  target="src/services/auth.py",
  purpose="Authentication service handling login/logout",
  importance="critical",
  key_points=["JWT tokens", "OAuth support"],
  gotchas=["Token expiry handling"],
  analysis="<detailed_logic_and_flow_explanation>",
  related_to=["UserRepository", "TokenService"]
)

# Claim: "Uses Repository pattern"
search_symbols(query="%Repository%", kind="class")
# Verify actual pattern used, correct if different

# Claim: "Configuration in config/settings.py"
list_files(pattern="**/config/**")
list_files(pattern="**/settings*")
# Verify actual config location
```

### 6.3 Fix Hallucinated Content

| Issue Found | Action |
|-------------|--------|
| Class doesn't exist | Replace with actual class or remove |
| Wrong file path | Correct to actual path |
| Wrong method signature | Read source, fix signature |
| Pattern not used | Describe actual pattern |
| Feature doesn't exist | Remove or mark as "not implemented" |

### 6.4 Enrich with Verified Content

After verification, ADD substantive improvements:

**Add missing implementation details:**

```text
# Read actual implementation
get_file_symbols(path="src/services/auth.py")
Read file: src/services/auth.py (lines with key logic)

# Add to docs:
- Actual method signatures with parameters
- Real error handling behavior
- Actual configuration options used
- True integration patterns
```

### 6.5 Update Cross-References

**IMPORTANT:** Add/update cross-references to connect related documentation:

**Types of cross-references to add:**

| From Document | Link To |
|---------------|---------|
| overview.md | Component docs, flow docs, architecture |
| flows/*.md | Component docs, API endpoints, error handling |
| components/*.md | Related flows, models used, config needed |
| api.md | Flow docs that use endpoints, error types |
| models.md | Components that use models, API responses |
| errors.md | Flows where errors occur, handling code |

**Add "See Also" sections to every document:**

```markdown
## See Also

- **Flows**: [Authentication](flows/authentication.md)
- **Components**: [AuthService](components/auth-service.md)
- **API**: [POST /auth/login](api.md#post-authlogin)
- **Errors**: [AuthError](errors.md#autherror)
```

**Add inline links throughout content:**

```markdown
The [AuthService](components/auth-service.md) validates credentials
and returns a [JWT token](flows/authentication.md#token-generation).
Errors are handled by [AuthError](errors.md#autherror).
```

---

## Step 7: Document-Specific Verification Checklist

| Document | Key Verifications |
|----------|-------------------|
| overview.md | Architecture claims, tech stack, main components exist |
| diagrams.md | Component names match code, relationships accurate |
| flows/*.md | Function calls exist, sequence accurate, error paths real |
| components/*.md | Classes exist, methods match signatures, dependencies correct |
| api.md | Routes exist, parameters match, response types accurate |
| models.md | Classes exist, fields match, relationships accurate |
| configuration/*.md | Files exist, options are real, defaults correct |
| dependencies.md | Packages used, versions match, integration accurate |
| errors.md | Error classes exist, handling matches code |
| examples.md | Code snippets work, imports valid |

---

## Step 8: Consistency Check

Ensure across all documents:

- Entity names match actual code exactly
- API paths match actual routes (verify with grep/search)
- Component names are spelled correctly
- Internal links resolve to existing files
- No orphaned references to non-existent code

---

## Step 9: Complete Stage

```bash
speckitadv deepwiki-update-state stage --stage=15-enrichment --status=completed --artifacts="{wiki_dir}/overview.md,{wiki_dir}/architecture/diagrams.md,{wiki_dir}/flows/README.md,{wiki_dir}/components/README.md,{wiki_dir}/api.md,{wiki_dir}/models.md" --wiki-dir={wiki_dir}
```

---

## Output Format

```text
===========================================================
  STAGE COMPLETE: 15-enrichment

  Documents verified: {count}
  Documents enriched: {count}
  Hallucinations fixed: {count}
  Cross-references added: {count}
  See Also sections added: {count}
  Content improvements: {count}

  AI Cache Efficiency:
    - Files read: <count_read>
    - Files cached (store_understanding): <count_stored>
    - Cache hits (found=true, fresh=true): <count_hits>

  Verification Summary:
  - overview.md: VERIFIED [OK], See Also [OK] (2 fixes)
  - diagrams.md: VERIFIED [OK], See Also [OK] (1 fix)
  - api.md: VERIFIED [OK], See Also [OK] (3 fixes - wrong signatures corrected)
  ...

  Next: Run {next_command}
===========================================================
```

---

## Anti-Hallucination Checklist

Before marking complete, confirm:

- [ ] Every class name mentioned exists in codebase
- [ ] Every file path referenced is valid
- [ ] Every method signature matches actual code
- [ ] Every architectural pattern claimed is actually used
- [ ] Every configuration option described is real
- [ ] Every error type listed exists
- [ ] No generic/assumed content remains unverified
- [ ] Every document has a "See Also" section with valid links

---

## Edge Cases

| Scenario | Action |
|----------|--------|
| Claim can't be verified | Read more source code until verified |
| Class name was hallucinated | Replace with actual class or remove section |
| Pattern doesn't exist | Describe what actually exists |
| Large doc set (>30 files) | Prioritize core documents, verify all |
| Conflicting information | Source code is truth - fix docs |

---

## Next Stage

Run `{next_command}` - CLI auto-detects current stage and emits next prompt.
