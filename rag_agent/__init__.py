"""RAG Agent - Semantic Search System.

A semantic search agent powered by Pydantic AI, PostgreSQL with PGVector,
providing intelligent knowledge base search capabilities.
"""

__version__ = "1.0.0"
__author__ = "RAG Agent Team"

# Core exports
from .core.agent import search_agent
from .core.fm_global_agent import fm_global_agent
from .core.dependencies import AgentDependencies
from .config.settings import load_settings

__all__ = [
    "search_agent",
    "fm_global_agent",
    "AgentDependencies", 
    "load_settings",
]