#!/usr/bin/env python3
"""
CLI entry point for the dev pipeline.

Usage:
    python -m src.dev_pipeline "Add Excel bulk upload with 3 columns"
    python -m src.dev_pipeline --iterations 5 "Fix failing tests in calculations"
    python -m src.dev_pipeline --help

Flow:
    1. Plan Agent → interrupt → human approves/rejects
    2. Build Agent → implements code
    3. Test Agent → runs tests → interrupt → human decides
    4. Validate Agent → reviews quality → interrupt → human approves
    5. Report final result
"""

import sys
import argparse
import time

sys.stdout.reconfigure(encoding="utf-8")

from langgraph.types import Command

from .state import DevState
from .graph import build_dev_pipeline


APP_NAME = "🧪 Dev Pipeline"
SEPARATOR = "=" * 60


def print_header(text: str):
    print(f"\n{SEPARATOR}")
    print(f"  {text}")
    print(SEPARATOR)


def run_pipeline(task: str, max_iterations: int = 3) -> dict:
    """Execute the dev pipeline with human-in-loop interaction."""
    graph = build_dev_pipeline()
    thread = {"configurable": {"thread_id": f"dev-{int(time.time())}"}}

    initial: DevState = {
        "task": task,
        "plan": "",
        "plan_approved": False,
        "plan_feedback": "",
        "build_summary": "",
        "test_output": "",
        "test_passed": True,
        "validation_report": "",
        "validation_passed": False,
        "iteration": 0,
        "max_iterations": max_iterations,
        "error_context": "",
        "final_result": "",
        "logs": [],
    }

    print_header(f"{APP_NAME} — Starting")
    print(f"  Task:       {task}")
    print(f"  Iterations: {max_iterations}")
    print("\n  Running... (graph will pause at each checkpoint)")

    # --- Initial run ---
    current_state = initial
    is_resume = False
    last_input = None

    while True:
        try:
            if is_resume:
                # Resume from interrupt
                for s in graph.stream(
                    Command(resume=last_input), thread, stream_mode="values"
                ):
                    current_state = s
            else:
                # First run
                for s in graph.stream(current_state, thread, stream_mode="values"):
                    current_state = s
                is_resume = True

        except Exception as e:
            print(f"\n  [ERROR] Pipeline exception: {e}")
            break

        # Check if we're at an interrupt
        state_snapshot = graph.get_state(thread)
        if state_snapshot.tasks:
            # There's an interrupt — handle it
            interrupt_value = state_snapshot.tasks[0].interrupts[0].value
            stage = interrupt_value.get("stage", "")
            content = interrupt_value.get("content", "")
            prompt = interrupt_value.get("prompt", "> ")

            current_state = state_snapshot.values

            if stage == "plan":
                print_header("📋 STEP 1/4 — PLAN REVIEW")
                print(content)
                last_input = input(prompt)

            elif stage == "test":
                print_header("🧪 STEP 2/4 — TEST RESULTS")
                print(content)
                last_input = input(prompt)

            elif stage == "validate":
                print_header("🔍 STEP 3/4 — VALIDATION REVIEW")
                print(content)
                last_input = input(prompt)

            continue
        else:
            # No more interrupts — pipeline complete
            break

    # --- Final report ---
    if isinstance(current_state, dict):
        final = current_state.get("final_result", "UNKNOWN")
        logs = current_state.get("logs", [])

        print_header(f"{APP_NAME} — Complete")
        print(f"  Result: {final}")
        if final == "APPROVED":
            print(f"  Iterations: {current_state.get('iteration', 0)}")
            plan = current_state.get("plan", "")
            if plan:
                print("\n  Plan:")
                for line in plan.strip().split("\n")[:10]:
                    print(f"    {line}")
                if plan.count("\n") > 10:
                    print(f"    ... ({plan.count(chr(10)) - 10} more lines)")
            build = current_state.get("build_summary", "")
            if build and build[:100] != plan[:100]:
                print("\n  Build summary:")
                for line in build.strip().split("\n")[:6]:
                    print(f"    {line}")
        elif final == "ABORTED":
            print("  Pipeline was cancelled by user.")
        else:
            print(f"  Pipeline ended with status: {final}")

        print(f"\n  ── Logs ({len(logs)} entries) ──")
        for log in logs[-10:]:
            print(f"    {log}")

    return current_state if isinstance(current_state, dict) else {}


def main():
    parser = argparse.ArgumentParser(
        description="LangGraph build-test-validate dev pipeline with human-in-loop"
    )
    parser.add_argument("task", nargs="?", help="Description of the development task")
    parser.add_argument(
        "--iterations",
        "-i",
        type=int,
        default=3,
        help="Maximum build iterations (default: 3)",
    )
    parser.add_argument("--list-tasks", action="store_true", help="Show example tasks")
    parser.add_argument(
        "--interactive",
        "-t",
        action="store_true",
        help="Interactive mode: prompt for task",
    )

    args = parser.parse_args()

    if args.list_tasks:
        print("Example tasks for the dev pipeline:\n")
        examples = [
            "Add Excel bulk upload page with 3-column template, validate teacher names",
            "Fix failing tests in test_compliance.py related to Điều 8 calculations",
            "Add session_teacher_totals table and wire into calculate_teacher_metrics()",
            "Create LangGraph validation pipeline for Excel row-level checks",
            "Add 'data source' badge to Dashboard showing Excel vs manual entry",
            "Lock 3_NhatKyHoatDong.py when session data exists from upload",
        ]
        for i, ex in enumerate(examples, 1):
            print(f'  {i}. python -m src.dev_pipeline "{ex}"')
        return

    task = args.task
    if not task or args.interactive:
        print(f"{APP_NAME} — Interactive mode")
        print("Describe the development task:")
        task = input("> ").strip()

    if not task:
        print("No task provided. Use --help for usage.")
        return

    run_pipeline(task, max_iterations=args.iterations)


if __name__ == "__main__":
    main()
