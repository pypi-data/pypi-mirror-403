"""
InsAIts SDK - Local LLM Integration
====================================
Ollama integration for local LLM-enhanced anomaly detection.
"""

import os
import requests
from typing import List, Dict, Optional

# Ollama URL can be configured via environment variable
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def ollama_chat(
    messages: List[Dict[str, str]],
    model: str = "llama3.2",
    temperature: float = 0.7
) -> Optional[str]:
    """
    Send a chat request to local Ollama instance.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Ollama model to use (default: llama3.2)
        temperature: Sampling temperature (0.0-1.0)

    Returns:
        Response text or None if Ollama unavailable
    """
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature}
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("message", {}).get("content", "")
        return None
    except requests.exceptions.RequestException:
        return None


def check_ollama_available() -> bool:
    """Check if Ollama is running locally."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def list_available_models() -> List[str]:
    """List available Ollama models."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        return []
    except requests.exceptions.RequestException:
        return []
