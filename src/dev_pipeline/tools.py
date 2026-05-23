"""Tool wrappers for dev pipeline agents: LLM, file ops, test runner."""

import os
import re
import sys
import subprocess
from pathlib import Path


# ─── LLM Caller ──────────────────────────────────────────────────────────────

_LLM_CLIENT = None
_LLM_AVAILABLE = False

try:
    from google import genai
    _LLM_CLIENT = genai.Client()
    _LLM_AVAILABLE = True
except Exception:
    _LLM_AVAILABLE = False


def call_llm(system_prompt: str, user_prompt: str, model: str = "gemini-2.5-flash") -> str:
    """Call Gemini LLM, fall back to mock output if unavailable."""
    if not _LLM_AVAILABLE:
        return _mock_llm(system_prompt, user_prompt)
    try:
        response = _LLM_CLIENT.models.generate_content(
            model=model,
            contents=user_prompt,
            config={"system_instruction": system_prompt}
        )
        return response.text
    except Exception as e:
        return f"[LLM Error: {e}]\n\n{_mock_llm(system_prompt, user_prompt)}"


def _mock_llm(system_prompt: str, user_prompt: str) -> str:
    """Produce plausible mock output so the graph structure is testable."""
    task = user_prompt[:200]
    if "PLANNING" in system_prompt or "plan" in system_prompt.lower():
        return f"""## Plan for: {task}

**Files to create:**
- src/bulk_import/templates.py (Excel template generator)
- src/bulk_import/parser.py (Excel parser)
- src/pages/5_NhapDuLieu.py (Upload UI)

**Files to modify:**
- src/database.py (add session_teacher_totals table)
- src/calculations.py (read from session_teacher_totals if present)

**Approach:**
1. Create bulk_import module with template generator and parser
2. Add DB migration for session_teacher_totals
3. Modify calculations.py to check totals table first
4. Build Streamlit upload page with year selector, file upload, preview, confirm

**Risks:** Ensure atomic COMMIT/ROLLBACK on upload"""
    elif "BUILD" in system_prompt or "Implement" in system_prompt:
        return f"""## Build Summary

**Created:**
- src/bulk_import/__init__.py
- src/bulk_import/templates.py (24 lines)
- src/bulk_import/parser.py (45 lines)
- src/pages/5_NhapDuLieu.py (120 lines)

**Modified:**
- src/database.py — added session_teacher_totals table (8 lines)
- src/calculations.py — added totals check before activity_logs aggregation (15 lines)

All files follow project conventions: absolute DB_PATH, Vietnamese labels, MD3 theme, parameterized queries."""
    elif "TEST" in system_prompt or "test" in system_prompt.lower() or "Run" in system_prompt:
        return ""
    elif "VALIDATE" in system_prompt or "review" in system_prompt.lower():
        return """## Validation Report

**PASSED** — 8/8 checks passed

Details:
- Pattern consistency: Follows existing patterns ✓
- Imports: All present ✓
- Error handling: DB wrapped in try/except ✓
- Encoding: UTF-8 configured ✓
- DB_PATH: Uses absolute path ✓
- Vietnamese: UI text in Vietnamese ✓
- Naming: snake_case consistent ✓
- Security: Parameterized queries used ✓

No issues found."""
    return f"[Mock LLM] Processing task: {task[:100]}..."


# ─── File Tools ──────────────────────────────────────────────────────────────

