"""
Workflow configurations for all spec-kit commands.

Each workflow is defined declaratively with stages, guards, and transitions.
"""

from speckit.core.workflow.configs.analyze_project import ANALYZE_PROJECT_WORKFLOW
from speckit.core.workflow.configs.constitution import CONSTITUTION_WORKFLOW
from speckit.core.workflow.configs.deepwiki import DEEPWIKI_WORKFLOW
from speckit.core.workflow.configs.feature_scoped import (
    ANALYZE_WORKFLOW,
    CHECKLIST_WORKFLOW,
    CLARIFY_WORKFLOW,
    IMPLEMENT_WORKFLOW,
    PLAN_WORKFLOW,
    REVIEW_WORKFLOW,
    TASKS_WORKFLOW,
    TESTS_WORKFLOW,
)
from speckit.core.workflow.configs.generate_guidelines import GENERATE_GUIDELINES_WORKFLOW
from speckit.core.workflow.configs.specify import SPECIFY_WORKFLOW
from speckit.core.workflow.definitions import WorkflowConfig

# Workflow registry - maps command name to workflow config
WORKFLOW_REGISTRY = {
    "specify": SPECIFY_WORKFLOW,
    "analyze-project": ANALYZE_PROJECT_WORKFLOW,
    "constitution": CONSTITUTION_WORKFLOW,
    "deepwiki": DEEPWIKI_WORKFLOW,
    "generate-guidelines": GENERATE_GUIDELINES_WORKFLOW,
    "clarify": CLARIFY_WORKFLOW,
    "plan": PLAN_WORKFLOW,
    "tasks": TASKS_WORKFLOW,
    "implement": IMPLEMENT_WORKFLOW,
    "checklist": CHECKLIST_WORKFLOW,
    "analyze": ANALYZE_WORKFLOW,
    "review": REVIEW_WORKFLOW,
    "tests": TESTS_WORKFLOW,
}


def get_workflow(command: str) -> WorkflowConfig | None:
    """
    Get workflow configuration for a command.

    Args:
        command: Command name (e.g., "specify", "analyze-project")

    Returns:
        WorkflowConfig or None if not found
    """
    return WORKFLOW_REGISTRY.get(command)


__all__ = [
    "SPECIFY_WORKFLOW",
    "ANALYZE_PROJECT_WORKFLOW",
    "CONSTITUTION_WORKFLOW",
    "DEEPWIKI_WORKFLOW",
    "GENERATE_GUIDELINES_WORKFLOW",
    "CLARIFY_WORKFLOW",
    "PLAN_WORKFLOW",
    "TASKS_WORKFLOW",
    "IMPLEMENT_WORKFLOW",
    "CHECKLIST_WORKFLOW",
    "ANALYZE_WORKFLOW",
    "REVIEW_WORKFLOW",
    "TESTS_WORKFLOW",
    "WORKFLOW_REGISTRY",
    "get_workflow",
]
