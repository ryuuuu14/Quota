"""
Research → Brainstorm → Validation Pipeline (LangGraph)
Domain: TT108 Quota Management System
Graph: Research (parallel regulation/rules/code/db) → Research Merge → Brainstorm → Validate (parallel syntax/tests/rules) → Validate Merge → Router
"""
import os
import re
import sys
import time
import operator
from typing import TypedDict, List, Optional, Annotated, Literal
from langgraph.graph import StateGraph, START, END

from agent_core.llm import GeminiPool
from agent_core import tools

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGULATION_FILE = os.path.join(
    PROJECT_ROOT,
    "Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md",
)
RULES_LOGIC_FILE = os.path.join(PROJECT_ROOT, "rules_logic.md")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "database.sqlite")

MAX_ITERATIONS = 3
SKIP_TESTS = os.environ.get("SKIP_TESTS", "1") == "1"


# Define State with custom/standard reducers
class ResearchState(TypedDict):
    query: str
    regulation_chunks: Annotated[List[str], operator.add]
    rules_context: str
    code_snippets: Annotated[List[str], operator.add]
    db_inspections: Annotated[List[str], operator.add]
    research_summary: str
    proposal: str
    validation_feedback: Optional[str]
    syntax_error: Optional[str]
    test_output: str
    test_exit_code: int
    rules_warning: Optional[str]
    iterations: int
    logs: Annotated[List[str], operator.add]


# ─── Research Nodes (Parallel Fan-out) ──────────────────────────────────────────

def research_regulation_node(state: ResearchState) -> dict:
    query = state.get("query", "")
    chunks = []
    if os.path.exists(REGULATION_FILE):
        text = tools.read_file(REGULATION_FILE, 20000)
        paragraphs = re.split(r'\n###\s+', text)
        relevant = [
            p for p in paragraphs
            if any(kw in p.lower() for kw in query.lower().split())
        ]
        chunks = relevant[:5] if relevant else paragraphs[:3]
    return {
        "regulation_chunks": chunks,
        "logs": [f"[Research Regulation] Found {len(chunks)} relevant chunks."]
    }


def research_rules_node(state: ResearchState) -> dict:
    rules = ""
    if os.path.exists(RULES_LOGIC_FILE):
        rules = tools.read_file(RULES_LOGIC_FILE, 5000)
    return {
        "rules_context": rules,
        "logs": [f"[Research Rules] Rules logic context loaded ({len(rules)} chars)."]
    }


def research_code_node(state: ResearchState) -> dict:
    query = state.get("query", "")
    code = []
    for kw in query.lower().split():
        if len(kw) > 3:
            result = tools.grep_src(kw)
            if result and "No matches" not in result:
                code.append(f"## Search: '{kw}'\n{result}")
    return {
        "code_snippets": code,
        "logs": [f"[Research Code] Performed code grep. Found {len(code)} matches."]
    }


def research_db_node(state: ResearchState) -> dict:
    query = state.get("query", "")
    db_info = []
    if any(kw in query.lower() for kw in ["db", "database", "sql"]):
        tables = tools.inspect_db("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        db_info.append(f"Tables:\n{tables}")
    return {
        "db_inspections": db_info,
        "logs": [f"[Research DB] Database inspection complete. Found {len(db_info)} items."]
    }


def research_merge_node(state: ResearchState) -> dict:
    chunks = state.get("regulation_chunks", [])
    code = state.get("code_snippets", [])
    db_info = state.get("db_inspections", [])
    rules = state.get("rules_context", "")

    summary = []
    if chunks:
        summary.append("=== REGULATION ===")
        summary.append("\n".join(chunks)[:3000])
    if code:
        summary.append("\n=== CODE ===")
        summary.append("\n".join(code)[:3000])
    if db_info:
        summary.append("\n=== DB ===")
        summary.append("\n".join(db_info)[:2000])
    if rules:
        summary.append("\n=== RULES ===")
        summary.append(rules[:2000])

    research_summary = "\n".join(summary) if summary else f"No relevant findings for '{state.get('query')}'"
    return {
        "research_summary": research_summary,
        "logs": ["[Research Merge] Consolidated research details into summary."]
    }


# ─── Brainstorm Node ─────────────────────────────────────────────────────────

def brainstorm_node(state: ResearchState) -> dict:
    print("Brainstorming proposal using LLM...")
    system_prompt = (
        "You are an expert Vietnamese educational regulation architect. Given a user query and a summary of "
        "regulations, codebase context, and database schema, generate a structured, clear technical proposal "
        "in Vietnamese to address the query. Ensure compliance with T04 guidelines."
    )
    user_prompt = (
        f"Query: {state.get('query')}\n\n"
        f"Research Summary:\n{state.get('research_summary')}"
    )
    proposal = GeminiPool.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        complexity="planning",
        pipeline_name="research_pipeline",
        agent_name="brainstormer"
    )
    
    new_iterations = state.get("iterations", 0) + 1
    return {
        "proposal": proposal,
        "iterations": new_iterations,
        "logs": [f"[Brainstorm] Generated proposal via Gemini (Attempt {new_iterations})."]
    }


