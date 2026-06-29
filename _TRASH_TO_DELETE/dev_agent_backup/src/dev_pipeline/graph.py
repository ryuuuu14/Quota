"""LangGraph state machine for Build -> Test -> Validate dev loop.

Graph structure with 3 human-in-loop interrupts:

    START
      │
      ▼
    [plan] ── interrupt 1: human reviews plan
      │  \
      │   (rejected → loop back with feedback)
      ▼
    [build] ── implements code
      │
      ▼
    [test] ── interrupt 2: human reviews test results
      │  \
      │   (rejected → loop back to build with error context)
      ▼
    [validate] ── interrupt 3: human reviews quality
      │  \
      │   (rejected → loop back to build)
      ▼
      END (approved or aborted)
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import DevState
from .agents import plan_node, build_node, test_node, validate_node


# ─── Router Functions ────────────────────────────────────────────────────────


def route_after_plan(state: DevState) -> str:
    """After plan interrupt: route to build, abort, or back to plan."""
    if state.get("final_result") == "ABORTED":
        return "abort"
    if state.get("plan_approved"):
        return "build"
    return "plan"  # retry planning with feedback


def route_after_test(state: DevState) -> str:
    """After test interrupt: route to validate, abort, or back to build."""
    if state.get("final_result") == "ABORTED":
        return "abort"
    if state.get("final_result", "").startswith("MAX ITERATIONS"):
        return "abort"

    if not state.get("test_passed", True) or state.get("error_context"):
        return "build"  # rebuild with error context
    return "validate"


def route_after_validate(state: DevState) -> str:
    """After validate interrupt: route to end or back to build."""
    if state.get("final_result") == "ABORTED":
        return "abort"
    if state.get("final_result", "").startswith("MAX ITERATIONS"):
        return "abort"

    if not state.get("validation_passed") and state.get("error_context"):
        return "build"  # rebuild with feedback
    return "end"


# ─── Build Graph ─────────────────────────────────────────────────────────────


def build_dev_pipeline(checkpointer=None):
    """Build and return the compiled LangGraph pipeline."""
    if checkpointer is None:
        checkpointer = MemorySaver()

    workflow = StateGraph(DevState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("build", build_node)
    workflow.add_node("test", test_node)
    workflow.add_node("validate", validate_node)

    workflow.set_entry_point("plan")

    # Conditional routing
    workflow.add_conditional_edges(
        "plan",
        route_after_plan,
        {"plan": "plan", "build": "build", "abort": END},
    )

    workflow.add_edge("build", "test")

    workflow.add_conditional_edges(
        "test",
        route_after_test,
        {"build": "build", "validate": "validate", "abort": END},
    )

    workflow.add_conditional_edges(
        "validate",
        route_after_validate,
        {"build": "build", "end": END, "abort": END},
    )

    return workflow.compile(checkpointer=checkpointer)
