import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from agent_core.llm import GeminiPool

# 1. State Definition
class BuilderState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    tt11_content: str
    db_schema: str
    brainstorm_doc: str
    backend_code: str
    frontend_code: str
    approved: bool
    errors: list[str]

# 2. Nodes
def research_agent(state: BuilderState) -> dict:
    print("Running Research Agent...")
    # Simulated extraction for now. In real run, read the files.
    # We will pass the contents of TT11 and database.py into state initially
    return {"messages": [SystemMessage(content="Research complete. Ready to brainstorm.")]}

def brainstorm_agent(state: BuilderState) -> dict:
    print("Running Brainstorm Agent...")
    
    prompt = f"""
    Design the DB updates and Python calculation logic for the Payroll feature.
    Output a concise design document.
    """
    system_prompt = f"""
    You are the Brainstorm Agent.
    TT11 Content: {state.get('tt11_content', '')[:1000]}...
    DB Schema: {state.get('db_schema', '')[:1000]}...
    """
    doc = GeminiPool.call(
        system_prompt=system_prompt,
        user_prompt=prompt,
        complexity="planning",
        pipeline_name="payroll_builder",
        agent_name="brainstormer"
    )
    return {"brainstorm_doc": doc, "messages": [SystemMessage(content="Brainstorm complete.")]}

def hitl_review(state: BuilderState) -> dict:
    # This node doesn't do much, it's just the interrupt point.
    print("HITL Review checkpoint. Waiting for approval...")
    return {}

def should_execute(state: BuilderState) -> str:
    if state.get("approved"):
        return "backend_builder"
    return END

def backend_builder(state: BuilderState) -> dict:
    print("Running Backend Builder Agent...")
    # LLM generation based on brainstorm_doc
    return {"backend_code": "def calculate_payroll(): pass"}

def frontend_builder(state: BuilderState) -> dict:
    print("Running Frontend Builder Agent...")
    # LLM generation based on backend_code and brainstorm_doc
    return {"frontend_code": "import streamlit as st\ndef show_payroll(): pass"}

def validation_agent(state: BuilderState) -> dict:
    print("Running Validation Agent...")
    # Run tests on generated code
    return {"errors": [], "messages": [SystemMessage(content="Validation passed.")]}

# 3. Build Graph
graph = StateGraph(BuilderState)

graph.add_node("research", research_agent)
graph.add_node("brainstorm", brainstorm_agent)
graph.add_node("hitl", hitl_review)
graph.add_node("backend_builder", backend_builder)
graph.add_node("frontend_builder", frontend_builder)
graph.add_node("validation", validation_agent)

# Edges
graph.add_edge(START, "research")
graph.add_edge("research", "brainstorm")
graph.add_edge("brainstorm", "hitl")

# Conditional edge from HITL
graph.add_conditional_edges("hitl", should_execute, ["backend_builder", END])

graph.add_edge("backend_builder", "frontend_builder")
graph.add_edge("frontend_builder", "validation")
graph.add_edge("validation", END)

# Compile with checkpointer
memory = MemorySaver()
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["hitl"]
)

if __name__ == "__main__":
    print("Builder graph compiled successfully.")
