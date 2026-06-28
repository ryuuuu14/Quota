"""Run debug pipeline and print results."""

import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from debug_pipeline import run_debug_pipeline

t0 = time.time()
out = run_debug_pipeline()
elapsed = time.time() - t0

print(f"Elapsed: {elapsed:.1f}s")
print(f"Verdict: {out['verdict']}")
print(f"Iterations: {out['test_run_count']}")
print(f"Console logs: {len(out['console_logs'])}")
print(f"Network errs: {len(out['network_errors'])}")
if out.get("feedback"):
    print(f"Feedback: {out['feedback'][:200]}")
else:
    print("All clean - no feedback")
