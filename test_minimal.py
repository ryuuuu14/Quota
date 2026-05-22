"""Test compiled langgraph."""
import os, sys, time
sys.path.insert(0, 'src')
from research_pipeline import ResearchState
from research_pipeline import build_research_pipeline, research_node, brainstorm_node, validate_node

# Test individual nodes
s = ResearchState(query='giam tru gio chuan', regulation_chunks=[], rules_context='', code_snippets=[], db_inspections=[], research_summary='', proposal='', validation_feedback=None, test_output='', test_exit_code=0, iterations=0, logs=[])

t0 = time.time()
r = research_node(s)
print("research_node:", time.time() - t0)
print("  summary len:", len(r.get('research_summary','')))
print("  code_snippets:", len(r.get('code_snippets',[])))

t0 = time.time()
b = brainstorm_node(r)
print("brainstorm_node:", time.time() - t0)

t0 = time.time()
v = validate_node(b)
print("validate_node:", time.time() - t0)
print("  feedback:", v.get('validation_feedback'))

# Now test compiled graph
print("\n--- Testing compiled graph ---")
t0 = time.time()
app = build_research_pipeline()
initial = ResearchState(query='giam tru gio chuan', regulation_chunks=[], rules_context='', code_snippets=[], db_inspections=[], research_summary='', proposal='', validation_feedback=None, test_output='', test_exit_code=0, iterations=0, logs=[])
print("  build graph:", time.time() - t0)
t0 = time.time()
result = app.invoke(initial)
print("  graph invoke:", time.time() - t0)
print("  status:", result.get('validation_feedback'))
