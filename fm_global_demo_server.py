#!/usr/bin/env python3
"""Demo FM Global server for testing without database."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import asyncio
import json
import uuid

app = FastAPI(title="FM Global 8-34 ASRS Expert API (Demo)", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# Demo responses based on query patterns
DEMO_RESPONSES = {
    "aisle width": {
        "response": """According to FM Global 8-34, aisle width requirements for Class IV commodities depend on several factors:

**Minimum Aisle Widths:**
- **Standard Configuration**: Minimum 8 ft (2.4 m) for Class IV commodities
- **With In-Rack Sprinklers**: Can be reduced to 6 ft (1.8 m) per Table 2-1
- **High-Rise Storage**: 10 ft (3.0 m) minimum for storage heights above 30 ft

**Key Considerations:**
1. **Crane/SRM Operation**: Ensure adequate clearance for equipment operation (typically add 2 ft to minimum)
2. **Fire Department Access**: Consider local fire code requirements
3. **Seismic Zones**: May require additional width per Figure 3-2

**Cost Optimization Tip**: Using in-rack sprinklers allows narrower aisles, maximizing storage density while maintaining protection levels. This can reduce building footprint costs by 15-20%.""",
        "tables": ["Table 2-1", "Table 4-3"],
        "figures": ["Figure 3-2"]
    },
    "table 2-1": {
        "response": """**Table 2-1: Minimum Aisle Width and Spacing Requirements**

This table provides critical spacing requirements for ASRS installations:

**Key Parameters from Table 2-1:**
- Minimum aisle widths based on commodity classification
- Transverse and longitudinal flue spacing requirements
- Clearances from walls and structural members
- Maximum storage heights for different configurations

**Specific Requirements:**
- Class I-III Commodities: 6 ft (1.8 m) minimum aisle
- Class IV Commodities: 8 ft (2.4 m) minimum aisle
- Plastics Group A: 10 ft (3.0 m) minimum aisle
- Transverse flues: 3 in. (76 mm) minimum
- Longitudinal flues: 6 in. (152 mm) for double-row racks

**Design Note**: These are minimum requirements. Consider operational needs and local codes which may require larger dimensions.""",
        "tables": ["Table 2-1"],
        "figures": []
    },
    "cost optimization": {
        "response": """**Cost Optimization Strategies for ASRS Fire Protection:**

Based on FM Global 8-34 guidelines, here are proven strategies to reduce costs while maintaining compliance:

**1. In-Rack Sprinkler Optimization (25-35% savings)**
- Use in-rack sprinklers to reduce ceiling sprinkler density requirements
- Allows narrower aisles (see Table 2-1), increasing storage density
- Consider ESFR sprinklers where ceiling height permits

**2. Zone-Based Protection (20-30% savings)**
- Design protection based on actual commodity hazard per zone
- Avoid over-protecting low-hazard areas
- Reference Table 4-2 for commodity-specific requirements

**3. Performance-Based Design (15-25% savings)**
- Work with FM Global engineers for alternative designs
- Use computational fluid dynamics (CFD) modeling
- Document per Appendix B guidelines

**4. Strategic Rack Configuration (10-20% savings)**
- Optimize rack heights to avoid additional sprinkler levels
- Use solid shelving strategically per Figure 5-1
- Implement automated barriers where appropriate

**5. Water Supply Optimization (15-20% savings)**
- Right-size pumps and tanks based on hydraulic calculations
- Consider on-site water storage vs. municipal upgrades
- Implement water recycling for testing

**Most Impactful**: Combining in-rack sprinklers with optimized aisle widths typically provides the best ROI.""",
        "tables": ["Table 2-1", "Table 4-2"],
        "figures": ["Figure 5-1"]
    },
    "seismic": {
        "response": """**Seismic Design Requirements for ASRS per FM Global 8-34:**

**Bracing Requirements:**
- **Longitudinal bracing**: Required at 40 ft (12.2 m) maximum spacing
- **Transverse bracing**: Every rack row per Figure 6-3
- **Vertical bracing**: At every level above 20 ft (6.1 m) height

**Key Design Criteria from Table 5-1:**
- Seismic Design Category D & E: Full bracing required
- Design for 2/3 of effective seismic weight
- Include commodity weight at 67% of rated load
- Connection capacity: 1.5 times calculated loads

