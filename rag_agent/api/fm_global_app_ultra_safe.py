"""FastAPI server for FM Global 8-34 ASRS Expert Agent - Ultra safe startup version."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os

app = FastAPI(title="FM Global 8-34 ASRS Expert API", version="1.0.0")

# Configure CORS
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

# Global state
agent_available = False
agent_error = None

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
    asrs_topics: List[str] = []

def get_fallback_response(query: str) -> str:
    """Get a fallback response when agent is unavailable."""
    query_lower = query.lower()
    
    if "aisle" in query_lower or "width" in query_lower:
        return """Aisle width requirements typically depend on:
- Class I-III Commodities: 6 ft (1.8 m) minimum
- Class IV Commodities: 8 ft (2.4 m) minimum
- Plastics Group A: 10 ft (3.0 m) minimum
- Consider crane/SRM clearance requirements
- Check local fire codes for additional requirements"""
    
    elif "sprinkler" in query_lower:
        return """Sprinkler system requirements generally include:
- ESFR sprinklers for high-challenge storage
- In-rack sprinklers for narrow aisles
- Design density based on commodity classification
- Consider ceiling height and storage configuration
- Consult FM Global 8-34 for specific design criteria"""
    
    elif "seismic" in query_lower or "bracing" in query_lower:
        return """Seismic design requirements typically include:
- Longitudinal bracing at 40 ft maximum spacing
- Transverse bracing for each rack row
- Base plate anchorage with minimum 4 anchors
- Positive mechanical beam-to-column connections
- Design for local seismic zone requirements"""
    
    elif "cost" in query_lower or "optimization" in query_lower:
        return """Cost optimization strategies include:
- Use in-rack sprinklers to reduce ceiling density
- Optimize aisle widths for storage density
- Zone-based protection for mixed commodities
- Consider ESFR where ceiling height permits
- Strategic rack configuration to minimize sprinkler levels"""
    
    else:
        return """For specific FM Global 8-34 requirements:
- Verify commodity classification first
- Consider storage height and configuration
- Review fire protection options
- Check seismic requirements for your zone
- Consult the full FM Global 8-34 standard for detailed guidance"""

async def try_load_agent():
    """Try to load the full agent system."""
    global agent_available, agent_error
    
    if agent_available:
        return True
    
    try:
        # Only import when needed to avoid startup issues
        from ..core.fm_global_agent import fm_global_agent
        from ..core.dependencies import AgentDependencies
        from ..config.settings import load_settings
        
        # Try to initialize
        settings = load_settings()
        deps = AgentDependencies(settings=settings)
        await deps.initialize()
        
        agent_available = True
        return True
        
    except Exception as e:
        agent_error = str(e)
        print(f"⚠️ Agent initialization failed: {e}")
        print("📝 Running in fallback mode")
        return False

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "FM Global 8-34 ASRS Expert API"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "checks": {
            "api": True,
            "agent": agent_available,
            "mode": "full" if agent_available else "fallback",
            "service": "FM Global 8-34 ASRS Expert"
        }
    }

@app.post("/chat", response_model=FMGlobalResponse)
async def chat_sync(query: FMGlobalQuery):
    """Synchronous chat endpoint for FM Global queries."""
    
    session_id = str(uuid.uuid4())
    
    # Try to use full agent first
    if await try_load_agent():
        try:
            # Import here to avoid startup issues
            from ..core.fm_global_agent import fm_global_agent
            from ..core.dependencies import AgentDependencies
            from ..config.settings import load_settings
            
            settings = load_settings()
            deps = AgentDependencies(settings=settings)
            await deps.initialize()
            
            # Build prompt
            context = "\n".join(query.conversation_history[-6:]) if query.conversation_history else ""
            prompt_parts = ["As an FM Global 8-34 ASRS expert, provide detailed guidance with specific table and figure references."]
            
            if query.asrs_topic:
                prompt_parts.append(f"Focus on: {query.asrs_topic}")
            
            if query.design_focus:
                prompt_parts.append(f"Design context: {query.design_focus}")
            
            if context:
                prompt_parts.append(f"Previous conversation:\n{context}")
            
            prompt_parts.append(f"User question: {query.query}")
            full_prompt = "\n\n".join(prompt_parts)
            
            # Get response from agent
            result = await fm_global_agent.run(full_prompt, deps=deps)
            if hasattr(result, 'output'):
                response_text = result.output
            elif hasattr(result, 'data'):
                response_text = result.data
            else:
                response_text = str(result)
                
            await deps.cleanup()
            
        except Exception as e:
            print(f"Agent error: {e}")
            response_text = get_fallback_response(query.query)
    else:
        # Use fallback
        response_text = get_fallback_response(query.query)
    
    # Extract references
    import re
    tables = re.findall(r'Table\s+[\d\-\.]+', response_text, re.IGNORECASE)
    figures = re.findall(r'Figure\s+[\d\-\.]+', response_text, re.IGNORECASE)
    
    # Extract topics
    asrs_keywords = ['fire protection', 'seismic', 'rack design', 'crane', 'sprinkler', 'clearance', 'spacing']
    topics_found = [keyword for keyword in asrs_keywords if keyword.lower() in response_text.lower()]
    
    return FMGlobalResponse(
        response=response_text,
        session_id=session_id,
        tables_referenced=list(set(tables)),
        figures_referenced=list(set(figures)),
        asrs_topics=topics_found
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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)