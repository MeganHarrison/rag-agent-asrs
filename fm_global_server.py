#!/usr/bin/env python3
"""Entry point for FM Global 8-34 ASRS Expert API server."""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    from rag_agent.api.fm_global_app import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Different port from the generic agent
        log_level="info",
        reload=False
    )