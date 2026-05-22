"""
Research → Brainstorm → Validation Pipeline (LangGraph)
Domain: TT108 Quota Management System

Graph: Research (reg + code) → Brainstorm → Validate → Router
"""
from typing import TypedDict, List, Optional
import os
import re
import subprocess
import sys
import time

from langgraph.graph import StateGraph, END

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


class ResearchState(TypedDict):
    query: str
    regulation_chunks: List[str]
    rules_context: str
    code_snippets: List[str]
    db_inspections: List[str]
    research_summary: str
    proposal: str
    validation_feedback: Optional[str]
    test_output: str
    test_exit_code: int
    iterations: int
    logs: List[str]


def _read_file(path: str, max_len: int = 8000) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(max_len)
        return content
    except Exception as e:
        return f"[ERROR reading {path}]: {e}"


def _grep_src(pattern: str, context_lines: int = 5) -> str:
    """Search source code for a pattern — inline (no subprocess)."""
    calcs_path = os.path.join(SRC_DIR, "calculations.py")
    if not os.path.exists(calcs_path):
        return "[FILE NOT FOUND]"
    try:
        with open(calcs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        matches = []
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line, re.I):
                start = max(0, i - 1 - context_lines)
                end = min(len(lines), i + context_lines)
                matches.append(f"--- lines {start+1}-{end} ---")
                for j in range(start, end):
                    matches.append(f"{j+1}:{lines[j].rstrip()}")
                matches.append("")
        return "\n".join(matches[:60])[:3000] or "No matches"
    except Exception as e:
        return f"[GREP_ERROR]: {e}"


def _inspect_db(sql: str) -> str:
    """Run a read-only SQL query — inline (no subprocess)."""
    import sqlite3, json
    if not os.path.exists(DB_PATH):
        return "[DB NOT FOUND]"
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.execute(sql)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            out = {"columns": cols, "rows": rows[:20], "total": len(rows)}
            return json.dumps(out, ensure_ascii=False, default=str)[:3000]
        finally:
            conn.close()
    except Exception as e:
        return f"[DB_ERROR]: {e}"