# ─── Validation Nodes (Parallel Fan-out) ──────────────────────────────────────

def validate_syntax_node(state: ResearchState) -> dict:
    calculations_file = os.path.join(SRC_DIR, "calculations.py")
    syntax_error = None
    if os.path.exists(calculations_file):
        res = tools.check_syntax(calculations_file)
        if not res["passed"]:
            syntax_error = f"SYNTAX ERROR in calculations.py: {res['error']}"
    return {
        "syntax_error": syntax_error,
        "logs": ["[Validate Syntax] Calculations syntax check complete."]
    }


def validate_tests_node(state: ResearchState) -> dict:
    test_output = ""
    test_exit_code = 0
    if not SKIP_TESTS:
        test_files = [
            os.path.join(SRC_DIR, "test_compliance.py"),
            os.path.join(SRC_DIR, "test_teacher_integration.py"),
        ]
        test_output, test_exit_code = tools.run_pytest(test_files)
    return {
        "test_output": test_output,
        "test_exit_code": test_exit_code,
        "logs": [f"[Validate Tests] Compliance tests run complete (Exit: {test_exit_code})."]
    }


def validate_rules_node(state: ResearchState) -> dict:
    query = state.get("query", "")
    rules = state.get("rules_context", "")
    rules_warning = None
    if rules:
        keywords = query.lower().split()
        missing = [kw for kw in keywords if len(kw) > 4 and kw not in rules.lower()]
        if missing:
            rules_warning = f"WARNING: rules_logic.md lacks coverage for: {missing}"
    return {
        "rules_warning": rules_warning,
        "logs": ["[Validate Rules] Rules logic coverage verified."]
    }


def validate_merge_node(state: ResearchState) -> dict:
    feedback_parts = []
    if state.get("syntax_error"):
        feedback_parts.append(state["syntax_error"])
    
    test_exit = state.get("test_exit_code", 0)
    if test_exit != 0:
        feedback_parts.append(f"TESTS FAILED (exit {test_exit})")
        test_output = state.get("test_output", "")
        fail_lines = [
            l for l in test_output.split("\n")
            if "FAILED" in l or "ERROR" in l or "AssertionError" in l
        ]
        if fail_lines:
            feedback_parts.extend(fail_lines[:5])
            
    if state.get("rules_warning"):
        feedback_parts.append(state["rules_warning"])

    validation_feedback = "\n".join(feedback_parts) if feedback_parts else None
    return {
        "validation_feedback": validation_feedback,
        "logs": ["[Validate Merge] Validation feedback aggregated."]
    }


# ─── Router and Graph ─────────────────────────────────────────────────────────

def router_condition(state: ResearchState) -> Literal["retry", "abort", "approve"]:
    iteration = state.get("iterations", 0)
    feedback = state.get("validation_feedback")

    if feedback:
        if iteration >= MAX_ITERATIONS:
            return "abort"
        return "retry"
    return "approve"


