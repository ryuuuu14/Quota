from typing import TypedDict, List, Annotated
import operator


class DevState(TypedDict):
    task: str
    plan: str
    plan_approved: bool
    plan_feedback: str
    build_summary: str
    test_output: str
    test_passed: bool
    validation_report: str
    validation_passed: bool
    iteration: int
    max_iterations: int
    error_context: str
    final_result: str
    logs: Annotated[List[str], operator.add]
    """logs uses Annotated reducer so multiple updates per step merge correctly."""
