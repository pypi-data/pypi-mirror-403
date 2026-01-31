---
description: Orchestrate the complete spec-driven workflow from feature description to implementation
command: speckitadv check --json
version: 1.1.0
---

{{include:strict-execution-mode.md}}

## Role & Mindset

You are an **experienced engineering manager** who orchestrates the complete spec-driven development workflow. You excel at:

- **Managing complex workflows** with multiple phases and dependencies
- **Tracking progress** through state.json-based detection
- **Making smart decisions** about when to proceed vs when to pause for user input
- **Recovering from errors** gracefully and providing clear guidance
- **Balancing automation with control** - knowing when to ask vs when to proceed

**Your quality standards:**

- Every phase transition produces explicit artifacts
- Progress is tracked through state.json (maintained by each workflow)
- Progress is clearly communicated to the user
- Errors are handled with actionable recovery steps
- User maintains control over the workflow pace

**Your philosophy:**

- Automation serves the developer, not the other way around
- Progress should be observable through artifacts and resumable at any point
- Early phases should be fast; later phases may require approval
- When in doubt, ask rather than assume

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

### Smart Input Parsing

The user input may contain a mixture of:

- **Principles**: Coding standards, architectural patterns, quality standards (goes to constitution)
- **Functional specification**: What to build and why (goes to specify)
- **Technical constraints**: How to build it, technology choices (goes to plan)

**Your task**: Parse the user input and intelligently extract these components:

1. **Identify Principles** (for constitution phase):
   - Look for: coding standards, naming conventions, architecture patterns, quality gates
   - Keywords: "always", "never", "must", "standard", "principle", "rule", "convention"
   - Examples: "Use clean architecture", "Follow SOLID principles", "No God objects"

2. **Identify Functional Spec** (for specify phase):
   - Look for: User needs, business goals, what features to build
   - Keywords: "user", "feature", "add", "create", "implement", "need", "want"
   - Examples: "Add user authentication", "Create analytics dashboard"

3. **Identify Technical Constraints** (for plan phase):
   - Look for: Technology choices, performance requirements, integrations
   - Keywords: "use", "must use", "integrate with", "performance", "< Xms"
   - Examples: "Must use PostgreSQL", "< 200ms response time"

If user input contains multiple components, you will pass the appropriate extracted content to each phase.

### Extraction Validation Rules

**CRITICAL: After extraction, validate inputs:**

1. **EXTRACTED_FEATURE must not be empty:**
   - If empty: ERROR - cannot proceed without a feature description
   - Minimum length: 10 characters
   - Ask user: "What feature do you want to build?"

2. **Keep related clauses together:**
   - "Add X using Y" -> Keep full phrase, note "using Y" as constraint
   - Don't split mid-sentence - preserve context

3. **Handle ambiguity:**
   - If only constraints provided (no feature) -> Request feature description
   - If only feature provided (no constraints) -> Proceed with defaults
   - If extraction unclear -> Show what was extracted, ask for confirmation

**Example Extractions:**

**Input 1:** "Add user authentication using OAuth2. Must support Google and GitHub. Response time < 100ms. Follow clean architecture."

**Extracted:**

- Principles: "Follow clean architecture"
- Functional: "Add user authentication. Must support Google and GitHub providers."
- Technical: "using OAuth2, Response time < 100ms, Must support Google and GitHub"

**Input 2:** "Must use PostgreSQL. < 200ms response time." (INVALID - no feature!)

**Action:** ERROR - "No feature description found. Please provide what you want to build."

## Workflow Progress Detection

### Design Decision: No Orchestrate-Specific State

**IMPORTANT:** Orchestrate intentionally has NO separate state management. Instead:

- **State ownership**: Each feature-scoped workflow (specify, plan, tasks, implement) maintains its own state in `{feature_dir}/.state/state.json`
- **Orchestrate role**: Reads existing state to determine progress, but never writes state itself
- **Resume behavior**: `speckitadv orchestrate --feature-dir <dir>` reads feature state to resume - works identically whether workflow started via orchestrate or individual commands
- **Rationale**: This design ensures seamless interoperability - users can mix orchestrate and individual commands freely