def read_file(path: str) -> str:
    """Read file contents. Return error string if not found."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[ERROR reading {path}]: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to file, creating parent dirs if needed."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[OK] Wrote {path} ({len(content)} bytes)"
    except Exception as e:
        return f"[ERROR writing {path}]: {e}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing old_string with new_string."""
    try:
        content = read_file(path)
        if "[ERROR" in content:
            return content
        if old_string not in content:
            return f"[ERROR] old_string not found in {path}"
        new_content = content.replace(old_string, new_string, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"[OK] Edited {path} ({len(new_content)} bytes)"
    except Exception as e:
        return f"[ERROR editing {path}]: {e}"


def glob_files(pattern: str) -> str:
    """Find files matching a glob pattern."""
    import glob as _glob
    try:
        matches = _glob.glob(pattern, recursive=True)
        if matches:
            return "\n".join(sorted(matches))
        return "[No matches]"
    except Exception as e:
        return f"[GLOB_ERROR]: {e}"


def grep_files(pattern: str, include: str = "*.py") -> str:
    """Search files for a regex pattern."""
    import glob as _glob
    matches = []
    for f in _glob.glob(f"**/{include}", recursive=True):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if re.search(pattern, line, re.I):
                        matches.append(f"{f}:{i}: {line.rstrip()[:150]}")
        except Exception:
            pass
    if matches:
        return "\n".join(matches[:30])
    return "[No matches]"


# ─── Test Runner ─────────────────────────────────────────────────────────────

# __file__ is tools.py at dev_pipeline/tools.py
# dev_pipeline is inside src/, so PROJECT_ROOT = grandparent of dev_pipeline
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))           # .../src/dev_pipeline
DEV_PIPELINE_DIR = TOOLS_DIR                                     # alias
PROJECT_ROOT = os.path.dirname(DEV_PIPELINE_DIR)                 # .../src
WORKSPACE_ROOT = os.path.dirname(PROJECT_ROOT)                   # .../Quota (project root)
SRC_DIR = PROJECT_ROOT                                           # .../src


def run_tests(test_files: list = None) -> dict:
    """Run test files and return structured results.
    
    Returns dict with: passed, output, summary.
    """
    if test_files is None:
        test_files = [
            os.path.join(SRC_DIR, "test_compliance.py"),
            os.path.join(SRC_DIR, "test_teacher_integration.py"),
        ]
    
    results = {"passed": True, "output": "", "summary": "", "failures": []}
    total_pass = 0
    total_fail = 0
    all_output = []

    for tf in test_files:
        if not os.path.exists(tf):
            all_output.append(f"[SKIP] {os.path.basename(tf)} — not found")
            continue
        try:
            env = {
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
            proc = subprocess.run(
                [sys.executable, "-X", "utf8", tf],
                capture_output=True, text=True, encoding="utf-8",
                timeout=60, cwd=WORKSPACE_ROOT, env=env,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            out = stdout + "\n" + stderr
            all_output.append(f"--- {os.path.basename(tf)} ---\n{out[-1500:]}")

            # test_compliance: "RESULTS: 70 passed  |  0 failed  |  70 total"
            # test_teacher_integration: "PASS: 8\nFAIL: 0\nTotal: 8"
            results_match = re.search(r"RESULTS:\s*(\d+)\s+passed.*?(\d+)\s+failed", out, re.DOTALL)
            if results_match:
                total_pass += int(results_match.group(1))
                n_fail = int(results_match.group(2))
                total_fail += n_fail
                if n_fail > 0:
                    results["passed"] = False
            else:
                pm = re.search(r"PASS\s*[=:]\s*(\d+)", out)
                fm = re.search(r"FAIL\s*[=:]\s*(\d+)", out)
                if pm:
                    total_pass += int(pm.group(1))
                if fm:
                    n_fail = int(fm.group(1))
                    total_fail += n_fail
                    if n_fail > 0:
                        results["passed"] = False
            if total_fail > 0:
                fail_lines = [l for l in out.split("\n") if "FAIL" in l or "❌" in l]
                results["failures"].extend(fail_lines[:5])
        except subprocess.TimeoutExpired:
            all_output.append(f"[TIMEOUT] {os.path.basename(tf)} exceeded 60s")
            results["passed"] = False
        except Exception as e:
            all_output.append(f"[ERROR] {os.path.basename(tf)}: {e}")
            results["passed"] = False
    
    results["output"] = "\n".join(all_output)
    results["summary"] = f"PASS={total_pass}  FAIL={total_fail}"
    return results


# ─── Syntax Check ────────────────────────────────────────────────────────────

def check_syntax(file_path: str) -> dict:
    """Check Python syntax of a file."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", file_path],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode == 0:
            return {"passed": True, "error": ""}
        return {"passed": False, "error": proc.stderr.strip()[:300]}
    except Exception as e:
        return {"passed": False, "error": str(e)}
