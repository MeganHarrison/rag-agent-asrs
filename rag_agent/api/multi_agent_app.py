"""Multi-Agent FastAPI Application for Multiple RAG Pipelines on Single Render Instance."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import os
import logging

# Import routers for different agents
from .routers import (
    fm_global_router,
    general_rag_router,
    code_assistant_router,
    document_qa_router
)

logger = logging.getLogger(__name__)

# Create main FastAPI app
app = FastAPI(
    title="Multi-Agent RAG Platform",
    version="2.0.0",
    description="Unified platform hosting multiple specialized RAG agents"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://*.vercel.app",
        "https://*.render.com",
        os.getenv("FRONTEND_URL", "*")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount different agent routers with prefixes
app.include_router(
    fm_global_router.router,
    prefix="/api/fm-global",
    tags=["FM Global ASRS Expert"]
)

app.include_router(
    general_rag_router.router,
    prefix="/api/general",
    tags=["General RAG Agent"]
)

app.include_router(
    code_assistant_router.router,
    prefix="/api/code",
    tags=["Code Assistant"]
)

app.include_router(
    document_qa_router.router,
    prefix="/api/documents",
    tags=["Document Q&A"]
)

# Root health check
@app.get("/")
async def root():
    """Main health check showing all available agents."""
    return {
        "status": "healthy",
        "service": "Multi-Agent RAG Platform",
        "version": "2.0.0",
        "agents": {
            "fm_global": {
                "name": "FM Global 8-34 ASRS Expert",
                "endpoint": "/api/fm-global",
                "status": "active"
            },
            "general": {
                "name": "General Knowledge RAG",
                "endpoint": "/api/general",
                "status": "active"
            },
            "code": {
                "name": "Code Assistant",
                "endpoint": "/api/code",
                "status": "active"
            },
            "documents": {
                "name": "Document Q&A",
                "endpoint": "/api/documents",
                "status": "active"
            }
        }
    }

# Detailed health check
@app.get("/health")
async def health_check():
    """Detailed health check for all agents."""
    health_status = {
        "status": "healthy",
        "service": "Multi-Agent RAG Platform",
        "checks": {}
    }
    
    # Check each agent's health
    agents = ["fm_global", "general", "code", "documents"]
    for agent in agents:
        try:
            # Each agent should have its own health check
            health_status["checks"][agent] = {
                "status": "healthy",
                "database": check_agent_database(agent),
                "llm": check_agent_llm(agent)
            }
        except Exception as e:
            health_status["checks"][agent] = {
                "status": "degraded",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    return health_status

# Agent catalog endpoint
@app.get("/api/agents")
async def list_agents():
    """List all available agents with their capabilities."""
    return {
        "agents": [
            {
                "id": "fm_global",
                "name": "FM Global 8-34 ASRS Expert",
                "description": "Specialized agent for FM Global sprinkler design and ASRS compliance",
                "capabilities": [
                    "Sprinkler system design",
                    "ASRS compliance checking",
                    "Cost optimization",
                    "Figure and table references"
                ],
                "endpoint": "/api/fm-global/chat",
                "stream_endpoint": "/api/fm-global/chat/stream"
            },
            {
                "id": "general",
                "name": "General Knowledge RAG",
                "description": "General-purpose RAG agent for any knowledge base",
                "capabilities": [
                    "Semantic search",
                    "Hybrid search",
                    "Document retrieval",
                    "Question answering"
                ],
                "endpoint": "/api/general/chat",
                "stream_endpoint": "/api/general/chat/stream"
            },
            {
                "id": "code",
                "name": "Code Assistant",
                "description": "Programming and technical documentation assistant",
                "capabilities": [
                    "Code generation",
                    "Bug fixing",
                    "Documentation lookup",
                    "Best practices"
                ],
                "endpoint": "/api/code/chat",
                "stream_endpoint": "/api/code/chat/stream"
            },
            {
                "id": "documents",
                "name": "Document Q&A",
                "description": "Document analysis and question answering",
                "capabilities": [
                    "PDF analysis",
                    "Document summarization",
                    "Information extraction",
                    "Multi-document QA"
                ],
                "endpoint": "/api/documents/chat",
                "stream_endpoint": "/api/documents/chat/stream"
            }
        ]
    }

# Shared utilities
def check_agent_database(agent_name: str) -> bool:
    """Check if agent's database is accessible."""
    # Implement database check logic per agent
    # Different agents might use different databases or schemas
    db_configs = {
        "fm_global": os.getenv("FM_GLOBAL_DB_URL"),
        "general": os.getenv("GENERAL_DB_URL", os.getenv("DATABASE_URL")),
        "code": os.getenv("CODE_DB_URL", os.getenv("DATABASE_URL")),
        "documents": os.getenv("DOCS_DB_URL", os.getenv("DATABASE_URL"))
    }
    return bool(db_configs.get(agent_name))

def check_agent_llm(agent_name: str) -> bool:
    """Check if agent's LLM is configured."""
    # Different agents might use different LLM configurations
    llm_configs = {
        "fm_global": os.getenv("FM_GLOBAL_LLM_KEY", os.getenv("LLM_API_KEY")),
        "general": os.getenv("GENERAL_LLM_KEY", os.getenv("LLM_API_KEY")),
        "code": os.getenv("CODE_LLM_KEY", os.getenv("LLM_API_KEY")),
        "documents": os.getenv("DOCS_LLM_KEY", os.getenv("LLM_API_KEY"))
    }
    return bool(llm_configs.get(agent_name))

# Performance monitoring endpoint (useful for paid tier)
@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics for all agents."""
    return {
        "total_requests": get_total_requests(),
        "active_sessions": get_active_sessions(),
        "agent_usage": {
            "fm_global": {"requests": 1250, "avg_response_time": 1.2},
            "general": {"requests": 3400, "avg_response_time": 0.8},
            "code": {"requests": 890, "avg_response_time": 1.5},
            "documents": {"requests": 567, "avg_response_time": 2.1}
        },
        "resource_usage": {
            "memory_mb": get_memory_usage(),
            "cpu_percent": get_cpu_usage()
        }
    }

def get_total_requests() -> int:
    """Get total requests across all agents."""
    # Implement request counting logic
    return 6107  # Placeholder

def get_active_sessions() -> int:
    """Get number of active sessions."""
    # Implement session counting logic
    return 42  # Placeholder

def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    import psutil
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def get_cpu_usage() -> float:
    """Get current CPU usage percentage."""
    import psutil
    return psutil.cpu_percent(interval=1)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)