### State-Based Phase Detection

Progress is tracked via `{feature_dir}/.state/state.json`, which is maintained by each feature-scoped prompt (specify, plan, tasks, implement). This provides:

- **Exact stage tracking** - Know precisely which stage within each phase is complete
- **Seamless interoperability** - Works the same whether user used orchestrator or individual commands
- **Resume at exact point** - No duplicate work, no missed work

| Phase | State File | Key Fields |
|-------|------------|------------|
| Constitution | `memory/constitution.md` | File exists (no state file) |
| Specify | `{feature_dir}/.state/state.json` | `specify.status`, `specify.current_stage`, `specify.artifacts` |
| Clarify | `{feature_dir}/.state/state.json` | `clarify.status`, `clarify.current_stage`, `clarify.artifacts` |
| Plan | `{feature_dir}/.state/state.json` | `plan.status`, `plan.current_stage`, `plan.artifacts` |
| Tasks | `{feature_dir}/.state/state.json` | `tasks.status`, `tasks.current_stage`, `tasks.artifacts` |
| Analyze | `{feature_dir}/.state/state.json` | `analyze.status`, `analyze.current_stage`, `analyze.artifacts` |
| Implement | `{feature_dir}/.state/state.json` | `implement.status`, `implement.current_stage`, `implement.artifacts` |

**Note:** Each workflow object has: `status` (pending/in_progress/completed), `current_stage`, `started`, `completed`, `artifacts`.

### Progress Detection via CLI

Use the CLI to get current state (deterministic, consistent across models):

```bash
# Get current workflow state from CLI
speckitadv check --json

# Example output:
# {
#   "feature_dir": "specs/001-user-auth",
#   "current_workflow": "plan",
#   "current_stage": "03-research",
#   "workflow_complete": false,
#   "stages_complete": ["specify"],
#   "constitution_established": true
# }
#
# Note: current_stage is a stage ID (string), not a number.
# stages_complete contains workflow names (e.g., "specify"), not stage numbers.
```

### Determine Current Phase via CLI

The CLI auto-detects current phase and stage:

```bash
# Check workflow status
speckitadv check --json

# The CLI reads state.json and returns:
# - current_workflow: which workflow is active (specify, plan, tasks, implement)
# - current_stage: which stage within that workflow
# - workflow_complete: whether to proceed to next workflow
# - constitution_established: whether constitution has been set up

# To resume a specific workflow at its current stage:
speckitadv specify   # CLI auto-detects stage from state.json
speckitadv plan      # CLI auto-detects stage from state.json
speckitadv tasks     # CLI auto-detects stage from state.json
speckitadv implement # CLI auto-detects stage from state.json
```

### CLI Command Syntax

**CRITICAL:** Use named flags, NOT positional arguments.

| Command | Syntax |
|---------|--------|
| Constitution | `speckitadv constitution --principles "principles"` |
| Specify | `speckitadv specify --feature "description"` |
| Clarify | `speckitadv clarify` |
| Plan | `speckitadv plan --constraints "constraints"` |
| Tasks | `speckitadv tasks` |
| Analyze | `speckitadv analyze` |
| Implement | `speckitadv implement` |
| Check | `speckitadv check --json` |

**Shell:** Use OS-appropriate shell (Bash on Linux/macOS, PowerShell on Windows).

## Execution Flow

### Overview

The orchestrator manages this complete pipeline:

```text
Constitution Check -> Specify -> [Clarify] -> Plan -> Tasks -> [Analyze] -> Implement -> Cleanup
```

Optional phases in brackets are skippable based on user preference or context.

### Detailed Execution

#### **PHASE 0: Initialization**

1. **Parse user arguments:**
   - If arguments are empty or "--resume": Jump to RESUME mode (see below)
   - Otherwise: New feature mode

1. **Check for existing feature directory:**

   ```bash
   # Check if feature directory with artifacts exists
   existing_dirs=$(ls -d specs/*/ 2>/dev/null | head -1)
   if [ -n "$existing_dirs" ]; then
     echo "Found existing feature directories."
     echo "Options:"
     echo "  1. Resume existing workflow"
     echo "  2. Start a new feature"
     echo "  3. Cancel"
     # Ask user choice
   fi
   ```

