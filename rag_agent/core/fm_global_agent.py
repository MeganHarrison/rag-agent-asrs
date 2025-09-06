"""FM Global 8-34 ASRS Expert Agent Implementation with lazy initialization."""

from pydantic_ai import Agent, RunContext
from typing import Any, Optional
import logging

from ..config.providers import get_llm_model
from .dependencies import AgentDependencies
from .fm_global_prompts import FM_GLOBAL_SYSTEM_PROMPT
from ..tools.fm_global_tools import (
    semantic_search_fm_global,
    hybrid_search_fm_global,
    get_fm_global_references,
    asrs_design_search
)

logger = logging.getLogger(__name__)

# Global agent instance (lazy-initialized)
_fm_global_agent: Optional[Agent] = None


def get_fm_global_agent() -> Agent:
    """Get or create the FM Global expert agent with lazy initialization."""
    global _fm_global_agent
    
    if _fm_global_agent is None:
        try:
            logger.info("Initializing FM Global expert agent...")
            
            # Create the agent
            _fm_global_agent = Agent(
                get_llm_model(),
                deps_type=AgentDependencies,
                system_prompt=FM_GLOBAL_SYSTEM_PROMPT
            )
            
            # Register FM Global search tools
            _fm_global_agent.tool(semantic_search_fm_global)
            _fm_global_agent.tool(hybrid_search_fm_global)
            _fm_global_agent.tool(get_fm_global_references)
            _fm_global_agent.tool(asrs_design_search)
            
            logger.info("FM Global expert agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FM Global agent: {e}")
            raise
    
    return _fm_global_agent


# For backward compatibility - create property that returns the agent
fm_global_agent = property(lambda self: get_fm_global_agent())