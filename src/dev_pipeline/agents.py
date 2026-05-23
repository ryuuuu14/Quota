"""LangGraph node functions for the dev pipeline.

Each node returns only NEW log entries (list of strings) since DevState uses
Annotated[list[str], operator.add] reducer for the 'logs' field.
"""

import os
import sys
from datetime import datetime

from langgraph.types import interrupt

from .state import DevState
from .prompts import PLAN_SYSTEM_PROMPT, BUILD_SYSTEM_PROMPT, TEST_SYSTEM_PROMPT, VALIDATE_SYSTEM_PROMPT
from .tools import call_llm, run_tests, read_file, write_file, edit_file, glob_files, grep_files, check_syntax

# __file__ is agents.py at .../src/dev_pipeline/agents.py
# dev_pipeline is inside src/, so workspace root = grandparent of dev_pipeline's parent
A_DIR = os.path.dirname(os.path.abspath(__file__))          # .../src/dev_pipeline
SRC_DIR = os.path.dirname(A_DIR)                             # .../src
WORKSPACE_ROOT = os.path.dirname(SRC_DIR)                    # .../Quota
PROJECT_ROOT = WORKSPACE_ROOT


# ─── Plan Agent ──────────────────────────────────────────────────────────────

def plan_node(state: DevState) -> dict:
    """Analyze task and produce implementation plan. Interrupt for human review."""
    log = []
    task = state.get("task", "")
    feedback = state.get("plan_feedback", "")
    error_ctx = state.get("error_context", "")

    log.append(f"[Plan] Analyzing task: {task}")

    if not state.get("plan_approved") and feedback:
        log.append(f"[Plan] Revising with feedback: {feedback[:100]}")
        user_prompt = f"ORIGINAL TASK: {task}\n\nFEEDBACK TO INCORPORATE: {feedback}"
        if error_ctx:
            user_prompt += f"\n\nPREVIOUS ERROR CONTEXT: {error_ctx}"
    elif not state.get("plan_approved") and error_ctx:
        log.append(f"[Plan] Revising with error context: {error_ctx[:100]}")
        user_prompt = f"ORIGINAL TASK: {task}\n\nERRORS TO FIX: {error_ctx}"
    else:
        user_prompt = task

    plan = call_llm(PLAN_SYSTEM_PROMPT, user_prompt)
    log.append(f"[Plan] Plan generated ({len(plan)} chars)")

    # ── HUMAN IN LOOP ──
    user_input = interrupt({
        "stage": "plan",
        "content": plan,
        "prompt": (
            "\n╔══════════════════════════════════════════════════════════╗\n"
            "║  PLAN REVIEW — Enter:                                  ║\n"
            "║  'approve' to continue                                 ║\n"
            "║  'abort' to cancel                                     ║\n"
            "║  <any text> as revision feedback for re-planning       ║\n"
            "╚══════════════════════════════════════════════════════════╝\n"
            "> "
        ),
    })

    decision = user_input.strip().lower() if isinstance(user_input, str) else ""

    if decision == "approve":
        log.append("[Plan] Approved by human")
        return {"plan": plan, "plan_approved": True, "logs": log}
    elif decision == "abort":
        log.append("[Plan] Aborted by human")
        return {"plan": plan, "plan_approved": False, "final_result": "ABORTED", "logs": log}
    else:
        log.append(f"[Plan] Revision requested: {user_input[:80]}...")
        return {
            "plan": plan, "plan_approved": False,
            "plan_feedback": user_input, "logs": log,
            "iteration": 0,
        }


# ─── Build Agent ─────────────────────────────────────────────────────────────

def build_node(state: DevState) -> dict:
    """Implement the plan by reading and writing files."""
    log = []
    plan = state.get("plan", "")
    feedback = state.get("plan_feedback", "")
    error_ctx = state.get("error_context", "")
    iteration = state.get("iteration", 0) + 1

    log.append(f"[Build] Iteration {iteration} — implementing plan")

    # Read key files for context
    existing_files = {}
    for f in ["src/app.py", "src/database.py", "src/calculations.py", "src/components.py"]:
        fpath = os.path.join(PROJECT_ROOT, f)
        if os.path.exists(fpath):
            existing_files[f] = read_file(fpath)[:2000]

    file_context = "\n\n".join(
        f"=== {f} ===\n{content}" for f, content in existing_files.items()
    )

    build_prompt = (
        f"PLAN TO IMPLEMENT:\n{plan}\n\n"
        f"PREVIOUS FEEDBACK TO INCORPORATE:\n{feedback or 'None'}\n\n"
        f"ERRORS FROM PREVIOUS RUN TO FIX:\n{error_ctx or 'None'}\n\n"
        f"EXISTING CODE SNIPPETS:\n{file_context}\n\n"
        f"Project root: {PROJECT_ROOT}\n"
        f"Current iteration: {iteration}"
    )

    build_result = call_llm(BUILD_SYSTEM_PROMPT, build_prompt)
    log.append(f"[Build] Build agent result: {len(build_result)} chars")

    return {
        "build_summary": build_result,
        "iteration": iteration,
        "logs": log,
    }


