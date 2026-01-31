---
description: Restore full context and resume workflow from saved state (ideal for new chat sessions)
command: speckitadv check --json
version: 1.1.0
---

{{include:strict-execution-mode.md}}

## Role & Mindset

You are a **context reconstruction specialist** who excels at resuming work from saved state. You excel at:

- **Loading and synthesizing** complex artifact sets into coherent context
- **Identifying exact stopping points** from partial work and state files
- **Reconstructing user intent** from specification and planning documents
- **Resuming execution** seamlessly as if no interruption occurred
- **Validating state consistency** before proceeding with work

**Your quality standards:**

- Context reconstruction must be complete and accurate
- All relevant artifacts must be loaded before resuming work
- State validation catches inconsistencies before they cause errors
- User is always shown a clear summary of what will resume
- Resume point is exact - no duplicate work, no missed work

**Your philosophy:**

- Chat history is ephemeral; artifacts and state are truth
- A good resume is indistinguishable from never having paused
- Show your work - user should understand the current state
- When state is ambiguous, ask rather than assume

## User Input

```text
$ARGUMENTS
```

You **MAY** use arguments to specify which feature to resume (optional).

## Purpose

This command restores full context when starting a new chat session after:

- **Token limit reached** during any workflow phase
- **Chat closed** mid-implementation
- **System interruption** during long-running operations
- **Deliberate pause** to review work before continuing
- **Multi-day workflows** where you resume the next day

**Key principle:** This command can reconstruct complete context even with ZERO chat history.

---

## Execution Flow

### **STEP 1: Identify What to Resume**

#### **Option A: Detect Feature Directory Automatically**

This is the primary resume path. The CLI detects progress by reading `state.json` from the feature directory.

```bash
# Use CLI to get current state (deterministic behavior)
speckitadv check --json

# CLI returns:
# {
#   "feature_dir": "specs/001-user-auth",
#   "feature_name": "user-auth",
#   "feature_number": "001",
#   "current_workflow": "implement",
#   "current_stage": 15,
#   "workflow_complete": false,
#   "stages_complete": ["1", "2", "3", ...],
#   "constitution_established": true,
#   "tasks_completed": 28,
#   "tasks_total": 47
# }

# If no feature directory found, CLI returns:
# { "error": "No feature directory found. Nothing to resume." }
```

**If feature directory exists:** Jump to STEP 2 (Load Context).

---

#### **Option B: User Provided Feature Identifier**

User ran: `/speckitadv.resume 001-user-auth` or `/speckitadv.resume user-auth`

```bash
# Parse user argument
feature_arg="$ARGUMENTS"

# Find matching feature directory
if [[ "$feature_arg" =~ ^[0-9]+-.*$ ]]; then
  # Full format: 001-user-auth
  feature_dir="specs/$feature_arg"
elif [[ "$feature_arg" =~ ^[0-9]+$ ]]; then
  # Just number: 001
  feature_dir=$(find specs -maxdepth 1 -type d -name "${feature_arg}-*" | head -1)
elif [ -n "$feature_arg" ]; then
  # Just name: user-auth
  feature_dir=$(find specs -maxdepth 1 -type d -name "*-${feature_arg}" | head -1)
else
  feature_dir=""
fi

if [ -z "$feature_dir" ] || [ ! -d "$feature_dir" ]; then
  echo "ERROR: Feature not found: $feature_arg"
  echo ""
  echo "Available features:"
  ls -1 specs/ | grep -E '^[0-9]+-' | sed 's/^/  - /'
  exit 1
fi

echo "[ok] Found feature directory: $feature_dir"
```

**If user provided identifier:** Jump to STEP 2 (Load Context).

---

#### **Option C: Auto-Detect from Git Branch**

User ran: `/speckitadv.resume` with no arguments and no state file.