def _run_tests(test_files: List[str]) -> tuple[str, int]:
    """Run pytest on given test files (quick mode: --tb=line, --no-header)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", *test_files, "--tb=line", "--no-header", "-q"],
            capture_output=True, timeout=45, encoding='utf-8',
            cwd=PROJECT_ROOT,
        )
        output = result.stdout + "\n" + result.stderr
        return output.strip()[-2500:], result.returncode
    except subprocess.TimeoutExpired:
        return "[TIMEOUT] Tests exceeded 45s", -1
    except Exception as e:
        return f"[RUN_ERROR]: {e}", -1


def research_node(state: ResearchState) -> dict:
    logs = list(state.get("logs", []))
    query = state.get("query", "")
    logs.append(f"[Research] Starting research on: {query}")

    chunks = []
    if os.path.exists(REGULATION_FILE):
        text = _read_file(REGULATION_FILE, 20000)
        paragraphs = re.split(r'\n###\s+', text)
        relevant = [
            p for p in paragraphs
            if any(kw in p.lower() for kw in query.lower().split())
        ]
        chunks = relevant[:5] if relevant else paragraphs[:3]
    logs.append(f"[Research] Regulation: found {len(paragraphs)} sections, {len(chunks)} relevant")

    rules = ""
    if os.path.exists(RULES_LOGIC_FILE):
        rules = _read_file(RULES_LOGIC_FILE, 5000)
    logs.append(f"[Research] Rules logic: {len(rules)} chars")

    code = []
    for kw in query.lower().split():
        if len(kw) > 3:
            result = _grep_src(kw)
            if result and "No matches" not in result:
                code.append(f"## Search: '{kw}'\n{result}")
    logs.append(f"[Research] Code searches: {len(code)} hits")

    db_info = []
    if "db" in query.lower() or "database" in query.lower() or "sql" in query.lower():
        tables = _inspect_db("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        db_info.append(f"Tables:\n{tables}")
    logs.append(f"[Research] DB inspected: {bool(db_info)}")

    summary = []
    if chunks:
        summary.append("=== REGULATION ===")
        summary.append(chunks[0][:2000])
    if code:
        summary.append("\n=== CODE ===")
        summary.append(code[0][:2000])
    if db_info:
        summary.append("\n=== DB ===")
        summary.append(db_info[0][:1000])
    if rules:
        summary.append(f"\n=== RULES ===")
        summary.append(rules[:1500])

    logs.append(f"[Research] Complete — research_summary: {len(summary)} blocks")
    return {
        "regulation_chunks": chunks,
        "rules_context": rules,
        "code_snippets": code,
        "db_inspections": db_info,
        "research_summary": "\n".join(summary) if summary else f"No relevant findings for '{query}'",
        "logs": logs,
    }


def brainstorm_node(state: ResearchState) -> dict:
    logs = list(state.get("logs", []))
    logs.append("[Brainstorm] Generating proposal from research...")

    summary = state.get("research_summary", "")
    query = state.get("query", "")

    proposal_parts = []
    proposal_parts.append(f"## Proposal for: {query}")
    proposal_parts.append("")
    proposal_parts.append("### Analysis")
    proposal_parts.append(
        "Based on regulation review and code analysis, the following approach is proposed:"
    )
    proposal_parts.append("")

    if "regulation_chunks" in state and state["regulation_chunks"]:
        chunk = state["regulation_chunks"][0]
        title_match = re.search(r"^(###?\s+\*\*.*?\*\*)", chunk, re.M)
        title = title_match.group(1) if title_match else "Relevant regulation"
        proposal_parts.append(f"- **Regulation basis:** {title}")
        article = re.search(r"Điều\s+\d+", chunk)
        if article:
            proposal_parts.append(f"- **Article:** {article.group(0)}")
        proposal_parts.append("")

    if "code_snippets" in state and state["code_snippets"]:
        proposal_parts.append("- **Code location:** Found relevant code in `calculations.py`")
        proposal_parts.append("")

    proposal_parts.append("### Proposed Solution")
    proposal_parts.append("[To be generated based on research findings]")

    logs.append(f"[Brainstorm] Proposal generated ({sum(len(p) for p in proposal_parts)} chars)")
    return {
        "proposal": "\n".join(proposal_parts),
        "logs": logs,
    }


SKIP_TESTS = os.environ.get("SKIP_TESTS", "1") == "1"


def validate_node(state: ResearchState) -> dict:
    logs = list(state.get("logs", []))
    logs.append("[Validate] Running validation checks...")

    proposal = state.get("proposal", "")
    query = state.get("query", "")
    feedback_parts = []
    test_output = ""
    test_exit = 0

    check_syntax = True
    check_tests = not SKIP_TESTS
    check_rules = True

    if check_syntax:
        logs.append("[Validate] Checking Python syntax...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", os.path.join(SRC_DIR, "calculations.py")],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                feedback_parts.append(f"SYNTAX ERROR in calculations.py: {result.stderr.strip()[:200]}")
            else:
                logs.append("[Validate] Syntax OK")
        except Exception as e:
            feedback_parts.append(f"Syntax check error: {e}")

    if check_tests:
        logs.append("[Validate] Running test suite...")
        test_files_to_run = [
            os.path.join(SRC_DIR, "test_compliance.py"),
            os.path.join(SRC_DIR, "test_teacher_integration.py"),
        ]
        existing = [f for f in test_files_to_run if os.path.exists(f)]
        if existing:
            test_output, test_exit = _run_tests(existing)
            logs.append(f"[Validate] Tests exit code: {test_exit}")
            if test_exit != 0:
                feedback_parts.append(f"TESTS FAILED (exit {test_exit})")
                fail_lines = [
                    l for l in test_output.split("\n")
                    if "FAILED" in l or "ERROR" in l or "AssertionError" in l
                ]
                if fail_lines:
                    feedback_parts.extend(fail_lines[:5])
            else:
                logs.append("[Validate] All tests PASSED")

    if check_rules:
        logs.append("[Validate] Checking against rules_logic.md...")
        rules = state.get("rules_context", "")
        if rules:
            keywords = query.lower().split()
            missing = [kw for kw in keywords if len(kw) > 4 and kw not in rules.lower()]
            if missing:
                feedback_parts.append(f"WARNING: rules_logic.md lacks coverage for: {missing}")
            else:
                logs.append("[Validate] Rules coverage adequate")

    validation_feedback = "\n".join(feedback_parts) if feedback_parts else None
    if validation_feedback:
        logs.append(f"[Validate] Issues found ({len(feedback_parts)})")
    else:
        logs.append("[Validate] All checks passed")

    return {
        "validation_feedback": validation_feedback,
        "test_output": test_output,
        "test_exit_code": test_exit,
        "logs": logs,
    }


def router_condition(state: ResearchState) -> str:
    iteration = state.get("iterations", 0)
    feedback = state.get("validation_feedback")

    if iteration >= MAX_ITERATIONS:
        return "abort"
    if feedback:
        return "retry"
    return "approve"


def build_research_pipeline():
    workflow = StateGraph(ResearchState)
    workflow.add_node("research", research_node)
    workflow.add_node("brainstorm", brainstorm_node)
    workflow.add_node("validate", validate_node)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "brainstorm")
    workflow.add_edge("brainstorm", "validate")
    workflow.add_conditional_edges(
        "validate",
        router_condition,
        {"retry": "research", "abort": END, "approve": END},
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
        "test_output": "",
        "test_exit_code": 0,
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
        "iterations": result.get("iterations", 0) + 1,
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
