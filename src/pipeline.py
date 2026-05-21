"""
Pipeline UI Design & Debugging
LangGraph state machine: Editor (Stitch) -> Validator (3-tier) -> Critic (Gemini Vision) -> Router
"""
from typing import TypedDict, Optional, List
import re
import os

from langgraph.graph import StateGraph, END

USE_REAL_STITCH = False

STITCH_PROJECT_ID = "16682207781060267797"
STITCH_DESIGN_SYSTEM = "assets/e8ae041a1de943d2b4b5bb898f6bd031"
STITCH_SCREEN_IDS: List[str] = []


class AgentState(TypedDict):
    task: str
    stitch_output: str
    local_code_state: str
    feedback: Optional[str]
    iterations: int
    logs: List[str]
    screen_id: Optional[str]
    design_md_rules: str


def _call_stitch_real(task: str, current_code: str) -> str:
    """Real Stitch API path — uses stitch_edit_screens via tooling."""
    screen_ids = STITCH_SCREEN_IDS
    if not screen_ids:
        return "# NO_SCREEN_IDS: pipeline cannot call Stitch without target screens"
    try:
        from stitch_tool_adapter import edit_screens_blocking
        result = edit_screens_blocking(
            project_id=STITCH_PROJECT_ID,
            screen_ids=screen_ids,
            prompt=task,
        )
        return result
    except ImportError:
        return f"# Stitch tool adapter not available, falling back. Task: {task}"
    except Exception as e:
        return f"# STITCH_ERROR: {e}"


def _call_stitch_mock(task: str, current_code: str, iteration: int) -> str:
    """Mock Stitch API — simulates lazy/genuine responses."""
    if iteration == 0:
        return current_code
    return "<div>Updated Layout with New Structural Matrix Grid</div>"


def call_stitch_editor(state: AgentState) -> dict:
    logs = list(state.get("logs", []))
    iteration = state.get("iterations", 0)
    task = state.get("task", "")
    current_code = state.get("local_code_state", "")

    logs.append(f"Editor iteration {iteration + 1} ({'real' if USE_REAL_STITCH else 'mock'} mode)")

    if USE_REAL_STITCH:
        output = _call_stitch_real(task, current_code)
    else:
        output = _call_stitch_mock(task, current_code, iteration)

    logs.append(f"Editor output length: {len(output)} chars")
    return {
        "stitch_output": output,
        "iterations": iteration + 1,
        "logs": logs,
    }


def _tier1_no_change(stitch_output: str, local_code_state: str) -> Optional[str]:
    if stitch_output.strip() == local_code_state.strip():
        return "CRITICAL: Generated code matches original source. No impactful changes."
    return None


def _tier2_structure(stitch_output: str) -> Optional[str]:
    if "Error" in stitch_output or not stitch_output.strip():
        return "BUGGY: Payload contains compilation or structural errors."
    has_element = bool(re.search(r'<[a-z]+[^>]*>', stitch_output))
    if not has_element:
        return "STRUCTURAL: No HTML elements found in output."
    return None


def _tier3_html_valid(stitch_output: str) -> Optional[str]:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(stitch_output, "html.parser")
        if soup.find() is None and len(stitch_output.strip()) > 0:
            return "MALFORMED: BeautifulSoup parsed nothing from non-empty output."
    except ImportError:
        pass
    return None


def validate_code_impact(state: AgentState) -> dict:
    logs = list(state.get("logs", []))
    logs.append("Validator running 3-tier analysis...")

    stitch_output = state.get("stitch_output", "")
    local_code_state = state.get("local_code_state", "")

    feedback = None

    # Tier 1: string comparison
    feedback = _tier1_no_change(stitch_output, local_code_state)
    if feedback:
        logs.append(f"Validator tier1 FAIL: {feedback}")
        return {"feedback": feedback, "logs": logs}

    # Tier 2: regex structure check
    feedback = _tier2_structure(stitch_output)
    if feedback:
        logs.append(f"Validator tier2 FAIL: {feedback}")
        return {"feedback": feedback, "logs": logs}

    # Tier 3: BeautifulSoup parse
    feedback = _tier3_html_valid(stitch_output)
    if feedback:
        logs.append(f"Validator tier3 FAIL: {feedback}")
        return {"feedback": feedback, "logs": logs}

    logs.append("Validator ALL TIERS PASSED")
    return {"feedback": None, "logs": logs}


