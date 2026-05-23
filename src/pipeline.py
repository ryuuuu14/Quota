import os
import requests
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from google import genai
from pydantic import BaseModel, Field

MAX_RETRIES = 2

# Check for Gemini API key for the agents (Designer, QA, Review)
# Assumes GEMINI_API_KEY is set in environment for the LLM agents.
try:
    client = genai.Client()
except Exception:
    client = None

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
def call_llm(system_instruction: str, user_prompt: str) -> str:
    """Helper to call Gemini for agent tasks."""
    if not client:
        return "LLM Mock Response. Set GEMINI_API_KEY to enable."
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config={'system_instruction': system_instruction}
        )
        return response.text
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

def designer_agent(state: PipelineState) -> PipelineState:
    print("Designer Agent analyzing taste...")
    system_prompt = "You are a UI Designer Agent. Given a user request, output a terse, bulleted style guide for a Streamlit app. Focus on layout, colors, elements, and modern taste."
    style_guide = call_llm(system_prompt, f"User request: {state['prompt']}")
    state["style_guide"] = style_guide
    print("Style guide generated.")
    return state

def coder_agent(state: PipelineState) -> PipelineState:
    state["retry_count"] = state.get("retry_count", 0) + 1
    print("Coder Agent writing Streamlit UI...")
    
    # Construct full context prompt
    context = f"Build a Streamlit app. Context: {state['prompt']}\\n\\nStyle:\\n{state['style_guide']}"
    if not state.get("qa_passed", True):
        context += f"\\nFix QA issues: {state.get('qa_feedback')}"
    if not state.get("review_passed", True):
        context += f"\\nFix Review issues: {state.get('review_feedback')}"
        
    system_prompt = "You are an expert Python Streamlit developer. Output ONLY valid Python code block with the Streamlit app. Do not include explanations."
    generated_code = call_llm(system_prompt, context)
    
    # Strip markdown block quotes if present
    if generated_code.startswith("```python"):
        generated_code = generated_code.split("```python")[1].split("```")[0].strip()
    elif generated_code.startswith("```"):
        generated_code = generated_code.split("```")[1].split("```")[0].strip()
        
    state["code"] = generated_code
    print("Code built successfully via LLM.")
    return state

def qa_agent(state: PipelineState) -> PipelineState:
    print("QA Agent checking functionality...")
    system_prompt = "You are a QA Agent. Review this Streamlit code. If it has syntax errors, missing imports, or lacks functionality, reply with 'FAIL: <reason>'. If good, reply 'PASS'."
    response = call_llm(system_prompt, f"Code:\\n```python\\n{state['code']}\\n```")
    
    if response.startswith("PASS"):
        state["qa_passed"] = True
        state["qa_feedback"] = ""
    else:
        state["qa_passed"] = False
        state["qa_feedback"] = response
    return state

def review_agent(state: PipelineState) -> PipelineState:
    print("Review Agent checking code quality...")
    system_prompt = "You are a Code Review Agent. Review this Streamlit code for best practices and security. If bad, reply 'FAIL: <reason>'. If good, reply 'PASS'."
    response = call_llm(system_prompt, f"Code:\\n```python\\n{state['code']}\\n```")
    
    if response.startswith("PASS"):
        state["review_passed"] = True
        state["review_feedback"] = ""
    else:
        state["review_passed"] = False
        state["review_feedback"] = response
    return state

def router(state: PipelineState) -> Literal["build", "end"]:
    """Route back to build if QA/Review fail, else end."""
    if state.get("qa_passed", True) and state.get("review_passed", True):
        print("All checks passed.")
        return "end"
    
    if state.get("retry_count", 0) > MAX_RETRIES:
        print("Max retries reached. Forcing end to save tokens.")
        return "end"
        
    print(f"Checks failed. Retrying (Attempt {state.get('retry_count', 0)} / {MAX_RETRIES})...")
    return "build"

# Build LangGraph
workflow = StateGraph(PipelineState)

workflow.add_node("designer", designer_agent)
workflow.add_node("coder", coder_agent)
workflow.add_node("qa", qa_agent)
workflow.add_node("review", review_agent)

workflow.set_entry_point("designer")
workflow.add_edge("designer", "coder")
workflow.add_edge("coder", "qa")
workflow.add_edge("qa", "review")
workflow.add_conditional_edges(
    "review",
    router,
    {"build": "coder", "end": END}
)

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
        "retry_count": 0
    }
    
    print("Starting LangGraph Pipeline...")
    final_state = pipeline_app.invoke(initial_state)
    print("\\nPipeline Finished.")
    print("Final Code Output:")
    print("--------------------------------------------------")
    print(final_state["code"])
    print("--------------------------------------------------")