```bash
# Get current git branch
current_branch=$(git branch --show-current 2>/dev/null || echo "")

# Check if branch matches feature pattern: ###-feature-name
if [[ "$current_branch" =~ ^[0-9]+-.*$ ]]; then
  feature_dir="specs/$current_branch"

  if [ -d "$feature_dir" ]; then
    echo "[ok] Auto-detected from branch: $current_branch"
    echo "[ok] Feature directory: $feature_dir"
  else
    echo "ERROR: Branch $current_branch exists but no matching feature directory"
    echo "Expected: $feature_dir"
    exit 1
  fi
else
  echo "ERROR: Cannot auto-detect feature to resume"
  echo ""
  echo "Current branch: ${current_branch:-<none>}"
  echo "Expected format: ###-feature-name (e.g., 001-user-auth)"
  echo ""
  echo "Options:"
  echo "  1. Switch to feature branch: git checkout <feature-branch>"
  echo "  2. Specify feature explicitly: speckitadv resume <feature-identifier>"
  echo ""
  echo "Available features:"
  ls -1 specs/ | grep -E '^[0-9]+-' | sed 's/^/  - /'
  exit 1
fi
```

---

### **STEP 2: Load Context from Artifacts**

#### **2.1: Discover Available Artifacts**

```bash
# Required artifacts
spec_file="$feature_dir/spec.md"
plan_file="$feature_dir/plan.md"
tasks_file="$feature_dir/tasks.md"

# Optional artifacts
research_file="$feature_dir/research.md"
data_model_file="$feature_dir/data-model.md"
quickstart_file="$feature_dir/quickstart.md"
contracts_dir="$feature_dir/contracts"
checklists_dir="$feature_dir/checklists"

# Constitution (project-level)
constitution_file="memory/constitution.md"

# Check what exists
artifacts_found=()
artifacts_missing=()

for file in "$spec_file" "$plan_file" "$tasks_file" "$research_file" \
            "$data_model_file" "$quickstart_file" "$constitution_file"; do
  if [ -f "$file" ]; then
    artifacts_found+=("$file")
  else
    artifacts_missing+=("$file")
  fi
done

# Report findings
echo ""
echo "+=======================================================+"
echo "|  ARTIFACT DISCOVERY                                   |"
echo "+=======================================================+"
echo ""
echo "Found (${#artifacts_found[@]} files):"
for artifact in "${artifacts_found[@]}"; do
  echo "  [ok] $artifact"
done

if [ ${#artifacts_missing[@]} -gt 0 ]; then
  echo ""
  echo "Missing (${#artifacts_missing[@]} files):"
  for artifact in "${artifacts_missing[@]}"; do
    echo "  [x] $artifact"
  done
fi
```

---

#### **2.2: Determine Workflow Phase**

The CLI provides current phase and stage information:

```bash
# Use CLI to get workflow state (deterministic, consistent across models)
speckitadv check --json

# CLI returns complete state information:
# {
#   "feature_dir": "specs/001-user-auth",
#   "current_workflow": "implement",
#   "current_stage": 15,
#   "workflow_complete": false,
#   "stages_complete": ["1", "2", ..., "14"],
#   "phase": "implement",
#   "phase_description": "Implementation in progress (28/47 tasks)",
#   "tasks_completed": 28,
#   "tasks_total": 47,
#   "next_task_id": "T029"
# }

# The CLI handles all state detection logic:
# - Reads state.json and parses workflow/stage
# - Determines if workflow is complete
# - Calculates task progress for implement phase
# - Returns structured JSON for deterministic processing
```

---

#### **2.3: Load Constitution (Project Context)**

```bash
if [ -f "$constitution_file" ]; then
  echo ""
  echo "+=======================================================+"
  echo "|  LOADING CONSTITUTION                                 |"
  echo "+=======================================================+"
  echo ""

  # Read constitution file
  constitution_content=$(cat "$constitution_file")

  # Extract key principles (MUST, SHOULD, MAY)
  must_count=$(echo "$constitution_content" | grep -c '^- \*\*MUST' || echo 0)
  should_count=$(echo "$constitution_content" | grep -c '^- \*\*SHOULD' || echo 0)
  may_count=$(echo "$constitution_content" | grep -c '^- \*\*MAY' || echo 0)

  echo "Constitution loaded:"
  echo "  - MUST principles: $must_count"
  echo "  - SHOULD principles: $should_count"
  echo "  - MAY principles: $may_count"
  echo ""
  echo "[CLIPBOARD] Constitution will guide all decisions during resumption."
else
  echo "[!]  Warning: No constitution found (memory/constitution.md)"
  echo "   Proceeding without project governance principles."
fi
```

