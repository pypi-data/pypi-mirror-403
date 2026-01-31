"""
Workflow module for declarative state machine pattern.

Architecture Overview
---------------------
This module centralizes workflow logic that was previously scattered across
multiple files (stages.py, analyze_project.py, constitution.py, cli.py).

The architecture follows a clear separation of concerns:

    WorkflowConfig     ->  WorkflowStateMachine  ->  StateMachineExecutor
    (Declarative)          (Transition Logic)        (Prompt Loading)
         |                        |                        |
         v                        v                        v
    Python configs          validate()              emit_stage()
    in configs/             get_next()              render_prompt()
                            can_execute()

Module Structure
----------------
- definitions.py: Core dataclasses (StageDefinition, Guard, WorkflowConfig)
- machine.py: WorkflowStateMachine for navigation and validation
- guards.py: Reusable guard functions for pre-condition validation
- executor.py: StateMachineExecutor for stage execution
- configs/: Workflow definitions for each command
    - specify.py: 6-stage feature specification workflow
    - analyze_project.py: 16-stage analysis with scope-based branching
    - constitution.py: 3-stage project constitution workflow
    - generate_guidelines.py: 4-stage guidelines generation (standalone)
    - deepwiki.py: 16-stage AI-powered documentation workflow
    - feature_scoped.py: Shared workflows (clarify, plan, tasks, etc.)

Key Concepts
------------
1. StageDefinition: A single workflow stage with guards, transitions, and chunks
2. Guard: Pre-condition that must pass before stage execution
3. WorkflowConfig: Complete workflow with stages and initial state
4. WorkflowStateMachine: Handles transitions and guard validation
5. StateMachineExecutor: Loads prompts and executes stages

Scope-Based Branching
---------------------
Some workflows (like analyze-project) support scope-based branching where
stage 2e (Quality Gates) branches to different paths based on scope A or B:
- Scope A -> Stage 3a (Full Application Analysis) -> Stage 4a
- Scope B -> Stage 3b (Cross-Cutting Analysis) -> Stage 4a

Both paths rejoin at stage 4a for report generation.

Chunked Stages
--------------
Some stages have multiple prompt fragments (chunks). For example,
analyze-project stage 3a has 4 chunks:
- 03a1-questions-part1, 03a2-questions-part2
- 03a3-validation-scoring, 03a4-recommendations

Use StateMachineExecutor.get_chunk_count() and load_prompt(chunk=N) for these.

Usage Example
-------------
    from speckit.core.workflow import (
        WorkflowStateMachine,
        WorkflowConfig,
        StageDefinition,
        Guard,
        create_executor,
    )

    # Define a workflow
    config = WorkflowConfig(
        name="my-workflow",
        initial_stage="01-init",
        stages=[
            StageDefinition(
                id="01-init",
                stage_num=1,
                fragment="01-init",
                title="Initialization",
                next_states={"default": "02-setup"},
            ),
            # ... more stages
        ],
    )

    # Create state machine
    machine = WorkflowStateMachine(config)

    # Navigate workflow
    next_stage = machine.get_next_stage("01-init", context={})
    can_run, errors = machine.can_execute("02-setup", context)

    # Or use the executor for full stage execution
    executor = create_executor("specify")
    context = ExecutionContext(command="specify", feature="My feature")
    result = executor.execute_stage("01-initialization", context)
"""

from speckit.core.workflow.definitions import (
    Guard,
    StageDefinition,
    WorkflowConfig,
)
from speckit.core.workflow.executor import (
    ExecutionContext,
    ExecutionResult,
    StateMachineExecutor,
    create_executor,
)
from speckit.core.workflow.guards import (
    custom_guard,
    requires_analysis_dir,
    requires_context_key,
    requires_feature,
    requires_folder_exists,
    requires_jira,
    requires_project_path,
    requires_scope,
    requires_state_exists,
)
from speckit.core.workflow.helpers import get_next_steps
from speckit.core.workflow.machine import WorkflowStateMachine

__all__ = [
    # Core classes
    "Guard",
    "StageDefinition",
    "WorkflowConfig",
    "WorkflowStateMachine",
    # Executor classes
    "ExecutionContext",
    "ExecutionResult",
    "StateMachineExecutor",
    "create_executor",
    # Helper functions
    "get_next_steps",
    # Guard factories
    "requires_feature",
    "requires_jira",
    "requires_scope",
    "requires_folder_exists",
    "requires_state_exists",
    "requires_analysis_dir",
    "requires_project_path",
    "requires_context_key",
    "custom_guard",
]
