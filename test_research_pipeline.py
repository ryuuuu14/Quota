"""Quick test of research pipeline with real query."""
import os, sys, time
sys.path.insert(0, 'src')
os.environ['SKIP_TESTS'] = '1'

from research_pipeline import run_research_pipeline

t0 = time.time()
out = run_research_pipeline(
    "Giải thích cách tính giảm định mức giờ chuẩn cho nhà giáo nữ nghỉ thai sản theo Điều 10",
    max_iterations=1,
)
elapsed = time.time() - t0

print(f"Time: {elapsed:.1f}s")
print(f"Status: {out['status']}")
print(f"Iterations: {out['iterations']}")
print()
print("=== RESEARCH SUMMARY ===")
print(out['research_summary'])
print()
print("=== PROPOSAL ===")
print(out['proposal'])
print()
if out.get('validation_feedback'):
    print("=== VALIDATION FEEDBACK ===")
    print(out['validation_feedback'])
    print()
print("=== LOGS ===")
for log in out['logs']:
    print(f"  {log}")