---

#### **2.4: Load Specification**

```bash
if [ -f "$spec_file" ]; then
  echo ""
  echo "+=======================================================+"
  echo "|  LOADING SPECIFICATION                                |"
  echo "+=======================================================+"
  echo ""

  # Read spec file
  spec_content=$(cat "$spec_file")

  # Extract summary information
  user_stories=$(echo "$spec_content" | grep -c '^### US[0-9]' || echo 0)
  functional_reqs=$(echo "$spec_content" | grep -c '^- \*\*FR[0-9]' || echo 0)
  nonfunctional_reqs=$(echo "$spec_content" | grep -c '^- \*\*NFR[0-9]' || echo 0)
  clarification_markers=$(echo "$spec_content" | grep -c '\[NEEDS CLARIFICATION' || echo 0)

  echo "Specification summary:"
  echo "  - User Stories: $user_stories"
  echo "  - Functional Requirements: $functional_reqs"
  echo "  - Non-Functional Requirements: $nonfunctional_reqs"
  if [ "$clarification_markers" -gt 0 ]; then
    echo "  - [!]  Unresolved clarifications: $clarification_markers"
  fi
  echo ""
  echo "[CLIPBOARD] Full specification loaded into context."
else
  echo "[x] ERROR: Specification file not found: $spec_file"
  echo ""
  echo "Cannot resume without specification."
  echo "Please run: speckitadv specify --feature '<description>'"
  exit 1
fi
```

---

#### **2.5: Load Plan (if exists)**

```bash
if [ -f "$plan_file" ]; then
  echo ""
  echo "+=======================================================+"
  echo "|  LOADING PLAN                                         |"
  echo "+=======================================================+"
  echo ""

  # Read plan file
  plan_content=$(cat "$plan_file")

  # Extract tech stack
  language=$(echo "$plan_content" | grep -m1 '^- \*\*Language' | sed 's/^- \*\*Language[^:]*: //' || echo "N/A")
  framework=$(echo "$plan_content" | grep -m1 '^- \*\*Framework' | sed 's/^- \*\*Framework[^:]*: //' || echo "N/A")
  storage=$(echo "$plan_content" | grep -m1 '^- \*\*Storage' | sed 's/^- \*\*Storage[^:]*: //' || echo "N/A")

  echo "Technical plan loaded:"
  echo "  - Language: $language"
  echo "  - Framework: $framework"
  echo "  - Storage: $storage"
  echo ""
  echo "[CLIPBOARD] Full plan loaded into context."

  # Load related artifacts
  if [ -f "$research_file" ]; then
    echo "  [ok] Research findings loaded"
  fi
  if [ -f "$data_model_file" ]; then
    echo "  [ok] Data model loaded"
  fi
  if [ -f "$quickstart_file" ]; then
    echo "  [ok] Quickstart scenarios loaded"
  fi
  if [ -d "$contracts_dir" ] && [ -n "$(ls -A $contracts_dir 2>/dev/null)" ]; then
    contract_count=$(ls -1 "$contracts_dir" | wc -l)
    echo "  [ok] API contracts loaded ($contract_count files)"
  fi
else
  if [ "$phase" = "plan" ]; then
    echo "[PIN] Phase: Planning (no plan file yet - will create)"
  else
    echo "[!]  Warning: Plan file not found (expected at this phase)"
  fi
fi
```

---

#### **2.6: Load Tasks and Identify Resume Point**

This is the MOST CRITICAL section for implementation resumption.

