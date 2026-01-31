from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from autosec.agent.state import AgentState
from autosec.agent.llm import get_llm

# Initialize LLM (configured via env vars)
llm = get_llm(temperature=0)

PLANNER_PROMPT = """You are a Senior Security Architect. Your goal is to analyze a vulnerability and plan a remediation strategy. 
You have access to the NVD description and the repository file structure.

Guidelines:
1. Analyze: specific vector (Network vs Local).
2. Locate: Identify the file and function likely responsible based on the file list.
3. Strategy: Propose a fix that uses standard libraries. Avoid adding new dependencies unless absolutely necessary.
4. Safety: Do not remove functionality. Focus on sanitization and validation.

Output a structured plan: 
1. Vulnerability Analysis
2. Affected Component
3. Proposed Fix."""

def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    The Planner node analyzes the CVE context and generates a remediation plan.
    """
    print("--- PLANNER NODE ---")
    cve_id = state['cve_id']
    rag_context = state['rag_context']
    
    # Construct the prompt
    messages = [
        SystemMessage(content=PLANNER_PROMPT),
        HumanMessage(content=f"Analyze CVE: {cve_id}\nContext: {rag_context}\n\nPlease provide the remediation plan.")
    ]
    
    # Invoke LLM
    response = llm.invoke(messages)
    
    # Return update to state (append to messages)
    return {"messages": [response]}
