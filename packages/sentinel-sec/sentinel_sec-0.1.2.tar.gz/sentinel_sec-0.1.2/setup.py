from setuptools import setup, find_packages

setup(
    name="sentinel-sec",
    version="0.1.2",
    packages=find_packages(),
    install_requires=[
        "langgraph",
        "langchain",
        "langchain-groq",
        "langchain-openai",
        "chromadb",
        "libcst",
        "pydantic",
        "qdrant-client",
        "docker",
        "coloredlogs",
        "chainlit",
        "python-dotenv"
    ],
    entry_points={
        "console_scripts": [
            "sentinel=autosec.cli:main",
        ],
    },
    author="Project Sentinel Team",
    description="Autonomous Security Agent that fixes vulnerabilities in your code.",
)
