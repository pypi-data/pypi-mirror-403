from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from autosec.agent.state import AgentState
from autosec.agent.llm import get_llm

llm = get_llm(temperature=0)

REFLECTOR_PROMPT = """You are a Lead Code Reviewer. You are reviewing a failed patch attempt.

Input:
- Current Patch Code
- Execution Logs (Test Failure Output)

Task:
1. Identify the root cause of the failure (Syntax Error, Logic Error, Test Assertion Failure).
2. Critically analyze the code logic.
3. Provide specific, actionable instructions to the Coder on how to fix it.
4. Output: A concise paragraph of feedback. Do not write the code yourself.
"""

def reflector_node(state: AgentState) -> Dict[str, Any]:
    print("--- REFLECTOR NODE ---")
    
    current_patch = state.get('current_patch', "")
    test_results = state.get('test_results', "No output recorded.")
    
    messages = [
        SystemMessage(content=REFLECTOR_PROMPT),
        HumanMessage(content=f"PATCH:\n{current_patch}\n\nLOGS:\n{test_results}\n\nPlease provide critique.")
    ]
    
    response = llm.invoke(messages)
    
    return {
        "messages": [response],
        "error_analysis": response.content
    }
