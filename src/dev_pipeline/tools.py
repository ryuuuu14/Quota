"""Tool wrappers for dev pipeline agents, redirected to agent_core."""

import os
from agent_core.llm import GeminiPool, _mock_llm
from agent_core.tools import (
    read_file,
    write_file,
    edit_file,
    glob_files,
    grep_files,
    grep_src,
    inspect_db,
    run_tests,
    check_syntax,
    WORKSPACE_ROOT,
    PROJECT_ROOT,
    SRC_DIR
)

def call_llm(system_prompt: str, user_prompt: str, model: str = "gemini-2.5-flash") -> str:
    """Call LLM utilizing GeminiPool."""
    complexity = "planning" if "plan" in system_prompt.lower() or "design" in system_prompt.lower() else "default"
    return GeminiPool.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        complexity=complexity,
        pipeline_name="dev_pipeline",
        agent_name="dev_agent",
        model_override=model
    )
