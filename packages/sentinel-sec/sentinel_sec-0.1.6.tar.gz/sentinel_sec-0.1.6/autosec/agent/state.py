from typing import TypedDict, List, Annotated, Optional
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    State schema for the Project Sentinel autonomous agent.
    
    Attributes:
        messages: The chat history, using operator.add to append new messages.
        cve_id: The ID of the vulnerability being remediated.
        repo_path: Absolute path to the repository on disk.
        rag_context: Data retrieved from NVD (serialized narrative).
        current_patch: The current python code proposed by the Coder.
        test_results: Output from the Sandbox execution (stdout/stderr).
        error_analysis: Logic critique from the Reflector node.
        iterations: Loop counter to prevent infinite recursion (redundant with graph limit, but good for logic).
    """
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Context
    cve_id: str
    repo_path: str
    rag_context: str
    
    # Execution Artifacts
    current_patch: Optional[str]
    test_results: Optional[str]
    error_analysis: Optional[str]
    
    # Control
    iterations: int
