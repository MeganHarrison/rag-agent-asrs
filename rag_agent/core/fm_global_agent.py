"""FM Global 8-34 ASRS Expert Agent Implementation with enhanced RAG capabilities."""

from pydantic_ai import Agent, RunContext
from typing import Any, Optional
import logging

from ..config.providers import get_llm_model
from .dependencies import AgentDependencies
from .fm_global_prompts import FM_GLOBAL_SYSTEM_PROMPT, get_active_prompt

# Import both standard and enhanced tools
from ..tools.fm_global_tools import (
    semantic_search_fm_global,
    hybrid_search_fm_global,
    get_fm_global_references,
    asrs_design_search
)
from ..tools.fm_global_tools_enhanced import (
    intelligent_fm_global_search,
    analyze_fm_global_query_intent,
    create_contextual_fm_global_embedding
)

logger = logging.getLogger(__name__)

# Global agent instance (lazy-initialized)
_fm_global_agent: Optional[Agent] = None


def get_fm_global_agent(mode: str = None, use_enhanced: bool = True) -> Agent:
    """
    Get or create the FM Global expert agent with lazy initialization.
    
    Args:
        mode: Prompt mode - "expert", "guided", or None (uses default)
        use_enhanced: Whether to use enhanced RAG tools (default: True)
    
    Returns:
        The configured FM Global agent
    """
    global _fm_global_agent
    
    if _fm_global_agent is None:
        try:
            logger.info(f"Initializing FM Global expert agent with mode: {mode or 'default'}, enhanced: {use_enhanced}")
            
            # Get the appropriate prompt based on mode
            system_prompt = get_active_prompt(mode)
            
            # Create the agent
            _fm_global_agent = Agent(
                get_llm_model(),
                deps_type=AgentDependencies,
                system_prompt=system_prompt
            )
            
            # Register enhanced tools if enabled
            if use_enhanced:
                # Primary enhanced tool
                _fm_global_agent.tool(intelligent_fm_global_search)
                _fm_global_agent.tool(analyze_fm_global_query_intent)
                
                # Keep standard tools as fallback
                _fm_global_agent.tool(get_fm_global_references)
                _fm_global_agent.tool(asrs_design_search)
                
                logger.info("FM Global agent initialized with enhanced RAG capabilities")
            else:
                # Register standard FM Global search tools
                _fm_global_agent.tool(semantic_search_fm_global)
                _fm_global_agent.tool(hybrid_search_fm_global)
                _fm_global_agent.tool(get_fm_global_references)
                _fm_global_agent.tool(asrs_design_search)
                
                logger.info("FM Global agent initialized with standard tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize FM Global agent: {e}")
            raise
    
    return _fm_global_agent


# For backward compatibility - direct function reference
fm_global_agent = get_fm_global_agent