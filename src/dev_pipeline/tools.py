"""Tool wrappers for dev pipeline agents, redirected to agent_core."""

from agent_core.llm import GeminiPool


def call_llm(
    system_prompt: str, user_prompt: str, model: str = "gemini-2.5-flash"
) -> str:
    """Call LLM utilizing GeminiPool."""
    complexity = (
        "planning"
        if "plan" in system_prompt.lower() or "design" in system_prompt.lower()
        else "default"
    )
    return GeminiPool.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        complexity=complexity,
        pipeline_name="dev_pipeline",
        agent_name="dev_agent",
        model_override=model,
    )
