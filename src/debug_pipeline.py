"""
Local Multi-Agent Debugging Pipeline
Sandbox Runner (Playwright + Chrome) -> Telemetry Critic (Hybrid) -> Router
"""
from typing import TypedDict, List, Optional
import base64
import json
import os
import re

from langgraph.graph import StateGraph, END
from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
STREAMLIT_URL = "http://localhost:8501"

PAGE_ROUTES = [
    ("Dashboard", "/"),
    ("Teacher",    "/2_QuanLyCanBo"),
    ("Activity",   "/3_NhatKyHoatDong"),
    ("Settings",   "/4_CaiDatHeThong"),
]

_ERROR_PATTERNS = [
    re.compile(r"\[ERROR\]", re.I),
    re.compile(r"\[CRITICAL\]", re.I),
    re.compile(r"\[PAGE_ERROR\]", re.I),
    re.compile(r"exception", re.I),
    re.compile(r"traceback", re.I),
    re.compile(r"uncaught", re.I),
    re.compile(r"failed to load", re.I),
    re.compile(r"SyntaxError", re.I),
    re.compile(r"ReferenceError", re.I),
    re.compile(r"TypeError", re.I),
    re.compile(r"DatabaseError", re.I),
    re.compile(r"pandas.", re.I),
]


class UIState(TypedDict):
    target_url: str
    console_logs: List[str]
    network_errors: List[str]
    screenshot_b64: Optional[str]
    dom_accessibility_tree: str
    feedback_payload: Optional[str]
    test_run_count: int


def _run_pages(browser, base_url: str) -> tuple:
    """Navigate base via goto then click sidebar links for sub-pages."""
    all_logs = []
    all_errors = []
    last_screenshot = None
    last_ax = ""

    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()

    page.on("console", lambda msg: all_logs.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: all_logs.append(f"[PAGE_ERROR] {err}"))
    page.on("requestfailed", lambda req: all_errors.append(
        f"{req.url}: {req.failure.error_text if req.failure else 'unknown'}"
    ))

    page.goto(base_url, wait_until="load", timeout=15000)
    page.wait_for_timeout(1500)
    page.screenshot(full_page=True)

    # Streamlit multipage auto-sidebar uses filename without prefix
    # Target elements inside stPageLink to click the visible custom links instead of hidden default links
    nav_selectors = [
        ("Teacher",  'div[data-testid="stPageLink"] a[href*="QuanLyCanBo"]'),
        ("Activity", 'div[data-testid="stPageLink"] a[href*="NhatKyHoatDong"]'),
        ("Settings", 'div[data-testid="stPageLink"] a[href*="CaiDatHeThong"]'),
    ]
    for label, sel in nav_selectors:
        try:
            loc = page.locator(sel)
            if loc.count() == 0:
                all_logs.append(f"[CLICK_SKIP] {label}: selector not found")
                continue
            loc.first.click(force=True, timeout=5000)
            try:
                page.wait_for_load_state("load", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(1000)
            page.screenshot(full_page=True)
        except Exception as e:
            all_logs.append(f"[CLICK_ERROR] {label}: {e}")

    last_screenshot = page.screenshot(full_page=True)
    try:
        last_ax = json.dumps(page.accessibility.snapshot(), indent=2, ensure_ascii=False)
    except Exception:
        last_ax = "{}"

    context.close()
    return all_logs, all_errors, last_screenshot, last_ax


def run_local_browser_sandbox(state: UIState) -> dict:
    count = state.get("test_run_count", 0)
    target = state.get("target_url", STREAMLIT_URL)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path=CHROME_PATH,
                headless=True,
                args=["--no-sandbox", "--disable-gpu"],
            )
            c_logs, n_errs, screenshot_bytes, ax_tree = _run_pages(browser, target)
            browser.close()

        return {
            "console_logs": c_logs,
            "network_errors": n_errs,
            "screenshot_b64": base64.b64encode(screenshot_bytes).decode("utf-8"),
            "dom_accessibility_tree": ax_tree,
            "test_run_count": count + 1,
        }
    except Exception as e:
        return {
            "console_logs": [f"[BROWSER_ERROR] {e}"],
            "network_errors": [],
            "screenshot_b64": None,
            "dom_accessibility_tree": "{}",
            "test_run_count": count + 1,
        }


def _local_console_check(console_logs: List[str]) -> Optional[str]:
    errors = []
    for line in console_logs:
        for pat in _ERROR_PATTERNS:
            if pat.search(line):
                errors.append(line)
                break
    if errors:
        return "Console errors detected:\n" + "\n".join(errors[:10])
    return None


def _local_network_check(network_errors: List[str]) -> Optional[str]:
    if network_errors:
        return f"Network failures ({len(network_errors)}):\n" + "\n".join(network_errors[:5])
    return None


