from langgraph.graph import StateGraph, END
from autosec.agent.state import AgentState
from autosec.agent.nodes.planner import planner_node
from autosec.agent.nodes.coder import coder_node
from autosec.agent.nodes.reflector import reflector_node

# Placeholder for the actual test node that uses SandboxRunner
def test_node(state: AgentState) -> dict:
    print("--- TEST NODE (MOCKED) ---")
    # In Phase 3, we will call SandboxRunner here.
    # For now, we mock a failure to test the Reflection loop, or success to finish.
    
    # Mocking a simplistic scenario:
    # If iteration < 2, fail. If iteration >= 2, pass.
    iteration = state.get("iterations", 0)
    
    if iteration < 2:
        return {
            "test_results": "AssertionError: Expected 'sanitized' but got 'raw_input'",
            "error_analysis": None # Reset error analysis on new test run? Data flow depends on graph.
        }
    else:
        return {
            "test_results": "TEST PASS: 5/5 tests passed."
        }

def should_continue(state: AgentState):
    """
    Conditional edge logic.
    If tests passed, go to END.
    If tests failed, go to reflector.
    Check recursion limit (handled by graph, but good to have explicit check).
    """
    results = state.get("test_results", "")
    if "TEST PASS" in results:
        return "end"
    else:
        return "reflect"

def build_graph():
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("test", test_node)
    workflow.add_node("reflector", reflector_node)
    
    # Add Edges
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "test")
    
    # Conditional Edge from Test
    workflow.add_conditional_edges(
        "test",
        should_continue,
        {
            "end": END,
            "reflect": "reflector"
        }
    )
    
    workflow.add_edge("reflector", "coder")
    
    return workflow.compile()