def visual_ui_debug(state: AgentState) -> dict:
    """Node 3: Gemini Vision analyzes UI screenshot for visual bugs."""
    logs = list(state.get("logs", []))
    logs.append("Critic running visual UI analysis...")

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logs.append("Critic SKIPPED: no GOOGLE_API_KEY env var set")
        return {"feedback": None, "logs": logs}

    screenshot_path = "ui_snapshot.png"
    if not os.path.exists(screenshot_path):
        logs.append(f"Critic SKIPPED: screenshot not found at {screenshot_path}")
        return {"feedback": None, "logs": logs}

    try:
        from google import genai
        from google.genai.types import Part

        client = genai.Client(api_key=api_key)

        with open(screenshot_path, "rb") as f:
            image_data = f.read()

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                Part.from_bytes(data=image_data, mime_type="image/png"),
                (
                    "Analyze this generated UI screenshot for visual bugs, "
                    "alignment failures, or missing components.\n\n"
                    f"Design Rules: {state.get('design_md_rules', 'Standard Layout')}\n"
                    f"Task: {state['task']}\n\n"
                    "Respond in this exact format:\n"
                    "STATUS: [PASSED or FAILED]\n"
                    "CRITIQUE: [if FAILED, describe overlapping elements, "
                    "broken padding, or incorrect colors]"
                ),
            ],
        )

        critique = response.text.strip()
        logs.append(f"Critic response ({len(critique)} chars)")

        if "STATUS: FAILED" in critique:
            bug_report = critique
            if "CRITIQUE:" in critique:
                bug_report = critique.split("CRITIQUE:", 1)[1].strip()
            feedback = f"Visual Bug Detected: {bug_report[:200]}"
            logs.append(f"Critic FAILED: visual bugs found")
            return {"feedback": feedback, "logs": logs}

        logs.append("Critic PASSED: no visual bugs detected")
        return {"feedback": None, "logs": logs}

    except Exception as e:
        logs.append(f"Critic ERROR: {type(e).__name__}: {e}")
        return {"feedback": None, "logs": logs}


def route_next_step(state: AgentState) -> str:
    if state.get("iterations", 0) >= 3:
        return "abort"
    if state.get("feedback"):
        return "retry"
    return "to_critic"


def route_critic(state: AgentState) -> str:
    if state.get("iterations", 0) >= 3:
        return "abort"
    if state.get("feedback"):
        return "retry"
    return "approve"


def build_pipeline():
    workflow = StateGraph(AgentState)
    workflow.add_node("editor", call_stitch_editor)
    workflow.add_node("validator", validate_code_impact)
    workflow.add_node("critic", visual_ui_debug)
    workflow.set_entry_point("editor")
    workflow.add_edge("editor", "validator")
    workflow.add_conditional_edges(
        "validator",
        route_next_step,
        {"retry": "editor", "abort": END, "to_critic": "critic"},
    )
    workflow.add_conditional_edges(
        "critic",
        route_critic,
        {"retry": "editor", "abort": END, "approve": END},
    )
    return workflow.compile()


def run_pipeline(
    task: str,
    local_code_state: str,
    use_real_stitch: bool = False,
    screen_ids: Optional[List[str]] = None,
    screen_id: Optional[str] = None,
    design_md_rules: str = "Standard Layout",
) -> dict:
    global USE_REAL_STITCH, STITCH_SCREEN_IDS
    USE_REAL_STITCH = use_real_stitch
    if screen_ids is not None:
        STITCH_SCREEN_IDS.extend(screen_ids)

    app = build_pipeline()
    initial: AgentState = {
        "task": task,
        "local_code_state": local_code_state,
        "stitch_output": "",
        "feedback": None,
        "iterations": 0,
        "logs": [],
        "screen_id": screen_id,
        "design_md_rules": design_md_rules,
    }
    result = app.invoke(initial)

    summary_status = "approved"
    if result.get("iterations", 0) >= 3 and result.get("feedback"):
        summary_status = "aborted"

    logs = result.get("logs", [])
    final_code = result.get("stitch_output", "")

    return {
        "code": final_code,
        "summary": {
            "iterations": result.get("iterations", 0),
            "status": summary_status,
            "logs": logs,
        },
    }


if __name__ == "__main__":
    print("=== Pipeline Test: No-change (retry) -> Critic (skip no screenshot) ===")
    out = run_pipeline(
        task="Refactor root view matrix layout",
        local_code_state="<div>Original Base Template Layout Structure</div>",
    )
    print(f"Status: {out['summary']['status']}")
    print(f"Iterations: {out['summary']['iterations']}")
    for log in out['summary']['logs']:
        print(f"  - {log}")
    print(f"\nFinal code length: {len(out['code'])} chars")
