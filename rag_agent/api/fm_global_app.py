"""FastAPI server for FM Global 8-34 ASRS Expert Agent - deployable on Render."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import asyncio
import json
import uuid

from ..core.fm_global_agent import fm_global_agent
from ..core.dependencies import AgentDependencies
from ..config.settings import load_settings
from pydantic_ai import Agent

app = FastAPI(title="FM Global 8-34 ASRS Expert API", version="1.0.0")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://localhost:3006",
        "https://alleato-ai-dashboard.vercel.app",
        "https://*.vercel.app",
        "https://*.render.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global dependencies - initialized at startup
deps: Optional[AgentDependencies] = None


class FMGlobalQuery(BaseModel):
    """Request model for FM Global queries."""
    query: str
    asrs_topic: Optional[str] = None  # fire_protection, seismic_design, rack_design, etc.
    design_focus: Optional[str] = None
    conversation_history: Optional[List[str]] = []


class FMGlobalResponse(BaseModel):
    """Response model for FM Global queries."""
    response: str
    session_id: str
    tables_referenced: List[str] = []
    figures_referenced: List[str] = []
    asrs_topics: List[str] = []


@app.on_event("startup")
async def startup_event():
    """Initialize dependencies on startup."""
    global deps
    try:
        settings = load_settings()
        deps = AgentDependencies(settings=settings)
        await deps.initialize()
        print("✅ FM Global 8-34 ASRS Expert API initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize FM Global Expert: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global deps
    if deps:
        await deps.cleanup()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "FM Global 8-34 ASRS Expert API"}


@app.get("/health")
async def health_check():
    """Detailed health check."""
    global deps
    
    if not deps:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        settings = deps.settings
        
        # Test database connection
        vector_store_healthy = False
        try:
            if deps.db_pool:
                async with deps.db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                vector_store_healthy = True
        except Exception:
            pass
        
        return {
            "status": "healthy",
            "checks": {
                "api": True,
                "llm_configured": bool(settings.llm_api_key),
                "model": settings.llm_model,
                "vector_store": vector_store_healthy,
                "service": "FM Global 8-34 ASRS Expert"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/chat", response_model=FMGlobalResponse)
async def chat_sync(query: FMGlobalQuery):
    """Synchronous chat endpoint for FM Global queries."""
    global deps
    
    if not deps:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        session_id = str(uuid.uuid4())
        
        # Build context with conversation history
        context = "\n".join(query.conversation_history[-6:]) if query.conversation_history else ""
        
        # Create specialized prompt for FM Global expertise
        prompt_parts = ["As an FM Global 8-34 ASRS expert, provide detailed guidance with specific table and figure references."]
        
        if query.asrs_topic:
            prompt_parts.append(f"Focus on: {query.asrs_topic}")
        
        if query.design_focus:
            prompt_parts.append(f"Design context: {query.design_focus}")
        
        if context:
            prompt_parts.append(f"Previous conversation:\n{context}")
        
        prompt_parts.append(f"User question: {query.query}")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        # Get response from FM Global agent
        result = await fm_global_agent.run(full_prompt, deps=deps)
        response_text = result.data
        
        # Extract table and figure references (simple regex approach)
        import re
        tables = re.findall(r'Table\s+[\d\-\.]+', response_text, re.IGNORECASE)
        figures = re.findall(r'Figure\s+[\d\-\.]+', response_text, re.IGNORECASE)
        
        # Extract ASRS topics mentioned
        asrs_keywords = ['fire protection', 'seismic', 'rack design', 'crane', 'sprinkler', 'clearance', 'spacing']
        topics_found = [keyword for keyword in asrs_keywords if keyword.lower() in response_text.lower()]
        
        return FMGlobalResponse(
            response=response_text,
            session_id=session_id,
            tables_referenced=list(set(tables)),
            figures_referenced=list(set(figures)),
            asrs_topics=topics_found
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


async def stream_fm_global_response(query: FMGlobalQuery) -> AsyncGenerator[str, None]:
    """Stream FM Global agent responses."""
    global deps
    
    if not deps:
        yield f"data: {json.dumps({'error': 'Service not initialized'})}\n\n"
        return
    
    try:
        session_id = str(uuid.uuid4())
        
        # Build specialized FM Global prompt
        context = "\n".join(query.conversation_history[-6:]) if query.conversation_history else ""
        
        prompt_parts = ["As an FM Global 8-34 ASRS expert, provide comprehensive guidance with specific references."]
        
        if query.asrs_topic:
            prompt_parts.append(f"ASRS Focus: {query.asrs_topic}")
        
        if query.design_focus:
            prompt_parts.append(f"Design Focus: {query.design_focus}")
        
        if context:
            prompt_parts.append(f"Conversation Context:\n{context}")
        
        prompt_parts.append(f"User Query: {query.query}")
        prompt_parts.append("\nProvide specific FM Global table/figure references and practical cost optimization guidance.")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        # Send session start
        yield f"data: {json.dumps({'type': 'session_start', 'session_id': session_id})}\n\n"
        
        response_text = ""
        tables_found = []
        figures_found = []
        
        # Stream the agent execution
        async with fm_global_agent.iter(full_prompt, deps=deps) as run:
            async for node in run:
                
                if Agent.is_tool_call_node(node):
                    tool_name = node.data.tool_name
                    tool_friendly_names = {
                        'hybrid_search_fm_global': 'Searching FM Global 8-34 database',
                        'semantic_search_fm_global': 'Semantic search of FM Global content', 
                        'get_fm_global_references': 'Finding tables and figures',
                        'asrs_design_search': 'ASRS design analysis'
                    }
                    tool_display = tool_friendly_names.get(tool_name, tool_name)
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_display})}\n\n"
                
                elif Agent.is_model_response_node(node):
                    # Stream response chunks
                    new_content = node.data.content[len(response_text):]
                    if new_content:
                        response_text += new_content
                        
                        # Extract references as we stream
                        import re
                        tables_found = list(set(re.findall(r'Table\s+[\d\-\.]+', response_text, re.IGNORECASE)))
                        figures_found = list(set(re.findall(r'Figure\s+[\d\-\.]+', response_text, re.IGNORECASE)))
                        
                        yield f"data: {json.dumps({'type': 'content', 'content': new_content})}\n\n"
        
        # Send completion with metadata
        asrs_topics = []
        topic_keywords = ['fire protection', 'seismic', 'rack design', 'crane systems', 'sprinkler', 'clearances']
        for keyword in topic_keywords:
            if keyword.lower() in response_text.lower():
                asrs_topics.append(keyword)
        
        completion_data = {
            'type': 'completion',
            'session_id': session_id,
            'tables_referenced': tables_found,
            'figures_referenced': figures_found,
            'asrs_topics': asrs_topics,
            'total_length': len(response_text)
        }
        
        yield f"data: {json.dumps(completion_data)}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@app.post("/chat/stream")
async def chat_stream(query: FMGlobalQuery):
    """Streaming chat endpoint for FM Global queries."""
    return StreamingResponse(
        stream_fm_global_response(query),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Content-Type-Options": "nosniff"
        }
    )


@app.get("/topics")
async def get_asrs_topics():
    """Get available ASRS topic filters."""
    return {
        "asrs_topics": [
            "fire_protection",
            "seismic_design", 
            "rack_design",
            "crane_systems",
            "clearances",
            "storage_categories",
            "structural_requirements"
        ],
        "design_focuses": [
            "cost_optimization",
            "compliance",
            "performance_based",
            "prescriptive",
            "innovative_solutions"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)