"""
Spec Kit Advanced Core Modules

Core infrastructure for state management, configuration, utilities,
template handling, and prompt fragment system.
"""

from speckit.core.config import Config

# State management types
from speckit.core.constants import RepoixMode
from speckit.core.emit import (
    emit_chunk,
    emit_complete,
    emit_error,
    emit_stage,
    emit_template,
)
from speckit.core.prompts import (
    count_fragment_lines,
    fragment_exists,
    get_next_stage,
    get_prompt_fragment,
    get_stage_order,
    list_fragments,
    render_prompt,
)
from speckit.core.templates import (
    emit_with_template,
    extract_template,
    get_embedded_template,
    list_templates,
    render_template,
    template_exists,
)
from speckit.core.utils import (
    atomic_write,
    count_lines,
    ensure_dir,
    generate_chain_id,
    get_file_info,
    get_relative_path,
    get_repo_root,
    is_git_repo,
    run_command,
    safe_json_dumps,
    safe_json_loads,
)

__all__ = [
    # Emit system
    "emit_stage",
    "emit_chunk",
    "emit_complete",
    "emit_error",
    "emit_template",
    # Configuration
    "Config",
    # Utilities
    "get_repo_root",
    "generate_chain_id",
    "safe_json_loads",
    "safe_json_dumps",
    "run_command",
    "is_git_repo",
    "get_file_info",
    "ensure_dir",
    "atomic_write",
    "get_relative_path",
    "count_lines",
    # Templates
    "get_embedded_template",
    "extract_template",
    "template_exists",
    "list_templates",
    "render_template",
    "emit_with_template",
    # Prompts
    "get_prompt_fragment",
    "render_prompt",
    "list_fragments",
    "get_stage_order",
    "fragment_exists",
    "get_next_stage",
    "count_fragment_lines",
    # State types
    "RepoixMode",
]
