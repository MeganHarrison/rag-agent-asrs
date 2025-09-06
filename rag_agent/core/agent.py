"""Main agent implementation for Semantic Search."""

from pydantic_ai import Agent, RunContext
from typing import Any, Optional
import logging

from ..config.providers import get_llm_model
from .dependencies import AgentDependencies
from .prompts import MAIN_SYSTEM_PROMPT
from ..tools.tools import semantic_search, hybrid_search

logger = logging.getLogger(__name__)

# Global agent instance (lazy-initialized)
_search_agent: Optional[Agent] = None


def get_search_agent() -> Agent:
    """Get or create the search agent with lazy initialization."""
    global _search_agent
    
    if _search_agent is None:
        try:
            logger.info("Initializing search agent...")
            # Initialize the semantic search agent
            _search_agent = Agent(
                get_llm_model(),
                deps_type=AgentDependencies,
                system_prompt=MAIN_SYSTEM_PROMPT
            )
            
            # Register search tools
            _search_agent.tool(semantic_search)
            _search_agent.tool(hybrid_search)
            
            logger.info("Search agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize search agent: {e}")
            raise
    
    return _search_agent


# Maintain backward compatibility
search_agent = property(lambda self: get_search_agent())