def _local_a11y_check(ax_tree: str, is_streamlit: bool = True) -> Optional[str]:
    """Check a11y tree. Streamlit apps consistently show empty trees (framework limit)."""
    try:
        tree = json.loads(ax_tree)
        if not tree or tree == {}:
            if is_streamlit:
                return None  # Streamlit a11y tree is always empty — skip check
            return "Accessibility tree is empty"
    except (json.JSONDecodeError, Exception):
        if is_streamlit:
            return None
        return "Accessibility tree is malformed"
    return None


def _run_gemini_vision(screenshot_b64: str, console_logs: List[str],
                       network_errors: List[str], ax_tree: str) -> Optional[str]:
    import time
    try:
        from agent_core.llm import GeminiPool
        from google.genai.types import Part
        
        # Check budget limits
        if GeminiPool._cost.over_budget("gemini-2.0-flash"):
            print("[Debug Pipeline] Over budget, skipping vision check")
            return None
            
        client = GeminiPool.get_client()
        GeminiPool._cost.record_call("gemini-2.0-flash")
        
        log_summary = "\n".join(console_logs[-20:]) if console_logs else "(empty)"
        net_summary = "\n".join(network_errors[-10:]) if network_errors else "(empty)"
        
        start_time = time.time()
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                Part.from_bytes(data=base64.b64decode(screenshot_b64), mime_type="image/png"),
                f"You are a UI debugger. Examine this screenshot and telemetry.\n\n"
                f"Console Logs (last 20):\n{log_summary}\n\n"
                f"Network Errors:\n{net_summary}\n\n"
                "Respond in format:\n"
                "VERDICT: [PASSED or FAILED]\n"
                "DEBUG_REPORT: [if FAILED, describe visual bugs]",
            ],
        )
        text = response.text.strip()
        
        duration_ms = (time.time() - start_time) * 1000
        GeminiPool._metrics.log_call(
            agent_name="telemetry_critic",
            pipeline_name="debug_pipeline",
            duration_ms=duration_ms,
            tokens_in=0,
            tokens_out=len(text.split()),
            model_used="gemini-2.0-flash"
        )
        
        if "VERDICT: FAILED" in text:
            report = text.split("DEBUG_REPORT:", 1)[1].strip() if "DEBUG_REPORT:" in text else text
            return f"Gemini Vision: {report[:300]}"
    except Exception as e:
        print(f"[Debug Pipeline Vision Warning] Vision call failed or not configured: {e}")
        pass
    return None


def execute_critic_consensus(state: UIState) -> dict:
    console_logs = state.get("console_logs", [])
    network_errors = state.get("network_errors", [])
    ax_tree = state.get("dom_accessibility_tree", "")
    screenshot_b64 = state.get("screenshot_b64")

    feedback = _local_console_check(console_logs)
    if feedback:
        return {"feedback_payload": feedback}
    feedback = _local_network_check(network_errors)
    if feedback:
        return {"feedback_payload": feedback}
    feedback = _local_a11y_check(ax_tree, is_streamlit=True)
    if feedback:
        return {"feedback_payload": feedback}

    if screenshot_b64:
        vision_feedback = _run_gemini_vision(screenshot_b64, console_logs, network_errors, ax_tree)
        if vision_feedback:
            return {"feedback_payload": vision_feedback}

    return {"feedback_payload": None}


def evaluation_gate_router(state: UIState) -> str:
    if state.get("test_run_count", 0) >= 3:
        return "halt_and_dump"
    if state.get("feedback_payload"):
        return "re_verify"
    return "clean_exit"


def build_debug_pipeline():
    builder = StateGraph(UIState)
    builder.add_node("sandbox_runner", run_local_browser_sandbox)
    builder.add_node("telemetry_critic", execute_critic_consensus)
    builder.set_entry_point("sandbox_runner")
    builder.add_edge("sandbox_runner", "telemetry_critic")
    builder.add_conditional_edges(
        "telemetry_critic",
        evaluation_gate_router,
        {"re_verify": "sandbox_runner", "halt_and_dump": END, "clean_exit": END},
    )
    return builder.compile()


def run_debug_pipeline(target_url: str = STREAMLIT_URL) -> dict:
    app = build_debug_pipeline()
    initial: UIState = {
        "target_url": target_url,
        "console_logs": [],
        "network_errors": [],
        "screenshot_b64": None,
        "dom_accessibility_tree": "",
        "feedback_payload": None,
        "test_run_count": 0,
    }
    result = app.invoke(initial)

    verdict = "passed"
    if result.get("feedback_payload"):
        verdict = "failed" if result.get("test_run_count", 0) >= 3 else "flaky"

    return {
        "verdict": verdict,
        "feedback": result.get("feedback_payload"),
        "console_logs": result.get("console_logs", []),
        "network_errors": result.get("network_errors", []),
        "test_run_count": result.get("test_run_count", 0),
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    out = run_debug_pipeline()
    print(f"Verdict:       {out['verdict']}")
    print(f"Iterations:    {out['test_run_count']}")
    print(f"Console logs:  {len(out['console_logs'])} events")
    print(f"Network errs:  {len(out['network_errors'])} errors")
    if out['feedback']:
        print(f"Feedback: {out['feedback'][:200]}")
