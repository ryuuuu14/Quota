from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from agent_core.llm import GeminiPool

MAX_RETRIES = 2


# Define State
class PipelineState(TypedDict):
    prompt: str
    style_guide: str
    code: str
    qa_passed: bool
    qa_feedback: str
    review_passed: bool
    review_feedback: str
    retry_count: int


# Agent Implementations


def designer_agent(state: PipelineState) -> dict:
    print("Designer Agent analyzing taste...")
    system_prompt = (
        "You are a UI Designer Agent. Given a user request, output a terse, bulleted style guide for a Streamlit app. "
        "Focus on layout, colors, elements, and modern taste."
    )
    user_prompt = f"User request: {state['prompt']}"
    style_guide = GeminiPool.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        complexity="default",
        pipeline_name="ui_design_pipeline",
        agent_name="designer",
    )
    print("Style guide generated.")
    return {"style_guide": style_guide}


def coder_agent(state: PipelineState) -> dict:
    new_retry_count = state.get("retry_count", 0) + 1
    print(f"Coder Agent writing Streamlit UI (Attempt {new_retry_count})...")

    # Construct full context prompt
    context = f"Build a Streamlit app. Context: {state['prompt']}\n\nStyle:\n{state.get('style_guide', '')}"
    if not state.get("qa_passed", True):
        context += f"\nFix QA issues: {state.get('qa_feedback')}"
    if not state.get("review_passed", True):
        context += f"\nFix Review issues: {state.get('review_feedback')}"

    system_prompt = (
        "You are an expert Python Streamlit developer. Output ONLY a valid Python code block with the Streamlit app. "
        "Do not include explanations."
    )
    generated_code = GeminiPool.call(
        system_prompt=system_prompt,
        user_prompt=context,
        complexity="planning" if new_retry_count == 1 else "default",
        pipeline_name="ui_design_pipeline",
        agent_name="coder",
    )

    # Strip markdown block quotes if present
    if generated_code.startswith("```python"):
        generated_code = generated_code.split("```python")[1].split("```")[0].strip()
    elif generated_code.startswith("```"):
        generated_code = generated_code.split("```")[1].split("```")[0].strip()

    print("Code built successfully via LLM.")
    return {"code": generated_code, "retry_count": new_retry_count}


def qa_agent(state: PipelineState) -> dict:
    print("QA Agent checking functionality...")
    system_prompt = (
        "You are a QA Agent. Review this Streamlit code. If it has syntax errors, missing imports, "
        "or lacks functionality, reply with 'FAIL: <reason>'. If good, reply 'PASS'."
    )
    user_prompt = f"Code:\n```python\n{state.get('code', '')}\n```"
    response = GeminiPool.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        complexity="default",
        pipeline_name="ui_design_pipeline",
        agent_name="qa",
    )

    if response.strip().startswith("PASS"):
        return {"qa_passed": True, "qa_feedback": ""}
    else:
        return {"qa_passed": False, "qa_feedback": response}


def review_agent(state: PipelineState) -> dict:
    print("Review Agent checking code quality...")
    system_prompt = (
        "You are a Code Review Agent. Review this Streamlit code for best practices and security. "
        "If bad, reply 'FAIL: <reason>'. If good, reply 'PASS'."
    )
    user_prompt = f"Code:\n```python\n{state.get('code', '')}\n```"
    response = GeminiPool.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        complexity="default",
        pipeline_name="ui_design_pipeline",
        agent_name="reviewer",
    )

    if response.strip().startswith("PASS"):
        return {"review_passed": True, "review_feedback": ""}
    else:
        return {"review_passed": False, "review_feedback": response}


def merge_node(state: PipelineState) -> dict:
    print("Merging parallel QA and Review results...")
    # This is a synchronization point for parallel branches.
    # It just returns an empty dict because the state is already updated with qa_passed/review_passed by the parallel nodes.
    return {}


def router(state: PipelineState) -> Literal["build", "end"]:
    """Route back to build if QA/Review fail, else end."""
    if state.get("qa_passed", True) and state.get("review_passed", True):
        print("All checks passed.")
        return "end"

    if state.get("retry_count", 0) > MAX_RETRIES:
        print("Max retries reached. Forcing end to save tokens.")
        return "end"

    print(
        f"Checks failed. Retrying (Attempt {state.get('retry_count', 0)} / {MAX_RETRIES})..."
    )
    return "build"


# Build LangGraph
workflow = StateGraph(PipelineState)

workflow.add_node("designer", designer_agent)
workflow.add_node("coder", coder_agent)
workflow.add_node("qa", qa_agent)
workflow.add_node("review", review_agent)
workflow.add_node("merge", merge_node)

workflow.set_entry_point("designer")
workflow.add_edge("designer", "coder")

# Fan-out to QA and Review in parallel from coder
workflow.add_edge("coder", "qa")
workflow.add_edge("coder", "review")

# Fan-in from QA and Review to merge node
workflow.add_edge("qa", "merge")
workflow.add_edge("review", "merge")

workflow.add_conditional_edges("merge", router, {"build": "coder", "end": END})

pipeline_app = workflow.compile()

if __name__ == "__main__":
    initial_state = {
        "prompt": "Create a data dashboard showing user metrics.",
        "style_guide": "",
        "code": "",
        "qa_passed": True,
        "qa_feedback": "",
        "review_passed": True,
        "review_feedback": "",
        "retry_count": 0,
    }

    print("Starting LangGraph Pipeline...")
    final_state = pipeline_app.invoke(initial_state)
    print("\nPipeline Finished.")
    print("Final Code Output:")
    print("--------------------------------------------------")
    print(final_state["code"])
    print("--------------------------------------------------")
