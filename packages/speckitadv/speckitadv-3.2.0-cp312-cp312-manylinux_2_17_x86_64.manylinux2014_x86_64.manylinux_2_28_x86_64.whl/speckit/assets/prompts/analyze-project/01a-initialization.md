---
stage: initialization
requires: nothing
outputs: agents_verified
version: 3.4.0
---

# Stage 1A: Initialization

## CRITICAL: Read AGENTS.md First

**Before doing anything else:** If `./AGENTS.md` exists in the repository root, read and honor all instructions in that file. AGENTS.md contains project-specific guidelines that take precedence over default behavior.

---

## Purpose

Initialize the analysis chain by verifying AGENTS.md guidelines and toolkit availability.

---

## How Context Is Provided

The CLI manages all state automatically. **You don't need to read or write state.json.**

**How it works:**

1. CLI loads state from `{analysis_dir}/state.json`
2. CLI renders this prompt with actual values already substituted
3. You receive the prompt with real paths and values - no template syntax
4. CLI auto-detects the current stage and persists progress

**To continue:** Run `speckitadv analyze-project` - no arguments needed.

---

## Step 1: Verify Agent Instructions

Check if `AGENTS.md` exists in repository root: `./AGENTS.md`

---

**[STOP: AGENTS_CHECK]**

Search for AGENTS.md in the repository root.

**IF AGENTS.md EXISTS:**

1. Read the ENTIRE file
2. Note the version number (line 3-4)
3. Internalize all guidelines
4. Output confirmation:

   ```text
   [ok] Read AGENTS.md v[X.X] - Following all guidelines
   ```

**IF AGENTS.md DOES NOT EXIST:**

1. Output: `[ok] No AGENTS.md found - Proceeding with default behavior`

---

## Step 2: Verify Toolkit Availability

Check that the speckitadv CLI is available:

```bash
speckitadv --version
```

---

**[STOP: TOOLKIT_CHECK]**

**IF CLI works:** Output: `[ok] Toolkit verified (vX.X.X)`
**IF CLI missing:** Output: `[x] Error: speckitadv CLI not found` -> STOP workflow

---

## Step 3: Load Corporate Guidelines

Check `.guidelines/` directory in project root for tech-stack guidelines.

**Detection:**

1. Detect tech stack from project markers (`package.json`, `requirements.txt`, `pom.xml`, etc.)
2. Detect profile from `memory/config.json` -> `.guidelines-profile` -> default `personal`

**Load (if exists):**

1. Base: `.guidelines/base/{stack}-base.md`
2. Override: `.guidelines/profiles/{profile}/{stack}-overrides.md`

**Output:**

- `[ok] Guidelines loaded: {stack} ({profile} profile)`
- OR `[ok] No guidelines found - using defaults`

---

## Output

```text
===========================================================
  SUBSTAGE COMPLETE: 01a-initialization
  AGENTS.md: {verified v[X.X] | not found}
  Toolkit: verified
  Guidelines: {loaded | not found}
  Analysis folder: {analysis_dir}
  Next: Run speckitadv analyze-project
===========================================================
```

---

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits the next prompt. **Do NOT analyze or generate artifacts until you run this command.**
