import argparse
import sys
import subprocess
import os
import asyncio
from langchain_core.messages import HumanMessage

# Add project root to path if running as script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agent.graph import build_graph

def run_fix_headless(file_path, issue_desc):
    """Runs the agent headlessly on a specific file."""
    print(f"🕵️ Sentinel starting analysis on: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return

    # Read file content
    with open(file_path, "r") as f:
        content = f.read()

    # Construct context
    issue = issue_desc if issue_desc else "Fix any security vulnerabilities found in this file."
    rag_context = (
        f"Vulnerability Report: {issue}\n\n"
        f"--- TARGET FILE ---\n"
        f"{file_path}\n"
        f"```python\n{content}\n```"
    )

    print("🧠 analyzing...")
    
    # Initialize Graph
    app = build_graph()
    
    initial_state = {
        "messages": [HumanMessage(content=f"Fix vulnerabilities in {file_path}. {issue}")],
        "cve_id": "CLI-HEADLESS-FIX",
        "repo_path": os.path.dirname(os.path.abspath(file_path)),
        "rag_context": rag_context,
        "iterations": 0
    }

    # Run Synchronously (using asyncio.run if needed, but invoke is sync/async compatible usually)
    # Since we are in a sync CLI, let's use invoke (which might block if not async compatible).
    # LangGraph compile() returns a Runnable. invoke() is sync.
    try:
        final_state = app.invoke(initial_state)
        
        patch = final_state.get("current_patch")
        if patch:
            print("\n✅ **PROPOSED PATCH**:\n")
            print(patch)
            print("\n------------------------------------")
            print("Tip: Use 'sentinel apply' (future) or copy-paste above.")
        else:
            print("\n⚠️ No patch generated. Check logs.")
            
    except Exception as e:
        print(f"❌ Error during execution: {e}")

def run_ui():
    """Launches the Chainlit UI."""
    print("🚀 Starting Sentinel Dashboard...")
    # We find the absolute path to app.py
    # Assuming src/ui/app.py structure relative to this file (src/cli.py)
    base_path = os.path.dirname(__file__)
    app_path = os.path.join(base_path, "ui", "app.py")
    
    # Run chainlit command
    cmd = [sys.executable, "-m", "chainlit", "run", app_path, "-w"]
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Sentinel: Autonomous Security Agent")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: ui
    ui_parser = subparsers.add_parser("ui", help="Launch the Web Dashboard")
    
    # Command: version
    version_parser = subparsers.add_parser("version", help="Show version")

    # Command: fix
    fix_parser = subparsers.add_parser("fix", help="Fix a specific file")
    fix_parser.add_argument("file", help="Path to the file to fix")
    fix_parser.add_argument("--message", "-m", help="Description of the vulnerability", default=None)

    args = parser.parse_args()

    if args.command == "ui":
        run_ui()
    elif args.command == "fix":
        run_fix_headless(args.file, args.message)
    elif args.command == "version":
        print("Sentinel v0.1.0 - The Autonomous Security Engineer")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