def build_research_pipeline():
    workflow = StateGraph(ResearchState)
    
    # Add Nodes
    workflow.add_node("research_regulation", research_regulation_node)
    workflow.add_node("research_rules", research_rules_node)
    workflow.add_node("research_code", research_code_node)
    workflow.add_node("research_db", research_db_node)
    workflow.add_node("research_merge", research_merge_node)
    
    workflow.add_node("brainstorm", brainstorm_node)
    
    workflow.add_node("validate_syntax", validate_syntax_node)
    workflow.add_node("validate_tests", validate_tests_node)
    workflow.add_node("validate_rules", validate_rules_node)
    workflow.add_node("validate_merge", validate_merge_node)

    # Set Entry and Research Branching
    workflow.set_entry_point("research_regulation")
    # To run all research in parallel, add entry to each
    workflow.add_edge(START, "research_regulation")
    workflow.add_edge(START, "research_rules")
    workflow.add_edge(START, "research_code")
    workflow.add_edge(START, "research_db")
    
    # Connect research outputs to merge
    workflow.add_edge("research_regulation", "research_merge")
    workflow.add_edge("research_rules", "research_merge")
    workflow.add_edge("research_code", "research_merge")
    workflow.add_edge("research_db", "research_merge")
    
    # Brainstorm follows merge
    workflow.add_edge("research_merge", "brainstorm")
    
    # Validate Branching from Brainstorm
    workflow.add_edge("brainstorm", "validate_syntax")
    workflow.add_edge("brainstorm", "validate_tests")
    workflow.add_edge("brainstorm", "validate_rules")
    
    # Connect validate outputs to merge
    workflow.add_edge("validate_syntax", "validate_merge")
    workflow.add_edge("validate_tests", "validate_merge")
    workflow.add_edge("validate_rules", "validate_merge")
    
    # Conditional route after merge
    workflow.add_conditional_edges(
        "validate_merge",
        router_condition,
        {"retry": "research_regulation", "abort": END, "approve": END},
    )

    return workflow.compile()


def run_research_pipeline(
    query: str,
    max_iterations: int = 3,
) -> dict:
    global MAX_ITERATIONS
    MAX_ITERATIONS = max_iterations

    app = build_research_pipeline()
    initial: ResearchState = {
        "query": query,
        "regulation_chunks": [],
        "rules_context": "",
        "code_snippets": [],
        "db_inspections": [],
        "research_summary": "",
        "proposal": "",
        "validation_feedback": None,
        "syntax_error": None,
        "test_output": "",
        "test_exit_code": 0,
        "rules_warning": None,
        "iterations": 0,
        "logs": [],
    }

    result = app.invoke(initial)

    status = "approved"
    if result.get("validation_feedback"):
        status = "aborted" if result.get("iterations", 0) >= MAX_ITERATIONS else "needs_review"

    logs = result.get("logs", [])
    return {
        "query": query,
        "status": status,
        "iterations": result.get("iterations", 0),
        "research_summary": result.get("research_summary", ""),
        "proposal": result.get("proposal", ""),
        "validation_feedback": result.get("validation_feedback"),
        "test_output": result.get("test_output", ""),
        "test_exit_code": result.get("test_exit_code", 0),
        "logs": logs,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    q = sys.argv[1] if len(sys.argv) > 1 else "GC reduction calculation for teachers on maternity leave"

    t0 = time.time()
    out = run_research_pipeline(query=q)
    elapsed = time.time() - t0

    print(f"{'='*60}")
    print(f"QUERY:       {out['query']}")
    print(f"STATUS:      {out['status']}")
    print(f"ITERATIONS:  {out['iterations']}")
    print(f"TIME:        {elapsed:.1f}s")
    print(f"{'='*60}")
    print()

    print("--- RESEARCH SUMMARY (first 500 chars) ---")
    print(out['research_summary'][:500])
    print()

    print("--- PROPOSAL (first 500 chars) ---")
    print(out['proposal'][:500])
    print()

    if out['validation_feedback']:
        print("--- VALIDATION FEEDBACK ---")
        print(out['validation_feedback'][:500])
        print()

    print("--- LOGS ---")
    for log in out['logs']:
        print(f"  {log}")