```bash
if [ -f "$tasks_file" ]; then
  echo ""
  echo "+=======================================================+"
  echo "|  LOADING TASKS                                        |"
  echo "+=======================================================+"
  echo ""

  # Read tasks file
  tasks_content=$(cat "$tasks_file")

  # Count total and completed tasks
  total_tasks=$(echo "$tasks_content" | grep -c '^\- \[[ X]\] \[T[0-9]' || echo 0)
  completed_tasks=$(echo "$tasks_content" | grep -c '^\- \[X\] \[T[0-9]' || echo 0)
  pending_tasks=$((total_tasks - completed_tasks))

  # Calculate progress percentage
  if [ "$total_tasks" -gt 0 ]; then
    progress_pct=$((completed_tasks * 100 / total_tasks))
  else
    progress_pct=0
  fi

  echo "Task Progress:"
  echo "  Total: $total_tasks"
  echo "  Completed: $completed_tasks [ok]"
  echo "  Pending: $pending_tasks"
  echo "  Progress: $progress_pct%"
  echo ""

  # Draw progress bar
  bar_width=40
  filled=$((progress_pct * bar_width / 100))
  empty=$((bar_width - filled))

  printf "  ["
  printf "%${filled}s" | tr ' ' '='
  printf "%${empty}s" | tr ' ' '-'
  printf "] $progress_pct%%\n"
  echo ""

  # Find next task to work on
  if [ "$pending_tasks" -gt 0 ]; then
    # Find first uncompleted task
    next_task=$(echo "$tasks_content" | grep '^\- \[ \] \[T[0-9]' | head -1)
    next_task_id=$(echo "$next_task" | grep -oE '\[T[0-9]+\]' | head -1)
    next_task_desc=$(echo "$next_task" | sed -E 's/^- \[ \] \[T[0-9]+\] (\[P[0-9]?\] )?(\[US[0-9]+\] )?//')

    echo "[PIN] Resume Point:"
    echo "  Task: $next_task_id"
    echo "  Description: $next_task_desc"
    echo ""

    # Show recently completed tasks (context)
    echo "Recently completed:"
    echo "$tasks_content" | grep '^\- \[X\] \[T[0-9]' | tail -3 | while read line; do
      task_id=$(echo "$line" | grep -oE '\[T[0-9]+\]')
      task_desc=$(echo "$line" | sed -E 's/^- \[X\] \[T[0-9]+\] (\[P[0-9]?\] )?(\[US[0-9]+\] )?//')
      echo "  [ok] $task_id: $task_desc"
    done
    echo ""

    # Show upcoming tasks (preview)
    echo "Coming up:"
    echo "$tasks_content" | grep '^\- \[ \] \[T[0-9]' | head -5 | while read line; do
      task_id=$(echo "$line" | grep -oE '\[T[0-9]+\]')
      task_desc=$(echo "$line" | sed -E 's/^- \[ \] \[T[0-9]+\] (\[P[0-9]?\] )?(\[US[0-9]+\] )?//')
      if [ "$task_id" = "$next_task_id" ]; then
        echo "  -> $task_id: $task_desc  <- NEXT"
      else
        echo "    $task_id: $task_desc"
      fi
    done
    echo ""

  elif [ "$total_tasks" -gt 0 ]; then
    echo "[ok] All tasks completed!"
    echo ""
  else
    echo "[PIN] No tasks generated yet (tasks file empty)"
    echo ""
  fi

  # Identify current phase based on task progress
  if [ "$total_tasks" -eq 0 ]; then
    task_phase="generate"
    task_phase_desc="Tasks file exists but empty - need to generate tasks"
  elif [ "$pending_tasks" -eq 0 ]; then
    task_phase="complete"
    task_phase_desc="All tasks completed"
  else
    # Find which phase group the next task belongs to
    phase_line=$(echo "$tasks_content" | grep -B20 "$next_task_id" | grep '^## Phase [0-9]' | tail -1)

    if echo "$phase_line" | grep -q 'Setup'; then
      task_phase="setup"
      task_phase_desc="Setup phase"
    elif echo "$phase_line" | grep -q 'Foundational'; then
      task_phase="foundational"
      task_phase_desc="Foundational phase (blocking prerequisites)"
    elif echo "$phase_line" | grep -q 'User Stor'; then
      task_phase="user_stories"
      task_phase_desc="User stories implementation"
    elif echo "$phase_line" | grep -q 'Polish'; then
      task_phase="polish"
      task_phase_desc="Polish and cross-cutting concerns"
    else
      task_phase="unknown"
      task_phase_desc="Implementation"
    fi
  fi

  echo "Current Implementation Phase: $task_phase_desc"
  echo ""

else
  if [ "$phase" = "tasks" ]; then
    echo "[PIN] Phase: Task Generation (no tasks file yet - will create)"
  elif [ "$phase" = "implement" ]; then
    echo "[x] ERROR: Phase is 'implement' but no tasks file found"
    echo "Expected: $tasks_file"
    exit 1
  fi
fi
```