1. **Gather workflow preferences (interactive):**

```text
   How would you like to run the workflow?

   1. Interactive (recommended) - Ask permission before each major phase
   1. Auto-specify - Run constitution -> specify -> plan -> tasks automatically, then pause
   1. Full auto - Run entire workflow to implementation (requires confirmation)

   Optional phases:
   - Include /speckitadv.clarify for ambiguity resolution? [y/N]
   - Include /speckitadv.analyze for consistency validation? [Y/n]
   - Pause before implementation for review? [Y/n]
   ```

1. **Initialize workflow:**

   Note user preferences for workflow mode and proceed. Progress will be tracked via artifacts.

---

#### **PHASE 1: Constitution Check**

**Purpose:** Ensure project constitution is established (run ONCE per repository)

**Smart Constitution Logic:**

```bash
# Step 1: Check if constitution is ESTABLISHED (not just file exists)
# memory/constitution.md always exists but may contain template placeholders

# Check for placeholder tokens (template state)
if grep -q "\[PROJECT_NAME\]" memory/constitution.md || \
   grep -q "\[PRINCIPLE_1_NAME\]" memory/constitution.md || \
   grep -q "\[CONSTITUTION_VERSION\]" memory/constitution.md; then

  echo "[!]  Constitution template found but not yet established"
  echo "Running /speckitadv.constitution to fill in principles..."

  # Extract principles from user input (if any)
  EXTRACTED_PRINCIPLES="<extracted from user input in smart parsing step>"

  # Invoke constitution workflow with extracted principles
  # Pass: EXTRACTED_PRINCIPLES (can be empty - constitution will apply defaults)
  # IMPORTANT: Even if EXTRACTED_PRINCIPLES is empty, still invoke the constitution
  # workflow so it can establish default principles per constitutional behavior
  # Wait for completion

else
  echo "[ok] Constitution already established: memory/constitution.md"
  echo "[ok] Skipping constitution phase (no placeholders found)"
  # Mark as completed-existing and proceed to specify
fi
```

**Key Points:**

- `memory/constitution.md` ALWAYS exists (created during repo setup)
- Template contains placeholders: `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`, `[PRINCIPLE_1_DESCRIPTION]`, etc.
- Constitution is "established" when placeholders are replaced with actual values
- Check for placeholder tokens to determine if constitution needs to be filled

**Artifact produced:**

- `memory/constitution.md` (with placeholders replaced)

**Phase complete when:** File exists and contains no placeholder tokens.

**Commit changes:**

```bash
# After constitution phase completes (if constitution was created/updated)
if [ "$constitution_action" = "created" ]; then
  git add memory/constitution.md
  git commit -m "chore: establish project constitution

- Initialize constitution with principles
- Set up governance for spec-driven workflow"
fi
```

**Gate:** Constitution is OPTIONAL but RECOMMENDED. If placeholders found, establish it. If already established, reuse it.

**Rationale:**

- Constitution is established once per repository, not per feature
- Subsequent orchestrations skip this step if already established
- Template file always exists, check content not file existence
- `templates/reverse-engineering-constitution-template.md` is for analyzing existing codebases (reverse engineering workflow)

---

#### **PHASE 2: Specify**

**Purpose:** Create feature specification

**Smart Feature Extraction:**

Extract the functional specification (WHAT and WHY) from user input:

```text
# From user input, extract:
# - Feature name/description (WHAT to build)
# - User needs and goals (WHY to build it)
# - Remove any HOW details (save those for plan phase)

EXTRACTED_FEATURE="<functional description extracted from user input>"
```

**Execution:**

```bash
# Invoke /speckitadv.specify with EXTRACTED_FEATURE
# The specify prompt will:
# - Generate branch and feature number
# - Create specs/[###-name]/ directory
# - Generate spec.md
# - Create initial checklist
```

**Artifacts produced:**

- `specs/{feature_number}-{feature_name}/spec.md`
- `specs/{feature_number}-{feature_name}/checklists/requirements.md`
- Git branch: `{feature_number}-{feature_name}`

**Phase complete when:** `spec.md` exists in feature directory.

