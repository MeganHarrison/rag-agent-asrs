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
    
    if "sprinkler" in query_lower or "k-factor" in query_lower or "pressure" in query_lower:
        return """**FM Global 8-34 Sprinkler Requirements:**

**Shuttle ASRS with Closed-Top Containers:**
- K-factor: K-11.2 or K-16.8 sprinklers typically required
- Spacing: 2.5-5.0 feet depending on rack depth and commodity
- Pressure: Varies by system design and storage height
- Ceiling protection: Required at warehouse ceiling level
- In-rack protection: Generally NOT required for closed-top containers

**Key Sprinkler Guidelines:**
- 4-inch minimum clearance between storage and sprinkler deflectors
- Wet systems preferred where temperature permits (fewer sprinklers needed)
- Enhanced protection may be required for heights over 20 feet
- Consider discharge density requirements based on commodity classification

Consult FM Global 8-34 tables for specific K-factor and pressure requirements for your configuration."""
    
    elif "container" in query_lower or "open" in query_lower or "closed" in query_lower:
        return """**Container Type Impact on Sprinkler Protection:**

**Closed-Top Containers (Recommended):**
- Eliminates need for in-rack sprinklers in most cases
- Ceiling-level sprinklers only (K-11.2 or K-16.8)
- Significant cost savings: $150,000-$300,000 typical
- Simpler system maintenance and testing

**Open-Top or Combustible Containers:**
- Requires in-rack sprinkler protection
- Multiple sprinkler levels may be needed
- Higher water demand and system complexity
- Consider upgrading to closed-top containers for cost optimization

**System Optimization:** Converting to closed-top containers often provides the highest ROI for ASRS fire protection cost reduction."""
    
    elif "cost" in query_lower or "optimization" in query_lower:
        return """**ASRS Sprinkler System Cost Optimization Strategies:**

**High-Impact Savings:**
1. **Use Closed-Top Containers:** Eliminates in-rack sprinklers ($150K-$300K savings)
2. **Wet vs. Dry Systems:** Wet systems require 25-40% fewer sprinklers if temperature permits
3. **Height Optimization:** Keeping storage under 20ft reduces enhanced protection needs

**Medium-Impact Savings:**
1. **Strategic Aisle Widths:** Balance storage density with sprinkler coverage
2. **Zone-Based Protection:** Different protection levels for different commodities
3. **System Type Selection:** ESFR vs. standard sprinklers based on ceiling height

**Typical Cost Breakdown:**
- Standard ASRS sprinkler system: $200K-$500K
- Enhanced systems (high storage/open containers): $400K-$800K
- Optimized systems (closed containers, proper design): $150K-$350K

Focus on container type first - it provides the largest cost impact."""
    
    elif "aisle" in query_lower or "width" in query_lower or "spacing" in query_lower:
        return """**FM Global 8-34 Spacing Requirements:**

**Aisle Width Requirements:**
- Standard commodities: 6-8 ft minimum for sprinkler coverage
- High-challenge storage: 8-10 ft may be required
- Consider crane/SRM clearance in addition to fire protection needs

**Sprinkler Spacing Guidelines:**
- Ceiling sprinklers: Maximum 100-130 sq ft coverage per sprinkler
- In-rack sprinklers (if required): 2.5-5.0 ft spacing depending on rack depth
- Clearance to storage: 4-inch minimum from sprinkler deflectors

**Optimization Note:** Wider aisles can sometimes reduce sprinkler density requirements, but balance with storage efficiency needs."""
    
    else:
        return """**FM Global 8-34 ASRS Sprinkler Protection Overview:**

**System Requirements:**
- K-factor selection: K-11.2 or K-16.8 based on commodity and height
- Pressure requirements: Varies by system design (typically 15-50 psi)
- Coverage: Based on rack configuration and container type
- Water supply: Adequate flow and pressure for design demand

**Key Considerations:**
- Container type has the largest impact on system requirements
- Ceiling height affects enhancement needs
- Commodity classification determines base protection level
- System type (wet/dry) affects sprinkler quantity needed

**Cost Optimization Priority:**
1. Evaluate closed-top containers first
2. Optimize storage height (under 20ft if possible)  
3. Consider wet systems where temperature permits
4. Review aisle widths for sprinkler coverage efficiency

For specific requirements, consult FM Global 8-34 tables and figures or contact a qualified fire protection engineer."""

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