---

### **STEP 3: Context Validation**

Before resuming, validate that context is consistent:

```bash
echo ""
echo "+=======================================================+"
echo "|  CONTEXT VALIDATION                                   |"
echo "+=======================================================+"
echo ""

validation_passed=true
validation_warnings=()
validation_errors=()

# Check 1: Branch matches feature
current_branch=$(git branch --show-current 2>/dev/null || echo "")
expected_branch=$(basename "$feature_dir")

if [ "$current_branch" != "$expected_branch" ]; then
  validation_warnings+=("Git branch mismatch: on '$current_branch', expected '$expected_branch'")
fi

# Check 2: Required artifacts exist for current phase
case "$phase" in
  "plan")
    if [ ! -f "$spec_file" ]; then
      validation_errors+=("Planning requires spec.md (not found)")
    fi
    ;;
  "tasks")
    if [ ! -f "$spec_file" ]; then
      validation_errors+=("Task generation requires spec.md (not found)")
    fi
    if [ ! -f "$plan_file" ]; then
      validation_errors+=("Task generation requires plan.md (not found)")
    fi
    ;;
  "implement")
    if [ ! -f "$spec_file" ]; then
      validation_errors+=("Implementation requires spec.md (not found)")
    fi
    if [ ! -f "$plan_file" ]; then
      validation_errors+=("Implementation requires plan.md (not found)")
    fi
    if [ ! -f "$tasks_file" ]; then
      validation_errors+=("Implementation requires tasks.md (not found)")
    fi
    ;;
esac

# Check 3: Git working directory state
git_status=$(git status --porcelain 2>/dev/null || echo "")
uncommitted_changes=$(echo "$git_status" | wc -l)

if [ "$uncommitted_changes" -gt 0 ]; then
  validation_warnings+=("$uncommitted_changes uncommitted changes in working directory")
fi

# Report validation results
if [ ${#validation_errors[@]} -eq 0 ] && [ ${#validation_warnings[@]} -eq 0 ]; then
  echo "[ok] Context validation passed"
  echo ""
else
  if [ ${#validation_warnings[@]} -gt 0 ]; then
    echo "[!]  Warnings (${#validation_warnings[@]}):"
    for warning in "${validation_warnings[@]}"; do
      echo "  - $warning"
    done
    echo ""
  fi

  if [ ${#validation_errors[@]} -gt 0 ]; then
    echo "[x] Errors (${#validation_errors[@]}):"
    for error in "${validation_errors[@]}"; do
      echo "  - $error"
    done
    echo ""
    validation_passed=false
  fi
fi

if [ "$validation_passed" = false ]; then
  echo "Cannot resume due to validation errors."
  echo "Please fix the errors above and try again."
  exit 1
fi
```

---

### **STEP 4: Context Summary**

Provide a comprehensive summary before resuming:

```bash
echo ""
echo "+=======================================================+"
echo "|  RESUME SUMMARY                                       |"
echo "+=======================================================+"
echo ""
echo "Feature: $feature_name ($(echo "$feature_dir" | grep -oE '^[0-9]+'))"
echo "Branch: $expected_branch"
echo "Directory: $feature_dir"
echo ""
echo "Loaded Context:"
echo "  [ok] Constitution: memory/constitution.md"
echo "  [ok] Specification: $spec_file"
if [ -f "$plan_file" ]; then
  echo "  [ok] Plan: $plan_file"
fi
if [ -f "$research_file" ]; then
  echo "  [ok] Research: $research_file"
fi
if [ -f "$data_model_file" ]; then
  echo "  [ok] Data Model: $data_model_file"
fi
if [ -f "$tasks_file" ]; then
  echo "  [ok] Tasks: $tasks_file ($completed_tasks/$total_tasks completed)"
fi
echo ""

# Show what will happen next
echo "What happens next:"
case "$phase" in
  "specify")
    echo "  -> Continue specification creation"
    echo "  -> Fill out spec.md template"
    echo "  -> Create quality checklist"
    ;;
  "clarify")
    echo "  -> Scan spec for ambiguities"
    echo "  -> Ask clarifying questions"
    echo "  -> Update spec with answers"
    ;;
  "plan")
    echo "  -> Create technical implementation plan"
    echo "  -> Research unknowns (Phase 0)"
    echo "  -> Design architecture (Phase 1)"
    ;;
  "tasks")
    echo "  -> Generate executable task breakdown"
    echo "  -> Organize by phases and user stories"
    echo "  -> Validate coverage"
    ;;
  "analyze")
    echo "  -> Validate consistency and coverage"
    echo "  -> Check for gaps and duplicates"
    echo "  -> Verify constitution alignment"
    ;;
  "implement")
    echo "  -> Resume implementation at task $next_task_id"
    echo "  -> Execute remaining $pending_tasks tasks"
    echo "  -> Mark tasks [X] as completed"
    echo "  -> Run tests and validate"
    ;;
  "complete")
    echo "  -> Implementation is complete"
    echo "  -> No further action needed"
    ;;
  *)
    echo "  -> Phase: $phase (see state file for details)"
    ;;
esac
echo ""
```

---

### **STEP 5: User Confirmation**

Before resuming, ask for confirmation:

```bash
# For implementation phase, be extra careful
if [ "$phase" = "implement" ] && [ "$pending_tasks" -gt 0 ]; then
  echo "+=======================================================+"
  echo "|  READY TO RESUME IMPLEMENTATION                       |"
  echo "+=======================================================+"
  echo ""
  echo "Next task: $next_task_id"
  echo "Description: $next_task_desc"
  echo ""
  echo "Remaining: $pending_tasks tasks ($((total_tasks - completed_tasks)) to go)"
  echo "Estimated time: $((pending_tasks * 2)) - $((pending_tasks * 5)) minutes"
  echo ""
  echo "Resume implementation? [Y/n/review]"
  echo "  'y' or Enter: Continue with task $next_task_id"
  echo "  'n': Cancel (state preserved)"
  echo "  'review': Show next 10 tasks before deciding"
  echo ""

  # Wait for user response
  # (In actual use, this would be interactive)

else
  echo "Ready to resume. Continue? [Y/n]"
fi
```

---

### **STEP 6: Resume Execution**

Based on the phase, invoke the appropriate workflow:

```bash
# Branch based on current phase
case "$phase" in
  "specify")
    echo "> Resuming specification creation..."
    # Invoke /speckitadv.specify
    ;;

  "clarify")
    echo "> Resuming clarification..."
    # Invoke /speckitadv.clarify
    ;;

  "plan")
    echo "> Resuming planning..."
    # Invoke /speckitadv.plan
    ;;

  "tasks")
    echo "> Resuming task generation..."
    # Invoke /speckitadv.tasks
    ;;

  "analyze")
    echo "> Resuming analysis..."
    # Invoke /speckitadv.analyze
    ;;

  "implement")
    echo "> Resuming implementation at task $next_task_id..."
    echo ""

    # Load all design artifacts for implementation context
    echo "Loading design artifacts into context..."

    # Constitution
    constitution_content=$(cat "$constitution_file" 2>/dev/null || echo "")

    # Spec
    spec_content=$(cat "$spec_file")

    # Plan
    plan_content=$(cat "$plan_file")

    # Research (if exists)
    if [ -f "$research_file" ]; then
      research_content=$(cat "$research_file")
    fi

    # Data model (if exists)
    if [ -f "$data_model_file" ]; then
      data_model_content=$(cat "$data_model_file")
    fi

    # Quickstart (if exists)
    if [ -f "$quickstart_file" ]; then
      quickstart_content=$(cat "$quickstart_file")
    fi

    # Contracts (if exist)
    if [ -d "$contracts_dir" ]; then
      contracts_list=$(find "$contracts_dir" -type f 2>/dev/null)
    fi

    # Tasks
    tasks_content=$(cat "$tasks_file")

    echo "[ok] All design artifacts loaded"
    echo ""

    # Invoke /speckitadv.implement
    # The implement prompt will:
    # - See tasks.md with some [X] completed
    # - Pick up from first [ ] uncompleted task
    # - Continue marking [X] as each completes
    ;;

  "complete")
    echo "[ok] Implementation already complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Review changes: git diff main...HEAD"
    echo "  2. Test manually: See $quickstart_file"
    echo "  3. Create PR: gh pr create"
    ;;

  *)
    echo "[x] Unknown phase: $phase"
    echo "Check feature directory for details: $feature_dir"
    exit 1
    ;;
esac
```

