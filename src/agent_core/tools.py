import os
import re
import sys
import subprocess
import glob as _glob
import sqlite3
import json
from typing import List

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_ROOT = os.path.dirname(PROJECT_ROOT)
SRC_DIR = PROJECT_ROOT
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "database.sqlite"))


def read_file(path: str, max_len: int = 8000) -> str:
    """Read file contents. Return error string if not found."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            if max_len:
                return f.read(max_len)
            return f.read()
    except Exception as e:
        return f"[ERROR reading {path}]: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to file, creating parent dirs if needed."""
    try:
        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[OK] Wrote {path} ({len(content)} bytes)"
    except Exception as e:
        return f"[ERROR writing {path}]: {e}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing old_string with new_string."""
    try:
        content = read_file(path, max_len=0)
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
    try:
        matches = _glob.glob(pattern, recursive=True)
        if matches:
            return "\n".join(sorted(matches))
        return "[No matches]"
    except Exception as e:
        return f"[GLOB_ERROR]: {e}"


def grep_files(pattern: str, include: str = "*.py") -> str:
    """Search files for a regex pattern."""
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


def grep_src(pattern: str, context_lines: int = 5) -> str:
    """Search source code for a pattern - optimized version of research pipeline's grep."""
    calcs_path = os.path.join(SRC_DIR, "calculations.py")
    if not os.path.exists(calcs_path):
        # search any calculations.py if path structure differs
        calcs_path = glob_files("**/calculations.py").split("\n")[0]
        if "[No matches]" in calcs_path or not os.path.exists(calcs_path):
            return "[FILE NOT FOUND]"

    try:
        with open(calcs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        matches = []
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line, re.I):
                start = max(0, i - 1 - context_lines)
                end = min(len(lines), i + context_lines)
                matches.append(f"--- lines {start + 1}-{end} ---")
                for j in range(start, end):
                    matches.append(f"{j + 1}:{lines[j].rstrip()}")
                matches.append("")
        return "\n".join(matches[:60])[:3000] or "No matches"
    except Exception as e:
        return f"[GREP_ERROR]: {e}"


def inspect_db(sql: str) -> str:
    """Run a read-only SQL query against the local SQLite database."""
    # Find current database path
    db_path = DB_PATH
    if not os.path.exists(db_path):
        # Try parent dir or data dir
        db_path = os.path.join(WORKSPACE_ROOT, "data", "database.sqlite")
        if not os.path.exists(db_path):
            # Scan for any sqlite/db file
            found = glob_files("**/*.sqlite").split("\n")
            if found and "[No" not in found[0] and os.path.exists(found[0]):
                db_path = found[0]
            else:
                return f"[DB NOT FOUND] Path checked: {DB_PATH} and {db_path}"

    try:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.execute(sql)
            rows = cur.fetchall()
            if cur.description:
                cols = [d[0] for d in cur.description]
                out = {"columns": cols, "rows": rows[:20], "total": len(rows)}
            else:
                out = {"rows_affected": cur.rowcount}
            return json.dumps(out, ensure_ascii=False, default=str)[:3000]
        finally:
            conn.close()
    except Exception as e:
        return f"[DB_ERROR]: {e}"


def run_tests(test_files: List[str] = None) -> dict:
    """Run test files and return structured results."""
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
            all_output.append(f"[SKIP] {os.path.basename(tf)} - not found")
            continue
        try:
            env = {
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
            proc = subprocess.run(
                [sys.executable, "-X", "utf8", tf],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
                cwd=WORKSPACE_ROOT,
                env=env,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            out = stdout + "\n" + stderr
            all_output.append(f"--- {os.path.basename(tf)} ---\n{out[-1500:]}")

            results_match = re.search(
                r"RESULTS:\s*(\d+)\s+passed.*?(\d+)\s+failed", out, re.DOTALL
            )
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


def run_pytest(test_files: List[str]) -> tuple[str, int]:
    """Run pytest on given test files."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *test_files,
                "--tb=line",
                "--no-header",
                "-q",
            ],
            capture_output=True,
            timeout=45,
            encoding="utf-8",
            cwd=WORKSPACE_ROOT,
        )
        output = result.stdout + "\n" + result.stderr
        return output.strip()[-2500:], result.returncode
    except subprocess.TimeoutExpired:
        return "[TIMEOUT] Tests exceeded 45s", -1
    except Exception as e:
        return f"[RUN_ERROR]: {e}", -1


def check_syntax(file_path: str) -> dict:
    """Check Python syntax of a file."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", file_path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            return {"passed": True, "error": ""}
        return {"passed": False, "error": proc.stderr.strip()[:300]}
    except Exception as e:
        return {"passed": False, "error": str(e)}