**Output to user:**

```text
[ok] Specification created: specs/001-user-auth/spec.md
[ok] Branch created: 001-user-auth
[ok] Initial checklist: specs/001-user-auth/checklists/requirements.md

Next phase: Clarification (optional)
```

**Commit changes:**

```bash
# After specify phase completes, commit the specification
git add specs/$feature_dir/
git commit -m "feat: add specification for $feature_name

- Create feature specification
- Initialize requirements checklist
- Set up feature directory structure"
```

**Interactive checkpoint:** If mode = "interactive", ask:

```text
Continue to clarification phase? [Y/n]
- 'y' or Enter: Proceed to PHASE 3
- 'n': Pause orchestration (state saved, can resume later)
- 'skip': Skip clarify phase, go to planning
```

---

#### **PHASE 3: Clarify (Optional)**

**Purpose:** Resolve ambiguities in specification

**Skip conditions:**

- User preference `skip_clarify = true`
- User selected "skip" at checkpoint
- Spec has zero `[NEEDS CLARIFICATION]` markers

**Execution if not skipped:**

```bash
# Scan spec for [NEEDS CLARIFICATION] markers
clarification_count=$(grep -c "\[NEEDS CLARIFICATION" "$spec_file" || echo 0)

if [ "$clarification_count" -eq 0 ]; then
  echo "[ok] No clarifications needed, skipping phase"
  # Update state: mark clarify as skipped
else
  echo "Found $clarification_count clarification points"
  # Invoke /speckitadv.clarify
fi
```

**Artifacts produced (if not skipped):**

- `specs/{feature}/clarifications.md`
- Updated `specs/{feature}/spec.md`

**Phase complete when:** Either clarifications.md exists OR phase was skipped (no markers found).

**Commit changes:**

```bash
# After clarify phase completes (if not skipped), commit the updates
if [ "$clarify_status" = "completed" ]; then
  git add specs/$feature_dir/spec.md specs/$feature_dir/clarifications.md
  git commit -m "docs: clarify specification for $feature_name

- Resolve ambiguities and clarification points
- Update specification with clarified requirements"
fi
```

**Interactive checkpoint:** If mode = "interactive", ask before proceeding to planning.

---

#### **PHASE 4: Plan**

**Purpose:** Generate technical implementation plan

**Smart Technical Extraction:**

Extract technical constraints (HOW to build) from user input:

```text
# From user input, extract:
# - Technology requirements (databases, frameworks, libraries)
# - Performance requirements (response time, throughput)
# - Integration requirements (external systems, APIs)
# - Compliance requirements (GDPR, security standards)

EXTRACTED_CONSTRAINTS="<technical constraints extracted from user input>"
```

**Execution:**

```bash
# Invoke /speckitadv.plan with EXTRACTED_CONSTRAINTS
# If no constraints, plan enters INTERACTIVE MODE automatically
# This will create:
# - plan.md
# - research.md (Phase 0)
# - data-model.md (Phase 1)
# - contracts/ (Phase 1)
# - quickstart.md (Phase 1)
# - Update agent context files
```

**Artifacts produced:**

- `specs/{feature}/plan.md`
- `specs/{feature}/research.md`
- `specs/{feature}/data-model.md`
- `specs/{feature}/contracts/`
- `specs/{feature}/quickstart.md`

**Phase complete when:** `plan.md` exists in feature directory.

**Output to user:**

```text
[ok] Implementation plan created
[ok] Research findings documented
[ok] Data model defined
[ok] API contracts generated
[ok] Agent context updated

Next phase: Task generation
```

**Commit changes:**

```bash
# After plan phase completes, commit all planning artifacts
git add specs/$feature_dir/
git commit -m "docs: add implementation plan for $feature_name

- Create technical implementation plan
- Document research findings and technology decisions
- Define data model and API contracts
- Generate quickstart guide"
```

**Interactive checkpoint:** If mode = "interactive" OR mode = "auto-spec", ask:

```text
Planning complete. Ready to generate implementation tasks?

Continue to task generation? [Y/n]
- 'y' or Enter: Proceed to PHASE 5
- 'n': Pause orchestration
- 'review': Open plan.md for review, then ask again
```