---

## Special Scenarios

| Scenario | Situation | Behavior |
|----------|-----------|----------|
| **Mid-Implementation** | Token limit at task T023 | Auto-detect branch, load all artifacts, identify next task, confirm and continue |
| **Cross-Day** | Fresh chat next day | Same as above - seamless multi-day workflow |
| **Manual Edits** | User edited spec.md | Detect changes, warn user, ask to confirm modified spec |
| **Different Machine** | Cloned repo elsewhere | `git checkout branch` then `/speckitadv.resume` - location-independent |
| **After Error** | Task T030 failed | Fix dependency, resume offers retry or skip, then continue |

**All scenarios:** Zero duplicate work, full context restored from state.json and artifacts.

---

## Integration with Orchestrator

The `/speckitadv.resume` command works seamlessly with `/speckitadv.orchestrate`:

**Orchestrator and individual commands share the same state:**

```text
specs/001-user-auth/
+-- .state/
|   +-- state.json     # Workflow state (maintained by CLI)
+-- spec.md            # Created by specify phase
+-- plan.md            # Created by plan phase
+-- tasks.md           # Created by tasks phase
+-- analysis.md        # Created by analyze phase (optional)
```

**Resume detects progress via CLI:**

```bash
/speckitadv.resume
# -> CLI runs: speckitadv check --json
# -> Reads specs/001-user-auth/.state/state.json
# -> Returns exact workflow, stage, and task progress
# -> Resumes at exact point (no duplicate work)
```

**How it works:**

- CLI reads state.json for exact workflow/stage information
- Same state file used by orchestrator and individual commands
- Seamless interoperability between normal and orchestrated flows
- Deterministic behavior across all AI models

---

## Best Practices

### **For Users:**

1. **Commit frequently:**

   - Commit after each major phase completion
   - Commit all artifacts for cross-machine resumption
   - Tag important milestones

2. **Use descriptive branch names:**

   - Format: `###-feature-name` (e.g., `001-user-auth`)
   - Makes auto-detection reliable

3. **Don't manually edit task checkboxes:**

   - Let commands mark [X] automatically
   - Manual edits can desync state

4. **Review before resuming implementation:**

   - Use `review` option to see upcoming tasks
   - Ensure you understand where you left off

### **For Context Restoration:**

1. **All critical info is in artifacts:**

   - Spec, plan, tasks, research contain everything needed
   - Artifact files provide all state information
   - Chat history is NOT needed

2. **Validation prevents errors:**

   - Context validation catches missing files
   - Branch checks prevent working on wrong feature
   - Git status warns about uncommitted work

3. **Progressive loading:**

   - Load constitution first (global context)
   - Then spec (requirements)
   - Then plan (architecture)
   - Finally tasks (execution)

---

## Example Session

