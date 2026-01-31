import chainlit as cl
import sys
import os
from langchain_core.messages import HumanMessage

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from autosec.agent.graph import build_graph

# Default to current working directory (where the user runs 'sentinel ui')
# But keep Lab Rat reachable if needed for tests
# For the pitch: "It works on your code" -> verify it looks at CWD.
REPO_DIR = os.getcwd()

@cl.on_chat_start
async def start():
    app = build_graph()
    cl.user_session.set("app", app)
    
    await cl.Message(
        content=f"**Project Sentinel Active.**\n\nWatching repository at:\n`{REPO_DIR}`\n\nI am ready to analyze vulnerabilities."
    ).send()

@cl.on_message
async def main(message: cl.Message):
    app = cl.user_session.get("app")
    
    # 1. Try to find the file mentioned in the prompt, or default to auth.py for demo
    target_file = "auth.py" 
    # In a real tool, the agent would search for files.
    
    auth_file_path = os.path.join(REPO_DIR, target_file)
    file_content = ""
    try:
        if os.path.exists(auth_file_path):
             with open(auth_file_path, "r") as f:
                file_content = f.read()
        else:
             file_content = f"# Context: File {target_file} not found in {REPO_DIR}"
    except Exception as e:
        file_content = f"# Error reading file: {e}"

    # 2. Construct context
    # We inject the file content so the Planner "sees" it (simulating RAG)
    rag_context = (
        f"Vulnerability Report/User Query: {message.content}\n\n"
        f"--- CONTEXT FILES ---\n"
        f"File: auth.py\n"
        f"```python\n{file_content}\n```"
    )

    initial_state = {
        "messages": [HumanMessage(content=message.content)],
        "cve_id": "DEMO-CVE-LAB-RAT", 
        "repo_path": LAB_RAT_DIR, 
        "rag_context": rag_context, 
        "iterations": 0
    }
    
    msg = cl.Message(content="")
    await msg.send()
    
    # Stream execution
    async for output in app.astream(initial_state):
        for node_name, state_update in output.items():
            step_name = node_name.title()
            
            # Formating output
            details = ""
            if "messages" in state_update and state_update["messages"]:
                last_msg = state_update["messages"][-1]
                details = last_msg.content
            elif "test_results" in state_update:
                details = f"**Test Analysis**:\n{state_update.get('test_results')}"
            elif "error_analysis" in state_update:
                details = f"**Critique**:\n{state_update.get('error_analysis')}"
            
            async with cl.Step(name=step_name) as step:
                 step.output = details
            
            # Display Patch
            if node_name == "coder":
                 patch = state_update.get("current_patch", "")
                 if patch:
                     await cl.Message(content=f"**Proposed Patch**:\n```python\n{patch}\n```").send()

    await cl.Message(content="**Remediation Cycle Complete.**").send()