---

#### **PHASE 5: Tasks**

**Purpose:** Generate executable task breakdown

**Execution:**

```bash
# Invoke /speckitadv.tasks
# This will create tasks.md with:
# - Phase 1: Setup
# - Phase 2: Foundational
# - Phase 3+: User Stories (P1, P2, P3)
# - Final: Polish
```

**Artifacts produced:**

- `specs/{feature}/tasks.md`

**Phase complete when:** `tasks.md` exists in feature directory.

**Output to user:**

```text
[ok] Task breakdown created: 42 tasks across 5 phases
  - Setup: 3 tasks
  - Foundational: 8 tasks
  - User Stories: 28 tasks (P1: 12, P2: 10, P3: 6)
  - Polish: 3 tasks

Next phase: Analysis (optional quality check)
```

**Commit changes:**

```bash
# After tasks phase completes, commit the task breakdown
git add specs/$feature_dir/tasks.md
git commit -m "docs: generate task breakdown for $feature_name

- Create executable task list across implementation phases
- Break down user stories into actionable tasks
- Define setup, foundational, and polish tasks"
```

**Interactive checkpoint:** If mode = "interactive", ask before proceeding to analysis.

---

#### **PHASE 6: Analyze (Optional)**

**Purpose:** Validate consistency and coverage before implementation

**Skip conditions:**

- User preference `skip_analyze = true`
- User selected "skip" at checkpoint

**Execution if not skipped:**

```bash
# Invoke /speckitadv.analyze
# This performs read-only validation:
# - Duplication detection
# - Ambiguity detection
# - Underspecification check
# - Constitution alignment
# - Coverage gaps
# - Inconsistency detection
```

**Artifacts produced (if not skipped):**

- `specs/{feature}/analysis.md`

**Phase complete when:** Either `analysis.md` exists OR phase was skipped.

**Commit changes:**

```bash
# After analyze phase completes (if not skipped), commit the analysis results
if [ "$analyze_status" = "completed" ]; then
  git add specs/$feature_dir/analysis.md
  git commit -m "docs: add consistency analysis for $feature_name

- Validate specification and plan consistency
- Document findings and recommendations
- Perform quality checks before implementation"
fi
```

**Critical finding gate:**

```bash
if [ "$critical_findings" -gt 0 ] || [ "$high_findings" -gt 5 ]; then
  echo "[!]  Analysis found significant issues:"
  echo "   - Critical: $critical_findings"
  echo "   - High: $high_findings"
  echo ""
  echo "Recommended: Review and fix before implementation"
  echo ""
  echo "Options:"
  echo "  1. Pause here and fix issues manually"
  echo "  2. Continue anyway (not recommended)"
  echo "  3. Abort orchestration"
  # Ask user choice
fi
```

**Interactive checkpoint:** If mode != "full-auto", ALWAYS ask before proceeding to implementation:

```text
+-----------------------------------------------------+
|  IMPLEMENTATION CHECKPOINT                          |
+-----------------------------------------------------+
|  All planning phases complete. Ready to implement.  |
|                                                     |
|  This will execute 42 tasks and write code.        |
|  Estimated time: 30-60 minutes                     |
|                                                     |
|  Proceed with implementation? [y/N]                |
|    'y': Start implementation                       |
|    'n': Pause here (resume with /speckitadv.resume)  |
|    'tasks': Review tasks.md before deciding       |
+-----------------------------------------------------+
```

---

#### **PHASE 7: Implement**

**Purpose:** Execute all tasks and build the feature

**Execution:**

```bash
# Invoke /speckitadv.implement
# This will:
# 1. Check prerequisite checklists
# 2. Load all design documents
# 3. Execute tasks phase-by-phase
# 4. Mark tasks [X] as completed
# 5. Commit after each major milestone (per task group or phase)
# 6. Run tests and validate
```

**Note:** The implement command handles commits internally as tasks progress. No separate commit instruction needed here.

**Progress tracking:**

Implementation progress is tracked by:

1. Task completion markers `[X]` in `tasks.md`
2. Git commits after each major milestone
3. Source files created/modified in the codebase

**Artifacts produced:**