```bash
# === NEW CHAT SESSION (no history) ===

$ /speckitadv.resume

[ok] Found orchestration state file
Feature: user-auth (001)
Directory: specs/001-user-auth
Current phase: implement
Mode: interactive

+=======================================================+
|  ARTIFACT DISCOVERY                                   |
+=======================================================+

Found (7 files):
  [ok] memory/constitution.md
  [ok] specs/001-user-auth/spec.md
  [ok] specs/001-user-auth/plan.md
  [ok] specs/001-user-auth/research.md
  [ok] specs/001-user-auth/data-model.md
  [ok] specs/001-user-auth/quickstart.md
  [ok] specs/001-user-auth/tasks.md

Detected phase: implement
Description: Implementation in progress (28/47 tasks)

+=======================================================+
|  LOADING CONSTITUTION                                 |
+=======================================================+

Constitution loaded:
  - MUST principles: 8
  - SHOULD principles: 12
  - MAY principles: 5

[CLIPBOARD] Constitution will guide all decisions during resumption.

+=======================================================+
|  LOADING SPECIFICATION                                |
+=======================================================+

Specification summary:
  - User Stories: 5
  - Functional Requirements: 18
  - Non-Functional Requirements: 7

[CLIPBOARD] Full specification loaded into context.

+=======================================================+
|  LOADING PLAN                                         |
+=======================================================+

Technical plan loaded:
  - Language: Node.js 20.x
  - Framework: Express 4.18.x
  - Storage: PostgreSQL 15.x + Redis 7.x

[CLIPBOARD] Full plan loaded into context.
  [ok] Research findings loaded
  [ok] Data model loaded
  [ok] Quickstart scenarios loaded
  [ok] API contracts loaded (3 files)

+=======================================================+
|  LOADING TASKS                                        |
+=======================================================+

Task Progress:
  Total: 47
  Completed: 28 [ok]
  Pending: 19
  Progress: 59%

  [=======================-----------------] 59%

[PIN] Resume Point:
  Task: [T029]
  Description: Add JWT expiration and refresh logic

Recently completed:
  [ok] [T026]: Create user registration endpoint
  [ok] [T027]: Implement password validation rules
  [ok] [T028]: Add email verification flow

Coming up:
  -> [T029]: Add JWT expiration and refresh logic  <- NEXT
    [T030]: Implement logout and token revocation
    [T031]: Add rate limiting for auth endpoints
    [T032]: Create user profile endpoints
    [T033]: Add password reset functionality

Current Implementation Phase: User stories implementation

+=======================================================+
|  CONTEXT VALIDATION                                   |
+=======================================================+

[ok] Context validation passed

+=======================================================+
|  RESUME SUMMARY                                       |
+=======================================================+

Feature: user-auth (001)
Branch: 001-user-auth
Directory: specs/001-user-auth

Loaded Context:
  [ok] Constitution: memory/constitution.md
  [ok] Specification: specs/001-user-auth/spec.md
  [ok] Plan: specs/001-user-auth/plan.md
  [ok] Research: specs/001-user-auth/research.md
  [ok] Data Model: specs/001-user-auth/data-model.md
  [ok] Tasks: specs/001-user-auth/tasks.md (28/47 completed)

What happens next:
  -> Resume implementation at task [T029]
  -> Execute remaining 19 tasks
  -> Mark tasks [X] as completed
  -> Run tests and validate

+=======================================================+
|  READY TO RESUME IMPLEMENTATION                       |
+=======================================================+

Next task: [T029]
Description: Add JWT expiration and refresh logic

Remaining: 19 tasks (19 to go)
Estimated time: 38 - 95 minutes

Resume implementation? [Y/n/review]
```

---

## Summary

The `/speckitadv.resume` command provides:

- [ok] **Complete context restoration** from artifacts (no chat history needed)
- [ok] **Exact resume point identification** via CLI reading state.json
- [ok] **State validation** before proceeding
- [ok] **Progress visualization** with clear next steps
- [ok] **Phase-aware resumption** (works for any workflow phase)
- [ok] **Cross-machine support** (works anywhere with branch checkout)
- [ok] **Error recovery** (handles failures gracefully)
- [ok] **Seamless interoperability** (same state.json for orchestrator and individual commands)
- [ok] **Deterministic behavior** (CLI-based state detection, consistent across AI models)

**Key principle:** The state.json file IS the source of truth. Chat history is ephemeral; state.json and artifacts are permanent.

**Recommended workflow:**

1. Start feature: `/speckitadv.orchestrate <description>`
2. Work until token limit or pause
3. New chat: `/speckitadv.resume`
4. Repeat step 3 as needed
5. Complete feature with zero context loss
