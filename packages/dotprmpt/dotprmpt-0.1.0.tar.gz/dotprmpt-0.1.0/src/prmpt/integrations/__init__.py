"""
prmpt integrations with LLM providers.

Available integrations:
- OllamaEnforcer: Enforcement layer for Ollama
"""

from .ollama import OllamaEnforcer

__all__ = ["OllamaEnforcer"]
