"""Debug - step by step with file output."""
import os, sys
sys.path.insert(0, 'src')

logfile = r'F:\annd\Quota\debug_log.txt'
def log(msg):
    with open(logfile, 'a', encoding='utf-8') as f:
        f.write(str(msg) + '\n')

log('start')

from langgraph.graph import StateGraph, END
from research_pipeline import ResearchState, research_node, brainstorm_node, validate_node, router_condition

log('imported')

workflow = StateGraph(ResearchState)
workflow.add_node('research', research_node)
workflow.add_node('brainstorm', brainstorm_node)
workflow.add_node('validate', validate_node)
workflow.set_entry_point('research')
workflow.add_edge('research', 'brainstorm')
workflow.add_edge('brainstorm', 'validate')
workflow.add_conditional_edges('validate', router_condition, {'retry': 'research', 'abort': END, 'approve': END})

log('building graph')
app = workflow.compile()
log('graph compiled')

initial = ResearchState(
    query='giam tru gio chuan',
    regulation_chunks=[],
    rules_context='',
    code_snippets=[],
    db_inspections=[],
    research_summary='',
    proposal='',
    validation_feedback=None,
    test_output='',
    test_exit_code=0,
    iterations=0,
    logs=[]
)
log('calling invoke')
result = app.invoke(initial)
log('invoke done')
log(f'status: {result.get("validation_feedback")}')
