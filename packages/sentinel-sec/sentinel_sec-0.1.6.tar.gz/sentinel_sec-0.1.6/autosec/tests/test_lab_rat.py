import sys
import os
from langchain_core.messages import HumanMessage

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from autosec.agent.graph import build_graph

def run_lab_rat_test():
    print("--- Lab Rat Test: SQL Injection Remediation ---")
    app = build_graph()
    
    # Synthetic CVE Input
    synthetic_prompt = (
        "Critical Vulnerability detected in auth.py. "
        "Type: SQL Injection (CWE-89). "
        "Description: User input is directly concatenated into the SQL query string, "
        "allowing attackers to manipulate the query logic."
    )
    
    # Helper to read the file content for context (usually RAG does this, but we force it here for the test)
    with open("src/tests/lab_rat/auth.py", "r") as f:
        file_content = f.read()
    
    # We add the file context to the RAG context for this test to ensure the Planner sees it
    # independent of the mocked RAG/NVD ingestion.
    rag_context = f"Vulnerability Report: {synthetic_prompt}\n\nAffected File Content:\n{file_content}"

    initial_state = {
        "messages": [HumanMessage(content=synthetic_prompt)],
        "cve_id": "SYNTHETIC-CVE-SQLI",
        "repo_path": os.path.abspath("src/tests/lab_rat"),
        "rag_context": rag_context,
        "iterations": 0
    }
    
    print("Invoking Agent...")
    try:
        final_state = app.invoke(initial_state)
        
        patch = final_state.get("current_patch", "NO PATCH GENERATED")
        print("\n--- FINAL PATCH ---")
        print(patch)
        
        # logical assertion check
        if "?" in patch and "execute(query, (username,))" in patch:
             print("\nSUCCESS: Parameterized query detected.")
        elif "replace" in patch or "strip" in patch:
             print("\nFAILURE: Sanitization detected instead of parameterization.")
        else:
             print("\nWARNING: unexpected output format. Check manually.")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_lab_rat_test()
