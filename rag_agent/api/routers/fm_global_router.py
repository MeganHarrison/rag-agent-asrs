"""FM Global 8-34 ASRS Expert Router."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class FMGlobalQuery(BaseModel):
    """Request model for FM Global queries."""
    query: str
    asrs_topic: Optional[str] = None
    design_focus: Optional[str] = None
    conversation_history: Optional[List[str]] = []

class FMGlobalResponse(BaseModel):
    """Response model for FM Global queries."""
    response: str
    session_id: str
    tables_referenced: List[str] = []
    figures_referenced: List[str] = []
    cost_estimate: Optional[float] = None

@router.get("/")
async def fm_global_info():
    """Information about FM Global agent."""
    return {
        "agent": "FM Global 8-34 ASRS Expert",
        "version": "1.0.0",
        "capabilities": [
            "ASRS sprinkler design",
            "FM Global 8-34 compliance",
            "Cost optimization",
            "Figure and table references"
        ]
    }

@router.post("/chat", response_model=FMGlobalResponse)
async def fm_global_chat(query: FMGlobalQuery):
    """FM Global ASRS expert chat endpoint."""
    session_id = str(uuid.uuid4())
    
    try:
        # Lazy import to avoid startup issues
        from ...core.fm_global_agent import get_fm_global_agent
        from ...core.dependencies import AgentDependencies
        from ...config.settings import load_settings
        
        settings = load_settings()
        agent = get_fm_global_agent()
        
        deps = AgentDependencies(
            settings=settings,
            session_id=session_id
        )
        await deps.initialize()
        
        # Build specialized prompt
        prompt = f"""As an FM Global 8-34 ASRS expert:
Topic Focus: {query.asrs_topic or 'general'}
Design Focus: {query.design_focus or 'compliance'}

Question: {query.query}

Provide specific guidance with table/figure references and cost implications."""
        
        result = await agent.run(prompt, deps=deps)
        response_text = str(result.response) if hasattr(result, 'response') else str(result)
        
        # Extract references
        import re
        tables = re.findall(r'Table\s+[\d\-\.]+', response_text, re.IGNORECASE)
        figures = re.findall(r'Figure\s+[\d\-\.]+', response_text, re.IGNORECASE)
        
        # Extract cost if mentioned
        cost_match = re.search(r'\$[\d,]+(?:\.\d{2})?', response_text)
        cost_estimate = float(cost_match.group().replace('$', '').replace(',', '')) if cost_match else None
        
        return FMGlobalResponse(
            response=response_text,
            session_id=session_id,
            tables_referenced=list(set(tables)),
            figures_referenced=list(set(figures)),
            cost_estimate=cost_estimate
        )
        
    except Exception as e:
        logger.error(f"FM Global agent error: {e}")
        # Return fallback response
        return FMGlobalResponse(
            response=get_fm_fallback_response(query.query),
            session_id=session_id,
            tables_referenced=[],
            figures_referenced=[]
        )

@router.post("/chat/stream")
async def fm_global_stream(query: FMGlobalQuery):
    """Streaming endpoint for FM Global agent."""
    session_id = str(uuid.uuid4())
    
    async def generate():
        try:
            from ...core.fm_global_agent import get_fm_global_agent
            from ...core.dependencies import AgentDependencies
            from ...config.settings import load_settings
            
            settings = load_settings()
            agent = get_fm_global_agent()
            deps = AgentDependencies(
                settings=settings,
                session_id=session_id
            )
            await deps.initialize()
            
            prompt = f"FM Global ASRS Expert Query: {query.query}"
            
            async with agent.iter(prompt, deps=deps) as run:
                async for chunk in run:
                    if hasattr(chunk, 'delta'):
                        yield f"data: {chunk.delta}\n\n"
                        
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/topics")
async def get_fm_topics():
    """Get available FM Global topics."""
    return {
        "asrs_topics": [
            "sprinkler_design",
            "container_types",
            "rack_configurations",
            "fire_protection",
            "seismic_requirements",
            "cost_optimization"
        ],
        "design_focuses": [
            "compliance",
            "cost_reduction",
            "performance",
            "safety",
            "efficiency"
        ]
    }

def get_fm_fallback_response(query: str) -> str:
    """Fallback response for FM Global queries."""
    return f"""I understand you're asking about: {query}

For FM Global 8-34 ASRS compliance, key considerations include:
- Sprinkler K-factors (typically K-11.2 or K-16.8)
- Container type impacts (closed-top vs open-top)
- Rack depth and spacing requirements
- Ceiling height limitations

Please consult the FM Global 8-34 document for specific requirements."""