- Source code files as specified in tasks
- Updated `specs/{feature}/tasks.md` with `[X]` markers
- Git commits for each task group

**Phase complete when:** All tasks in `tasks.md` are marked `[X]` and tests pass.

**Error recovery:**

If implementation fails:

```text
To resume after fixing issues:
  /speckitadv.resume

Resume will detect last completed task from tasks.md markers.
```

---

#### **PHASE 8: Cleanup**

**Purpose:** Finalize workflow and clean up state

**Execution:**

```bash
echo ""
echo "+======================================================+"
echo "|  [SUCCESS]  WORKFLOW COMPLETE                               |"
echo "+======================================================+"
echo ""
echo "Feature: $feature_name"
echo "Branch: $branch_name"
echo "Directory: $feature_dir"
echo ""
echo "Summary:"
echo "  [ok] Specification created and clarified"
echo "  [ok] Technical plan designed"
echo "  [ok] 42 tasks generated and executed"
echo "  [ok] All tests passing"
echo "  [ok] Build successful"
echo ""
echo "Next steps:"
echo "  1. Review implementation: git diff main...HEAD"
echo "  2. Manual testing: See $feature_dir/quickstart.md"
echo "  3. Create PR: gh pr create"
echo ""
echo "Cleaning up workflow state..."
```

**Workflow completion:**

```bash
echo "[ok] Workflow completed successfully"
```

---

### RESUME Mode

When invoked with `--resume` or when resuming existing work:

1. **Detect feature directory and progress via CLI:**

   ```bash
   # Use CLI to get current state (deterministic behavior)
   speckitadv check --json

   # CLI returns:
   # {
   #   "feature_dir": "specs/001-user-auth",
   #   "current_workflow": "implement",
   #   "current_stage": 15,
   #   "workflow_complete": false,
   #   "stages_complete": ["1", "2", "3", ...],
   #   "constitution_established": true
   # }

   # If no feature directory found, CLI returns error:
   # { "error": "No feature directory found. Nothing to resume." }
   ```

1. **Display resume summary:**

```text
   +======================================================+
   |  RESUMING WORKFLOW                                   |
   +======================================================+

   Feature: user-auth (001)
   Directory: specs/001-user-auth

   Completed phases:
     [ok] Constitution check
     [ok] Specification
     [ok] Planning
     [ok] Task generation

   Current phase: Implementation (15/42 tasks completed)

   Resume from task T016? [Y/n]
   ```

1. **Jump to current phase:**

   ```bash
   case "$current_phase" in
     "specify")
       # Continue specify workflow
       ;;
     "clarify")
       # Continue clarify workflow
       ;;
     "plan")
       # Continue plan workflow
       ;;
     "tasks")
       # Continue tasks workflow
       ;;
     "analyze")
       # Continue analyze workflow
       ;;
     "implement")
       # Continue implement workflow from last completed task
       ;;
     *)
       echo "ERROR: Unknown phase: $current_phase"
       exit 1
       ;;
   esac
   ```

1. **Continue workflow from detected phase** with normal execution flow.

---

## Error Handling

### Types of Errors

1. **Phase execution failure:**
   - Save current state with error details
   - Provide clear error message and recovery steps
   - Exit with non-zero code

1. **User abort:**
   - Save current state
   - Provide resume instructions
   - Exit cleanly

1. **Missing dependencies:**
   - Check for required files before each phase
   - Provide clear error if prerequisites missing
   - Suggest fixes

### Error Recovery

For any error:

```bash
echo "[x] Error in phase: $current_phase"
echo ""
echo "Error details: $error_message"
echo ""
echo "Your progress has been saved."
echo ""
echo "To resume after fixing the issue:"
echo "  /speckitadv.resume"
echo ""
echo "To start fresh with a new feature:"
echo "  /speckitadv.orchestrate <feature-description>"
```

---

## Progress Reporting

Throughout execution, provide clear progress indicators:

```text
[1/7] [ok] Constitution check
[2/7] [ok] Specification created
[3/7] [SKIP]  Clarification skipped
[4/7] [GEAR]  Planning in progress...
```

For long-running phases (plan, implement), show sub-progress:

