from setuptools import setup, find_packages

# Read the README for PyPI description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sentinel-sec",
    version="0.1.6",
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
    author_email="sentinel@example.com",
    description="🛡️ Autonomous Security Agent that finds AND fixes vulnerabilities in your code.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/project-sentinel",
    project_urls={
        "Bug Tracker": "https://github.com/YOUR_USERNAME/project-sentinel/issues",
        "Documentation": "https://github.com/YOUR_USERNAME/project-sentinel#readme",
        "Source Code": "https://github.com/YOUR_USERNAME/project-sentinel",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="security, vulnerability, ai, llm, code-fix, sast, devsecops, llama, groq",
    python_requires=">=3.10",
)