**Critical Components:**
- Base plate anchorage: Minimum 4 anchors per upright
- Beam-to-column connections: Positive mechanical connections required
- Cross-aisle ties: Required for back-to-back racks

**Special ASRS Considerations:**
- Crane rail alignment critical - use isolation joints
- Emergency shutdown systems required
- Post-event inspection protocols per Appendix C

**Cost Tip**: Pre-engineered seismic systems can reduce engineering costs by 40% while ensuring compliance.""",
        "tables": ["Table 5-1"],
        "figures": ["Figure 6-3"]
    }
}


def get_demo_response(query: str) -> dict:
    """Get a demo response based on query keywords."""
    query_lower = query.lower()
    
    if "aisle" in query_lower or "width" in query_lower:
        return DEMO_RESPONSES["aisle width"]
    elif "table 2-1" in query_lower or "spacing" in query_lower:
        return DEMO_RESPONSES["table 2-1"]
    elif "cost" in query_lower or "optimization" in query_lower or "saving" in query_lower:
        return DEMO_RESPONSES["cost optimization"]
    elif "seismic" in query_lower or "bracing" in query_lower:
        return DEMO_RESPONSES["seismic"]
    else:
        # Default response
        return {
            "response": f"""I understand you're asking about: "{query}"

As an FM Global 8-34 ASRS expert, I can help with:
- Fire protection system requirements and design
- Specific table and figure references from FM Global 8-34
- ASRS rack configurations and spacing requirements
- Seismic design and bracing specifications
- Cost optimization strategies

Please ask about specific requirements such as:
- Aisle width requirements for different commodity classes
- In-rack sprinkler design criteria
- Clearance and spacing requirements
- Seismic bracing requirements

For the most accurate information, please specify the commodity classification, storage height, and building configuration relevant to your ASRS system.""",
            "tables": [],
            "figures": []
        }


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "FM Global 8-34 ASRS Expert API (Demo)"}


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "checks": {
            "api": True,
            "mode": "demo",
            "service": "FM Global 8-34 ASRS Expert"
        }
    }


@app.post("/chat", response_model=FMGlobalResponse)
async def chat_sync(query: FMGlobalQuery):
    """Synchronous chat endpoint for FM Global queries."""
    session_id = str(uuid.uuid4())
    
    # Get demo response
    demo_data = get_demo_response(query.query)
    
    return FMGlobalResponse(
        response=demo_data["response"],
        session_id=session_id,
        tables_referenced=demo_data.get("tables", []),
        figures_referenced=demo_data.get("figures", []),
        asrs_topics=["fire_protection", "rack_design"] if demo_data.get("tables") else []
    )


async def stream_demo_response(query: FMGlobalQuery) -> AsyncGenerator[str, None]:
    """Stream demo FM Global responses."""
    session_id = str(uuid.uuid4())
    
    # Send session start
    yield f"data: {json.dumps({'type': 'session_start', 'session_id': session_id})}\n\n"
    
    # Simulate tool call
    yield f"data: {json.dumps({'type': 'tool_call', 'tool': 'Searching FM Global 8-34 database'})}\n\n"
    await asyncio.sleep(0.5)
    
    # Get demo response
    demo_data = get_demo_response(query.query)
    response_text = demo_data["response"]
    
    # Stream response in chunks
    chunk_size = 50
    for i in range(0, len(response_text), chunk_size):
        chunk = response_text[i:i+chunk_size]
        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
        await asyncio.sleep(0.05)  # Simulate typing
    
    # Send completion with metadata
    completion_data = {
        'type': 'completion',
        'session_id': session_id,
        'tables_referenced': demo_data.get("tables", []),
        'figures_referenced': demo_data.get("figures", []),
        'asrs_topics': ["fire_protection", "rack_design"] if demo_data.get("tables") else [],
        'total_length': len(response_text)
    }
    
    yield f"data: {json.dumps(completion_data)}\n\n"


@app.post("/chat/stream")
async def chat_stream(query: FMGlobalQuery):
    """Streaming chat endpoint for FM Global queries."""
    return StreamingResponse(
        stream_demo_response(query),
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
    print("🚀 Starting FM Global 8-34 ASRS Expert Demo Server on port 8003")
    print("📝 This is a demo server with sample responses for testing")
    print("🌐 Open frontend/index.html in your browser to test the chat interface")
    uvicorn.run(app, host="0.0.0.0", port=8003)