from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from autosec.agent.state import AgentState
from autosec.agent.llm import get_llm

llm = get_llm(temperature=0)

CODER_PROMPT = """You are an expert Python Developer specializing in secure coding. You will implement the fix proposed by the Architect.

Input:
- CVE ID
- Architectural Plan
- Context (NVD Description)
- (Optional) Feedback from Code Reviewer

Instructions:
1. Return ONLY the python code for the fixed function/component.
2. Do not return the full file unless necessary, but prefer surgical function bodies.
3. Maintain the existing coding style (naming conventions, type hints).
4. If this is a retry, address the Critic's feedback explicitly.
5. Constraint: Your code must be syntactically correct Python 3.9+.

IMPORTANT: Return the code inside a markdown block ```python ... ```.
"""

def coder_node(state: AgentState) -> Dict[str, Any]:
    print("--- CODER NODE ---")
    
    # Extract context
    messages = state['messages']
    # The last message should be the Plan (from Planner) or Feedback (from Reflector)
    last_message = messages[-1]
    
    cve_id = state['cve_id']
    error_analysis = state.get('error_analysis')
    
    # Construct prompt
    prompt_content = f"CVE: {cve_id}\n\n"
    
    if error_analysis:
        prompt_content += f"PREVIOUS ATTEMPT FAILED. \nCRITIC FEEDBACK: {error_analysis}\n\nPlease fix the code."
    else:
        prompt_content += f"PLAN: {last_message.content}\n\nPlease implement the fix."

    # Invoke LLM
    final_messages = [
        SystemMessage(content=CODER_PROMPT),
        HumanMessage(content=prompt_content)
    ]
    
    response = llm.invoke(final_messages)
    
    # Extract code from response (simple stripping for MVP)
    content = response.content
    code_block = content
    if "```python" in content:
        code_block = content.split("```python")[1].split("```")[0].strip()
    elif "```" in content:
        code_block = content.split("```")[1].strip()
        
    return {
        "messages": [response],
        "current_patch": code_block,
        "iterations": state.get("iterations", 0) + 1
    }
