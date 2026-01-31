# Project Sentinel 🛡️
### The Autonomous Security Engineer

Project Sentinel is an AI-powered agent that lives in your codebase. It doesn't just find vulnerabilities—it **fixes** them.

Using **Groq (Llama-3)** for high-speed reasoning and **Docker** for secure sandboxed verification, Sentinel patches security holes (like SQL Injection/CWE-89) automatically.

---

## 🚀 How It Works (The Pitch)

1.  **Detect**: You give it a CVE ID or a vulnerability report.
2.  **Plan**: It analyzes your code to understand the attack surface.
3.  **Code**: It writes a surgical patch (preserving your comments/style).
4.  **Verify**: It runs the patch in an isolated Docker sandbox to ensure it works.
5.  **Reflect**: If the test fails, it self-corrects until the code is secure.

---

## 📦 Installation (The Cool Way)

Sentinel is packaged as a standard Python library.

```bash
# 1. Install via pip
pip install sentinel-sec

# 2. Setup Keys
$env:GROQ_API_KEY="gsk_..."
```

---

## ⚡ Quick Start

Just run the command:


```bash
# Launch the Dashboard
sentinel ui

# Or Fix a specific file (Headless Mode)
sentinel fix ./path/to/script.py -m "SQL Injection"
```



2.  **Open Browser**: Go to `http://localhost:8000`.

3.  **Fix a Bug**:
    Type the following command to verify the agent on a demo file:
    > "Critical SQL Injection in auth.py"

4.  **Watch the Magic**:
    The agent will show its thought process, write the code, and present you with the final fix.

---

## 🛠️ Tech Stack
- **LangGraph**: Cyclic Agent Orchestration.
- **Groq**: Llama-3 8B (Instant inference).
- **LibCST**: Surgical Python code modification.
- **Chainlit**: Interactive Chat UI.
- **Docker**: Ephemeral execution sandbox.