# ─── Test Agent ──────────────────────────────────────────────────────────────

def test_node(state: DevState) -> dict:
    """Run test suites and report results. Interrupt for human review."""
    log = []
    log.append("[Test] Running test suites...")

    results = run_tests()
    log.append(f"[Test] Results: {results['summary']}")

    # ── HUMAN IN LOOP ──
    summary = results["summary"]
    output = results["output"]

    user_input = interrupt({
        "stage": "test",
        "content": f"=== TEST RESULTS ===\n{summary}\n\n{output[-1200:]}",
        "prompt": (
            "\n╔══════════════════════════════════════════════════════════╗\n"
            "║  TEST REVIEW — Enter:                                   ║\n"
            "║  'approve' to continue to validation                    ║\n"
            "║  'abort' to cancel                                      ║\n"
            "║  <any text> as fix instructions for rebuild             ║\n"
            "╚══════════════════════════════════════════════════════════╝\n"
            "> "
        ),
    })

    decision = user_input.strip().lower() if isinstance(user_input, str) else ""
    passed = results["passed"]

    if decision == "approve":
        log.append("[Test] Approved by human")
        return {"test_output": output, "test_passed": passed, "logs": log}
    elif decision == "abort":
        log.append("[Test] Aborted by human")
        return {
            "test_output": output, "test_passed": passed,
            "final_result": "ABORTED", "logs": log,
        }
    else:
        log.append(f"[Test] Fix requested: {user_input[:80]}...")
        if state.get("iteration", 0) >= state.get("max_iterations", 3):
            log.append("[Test] Max iterations reached, aborting")
            return {
                "test_output": output, "test_passed": False,
                "final_result": f"MAX ITERATIONS REACHED ({state.get('iteration', 0)})",
                "logs": log,
            }
        fix_ctx = user_input
        if not results["passed"] and results["failures"]:
            fix_ctx += "\n\nTest failures:\n" + "\n".join(results["failures"])
        return {
            "test_output": output, "test_passed": False,
            "error_context": fix_ctx, "logs": log,
        }


# ─── Validate Agent ──────────────────────────────────────────────────────────

def validate_node(state: DevState) -> dict:
    """Review code quality. Interrupt for human final approval."""
    log = []
    log.append("[Validate] Running quality review...")

    # Read recently created/modified files for review
    recent_files = []
    for root, dirs, files in os.walk(os.path.join(PROJECT_ROOT, "src")):
        if "dev_pipeline" in root or "__pycache__" in root or ".pytest_cache" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                recent_files.append(fpath)

    file_samples = []
    for f in sorted(recent_files)[-5:]:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                content = fh.read()
            file_samples.append(f"=== {os.path.relpath(f, PROJECT_ROOT)} ===\n{content[:1500]}")
        except Exception:
            pass

    review_prompt = (
        f"Task: {state.get('task', '')}\n\n"
        f"Plan implemented:\n{state.get('plan', '')[:500]}\n\n"
        f"Build summary:\n{state.get('build_summary', '')[:500]}\n\n"
        f"Test results:\n{state.get('test_output', '')[:500]}\n\n"
        f"Recent files to review:\n" + "\n\n".join(file_samples)
    )

    report = call_llm(VALIDATE_SYSTEM_PROMPT, review_prompt)
    log.append(f"[Validate] Quality report: {len(report)} chars")

    # ── HUMAN IN LOOP ──
    user_input = interrupt({
        "stage": "validate",
        "content": report,
        "prompt": (
            "\n╔══════════════════════════════════════════════════════════╗\n"
            "║  VALIDATION REVIEW — Enter:                             ║\n"
            "║  'approve' to finish                                    ║\n"
            "║  'abort' to cancel                                      ║\n"
            "║  <any text> as fix instructions for rebuild             ║\n"
            "╚══════════════════════════════════════════════════════════╝\n"
            "> "
        ),
    })

    decision = user_input.strip().lower() if isinstance(user_input, str) else ""

    if decision == "approve":
        log.append("[Validate] Approved by human")
        return {
            "validation_report": report.strip(), "validation_passed": True,
            "final_result": "APPROVED", "logs": log,
        }
    elif decision == "abort":
        log.append("[Validate] Aborted by human")
        return {
            "validation_report": report, "validation_passed": False,
            "final_result": "ABORTED", "logs": log,
        }
    else:
        log.append(f"[Validate] Fix requested: {user_input[:80]}...")
        if state.get("iteration", 0) >= state.get("max_iterations", 3):
            log.append("[Validate] Max iterations reached, aborting")
            return {
                "validation_report": report, "validation_passed": False,
                "final_result": f"MAX ITERATIONS ({state.get('iteration', 0)})",
                "logs": log,
            }
        return {
            "validation_report": report, "validation_passed": False,
            "error_context": user_input, "logs": log,
        }
