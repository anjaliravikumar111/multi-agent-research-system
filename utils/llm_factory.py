"""Returns a configured Groq ChatLLM instance."""
from __future__ import annotations

import os
from langchain_groq import ChatGroq


def get_llm(temperature: float | None = None) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set.")
    return ChatGroq(
        api_key=api_key,
        model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        temperature=temperature if temperature is not None
                    else float(os.getenv("LLM_TEMPERATURE", 0.1)),
    )
