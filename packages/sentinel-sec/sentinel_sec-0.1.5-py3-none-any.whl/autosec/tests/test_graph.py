import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from autosec.agent.graph import build_graph
from langchain_core.messages import HumanMessage

def test_graph_execution():
    print("Initializing Graph (REAL LLM MODE)...")
    app = build_graph()
    
    # Initial State
    initial_state = {
        "messages": [],
        "cve_id": "CVE-2024-TEST",
        "repo_path": "/tmp/test_repo",
        "rag_context": "Simulated RAG Context: SQL Injection in login",
        "iterations": 0
    }
    
    print("Invoking Graph with 'Simulated RAG Context'...")
    # This will actually hit OpenAI if not mocked.
    try:
        # We need to run the graph. .invoke is the method for StateGraph compiled apps.
        # The input is the state.
        final_state = app.invoke(initial_state)
        
        print("\n--- EXECUTION COMPLETE ---")
        print("Final Messages:", len(final_state['messages']))
        print("Last Message Content:\n", final_state['messages'][-1].content)
        
        if "messages" in final_state and len(final_state['messages']) > 0:
            print("Graph execution successful.")
        else:
            print("Graph execution returned empty state?")
            
    except Exception as e:
        print(f"\nCRITICAL FAILURE during execution: {e}")
        # Re-raise to fail the test exit code
        raise e

if __name__ == "__main__":
    test_graph_execution()
