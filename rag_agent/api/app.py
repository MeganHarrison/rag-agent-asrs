"""FastAPI server for RAG Agent - deployable on Render."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import asyncio
import json
import uuid
import os
import logging

logger = logging.getLogger(__name__)

from ..core.agent import get_search_agent
from ..core.dependencies import AgentDependencies
from ..config.settings import load_settings
from pydantic_ai import Agent

app = FastAPI(title="RAG Agent API", version="1.0.0")

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
        "https://rag-agent-chat.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load settings
settings = load_settings()

# Request/Response models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: Optional[List[dict]] = None


async def stream_response(
    message: str, 
    conversation_history: List[ChatMessage],
    session_id: str
) -> AsyncGenerator[str, None]:
    """Stream agent responses as Server-Sent Events."""
    
    # Create dependencies
    deps = AgentDependencies(
        api_key=settings.llm_api_key,
        session_id=session_id
    )
    
    # Build context from conversation history
    context = "\n".join([
        f"{msg.role}: {msg.content}" 
        for msg in conversation_history[-6:]
    ]) if conversation_history else ""
    
    prompt = f"""Previous conversation:
{context}

User: {message}

Search the knowledge base to answer the user's question. Choose the appropriate search strategy (semantic_search or hybrid_search) based on the query type. Provide a comprehensive summary of your findings."""

    try:
        # Get the agent and stream the execution
        agent = get_search_agent()
        async with agent.iter(prompt, deps=deps) as run:
            
            tool_calls = []
            response_text = ""
            
            async for node in run:
                
                # Handle tool call nodes
                if Agent.is_tool_call_node(node):
                    for tool_call in node:
                        tool_info = {
                            "tool": tool_call.name,
                            "args": tool_call.args
                        }
                        tool_calls.append(tool_info)
                        
                        # Send tool call event
                        yield f"data: {json.dumps({'type': 'tool_call', 'data': tool_info})}\n\n"
                
                # Handle tool response nodes
                elif Agent.is_tool_return_node(node):
                    for tool_return in node:
                        # Send tool result event
                        yield f"data: {json.dumps({'type': 'tool_result', 'data': {'result': str(tool_return.response)[:200]}})}\n\n"
                
                # Handle model text response
                elif Agent.is_text_chunk_node(node):
                    chunk = node.delta
                    response_text += chunk
                    # Send text chunk event
                    yield f"data: {json.dumps({'type': 'text', 'data': chunk})}\n\n"
            
            # Send final complete event
            yield f"data: {json.dumps({'type': 'complete', 'data': {'response': response_text, 'tool_calls': tool_calls}})}\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"


@app.get("/")
async def root():
    """Basic health check endpoint - no external dependencies."""
    return {
        "status": "healthy", 
        "service": "FM Global Expert RAG Agent",
        "version": "1.0.0",
        "endpoints": ["/", "/health", "/chat", "/chat/stream"]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Create dependencies
    deps = AgentDependencies(
        api_key=settings.llm_api_key,
        session_id=session_id
    )
    
    # Build context
    context = "\n".join([
        f"{msg.role}: {msg.content}" 
        for msg in request.conversation_history[-6:]
    ]) if request.conversation_history else ""
    
    prompt = f"""Previous conversation:
{context}

User: {request.message}

Search the knowledge base to answer the user's question. Choose the appropriate search strategy (semantic_search or hybrid_search) based on the query type. Provide a comprehensive summary of your findings."""
    
    try:
        # Get the agent and run
        agent = get_search_agent()
        result = await agent.run(prompt, deps=deps)
        
        # Extract tool calls from result if available
        tool_calls = []
        if hasattr(result, '_tool_calls'):
            for tc in result._tool_calls:
                tool_calls.append({
                    "tool": tc.name,
                    "args": tc.args
                })
        
        return ChatResponse(
            response=str(result.response) if hasattr(result, 'response') else str(result),
            session_id=session_id,
            tool_calls=tool_calls if tool_calls else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    return StreamingResponse(
        stream_response(
            request.message, 
            request.conversation_history,
            session_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )


@app.get("/health")
async def health_check():
    """Detailed health check with dependency status (lazy check)."""
    
    health_status = {
        "status": "healthy",
        "service": "FM Global Expert RAG Agent",
        "checks": {
            "api": True,
            "environment": {
                "llm_configured": bool(settings.llm_api_key),
                "database_configured": bool(os.getenv('DATABASE_URL')),
                "model": settings.llm_model,
                "provider": settings.llm_provider
            }
        }
    }
    
    # Only test external connections if explicitly requested via query param
    # This prevents startup failures in containerized environments
    if os.getenv('CHECK_EXTERNAL_CONNECTIONS', 'false').lower() == 'true':
        try:
            # Test LLM connection (lazy)
            from ..core.agent import get_search_agent
            agent = get_search_agent()
            health_status["checks"]["llm_connection"] = True
        except Exception as e:
            health_status["checks"]["llm_connection"] = False
            health_status["checks"]["llm_error"] = str(e)
            health_status["status"] = "degraded"
        
        try:
            # Test database connection (lazy)
            from ..core.dependencies import AgentDependencies
            deps = AgentDependencies(
                api_key=settings.llm_api_key,
                session_id="health-check"
            )
            # Just check if we can create deps
            health_status["checks"]["database_ready"] = True
        except Exception as e:
            health_status["checks"]["database_ready"] = False
            health_status["checks"]["database_error"] = str(e)
            health_status["status"] = "degraded"
    else:
        health_status["note"] = "External connection checks disabled for fast startup"
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)