"""General RAG Agent Router."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Literal
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class GeneralQuery(BaseModel):
    """Request model for general RAG queries."""
    query: str
    search_strategy: Optional[Literal["semantic", "hybrid", "auto"]] = "auto"
    max_results: Optional[int] = 5
    conversation_history: Optional[List[dict]] = []

class GeneralResponse(BaseModel):
    """Response model for general RAG queries."""
    response: str
    session_id: str
    search_strategy_used: str
    sources: List[dict] = []

@router.get("/")
async def general_info():
    """Information about General RAG agent."""
    return {
        "agent": "General Knowledge RAG",
        "version": "1.0.0",
        "capabilities": [
            "Semantic search",
            "Hybrid search",
            "Knowledge retrieval",
            "Question answering"
        ],
        "search_strategies": ["semantic", "hybrid", "auto"]
    }

@router.post("/chat", response_model=GeneralResponse)
async def general_chat(query: GeneralQuery):
    """General RAG chat endpoint."""
    session_id = str(uuid.uuid4())
    
    try:
        from ...core.agent import get_search_agent
        from ...core.dependencies import AgentDependencies
        from ...config.settings import load_settings
        
        settings = load_settings()
        agent = get_search_agent()
        
        deps = AgentDependencies(
            api_key=settings.llm_api_key,
            session_id=session_id,
            agent_type="general"
        )
        
        # Build prompt with search strategy hint
        strategy_hint = ""
        if query.search_strategy != "auto":
            strategy_hint = f"Use {query.search_strategy} search strategy. "
        
        prompt = f"""{strategy_hint}Search the knowledge base to answer: {query.query}
        
Return up to {query.max_results} relevant results."""
        
        result = await agent.run(prompt, deps=deps)
        response_text = str(result.response) if hasattr(result, 'response') else str(result)
        
        # Determine which strategy was used (from response or tool calls)
        strategy_used = query.search_strategy
        if hasattr(result, '_tool_calls'):
            for tc in result._tool_calls:
                if 'semantic' in tc.name:
                    strategy_used = 'semantic'
                elif 'hybrid' in tc.name:
                    strategy_used = 'hybrid'
        
        return GeneralResponse(
            response=response_text,
            session_id=session_id,
            search_strategy_used=strategy_used,
            sources=[]  # Could extract from tool results
        )
        
    except Exception as e:
        logger.error(f"General RAG agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def general_stream(query: GeneralQuery):
    """Streaming endpoint for General RAG agent."""
    session_id = str(uuid.uuid4())
    
    async def generate():
        try:
            from ...core.agent import get_search_agent
            from ...core.dependencies import AgentDependencies
            from ...config.settings import load_settings
            
            settings = load_settings()
            agent = get_search_agent()
            deps = AgentDependencies(
                api_key=settings.llm_api_key,
                session_id=session_id,
                agent_type="general"
            )
            
            async with agent.iter(query.query, deps=deps) as run:
                async for chunk in run:
                    if hasattr(chunk, 'delta'):
                        yield f"data: {chunk.delta}\n\n"
                        
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/search")
async def direct_search(query: GeneralQuery):
    """Direct search without LLM processing."""
    try:
        from ...tools.tools import semantic_search, hybrid_search
        from ...core.dependencies import AgentDependencies
        from ...config.settings import load_settings
        
        settings = load_settings()
        deps = AgentDependencies(
            api_key=settings.llm_api_key,
            session_id=str(uuid.uuid4())
        )
        
        # Choose search function
        if query.search_strategy == "semantic":
            results = await semantic_search(deps, query.query, query.max_results)
        elif query.search_strategy == "hybrid":
            results = await hybrid_search(deps, query.query, query.max_results)
        else:
            # Auto-select based on query characteristics
            if len(query.query.split()) > 5:
                results = await semantic_search(deps, query.query, query.max_results)
            else:
                results = await hybrid_search(deps, query.query, query.max_results)
        
        return {
            "query": query.query,
            "results": results,
            "strategy_used": query.search_strategy
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))