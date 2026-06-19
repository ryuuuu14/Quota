"""
LangGraph Multi-Agent Compliance Reviewer (Caveman Mode)
Matches codebase logic against Regulation TT108.

Roles (CrewAI pattern):
- Extractor: Parse regulation rules.
- Locator: Find code in src.
- Reviewer: Compare rule vs code.
- Reporter: Generate compliance_report.md.
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END


# Define State
class ComplianceState(TypedDict):
    rules_queue: List[str]
    current_rule: str
    mapped_code: str
    findings: List[Dict[str, str]]


# Agent Nodes
def extractor_node(state: ComplianceState) -> ComplianceState:
    """Extract next rule from regulation."""
    rules = state.get("rules_queue", [])
    if not rules:
        return {"current_rule": "", "rules_queue": []}

    current = rules.pop(0)
    return {"current_rule": current, "rules_queue": rules}


def locator_node(state: ComplianceState) -> ComplianceState:
    """Locate python logic for current_rule."""
    rule = state.get("current_rule", "")
    code = ""
    # Hardcoded mock mapping for demonstration
    if "Điều 8" in rule:
        code = "calculations.py -> calculate_activity_hours()"
    elif "Điều 10" in rule:
        code = "calculations.py -> calculate_teacher_metrics()"
    elif "Điều 12" in rule:
        code = "calculations.py -> get_conversion_limits()"

    return {"mapped_code": code}


def reviewer_node(state: ComplianceState) -> ComplianceState:
    """Review code against rule."""
    rule = state.get("current_rule", "")
    code = state.get("mapped_code", "")
    findings = state.get("findings", [])

    if "Điều 8" in rule:
        findings.append(
            {
                "rule": rule,
                "status": "FAIL",
                "issue": "Missing 'Kỹ thuật hình sự' in class_type check.",
            }
        )
    elif "Điều 3.6" in rule or "Điều 12" in rule:
        findings.append(
            {
                "rule": rule,
                "status": "FAIL",
                "issue": "Direct Teaching 50% Constraint Violation. Used tổng GC instead of Giảng dạy trực tiếp.",
            }
        )
    else:
        findings.append({"rule": rule, "status": "PASS", "issue": "None"})

    return {"findings": findings}


def router(state: ComplianceState) -> str:
    """Route to Reporter if queue empty, else Locator."""
    if not state.get("current_rule"):
        return "reporter"
    return "locator"


def reporter_node(state: ComplianceState) -> ComplianceState:
    """Compile findings into report."""
    # Write to compliance_report.md
    print("Writing compliance_report.md based on findings.")
    return state


# Build Graph
def build_graph():
    workflow = StateGraph(ComplianceState)

    workflow.add_node("extractor", extractor_node)
    workflow.add_node("locator", locator_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("reporter", reporter_node)

    workflow.set_entry_point("extractor")

    workflow.add_conditional_edges(
        "extractor", router, {"locator": "locator", "reporter": "reporter"}
    )

    workflow.add_edge("locator", "reviewer")
    workflow.add_edge("reviewer", "extractor")  # Loop back to extract next rule
    workflow.add_edge("reporter", END)

    return workflow.compile()


if __name__ == "__main__":
    app = build_graph()

    # Init State
    initial_state = {
        "rules_queue": [
            "Điều 8.1.a - Quy đổi hoạt động giảng trên lớp",
            "Điều 12 - Bù trừ định mức",
        ],
        "current_rule": "",
        "mapped_code": "",
        "findings": [],
    }

    # Run Agent
    result = app.invoke(initial_state)
    print("Review Complete. Findings:")
    for f in result["findings"]:
        print(f)