```text
[4/7] Planning
  +- [1/2] [ok] Phase 0: Research complete
  +- [2/2] [GEAR]  Phase 1: Design in progress...
```

```text
[7/7] Implementation
  +- Phase 1: Setup [3/3] [ok]
  +- Phase 2: Foundational [8/8] [ok]
  +- Phase 3: User Stories [15/28] [GEAR]
  |   +- US1 (P1) [5/5] [ok]
  |   +- US2 (P1) [4/4] [ok]
  |   +- US3 (P1) [6/7] [GEAR] Current: [T016] JWT validation
  +- Final: Polish [0/3] [-]
```

---

## Integration with Existing Commands

The orchestrator does NOT replace individual commands. Users can still run:

- `/speckitadv.specify` - Direct specification creation
- `/speckitadv.plan` - Direct planning
- `/speckitadv.implement` - Direct implementation
- etc.

The orchestrator simply chains them together with state management.

**When to use orchestrator vs individual commands:**

- **Use `/speckitadv.orchestrate`** for new features start-to-finish
- **Use individual commands** for:

  - Re-running a single phase
  - Manual iteration on specific artifacts
  - Non-linear workflows
  - Learning the workflow step-by-step

---

## Example Usage

### Example 1: Interactive Full Workflow

```bash
/speckitadv.orchestrate Add user authentication with OAuth2 and JWT tokens
```

**Workflow:**

1. Asks for preferences (interactive mode selected)
1. Checks constitution (exists, skips creation)
1. Creates spec -> asks to continue
1. Runs clarify (3 questions) -> asks to continue
1. Creates plan -> asks to continue
1. Generates tasks -> asks to continue
1. Runs analysis (no critical issues) -> asks to continue
1. Implements 42 tasks
1. Completes and cleans up

### Example 2: Quick Iteration Mode

```bash
/speckitadv.orchestrate Create analytics dashboard
```

**Workflow (when user confirms auto-continue at each checkpoint):**

1. Runs constitution -> specify -> plan -> tasks with confirmations
1. Pauses before implementation for review
1. User reviews tasks.md
1. User confirms to continue implementation
1. Implements and completes

### Example 3: Resume After Chat Limit

```bash
# Original chat (reached token limit during implementation)
/speckitadv.orchestrate Build payment processing system

# New chat (restored context)
/speckitadv.resume
```

**Workflow:**

1. Detects feature directory with existing artifacts
1. Reads tasks.md to find progress (28/42 tasks completed)
1. Asks to continue from task T029
1. Resumes implementation
1. Completes remaining 14 tasks

---

## Workflow Visualization

```mermaid
flowchart TD
    A[Constitution] -->|if missing, create| B[Specify]
    B -->|spec.md, branch| C{Clarify?}
    C -->|yes| C1[Clarify]
    C -->|skip| D
    C1 --> D[Plan]
    D -->|plan.md, research.md| E[Tasks]
    E -->|tasks.md| F{Analyze?}
    F -->|yes| F1[Analyze]
    F -->|skip| G
    F1 --> G[Implement]
    G -->|execute tasks| H[Cleanup]
    H --> I((Done))

    subgraph State
        S[specs/feature/.state/state.json]
    end

    S -.->|tracks| B & C1 & D & E & F1 & G & H
```

**Optional Steps:** Clarify and Analyze can be skipped based on feature complexity.

**Resume:** `/speckitadv.resume` restores context from state.json

---

## Summary

The orchestrator provides:

- [ok] **Single-command workflow**: One entry point for entire pipeline
- [ok] **State-based progress**: Resume from exact stage via `{feature_dir}/.state/state.json`
- [ok] **Seamless interoperability**: Works identically whether user used orchestrator or individual commands
- [ok] **Flexible control**: Interactive, auto-spec, or full-auto modes
- [ok] **Error recovery**: Graceful handling with clear recovery paths
- [ok] **Progress visibility**: Real-time phase and task tracking
- [ok] **Optional phases**: Skip clarify/analyze if not needed
- [ok] **Integration**: Works alongside individual commands

**Next:** See `/speckitadv.resume` for context restoration and seamless chat continuity.
