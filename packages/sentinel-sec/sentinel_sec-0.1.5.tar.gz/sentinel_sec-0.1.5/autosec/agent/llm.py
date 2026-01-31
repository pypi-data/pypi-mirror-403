import os
from langchain_groq import ChatGroq

# Default API key for demo purposes
DEFAULT_GROQ_API_KEY = "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"

def get_llm(temperature=0):
    """
    Returns the configured LLM instance.
    Currently set to use Groq with Llama 3 (8B).
    """
    api_key = os.environ.get("GROQ_API_KEY", DEFAULT_GROQ_API_KEY)
    
    return ChatGroq(
        temperature=temperature,
        model_name="llama-3.1-8b-instant", # Updated to currently supported model 
        # User asked for "7b", Llama 3 8b is the modern equivalent standard on Groq.
        api_key=api_key
    )
