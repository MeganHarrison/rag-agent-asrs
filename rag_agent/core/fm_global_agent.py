"""FM Global 8-34 ASRS Expert Agent Implementation."""

from pydantic_ai import Agent, RunContext
from typing import Any

from ..config.providers import get_llm_model
from .dependencies import AgentDependencies
from .fm_global_prompts import FM_GLOBAL_SYSTEM_PROMPT
from ..tools.fm_global_tools import (
    semantic_search_fm_global,
    hybrid_search_fm_global,
    get_fm_global_references,
    asrs_design_search
)


# Initialize the FM Global ASRS expert agent
fm_global_agent = Agent(
    get_llm_model(),
    deps_type=AgentDependencies,
    system_prompt=FM_GLOBAL_SYSTEM_PROMPT
)

# Register FM Global search tools
fm_global_agent.tool(semantic_search_fm_global)
fm_global_agent.tool(hybrid_search_fm_global)
fm_global_agent.tool(get_fm_global_references)
fm_global_agent.tool(asrs_design_search)